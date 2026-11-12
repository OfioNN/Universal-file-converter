import csv
import json
from pathlib import Path

from file_converter.errors import ConversionError


def not_utf8_error(source: Path) -> ConversionError:
    return ConversionError(
        f"Plik {source.name} nie jest zapisany w UTF-8. "
        "Zapisz go ponownie z kodowaniem UTF-8 i spróbuj jeszcze raz."
    )


def csv_to_json(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.json"

    try:
        with open(source, encoding="utf-8-sig", newline="") as source_file:
            sample = source_file.read(2048)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            except csv.Error:
                dialect = csv.excel
            source_file.seek(0)
            rows = list(csv.DictReader(source_file, dialect=dialect))
    except UnicodeDecodeError as error:
        raise not_utf8_error(source) from error

    with open(target, "w", encoding="utf-8") as target_file:
        json.dump(rows, target_file, ensure_ascii=False, indent=2)

    return target


def json_to_csv(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.csv"

    try:
        with open(source, encoding="utf-8-sig") as source_file:
            rows = json.load(source_file)
    except UnicodeDecodeError as error:
        raise not_utf8_error(source) from error
    except json.JSONDecodeError as error:
        raise ConversionError(
            f"Plik {source.name} nie jest poprawnym JSON-em "
            f"(linia {error.lineno}, kolumna {error.colno}). "
            "Popraw składnię pliku i spróbuj ponownie."
        ) from error

    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ConversionError(
            f"Plik {source.name} ma niepoprawną strukturę: oczekiwano listy obiektów. "
            "Zapisz dane w formacie opisanym w README."
        )

    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with open(target, "w", encoding="utf-8-sig", newline="") as target_file:
        writer = csv.DictWriter(target_file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    return target