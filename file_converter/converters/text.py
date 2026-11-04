from pathlib import Path
from zipfile import BadZipFile

from docx import Document

from file_converter.errors import ConversionError


def txt_to_docx(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.docx"

    try:
        text = source.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise ConversionError(
            f"Plik {source.name} nie jest zapisany w UTF-8. "
            "Zapisz go ponownie z kodowaniem UTF-8 i spróbuj jeszcze raz."
        ) from error

    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    document.save(target)

    return target


def docx_to_txt(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.txt"

    try:
        document = Document(source)
    except (BadZipFile, KeyError, ValueError) as error:
        raise ConversionError(
            f"Plik {source.name} nie jest poprawnym dokumentem DOCX. "
            "Otwórz go w Wordzie lub LibreOffice i zapisz ponownie jako .docx."
        ) from error

    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    target.write_text(text, encoding="utf-8")

    return target