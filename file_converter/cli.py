import argparse
import sys
from pathlib import Path

from file_converter.log_config import configure_logging
from file_converter.errors import ConversionError
from file_converter.registry import ConversionRequest, execute


def main() -> None:
    configure_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target_format")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    request = ConversionRequest(args.source, args.target_format.lower(), args.output_dir, args.overwrite)

    try:
        target = execute(request)
    except ConversionError as error:
        sys.exit(f"Błąd: {error}")

    print(f"Utworzono: {target}")


if __name__ == "__main__":
    main()