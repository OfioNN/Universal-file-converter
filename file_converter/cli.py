import argparse
import sys
from pathlib import Path

from file_converter.converters.structured import csv_to_json, json_to_csv
from file_converter.errors import ConversionError

CONVERTERS = {
    (".csv", ".json"): csv_to_json,
    (".json", ".csv"): json_to_csv,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target_format")
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    key = (args.source.suffix.lower(), args.target_format.lower())
    if key not in CONVERTERS:
        sys.exit(f"Nieobsługiwana konwersja: {key[0]} -> {key[1]}")

    try:
        target = CONVERTERS[key](args.source, args.output_dir)
    except ConversionError as error:
        sys.exit(f"Błąd: {error}")

    print(f"Utworzono: {target}")


if __name__ == "__main__":
    main()