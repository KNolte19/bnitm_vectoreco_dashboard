"""Dropbox sync script – copies new JSON files to the data inbox every 15 minutes.

Usage:
    python scripts/sync_dropbox.py [--once]

Options:
    --once    Run a single sync and exit (useful for testing or cron jobs).

Configuration:
    Set the DROPBOX_ACCESS_TOKEN environment variable (or replace the
    placeholder below) with a valid Dropbox OAuth2 access token.

    The DROPBOX_FOLDER path is the remote Dropbox folder that contains the
    sensor JSON files (e.g. '/vectoreco/sensor_data').

    Copied files are tracked in a local state file so they are not
    downloaded twice.
"""
import argparse
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
import dropbox
from dotenv import load_dotenv
load_dotenv()  # loads variables from .env file into os.environ

# ---------------------------------------------------------------------------
# Configuration – adjust as needed or override via environment variables
# ---------------------------------------------------------------------------
DROPBOX_APP_KEY      = os.getenv("DROPBOX_APP_KEY", "")
DROPBOX_APP_SECRET   = os.getenv("DROPBOX_APP_SECRET", "")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN", "")
DROPBOX_FOLDER = os.getenv("DROPBOX_FOLDER", "/ab_uploads/")

# Local paths (relative to repo root when run from the project directory)
_REPO_ROOT = Path(__file__).parent.parent.absolute()
INBOX_DIR = Path(os.getenv("INBOX_DIR", str(_REPO_ROOT / "data" / "inbox")))
STATE_FILE = Path(os.getenv("DROPBOX_STATE_FILE", str(_REPO_ROOT / "data" / ".dropbox_synced.json")))

POLL_INTERVAL_SECONDS = 15 * 60  # 15 minutes

# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _load_state() -> set:
    """Load the set of already-synced file paths from the state file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def _save_state(synced: set) -> None:
    """Persist the set of synced file paths to the state file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(synced), f, indent=2)


def sync_once() -> int:
    """Download new JSON files from Dropbox to the inbox.

    Returns:
        Number of new files copied.
    """
    try:
        import dropbox  # pip install dropbox
    except ImportError:
        logger.error(
            "The 'dropbox' package is not installed. "
            "Run: pip install dropbox"
        )
        return 0

    if not DROPBOX_APP_KEY or not DROPBOX_APP_SECRET or not DROPBOX_REFRESH_TOKEN:
        logger.error(
            "Dropbox credentials not fully configured. "
            "Set DROPBOX_APP_KEY, DROPBOX_APP_SECRET, and DROPBOX_REFRESH_TOKEN."
        )
        return 0

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    synced = _load_state()
    copied = 0

    try:
        dbx = dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
    )
        result = dbx.files_list_folder(DROPBOX_FOLDER)

        while True:
            for entry in result.entries:
                if not isinstance(entry, dropbox.files.FileMetadata):
                    continue
                if not entry.name.lower().endswith(".json"):
                    continue
                if entry.path_lower in synced:
                    continue

                dest = INBOX_DIR / entry.name
                # Avoid overwriting a file that is already in the inbox
                if dest.exists():
                    logger.debug("Skipping %s – already in inbox", entry.name)
                    synced.add(entry.path_lower)
                    continue

                try:
                    _metadata, response = dbx.files_download(entry.path_lower)
                    dest.write_bytes(response.content)
                    synced.add(entry.path_lower)
                    copied += 1
                    logger.info("Downloaded %s", entry.name)
                except Exception as exc:
                    logger.warning("Failed to download %s: %s", entry.name, exc)

            if not result.has_more:
                break
            result = dbx.files_list_folder_continue(result.cursor)

    except Exception as exc:
        logger.error("Dropbox sync error: %s", exc)
    finally:
        _save_state(synced)

    logger.info("Sync complete – %d new file(s) copied to inbox", copied)
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Dropbox sensor files to the data inbox")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single sync and exit instead of polling every 15 minutes",
    )
    args = parser.parse_args()

    if args.once:
        sync_once()
    else:
        logger.info("Starting Dropbox sync daemon (interval: %d s)", POLL_INTERVAL_SECONDS)
        while True:
            sync_once()
            logger.info("Next sync in %d minutes", POLL_INTERVAL_SECONDS // 60)
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
