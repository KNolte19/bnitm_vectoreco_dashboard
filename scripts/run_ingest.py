#!/usr/bin/env python3
"""CLI tool for running data ingestion."""
import sys
import time
import logging
import argparse
from pathlib import Path

# Add repo root to path so both 'app' and 'scripts' packages are importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

import scripts.sync_dropbox as sync_dropbox
from app.ingestion.ingest import ingest_folder
from app.leif.ingest import ingest_leif_folder
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
        
        print("\nFelix Ingestion Summary:")
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

        leif_stats = ingest_leif_folder(delete_after=args.delete)

        print("\nLeif Ingestion Summary:")
        print(f"  Files found:    {leif_stats.found}")
        print(f"  Files parsed:   {leif_stats.parsed}")
        print(f"  BS inserted:    {leif_stats.inserted_bs}")
        print(f"  RS inserted:    {leif_stats.inserted_rs}")
        print(f"  Duplicates:     {leif_stats.duplicates}")
        print(f"  Dropped:        {leif_stats.dropped}")
        print(f"  Errors:         {leif_stats.errors}")

        if leif_stats.error_details:
            print("\nLeif Error Details:")
            for error in leif_stats.error_details:
                print(f"  - {error}")

        return 0 if (stats.errors == 0 and leif_stats.errors == 0) else 1
    
    else:  # watch mode
        logger.info(f"Watching folder every {args.interval} seconds (Ctrl+C to stop)")
        
        try:
            while True:
                sync_dropbox.sync_once()
                sync_dropbox.sync_leif_once()

                stats = ingest_folder(
                    inbox_path=args.inbox,
                    archive_path=args.archive,
                    delete_after=args.delete
                )
                
                if stats.found > 0:
                    logger.info(
                        f"Felix: {stats.found} files, "
                        f"{stats.inserted} inserted, {stats.duplicates} duplicates, "
                        f"{stats.dropped} dropped"
                    )

                leif_stats = ingest_leif_folder(delete_after=args.delete)

                if leif_stats.found > 0:
                    logger.info(
                        f"Leif: {leif_stats.found} files, "
                        f"{leif_stats.inserted_bs} BS + {leif_stats.inserted_rs} RS inserted, "
                        f"{leif_stats.duplicates} duplicates, {leif_stats.dropped} dropped"
                    )
                
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping watch mode")
            return 0


if __name__ == '__main__':
    sys.exit(main())
