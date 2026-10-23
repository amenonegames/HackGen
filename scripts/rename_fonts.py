import argparse
from pathlib import Path
import re

from fontTools.ttLib import TTFont

from validate_fonts import compare_fonts, find_fonts, sha256, write_report


IDENTITY_NAME_IDS = {1, 2, 3, 4, 6, 16, 17, 18, 20, 21, 22, 25}


def compare_preserved_tables(baseline, candidate):
    errors = []
    old_tags = set(baseline.reader.keys()) - {"name", "head", "DSIG"}
    new_tags = set(candidate.reader.keys()) - {"name", "head", "DSIG"}
    for tag in sorted(old_tags | new_tags):
        if tag not in old_tags or tag not in new_tags:
            errors.append({"kind": "table_presence_changed", "table": tag})
        elif baseline.reader[tag] != candidate.reader[tag]:
            errors.append({"kind": "table_bytes_changed", "table": tag})
    old_head, new_head = vars(baseline["head"]), vars(candidate["head"])
    for field in sorted((old_head.keys() | new_head.keys()) - {"checkSumAdjustment"}):
        if old_head.get(field) != new_head.get(field):
            errors.append({"kind": "head_field_changed", "field": field,
                           "baseline": old_head.get(field), "candidate": new_head.get(field)})
    return errors


def rename_font(source, destination):
    with TTFont(source, recalcTimestamp=False, lazy=True) as font:
        changed_names = []
        for record in font["name"].names:
            if record.nameID not in IDENTITY_NAME_IDS:
                continue
            original = record.toUnicode()
            replacement = re.sub("HackGen", "Ameno", original, flags=re.IGNORECASE)
            if original != replacement:
                record.string = replacement.encode(record.getEncoding())
                changed_names.append({"id": record.nameID, "before": original, "after": replacement})
        if not changed_names:
            raise ValueError(f"No HackGen identity found in {source}")
        if "DSIG" in font:
            del font["DSIG"]
        font.save(destination)
    with TTFont(source) as baseline, TTFont(destination) as candidate:
        preserved_table_errors = compare_preserved_tables(baseline, candidate)
        validation = compare_fonts(baseline, candidate, include_private=True, all_glyphs=True)
        validation["errors"].extend(preserved_table_errors)
        for old_record in baseline["name"].names:
            if old_record.nameID in IDENTITY_NAME_IDS:
                continue
            new_record = candidate["name"].getName(old_record.nameID, old_record.platformID,
                                                   old_record.platEncID, old_record.langID)
            if new_record is None or old_record.toUnicode() != new_record.toUnicode():
                validation["errors"].append({"kind": "preserved_name_changed", "id": old_record.nameID})
        for record in candidate["name"].names:
            if record.nameID in IDENTITY_NAME_IDS and "hackgen" in record.toUnicode().lower():
                validation["errors"].append({"kind": "reserved_name_retained", "id": record.nameID})
    return {"source": source.name, "output": destination.name, "changed_names": changed_names,
            "source_sha256": sha256(source), "output_sha256": sha256(destination), **validation}


def main():
    parser = argparse.ArgumentParser(description="Rename 12 verified HackGen TTFs to Ameno, preserving outlines, metrics and license records.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    report = {"passed": False, "fonts": [], "errors": []}
    try:
        sources = find_fonts(args.input)
        output = args.output.resolve()
        if output == args.input.resolve() or output.is_relative_to(args.input.resolve()):
            raise ValueError("Output must be outside the input directory")
        if output.exists() and any(output.iterdir()):
            raise ValueError("Output directory must be empty")
        output.mkdir(parents=True, exist_ok=True)
        for name, source in sorted(sources.items()):
            destination = output / name.replace("HackGen", "Ameno")
            report["fonts"].append(rename_font(source, destination))
        report["passed"] = all(not font["errors"] for font in report["fonts"])
    except Exception as error:
        report["errors"].append(f"{type(error).__name__}: {error}")
    write_report(args.report, report)
    print(f"Font renaming {'passed' if report['passed'] else 'failed'}: {args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
