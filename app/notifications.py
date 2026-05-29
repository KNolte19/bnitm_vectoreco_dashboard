"""Email notification service for sensor warnings."""
import json
import logging
import os
import smtplib
import threading
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)

SUBSCRIPTIONS_FILE = Path(__file__).parent.parent / "data" / "subscriptions.json"
ALERT_STATE_FILE = Path(__file__).parent.parent / "data" / "alert_state.json"

# SMTP settings read from environment variables:
# SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD, SMTP_FROM


def _load_json(path: Path, default):
    """Load JSON from a file, returning default if missing or invalid."""
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("Could not load %s: %s", path, e)
    return default


def _save_json(path: Path, data) -> None:
    """Save data as JSON to a file, creating parent directories if needed."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Could not save %s: %s", path, e)


def save_subscription(
    email: str,
    temp_warnings: bool,
    temp_threshold: float,
    conn_warnings: bool,
    grace_period_hours: float,
) -> None:
    """Save or update a subscription in the subscriptions file.

    Args:
        email: Subscriber's email address.
        temp_warnings: Whether to receive temperature warnings.
        temp_threshold: Temperature deviation threshold in °C.
        conn_warnings: Whether to receive connectivity warnings.
        grace_period_hours: Hours to wait before sending an alert.
    """
    subscriptions = load_subscriptions()
    entry = {
        "email": email,
        "temp_warnings": bool(temp_warnings),
        "temp_threshold": float(temp_threshold),
        "conn_warnings": bool(conn_warnings),
        "grace_period_hours": float(grace_period_hours),
    }
    # Update existing entry for the same email, or append
    for i, sub in enumerate(subscriptions):
        if sub.get("email") == email:
            subscriptions[i] = entry
            break
    else:
        subscriptions.append(entry)
    _save_json(SUBSCRIPTIONS_FILE, subscriptions)


def load_subscriptions() -> list:
    """Load and return the list of subscriptions.

    Returns:
        List of subscription dicts.
    """
    return _load_json(SUBSCRIPTIONS_FILE, [])


def send_warning_email(to_email: str, subject: str, body: str) -> None:
    """Send a warning email via SMTP using STARTTLS.

    SMTP settings are read from environment variables:
        SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD, SMTP_FROM

    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        body: Plain-text email body.

    Raises:
        ValueError: If required SMTP credentials are missing.
        smtplib.SMTPException: On SMTP transmission errors.
    """
    host = os.environ.get("SMTP_HOST", "").strip()
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("SMTP_FROM", user).strip()

    if not host:
        raise ValueError("SMTP_HOST is not configured")
    if not user:
        raise ValueError("SMTP_USER is not configured")
    if not password:
        raise ValueError("SMTP_PASSWORD is not configured")

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(user, password)
            smtp.sendmail(from_addr, to_email, msg.as_string())
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending to %s: %s", to_email, exc)
        raise


def check_and_send_alerts() -> None:
    """Check for active warnings and send alert emails to subscribers.

    Loads alert state from ``alert_state.json`` to track when each warning
    first appeared, respects each subscriber's grace period, and avoids
    sending duplicate emails until the issue clears and reappears.
    """
    # Lazy imports to avoid circular dependencies at module load time
    from app.data import repository  # noqa: PLC0415
    from app.ingestion.parser import TREATMENT_DELTA_RANGES  # noqa: PLC0415

    now = datetime.utcnow()
    alert_state: dict = _load_json(ALERT_STATE_FILE, {})

    # ── Connectivity warnings ──────────────────────────────────────────────
    gap_issues = repository.check_sensor_gaps(gap_threshold_hours=3.0)
    conn_warning_active = len(gap_issues) > 0
    conn_warning_details = "; ".join(
        f"Sensor {i['sensor_id']} ({i['location']}): {i['max_gap_hours']}h"
        for i in gap_issues
    )

    if conn_warning_active:
        if "connectivity" not in alert_state:
            alert_state["connectivity"] = {
                "first_seen": now.isoformat(),
                "notified": [],
            }
    else:
        alert_state.pop("connectivity", None)

    # ── Temperature warnings ───────────────────────────────────────────────
    df_latest = repository.fetch_latest_per_location_treatment()
    active_temp_keys: set = set()

    if not df_latest.empty:
        for _, row in df_latest.iterrows():
            t_id = int(row["treatment_id"])
            if t_id not in TREATMENT_DELTA_RANGES:
                continue
            min_delta, max_delta = TREATMENT_DELTA_RANGES[t_id]
            expected_mid = (min_delta + max_delta) / 2.0
            actual_delta = float(row["treatment_temp"]) - float(row["control_temp"])
            deviation = abs(actual_delta - expected_mid)

            key = f"temp_{int(row['sensor_id'])}_{t_id}"
            active_temp_keys.add(key)
            if key not in alert_state:
                alert_state[key] = {
                    "first_seen": now.isoformat(),
                    "deviation": deviation,
                    "sensor_id": int(row["sensor_id"]),
                    "treatment_id": t_id,
                    "location": str(row["location"]),
                    "notified": [],
                }
            else:
                alert_state[key]["deviation"] = deviation

    # Clear resolved temperature warnings
    for key in list(alert_state.keys()):
        if key.startswith("temp_") and key not in active_temp_keys:
            del alert_state[key]

    # ── Notify subscribers ─────────────────────────────────────────────────
    subscriptions = load_subscriptions()
    for sub in subscriptions:
        email = sub.get("email", "")
        if not email:
            continue
        grace_hours = float(sub.get("grace_period_hours", 24))
        messages = []

        # Connectivity check
        if sub.get("conn_warnings") and conn_warning_active:
            state = alert_state.get("connectivity", {})
            first_seen = datetime.fromisoformat(state.get("first_seen", now.isoformat()))
            hours_active = (now - first_seen).total_seconds() / 3600.0
            if hours_active >= grace_hours and email not in state.get("notified", []):
                messages.append(f"Connectivity warning: {conn_warning_details}")
                state.setdefault("notified", []).append(email)

        # Temperature check
        if sub.get("temp_warnings"):
            threshold = float(sub.get("temp_threshold", 2.5))
            for key, state in alert_state.items():
                if not key.startswith("temp_"):
                    continue
                deviation = float(state.get("deviation", 0.0))
                if deviation < threshold:
                    continue
                first_seen = datetime.fromisoformat(state.get("first_seen", now.isoformat()))
                hours_active = (now - first_seen).total_seconds() / 3600.0
                if hours_active >= grace_hours and email not in state.get("notified", []):
                    messages.append(
                        f"Temperature warning for sensor {state.get('sensor_id')} "
                        f"at {state.get('location')} (treatment {state.get('treatment_id')}): "
                        f"deviation {deviation:.1f}°C exceeds threshold {threshold:.1f}°C"
                    )
                    state.setdefault("notified", []).append(email)

        if messages:
            alert_types = []
            if any("Connectivity" in m for m in messages):
                alert_types.append("Connectivity")
            if any("Temperature" in m for m in messages):
                alert_types.append("Temperature")
            subject = "VectorEco Dashboard Alert: " + " & ".join(alert_types)
            body = "\n\n".join(messages)
            try:
                send_warning_email(
                    email,
                    subject,
                    body,
                )
                logger.info("Alert email sent to %s", email)
            except Exception as exc:
                logger.error("Failed to send alert email to %s: %s", email, exc)

    _save_json(ALERT_STATE_FILE, alert_state)


def start_alert_scheduler(interval_minutes: int = 30) -> None:
    """Start a background timer loop that calls :func:`check_and_send_alerts` repeatedly.

    The scheduler runs as a daemon thread so it will not prevent the process
    from exiting.

    Args:
        interval_minutes: How often to run the alert check (default: 30 minutes).
    """
    def _run() -> None:
        try:
            check_and_send_alerts()
        except Exception as exc:
            logger.error("Alert check failed: %s", exc)
        finally:
            timer = threading.Timer(interval_minutes * 60, _run)
            timer.daemon = True
            timer.start()

    # Start first run after one full interval to let the app finish starting
    first_timer = threading.Timer(interval_minutes * 60, _run)
    first_timer.daemon = True
    first_timer.start()
    logger.info("Alert scheduler started (interval: %d min)", interval_minutes)
