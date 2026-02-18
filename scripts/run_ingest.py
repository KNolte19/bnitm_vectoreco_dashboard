#!/usr/bin/env python3
"""CLI tool for running data ingestion."""
import sys
import time
import logging
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from app.ingestion.ingest import ingest_folder
from app import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run data ingestion."""
    parser = argparse.ArgumentParser(description='Ingest JSON measurement files')
    parser.add_argument(
        '--mode',
        choices=['once', 'watch'],
        default='once',
        help='Run once or watch folder continuously'
    )
    parser.add_argument(
        '--inbox',
        default=config.INBOX_DIR,
        help=f'Inbox directory (default: {config.INBOX_DIR})'
    )
    parser.add_argument(
        '--archive',
        default=config.ARCHIVE_DIR,
        help=f'Archive directory (default: {config.ARCHIVE_DIR})'
    )
    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete processed files instead of archiving'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Watch interval in seconds (default: 60)'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting ingestion in {args.mode} mode")
    logger.info(f"Inbox: {args.inbox}")
    logger.info(f"Archive: {args.archive}")
    
    if args.mode == 'once':
        stats = ingest_folder(
            inbox_path=args.inbox,
            archive_path=args.archive,
            delete_after=args.delete
        )
        
        print("\nIngestion Summary:")
        print(f"  Files found:    {stats.found}")
        print(f"  Files parsed:   {stats.parsed}")
        print(f"  Records inserted: {stats.inserted}")
        print(f"  Duplicates:     {stats.duplicates}")
        print(f"  Dropped:        {stats.dropped}")
        print(f"  Errors:         {stats.errors}")
        
        if stats.error_details:
            print("\nError Details:")
            for error in stats.error_details:
                print(f"  - {error}")
        
        return 0 if stats.errors == 0 else 1
    
    else:  # watch mode
        logger.info(f"Watching folder every {args.interval} seconds (Ctrl+C to stop)")
        
        try:
            while True:
                stats = ingest_folder(
                    inbox_path=args.inbox,
                    archive_path=args.archive,
                    delete_after=args.delete
                )
                
                if stats.found > 0:
                    logger.info(
                        f"Processed {stats.found} files: "
                        f"{stats.inserted} inserted, {stats.duplicates} duplicates, "
                        f"{stats.dropped} dropped"
                    )
                
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping watch mode")
            return 0


if __name__ == '__main__':
    sys.exit(main())
