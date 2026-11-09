import os
import shutil
import subprocess
from pathlib import Path
from zipfile import is_zipfile

from file_converter.errors import ConversionError

LIBREOFFICE_DEFAULT_PATHS = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
]


def find_libreoffice() -> str:
    custom_path = os.environ.get("LIBREOFFICE_PATH")
    if custom_path:
        candidates = [custom_path]
    else:
        candidates = [shutil.which("soffice"), shutil.which("libreoffice")] + LIBREOFFICE_DEFAULT_PATHS

    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate

    raise ConversionError(
        "Nie znaleziono LibreOffice. Zainstaluj je ze strony libreoffice.org "
        "albo ustaw zmienną LIBREOFFICE_PATH na ścieżkę do programu soffice."
    )


def document_to_pdf(source: Path, output_dir: Path) -> Path:
    if not is_zipfile(source):
        raise ConversionError(
            f"Plik {source.name} jest uszkodzony albo nie jest dokumentem {source.suffix}. "
            "Otwórz go w edytorze tekstu i zapisz ponownie."
        )

    command = [
        find_libreoffice(),
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(source),
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired as error:
        raise ConversionError(
            "LibreOffice nie zakończył konwersji w ciągu 60 sekund. "
            "Zamknij otwarte okna LibreOffice i spróbuj ponownie."
        ) from error

    if result.returncode != 0:
        raise ConversionError(
            f"LibreOffice zakończył pracę z błędem (kod {result.returncode}): "
            f"{result.stderr.strip() or 'brak szczegółów'}"
        )

    target = output_dir / f"{source.stem}.pdf"
    if not target.is_file():
        raise ConversionError(
            f"LibreOffice nie utworzył pliku {target.name}. Sprawdź, czy dokument "
            "otwiera się w LibreOffice, i zamknij inne otwarte okna LibreOffice."
        )

    return target