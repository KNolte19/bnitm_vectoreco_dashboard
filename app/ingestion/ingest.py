"""Main ingestion module for batch processing JSON files."""
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple
from app.ingestion.parser import parse_json_file
from app.ingestion.transform import dicts_to_dataframe
from app.data.db import get_connection
from app import config

logger = logging.getLogger(__name__)


class IngestionStats:
    """Statistics for an ingestion run."""
    def __init__(self):
        self.found = 0
        self.parsed = 0
        self.inserted = 0
        self.duplicates = 0
        self.dropped = 0
        self.errors = 0
        self.error_details: List[str] = []


def ingest_folder(
    inbox_path: str = None,
    archive_path: str = None,
    delete_after: bool = False
) -> IngestionStats:
    """Ingest all JSON files from an inbox folder.
    
    Args:
        inbox_path: Path to inbox directory (default: config.INBOX_DIR)
        archive_path: Path to archive directory (default: config.ARCHIVE_DIR)
        delete_after: If True, delete files instead of archiving
        
    Returns:
        IngestionStats with counts and error details
    """
    if inbox_path is None:
        inbox_path = config.INBOX_DIR
    if archive_path is None:
        archive_path = config.ARCHIVE_DIR
    
    inbox = Path(inbox_path)
    archive = Path(archive_path)
    
    # Create directories if they don't exist
    inbox.mkdir(parents=True, exist_ok=True)
    if not delete_after:
        archive.mkdir(parents=True, exist_ok=True)
    
    stats = IngestionStats()
    
    # Find all JSON files
    json_files = list(inbox.glob('*.json'))
    stats.found = len(json_files)
    
    if stats.found == 0:
        logger.info("No JSON files found in inbox")
        return stats
    
    logger.info(f"Found {stats.found} JSON files to process")
    
    # Parse all files – each file may yield multiple records (one per treatment)
    valid_records = []
    files_to_archive = []
    
    for json_file in json_files:
        records, error = parse_json_file(str(json_file))
        
        if records is not None:
            valid_records.extend(records)
            files_to_archive.append(json_file)
            stats.parsed += 1
        else:
            stats.dropped += 1
            error_msg = f"{json_file.name}: {error}"
            stats.error_details.append(error_msg)
            logger.warning(f"Dropped {error_msg}")
            # Still archive/delete invalid files
            files_to_archive.append(json_file)
    
    # Bulk insert valid records
    if valid_records:
        inserted, duplicates = bulk_insert_measurements(valid_records)
        stats.inserted = inserted
        stats.duplicates = duplicates
        logger.info(f"Inserted {inserted} new records, {duplicates} duplicates ignored")
    
    # Archive or delete processed files
    for json_file in files_to_archive:
        try:
            if delete_after:
                json_file.unlink()
            else:
                dest = archive / json_file.name
                # Handle filename conflicts in archive
                counter = 1
                while dest.exists():
                    dest = archive / f"{json_file.stem}_{counter}{json_file.suffix}"
                    counter += 1
                json_file.rename(dest)
        except Exception as e:
            stats.errors += 1
            error_msg = f"Failed to archive {json_file.name}: {e}"
            stats.error_details.append(error_msg)
            logger.error(error_msg)
    
    logger.info(
        f"Ingestion complete: {stats.found} found, {stats.parsed} parsed, "
        f"{stats.inserted} inserted, {stats.duplicates} duplicates, "
        f"{stats.dropped} dropped, {stats.errors} errors"
    )
    
    return stats


def bulk_insert_measurements(records: List[Dict]) -> Tuple[int, int]:
    """Bulk insert measurement records into the database.
    
    Uses INSERT OR IGNORE to handle duplicates based on unique constraint.
    
    Args:
        records: List of validated measurement dictionaries
        
    Returns:
        Tuple of (inserted_count, duplicate_count)
    """
    if not records:
        return 0, 0
    
    # Convert to DataFrame
    df = dicts_to_dataframe(records)
    
    if df.empty:
        return 0, 0
    
    conn = get_connection()
    total_records = len(df)
    
    try:
        # Use INSERT OR IGNORE to skip duplicates
        cursor = conn.cursor()
        
        insert_sql = """
            INSERT OR IGNORE INTO measurements (
                sensor_id, treatment_id, location,
                window_start, window_end, n_observations,
                control_temp, treatment_temp,
                received_packets, expected_packets,
                connection_quality
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Convert DataFrame to list of tuples
        records_tuples = [
            (
                row['sensor_id'],
                row['treatment_id'],
                row['location'],
                row['window_start'].strftime('%Y-%m-%d %H:%M:%S'),
                row['window_end'].strftime('%Y-%m-%d %H:%M:%S'),
                row['n_observations'],
                row['control_temp'],
                row['treatment_temp'],
                row['received_packets'],
                row['expected_packets'],
                row['connection_quality'],
            )
            for _, row in df.iterrows()
        ]
        
        cursor.executemany(insert_sql, records_tuples)
        conn.commit()
        
        # Count how many were actually inserted
        inserted_count = cursor.rowcount
        duplicate_count = total_records - inserted_count
        
        return inserted_count, duplicate_count
        
    except sqlite3.Error as e:
        logger.error(f"Database error during bulk insert: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
