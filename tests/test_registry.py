from pathlib import Path

import pytest

from file_converter.errors import ConversionError
from file_converter.registry import ConversionRequest, available_targets


@pytest.fixture
def csv_file(tmp_path):
    source = tmp_path / "people.csv"
    source.write_text("name\nJan\n", encoding="utf-8")
    return source


def test_available_targets_for_docx():
    assert available_targets(Path("report.DOCX")) == [".pdf", ".txt"]


def test_available_targets_for_unsupported_file():
    assert available_targets(Path("photo.png")) == []


def test_validate_accepts_correct_request(csv_file, tmp_path):
    ConversionRequest(csv_file, ".json", tmp_path).validate()


def test_validate_rejects_missing_file(tmp_path):
    with pytest.raises(ConversionError, match="Nie znaleziono pliku"):
        ConversionRequest(tmp_path / "missing.csv", ".json", tmp_path).validate()


def test_validate_rejects_unsupported_pair(csv_file, tmp_path):
    with pytest.raises(ConversionError, match="Nie można przekonwertować"):
        ConversionRequest(csv_file, ".pdf", tmp_path).validate()


def test_validate_rejects_existing_target_without_overwrite(csv_file, tmp_path):
    (tmp_path / "people.json").write_text("[]", encoding="utf-8")

    with pytest.raises(ConversionError, match="już istnieje"):
        ConversionRequest(csv_file, ".json", tmp_path).validate()

    ConversionRequest(csv_file, ".json", tmp_path, overwrite=True).validate()