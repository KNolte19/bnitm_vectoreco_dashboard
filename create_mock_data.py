import json
import math
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ----------------------------
# Configuration (edit as needed)
# ----------------------------
DEFAULT_LOCATIONS = [
    "Renke Garden 1", "Renke Garden 2", "Renke Garden 3", "Renke Garden 4",
    "Renke Garden 5", "Renke Garden 6", "Renke Garden 7", "Renke Garden 8",
    "Renke Garden 9", "Renke Garden 10", "Renke Garden 11", "Renke Garden 12",
    "Renke Garden 13", "Renke Garden 14", "Renke Garden 15", "Renke Garden 16",
    "Renke Garden 17", "Renke Garden 18", "Renke Garden 19", "Renke Garden 20",
]

def _iso_z(dt: datetime) -> str:
    """UTC ISO string with Z suffix."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _clamp(x, lo, hi):
    return max(lo, min(hi, x))

def _weighted_connection_quality(rng: random.Random) -> int:
    # Bias toward good connection (3-4), still allow 1-2.
    # probabilities: 1:5%, 2:15%, 3:40%, 4:40%
    r = rng.random()
    if r < 0.05:
        return 1
    if r < 0.20:
        return 2
    if r < 0.60:
        return 3
    return 4

def generate_measurement(
    *,
    rng: random.Random,
    sensor_id: int,
    container_id: int,
    location: str,
    timestamp: datetime,
    container_offset_c: float,
) -> dict:
    """
    Create one realistic measurement record.
    """
    # Daily air temperature cycle (sinusoid) + small random noise
    # Peak around mid-afternoon; min around early morning.
    seconds_in_day = 24 * 3600
    t = (timestamp.hour * 3600 + timestamp.minute * 60 + timestamp.second) / seconds_in_day
    # Shift phase so peak ~15:00 (0.625 of day)
    phase_shift = 0.625
    daily = math.sin(2 * math.pi * (t - phase_shift))

    # Base climate; adjust to taste
    air_base = 18.0
    air_amp = 7.0
    air_noise = rng.normalvariate(0, 0.6)
    temperature_air = air_base + air_amp * daily + air_noise

    # Water temperature is smoother/lagging: smaller amplitude + correlated with air
    water_base = 17.0
    water_amp = 3.5
    water_noise = rng.normalvariate(0, 0.25)
    temperature_water = water_base + water_amp * daily + water_noise + container_offset_c

    # Keep plausible bounds
    temperature_air = _clamp(temperature_air, -5.0, 40.0)
    temperature_water = _clamp(temperature_water, 0.0, 35.0)

    connection_quality = _weighted_connection_quality(rng)

    # received_at: a few seconds after timestamp, worse connection => larger delay
    delay_seconds = rng.randint(2, 8) + (4 - connection_quality) * rng.randint(0, 4)
    received_at = timestamp + timedelta(seconds=delay_seconds)

    return {
        "sensor_id": sensor_id,
        "container_id": container_id,
        "location": location,
        "timestamp": _iso_z(timestamp),
        "received_at": _iso_z(received_at),
        "temperature_water": round(temperature_water, 2),
        "temperature_air": round(temperature_air, 2),
        "connection_quality": int(connection_quality),
    }

def write_mock_json_inbox(
    *,
    out_dir: str = "data/inbox",
    stations: int = 20,
    containers_per_station: int = 4,
    start_utc: str = "2024-06-01T00:00:00Z",
    duration_hours: int = 24,
    freq_minutes: int = 5,
    seed: int = 42,
    locations=None,
    include_duplicates: bool = False,
    duplicate_rate: float = 0.01,
) -> int:
    """
    Generate JSON files into out_dir.

    - stations: number of sensor stations
    - containers_per_station: fixed at 4 for your case
    - duration_hours + freq_minutes define the time grid
    - include_duplicates: optionally emit exact duplicates (same sensor_id, container_id, timestamp)
      to test "ignore duplicates" behavior. Default False.
    """
    rng = random.Random(seed)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if locations is None:
        locations = DEFAULT_LOCATIONS[:stations]
    if len(locations) < stations:
        raise ValueError("Provide at least `stations` locations.")

    # Parse start time
    start_dt = datetime.fromisoformat(start_utc.replace("Z", "+00:00")).astimezone(timezone.utc)

    step = timedelta(minutes=freq_minutes)
    total_steps = int((duration_hours * 60) / freq_minutes)

    written = 0

    # Pre-create container IDs per station (numbered 1-4 for all sensors)
    station_container_ids = {
        sensor_id: [i + 1 for i in range(containers_per_station)]
        for sensor_id in range(1, stations + 1)
    }

    # Give each container a slight stable offset (some containers run warmer/cooler)
    container_offsets = {}
    for sensor_id in range(1, stations + 1):
        for cid in station_container_ids[sensor_id]:
            container_offsets[(sensor_id, cid)] = rng.normalvariate(0.0, 0.4)

    for step_idx in range(total_steps):
        ts = start_dt + step_idx * step

        for sensor_id in range(1, stations + 1):
            location = locations[sensor_id - 1]
            for cid in station_container_ids[sensor_id]:
                entry = generate_measurement(
                    rng=rng,
                    sensor_id=sensor_id,
                    container_id=cid,
                    location=location,
                    timestamp=ts,
                    container_offset_c=container_offsets[(sensor_id, cid)],
                )

                # Unique filename per measurement (avoid overwriting)
                fname = (
                    f"mock_s{sensor_id}_c{cid}_"
                    f"{ts.strftime('%Y%m%dT%H%M%SZ')}.json"
                )
                fpath = out / fname
                with fpath.open("w", encoding="utf-8") as f:
                    json.dump(entry, f, indent=2)
                written += 1

                # Optional: emit an exact duplicate sometimes
                if include_duplicates and rng.random() < duplicate_rate:
                    dup_name = (
                        f"DUPE_mock_s{sensor_id}_c{cid}_"
                        f"{ts.strftime('%Y%m%dT%H%M%SZ')}_{rng.randint(1000,9999)}.json"
                    )
                    dup_path = out / dup_name
                    with dup_path.open("w", encoding="utf-8") as f:
                        json.dump(entry, f, indent=2)
                    written += 1

    return written

if __name__ == "__main__":
    # Calculate duration from 01.01.2026 to 18.02.2026
    # From Jan 1 to Feb 18 is 48 days
    count = write_mock_json_inbox(
        out_dir="data/inbox",
        stations=20,
        containers_per_station=4,
        start_utc="2026-01-01T00:00:00Z",
        duration_hours=48 * 24,  # 48 days from Jan 1 to Feb 18, 2026
        freq_minutes=5,
        seed=42,
        include_duplicates=False,  # set True to test dedupe/ignore behavior
        duplicate_rate=0.02,
    )
    print(f"Wrote {count} JSON files to data/inbox")