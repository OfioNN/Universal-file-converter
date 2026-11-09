import json

import pytest
from docx import Document

from file_converter.converters.office import document_to_pdf, find_libreoffice
from file_converter.converters.structured import csv_to_json, json_to_csv
from file_converter.converters.text import docx_to_txt, txt_to_docx
from file_converter.errors import ConversionError


@pytest.fixture
def output_dir(tmp_path):
    directory = tmp_path / "output"
    directory.mkdir()
    return directory


def test_csv_json_round_trip_keeps_polish_characters_and_empty_values(tmp_path, output_dir):
    source = tmp_path / "people.csv"
    source.write_text('name,city,phone\nZażółć Gęślą,Łódź,\n"Kowalski, Jan",Kraków,123\n', encoding="utf-8")

    json_file = csv_to_json(source, output_dir)
    csv_file = json_to_csv(json_file, output_dir)

    assert json.loads(json_file.read_text(encoding="utf-8")) == [
        {"name": "Zażółć Gęślą", "city": "Łódź", "phone": ""},
        {"name": "Kowalski, Jan", "city": "Kraków", "phone": "123"},
    ]
    assert csv_file.read_text(encoding="utf-8-sig").splitlines() == [
        "name;city;phone",
        "Zażółć Gęślą;Łódź;",
        "Kowalski, Jan;Kraków;123",
    ]


def test_csv_to_json_detects_semicolon(tmp_path, output_dir):
    source = tmp_path / "excel.csv"
    source.write_text("name;city\nJan;Łódź\n", encoding="utf-8-sig")

    json_file = csv_to_json(source, output_dir)

    assert json.loads(json_file.read_text(encoding="utf-8")) == [{"name": "Jan", "city": "Łódź"}]


def test_json_to_csv_rejects_broken_json(tmp_path, output_dir):
    source = tmp_path / "broken.json"
    source.write_text('[{"name": "Jan" "city": "Łódź"}]', encoding="utf-8")

    with pytest.raises(ConversionError, match="nie jest poprawnym JSON-em"):
        json_to_csv(source, output_dir)

    assert not (output_dir / "broken.csv").exists()


def test_txt_docx_round_trip_keeps_paragraphs(tmp_path, output_dir):
    text = "Zażółć gęślą jaźń\n\nDrugi akapit"
    source = tmp_path / "notes.txt"
    source.write_text(text, encoding="utf-8")

    docx_file = txt_to_docx(source, output_dir)
    txt_file = docx_to_txt(docx_file, output_dir)

    assert txt_file.read_text(encoding="utf-8") == text


def test_docx_to_txt_rejects_broken_file(tmp_path, output_dir):
    source = tmp_path / "broken.docx"
    source.write_text("to nie jest dokument Word", encoding="utf-8")

    with pytest.raises(ConversionError, match="nie jest poprawnym dokumentem DOCX"):
        docx_to_txt(source, output_dir)


def test_document_to_pdf_reports_missing_libreoffice(tmp_path, output_dir, monkeypatch):
    monkeypatch.setenv("LIBREOFFICE_PATH", str(tmp_path / "missing" / "soffice.exe"))
    source = tmp_path / "report.docx"
    Document().save(source)

    with pytest.raises(ConversionError, match="Nie znaleziono LibreOffice"):
        document_to_pdf(source, output_dir)


def test_document_to_pdf_creates_pdf(tmp_path, output_dir):
    try:
        find_libreoffice()
    except ConversionError:
        pytest.skip("LibreOffice nie jest zainstalowane")

    source = tmp_path / "report.docx"
    document = Document()
    document.add_paragraph("Zażółć gęślą jaźń")
    document.save(source)

    target = document_to_pdf(source, output_dir)

    assert target.read_bytes().startswith(b"%PDF")