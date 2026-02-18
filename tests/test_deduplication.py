"""Test deduplication behavior."""
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from app.data.models import create_tables
from app.data.db import get_connection
from app.ingestion.ingest import ingest_folder
from app import config


def test_duplicate_handling():
    """Test that duplicate records are ignored."""
    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        inbox = Path(tmpdir) / 'inbox'
        archive = Path(tmpdir) / 'archive'
        db_path = Path(tmpdir) / 'test.db'
        
        inbox.mkdir()
        archive.mkdir()
        
        # Initialize database
        conn = get_connection(str(db_path))
        create_tables(conn)
        conn.close()
        
        # Copy test fixtures to inbox
        fixtures_dir = Path(__file__).parent / 'fixtures'
        shutil.copy(fixtures_dir / 'valid_1.json', inbox / 'valid_1.json')
        shutil.copy(fixtures_dir / 'valid_2.json', inbox / 'valid_2.json')
        shutil.copy(fixtures_dir / 'duplicate.json', inbox / 'duplicate.json')
        
        # Temporarily override config
        original_db = config.DB_PATH
        config.DB_PATH = str(db_path)
        
        try:
            # First ingestion
            stats1 = ingest_folder(
                inbox_path=str(inbox),
                archive_path=str(archive),
                delete_after=False
            )
            
            assert stats1.found == 3, "Should find 3 files"
            assert stats1.parsed == 3, "Should parse 3 files"
            assert stats1.inserted == 2, "Should insert 2 unique records"
            assert stats1.duplicates == 1, "Should detect 1 duplicate"
            
            # Verify database content
            conn = get_connection(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM measurements")
            count = cursor.fetchone()[0]
            conn.close()
            
            assert count == 2, f"Database should have 2 records, found {count}"
            
            print("✓ test_duplicate_handling passed")
            
        finally:
            config.DB_PATH = original_db


def test_idempotency():
    """Test that re-running ingestion doesn't create duplicates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inbox = Path(tmpdir) / 'inbox'
        archive = Path(tmpdir) / 'archive'
        db_path = Path(tmpdir) / 'test.db'
        
        inbox.mkdir()
        archive.mkdir()
        
        # Initialize database
        conn = get_connection(str(db_path))
        create_tables(conn)
        conn.close()
        
        # Copy test fixture
        fixtures_dir = Path(__file__).parent / 'fixtures'
        shutil.copy(fixtures_dir / 'valid_1.json', inbox / 'valid_1.json')
        
        original_db = config.DB_PATH
        config.DB_PATH = str(db_path)
        
        try:
            # First ingestion
            stats1 = ingest_folder(
                inbox_path=str(inbox),
                archive_path=str(archive),
                delete_after=False
            )
            
            assert stats1.inserted == 1, "First run should insert 1 record"
            
            # Copy the same file again
            shutil.copy(fixtures_dir / 'valid_1.json', inbox / 'valid_1_again.json')
            
            # Second ingestion
            stats2 = ingest_folder(
                inbox_path=str(inbox),
                archive_path=str(archive),
                delete_after=False
            )
            
            assert stats2.found == 1, "Should find 1 file in second run"
            assert stats2.inserted == 0, "Second run should insert 0 records"
            assert stats2.duplicates == 1, "Second run should detect 1 duplicate"
            
            # Verify database still has only 1 record
            conn = get_connection(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM measurements")
            count = cursor.fetchone()[0]
            conn.close()
            
            assert count == 1, f"Database should still have 1 record, found {count}"
            
            print("✓ test_idempotency passed")
            
        finally:
            config.DB_PATH = original_db


if __name__ == '__main__':
    test_duplicate_handling()
    test_idempotency()
    print("\nAll deduplication tests passed!")
