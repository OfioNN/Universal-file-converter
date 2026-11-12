import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from file_converter.converters.office import document_to_pdf
from file_converter.converters.structured import csv_to_json, json_to_csv
from file_converter.converters.text import docx_to_txt, txt_to_docx
from file_converter.errors import ConversionError

logger = logging.getLogger(__name__)

REGISTRY = {
    (".csv", ".json"): csv_to_json,
    (".json", ".csv"): json_to_csv,
    (".txt", ".docx"): txt_to_docx,
    (".docx", ".txt"): docx_to_txt,
    (".docx", ".pdf"): document_to_pdf,
    (".odt", ".pdf"): document_to_pdf,
}


def available_targets(source: Path) -> list[str]:
    return sorted(target for (source_format, target) in REGISTRY if source_format == source.suffix.lower())


@dataclass(frozen=True)
class ConversionRequest:
    source: Path
    target_format: str
    output_dir: Path
    overwrite: bool = False
    target_name: str | None = None

    @property
    def target_path(self) -> Path:
        return self.output_dir / (self.target_name or f"{self.source.stem}{self.target_format}")

    def validate(self) -> None:
        if not self.source.is_file():
            raise ConversionError(f"Nie znaleziono pliku {self.source}. Wybierz istniejący plik.")

        if not self.output_dir.is_dir():
            raise ConversionError(f"Nie znaleziono folderu {self.output_dir}. Wybierz istniejący folder zapisu.")

        if (self.source.suffix.lower(), self.target_format) not in REGISTRY:
            targets = ", ".join(available_targets(self.source)) or "brak"
            raise ConversionError(
                f"Nie można przekonwertować pliku {self.source.suffix} na {self.target_format}. "
                f"Dostępne formaty dla tego pliku: {targets}."
            )

        if self.target_path.suffix.lower() != self.target_format:
            raise ConversionError(
                f"Plik wynikowy {self.target_path.name} musi mieć rozszerzenie {self.target_format}. "
                "Popraw nazwę pliku i spróbuj ponownie."
            )

        if self.target_path.exists() and not self.overwrite:
            raise ConversionError(
                f"Plik {self.target_path.name} już istnieje w folderze {self.output_dir}. "
                "Zezwól na nadpisanie albo wybierz inny folder."
            )


def execute(request: ConversionRequest) -> Path:
    description = f"{request.source} -> {request.target_format}"
    started = time.perf_counter()

    try:
        request.validate()
        convert = REGISTRY[(request.source.suffix.lower(), request.target_format)]
        with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            converted = convert(request.source, Path(temp_dir))
            shutil.move(converted, request.target_path)
        target = request.target_path
    except PermissionError as error:
        logger.error(f"{description}: brak dostępu ({error})")
        raise ConversionError(
            f"Brak dostępu do pliku {request.target_path.name}. Zamknij go, jeśli jest otwarty "
            "w innym programie (np. w Excelu), albo wybierz inny folder."
        ) from error
    except ConversionError as error:
        logger.error(f"{description}: {error}")
        raise
    except Exception:
        logger.exception(f"{description}: nieoczekiwany błąd")
        raise

    logger.info(f"{description}: utworzono {target} w {time.perf_counter() - started:.2f} s")
    return target