import json
import math
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ----------------------------
# Sensor configuration (matches sensor_config.yaml)
# ----------------------------
SENSOR_ID = 1
SENSOR_LOCATION = "BNITM Garden Testing"

# Treatment target deltas (centre of the allowed range)
TREATMENT_TARGETS = {
    1: 1.5,   # +1.5°C
    2: 3.0,   # +3°C
    3: 4.5,   # +4.5°C
}


def _iso(dt: datetime) -> str:
    """UTC ISO string without timezone suffix (naive UTC)."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.replace(microsecond=0).isoformat()


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def generate_window(
    *,
    rng: random.Random,
    sensor_id: int,
    window_start: datetime,
    window_end: datetime,
    freq_minutes: int = 15,
) -> dict:
    """
    Create one realistic measurement window record in the new JSON format.

    Generates a realistic sinusoidal control temperature and realistic
    treatment temperatures for each of the three treatments.
    """
    # Daily air/control temperature cycle (sinusoid) + small random noise
    seconds_in_day = 24 * 3600
    t = (
        window_start.hour * 3600 + window_start.minute * 60 + window_start.second
    ) / seconds_in_day
    phase_shift = 0.625  # peak ~15:00
    daily = math.sin(2 * math.pi * (t - phase_shift))

    base_temp = 22.0
    amplitude = 6.0
    control_noise = rng.normalvariate(0, 0.3)
    control_temp = _clamp(base_temp + amplitude * daily + control_noise, 5.0, 45.0)

    # Number of observations in this window
    n_observations = freq_minutes  # one per minute

    treatments = []
    for tid, target_delta in TREATMENT_TARGETS.items():
        # Small jitter around target delta (simulate real-world deviation)
        delta_noise = rng.normalvariate(0, 0.15)
        treatment_temp = _clamp(control_temp + target_delta + delta_noise, 5.0, 55.0)

        # Packet counts (mostly perfect, occasional drops)
        expected_packets = n_observations
        drop_rate = rng.uniform(0.0, 0.05)  # up to 5% packet loss
        received_packets = max(0, int(expected_packets * (1.0 - drop_rate)))
        connection_quality = round(
            received_packets / expected_packets if expected_packets > 0 else 0.0, 3
        )

        treatments.append({
            "treatment_id": tid,
            "mean_control_temp": round(control_temp, 2),
            "mean_treatment_temp": round(treatment_temp, 2),
            "received_packets": received_packets,
            "expected_packets": expected_packets,
            "connection_quality": connection_quality,
        })

    return {
        "site_id": sensor_id,
        "window_start": _iso(window_start),
        "window_end": _iso(window_end),
        "n_observations": n_observations,
        "treatments": treatments,
    }


def write_mock_json_inbox(
    *,
    out_dir: str = "data/inbox",
    start_utc: str = "2026-01-01T00:00:00Z",
    duration_hours: int = 24,
    freq_minutes: int = 15,
    seed: int = 42,
    include_duplicates: bool = False,
    duplicate_rate: float = 0.01,
) -> int:
    """
    Generate mock JSON window files into out_dir for the single configured sensor.

    - duration_hours + freq_minutes define the time grid
    - Each file represents one 15-minute window for all three treatments
    - include_duplicates: optionally emit exact duplicates to test deduplication
    """
    rng = random.Random(seed)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    start_dt = datetime.fromisoformat(start_utc.replace("Z", "+00:00")).astimezone(timezone.utc)
    step = timedelta(minutes=freq_minutes)
    total_steps = int((duration_hours * 60) / freq_minutes)

    written = 0

    for step_idx in range(total_steps):
        window_start = start_dt + step_idx * step
        window_end = window_start + step

        entry = generate_window(
            rng=rng,
            sensor_id=SENSOR_ID,
            window_start=window_start,
            window_end=window_end,
            freq_minutes=freq_minutes,
        )

        fname = (
            f"mock_s{SENSOR_ID}_"
            f"{window_start.strftime('%Y%m%dT%H%M%SZ')}.json"
        )
        fpath = out / fname
        with fpath.open("w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)
        written += 1

        if include_duplicates and rng.random() < duplicate_rate:
            dup_name = (
                f"DUPE_mock_s{SENSOR_ID}_"
                f"{window_start.strftime('%Y%m%dT%H%M%SZ')}_{rng.randint(1000,9999)}.json"
            )
            dup_path = out / dup_name
            with dup_path.open("w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)
            written += 1

    return written


if __name__ == "__main__":
    count = write_mock_json_inbox(
        out_dir="data/inbox",
        start_utc="2026-01-01T00:00:00Z",
        duration_hours=10 * 24,  # 10 days
        freq_minutes=15,
        seed=42,
        include_duplicates=False,
    )
    print(f"Wrote {count} JSON files to data/inbox")
