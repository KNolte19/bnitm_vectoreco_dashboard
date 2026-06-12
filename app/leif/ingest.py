"""Ingestion module for Leif's JSONL sensor files."""
import logging
import sqlite3
from pathlib import Path
from typing import List, Tuple
from app.leif.parser import parse_jsonl_file
from app.leif.db import get_leif_connection

logger = logging.getLogger(__name__)


class LeifIngestionStats:
    """Statistics for a Leif ingestion run."""

    def __init__(self):
        self.found = 0
        self.parsed = 0
        self.inserted_bs = 0
        self.inserted_rs = 0
        self.duplicates = 0
        self.dropped = 0
        self.errors = 0
        self.error_details: List[str] = []


def ingest_leif_folder(
    inbox_path: str = None,
    archive_path: str = None,
    delete_after: bool = False,
) -> LeifIngestionStats:
    """Ingest all JSONL files from Leif's inbox folder.

    Args:
        inbox_path: Path to inbox directory. Defaults to config.LEIF_INBOX_DIR.
        archive_path: Path to archive directory. Defaults to config.LEIF_ARCHIVE_DIR.
        delete_after: If True, delete files instead of archiving.

    Returns:
        LeifIngestionStats with counts and error details.
    """
    from app import config  # late import to avoid circular imports at load time

    if inbox_path is None:
        inbox_path = config.LEIF_INBOX_DIR
    if archive_path is None:
        archive_path = config.LEIF_ARCHIVE_DIR

    inbox = Path(inbox_path)
    archive = Path(archive_path)

    inbox.mkdir(parents=True, exist_ok=True)
    if not delete_after:
        archive.mkdir(parents=True, exist_ok=True)

    stats = LeifIngestionStats()

    jsonl_files = list(inbox.glob('*.jsonl'))
    stats.found = len(jsonl_files)

    if stats.found == 0:
        logger.info("No JSONL files found in Leif's inbox")
        return stats

    logger.info("Found %d JSONL file(s) to process", stats.found)

    bs_records: List[dict] = []
    rs_records: List[dict] = []
    files_to_archive: List[Path] = []

    for jsonl_file in jsonl_files:
        results, error = parse_jsonl_file(str(jsonl_file))

        if results is not None:
            for logger_type, record in results:
                if logger_type == 'BS':
                    bs_records.append(record)
                else:
                    rs_records.append(record)
            stats.parsed += 1
        else:
            stats.dropped += 1
            error_msg = f"{jsonl_file.name}: {error}"
            stats.error_details.append(error_msg)
            logger.warning("Dropped %s", error_msg)

        # Archive / delete regardless of parse outcome
        files_to_archive.append(jsonl_file)

    # Bulk insert valid records
    if bs_records:
        inserted, dupes = _bulk_insert_bs(bs_records)
        stats.inserted_bs = inserted
        stats.duplicates += dupes
        logger.info("BS: inserted %d new records, %d duplicates", inserted, dupes)

    if rs_records:
        inserted, dupes = _bulk_insert_rs(rs_records)
        stats.inserted_rs = inserted
        stats.duplicates += dupes
        logger.info("RS: inserted %d new records, %d duplicates", inserted, dupes)

    # Archive or delete processed files
    for jsonl_file in files_to_archive:
        try:
            if delete_after:
                jsonl_file.unlink()
            else:
                dest = archive / jsonl_file.name
                counter = 1
                while dest.exists():
                    dest = archive / f"{jsonl_file.stem}_{counter}{jsonl_file.suffix}"
                    counter += 1
                jsonl_file.rename(dest)
        except Exception as exc:
            stats.errors += 1
            error_msg = f"Failed to archive {jsonl_file.name}: {exc}"
            stats.error_details.append(error_msg)
            logger.error(error_msg)

    logger.info(
        "Leif ingestion complete: %d found, %d parsed, "
        "%d BS inserted, %d RS inserted, %d duplicates, %d dropped, %d errors",
        stats.found, stats.parsed,
        stats.inserted_bs, stats.inserted_rs,
        stats.duplicates, stats.dropped, stats.errors,
    )

    return stats


def _bulk_insert_bs(records: List[dict]) -> Tuple[int, int]:
    """Bulk-insert Breeding Site records; ignores duplicates.

    Returns:
        (inserted_count, duplicate_count)
    """
    conn = get_leif_connection()
    total = len(records)
    try:
        cursor = conn.cursor()
        sql = """
            INSERT OR IGNORE INTO leif_bs_measurements
                (site, replica, time_sent, water_temperature, distance_cm)
            VALUES (?, ?, ?, ?, ?)
        """
        rows = [
            (r['site'], r['replica'], r['time_sent'], r['water_temperature'], r['distance_cm'])
            for r in records
        ]
        cursor.executemany(sql, rows)
        conn.commit()
        inserted = cursor.rowcount
        return inserted, total - inserted
    except sqlite3.Error as exc:
        logger.error("Database error inserting BS records: %s", exc)
        conn.rollback()
        raise
    finally:
        conn.close()


def _bulk_insert_rs(records: List[dict]) -> Tuple[int, int]:
    """Bulk-insert Resting Site records; ignores duplicates.

    Returns:
        (inserted_count, duplicate_count)
    """
    conn = get_leif_connection()
    total = len(records)
    try:
        cursor = conn.cursor()
        sql = """
            INSERT OR IGNORE INTO leif_rs_measurements
                (site, replica, time_sent, temperature, humidity, pressure, full_spectrum, ir)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = [
            (
                r['site'], r['replica'], r['time_sent'],
                r['temperature'], r['humidity'], r['pressure'],
                r['full_spectrum'], r['ir'],
            )
            for r in records
        ]
        cursor.executemany(sql, rows)
        conn.commit()
        inserted = cursor.rowcount
        return inserted, total - inserted
    except sqlite3.Error as exc:
        logger.error("Database error inserting RS records: %s", exc)
        conn.rollback()
        raise
    finally:
        conn.close()
