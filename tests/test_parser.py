"""Test JSON parser and validation."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from app.ingestion.parser import parse_json_file


def test_valid_json():
    """Test parsing a valid JSON file."""
    fixture_path = Path(__file__).parent / 'fixtures' / 'valid_1.json'
    record, error = parse_json_file(str(fixture_path))
    
    assert record is not None, "Valid JSON should parse successfully"
    assert error is None, "Valid JSON should have no error"
    assert record['sensor_id'] == 1
    assert record['container_id'] == 101
    assert record['connection_quality'] == 4
    print("✓ test_valid_json passed")


def test_invalid_connection_quality():
    """Test that invalid connection quality is rejected."""
    fixture_path = Path(__file__).parent / 'fixtures' / 'invalid_quality.json'
    record, error = parse_json_file(str(fixture_path))
    
    assert record is None, "Invalid quality should be rejected"
    assert error is not None, "Should have error message"
    assert 'out of valid range' in error.lower()
    print("✓ test_invalid_connection_quality passed")


def test_missing_required_field():
    """Test that missing required field is rejected."""
    fixture_path = Path(__file__).parent / 'fixtures' / 'missing_field.json'
    record, error = parse_json_file(str(fixture_path))
    
    assert record is None, "Missing field should be rejected"
    assert error is not None, "Should have error message"
    assert 'missing' in error.lower() or 'required' in error.lower()
    print("✓ test_missing_required_field passed")


if __name__ == '__main__':
    test_valid_json()
    test_invalid_connection_quality()
    test_missing_required_field()
    print("\nAll parser tests passed!")
