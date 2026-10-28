import csv
import json
from pathlib import Path


def csv_to_json(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.json"

    with open(source, encoding="utf-8-sig", newline="") as source_file:
        dialect = csv.Sniffer().sniff(source_file.read(2048), delimiters=",;")
        source_file.seek(0)
        rows = list(csv.DictReader(source_file, dialect=dialect))

    with open(target, "w", encoding="utf-8") as target_file:
        json.dump(rows, target_file, ensure_ascii=False, indent=2)

    return target


def json_to_csv(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.csv"

    with open(source, encoding="utf-8-sig") as source_file:
        rows = json.load(source_file)

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


if __name__ == "__main__":
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    json_file = csv_to_json(Path("samples/people.csv"), output_dir)
    csv_file = json_to_csv(json_file, output_dir)
    print(f"Utworzono: {json_file}, {csv_file}")