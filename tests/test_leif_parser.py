"""Tests for Leif's JSONL parser."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from app.leif.parser import parse_jsonl_file


def test_valid_bs():
    """Parse a valid BS (Breeding Site) JSONL file."""
    fixture = Path(__file__).parent / 'fixtures' / 'valid_bs.jsonl'
    results, error = parse_jsonl_file(str(fixture))

    assert results is not None, f"Valid BS JSONL should parse successfully, got error: {error}"
    assert error is None
    assert len(results) == 1
    logger_type, record = results[0]
    assert logger_type == 'BS'
    assert record['site'] == 3
    assert record['replica'] == 2
    assert record['water_temperature'] == 13.812
    assert record['distance_cm'] == 42.1
    print("✓ test_valid_bs passed")


def test_valid_rs():
    """Parse a valid RS (Resting Site) JSONL file."""
    fixture = Path(__file__).parent / 'fixtures' / 'valid_rs.jsonl'
    results, error = parse_jsonl_file(str(fixture))

    assert results is not None, f"Valid RS JSONL should parse successfully, got error: {error}"
    assert error is None
    assert len(results) == 1
    logger_type, record = results[0]
    assert logger_type == 'RS'
    assert record['site'] == 3
    assert record['replica'] == 2
    assert abs(record['temperature'] - 18.3481157541275) < 1e-6
    assert record['humidity'] == 100.0
    assert record['full_spectrum'] == 6
    assert record['ir'] == 5
    print("✓ test_valid_rs passed")


def test_missing_field_bs():
    """A BS record missing distance_cm should be rejected."""
    fixture = Path(__file__).parent / 'fixtures' / 'missing_field_bs.jsonl'
    results, error = parse_jsonl_file(str(fixture))

    assert results is None, "BS with missing field should be rejected"
    assert error is not None
    assert 'distance_cm' in error
    print("✓ test_missing_field_bs passed")


def test_unknown_logger_type():
    """A record with an unknown logger type should be rejected."""
    fixture = Path(__file__).parent / 'fixtures' / 'unknown_logger.jsonl'
    results, error = parse_jsonl_file(str(fixture))

    assert results is None, "Unknown logger type should be rejected"
    assert error is not None
    assert 'XX' in error or 'logger' in error.lower()
    print("✓ test_unknown_logger_type passed")


def test_real_example_bs():
    """Parse the real example BS file committed to the repository."""
    fixture = Path(__file__).parent.parent / 'site3_BS2_20260612_1500example_leif.jsonl'
    if not fixture.exists():
        print("⚠ Real BS example file not found – skipping")
        return
    results, error = parse_jsonl_file(str(fixture))
    assert results is not None, f"Real BS example should parse, got: {error}"
    logger_type, record = results[0]
    assert logger_type == 'BS'
    assert record['site'] == 3
    print("✓ test_real_example_bs passed")


def test_real_example_rs():
    """Parse the real example RS file committed to the repository."""
    fixture = Path(__file__).parent.parent / 'site3_RS_2_20260612_1500example_leif.jsonl'
    if not fixture.exists():
        print("⚠ Real RS example file not found – skipping")
        return
    results, error = parse_jsonl_file(str(fixture))
    assert results is not None, f"Real RS example should parse, got: {error}"
    logger_type, record = results[0]
    assert logger_type == 'RS'
    assert record['site'] == 3
    print("✓ test_real_example_rs passed")


if __name__ == '__main__':
    test_valid_bs()
    test_valid_rs()
    test_missing_field_bs()
    test_unknown_logger_type()
    test_real_example_bs()
    test_real_example_rs()
    print("\nAll Leif parser tests passed!")
