import argparse
import hashlib
import json
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont


FAMILIES = (
    "HackGen", "HackGenConsole", "HackGen35", "HackGen35Console",
    "HackGenConsoleNF", "HackGen35ConsoleNF",
)
STYLES = ("Regular", "Bold")
METRIC_FIELDS = {
    "head": ("unitsPerEm",),
    "hhea": ("ascent", "descent", "lineGap", "caretSlopeRise", "caretSlopeRun"),
    "OS/2": (
        "sTypoAscender", "sTypoDescender", "sTypoLineGap", "usWinAscent",
        "usWinDescent", "sxHeight", "sCapHeight", "fsSelection",
    ),
}


def is_private_use(codepoint):
    return any(start <= codepoint <= end for start, end in (
        (0xE000, 0xF8FF), (0xF0000, 0xFFFFD), (0x100000, 0x10FFFD),
    ))


def unicode_cmap(font):
    result = {}
    for table in font["cmap"].tables:
        if table.isUnicode() and hasattr(table, "cmap"):
            for codepoint, glyph_name in table.cmap.items():
                result.setdefault(codepoint, set()).add(glyph_name)
    return result


def glyph_signature(font, glyph_set, glyph_name):
    pen = DecomposingRecordingPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    glyph = font["glyf"][glyph_name]
    instructions = bytes(glyph.program.getBytecode()) if hasattr(glyph, "program") else b""
    return pen.value, font["hmtx"][glyph_name], instructions


def compare_fonts(baseline, candidate, include_private=False, all_glyphs=False):
    errors = []
    for table, fields in METRIC_FIELDS.items():
        for field in fields:
            old = getattr(baseline[table], field, None)
            new = getattr(candidate[table], field, None)
            if old != new:
                errors.append({"kind": "font_metric", "field": f"{table}.{field}",
                               "baseline": old, "candidate": new})
    for tag in ("fpgm", "prep", "cvt "):
        old = baseline.getTableData(tag) if tag in baseline else None
        new = candidate.getTableData(tag) if tag in candidate else None
        if old != new:
            errors.append({"kind": "global_hinting", "table": tag})
    old_cmap, new_cmap = unicode_cmap(baseline), unicode_cmap(candidate)
    old_set, new_set = baseline.getGlyphSet(), candidate.getGlyphSet()
    checked = 0
    for codepoint, old_names in sorted(old_cmap.items()):
        if not include_private and is_private_use(codepoint):
            continue
        checked += 1
        label = f"U+{codepoint:04X}"
        new_names = new_cmap.get(codepoint)
        if not new_names:
            errors.append({"kind": "missing_codepoint", "codepoint": label})
            continue
        old_signatures = [glyph_signature(baseline, old_set, name) for name in old_names]
        new_signatures = [glyph_signature(candidate, new_set, name) for name in new_names]
        for index, kind in enumerate(("outline", "advance_or_lsb", "glyph_hinting")):
            if any(not any(old[index] == new[index] for new in new_signatures)
                   for old in old_signatures):
                errors.append({"kind": kind, "codepoint": label})
    if all_glyphs:
        for name in baseline.getGlyphOrder():
            if name not in new_set:
                errors.append({"kind": "missing_glyph", "glyph": name})
            elif glyph_signature(baseline, old_set, name) != glyph_signature(candidate, new_set, name):
                errors.append({"kind": "glyph_changed", "glyph": name})
    return {"checked_codepoints": checked, "errors": errors}


def validate_icons(font):
    errors, details = [], {}
    cmap, glyph_set = unicode_cmap(font), font.getGlyphSet()
    for codepoint in (0xEC81, 0xEC82):
        label = f"U+{codepoint:04X}"
        names = cmap.get(codepoint)
        if not names:
            errors.append({"kind": "missing_icon", "codepoint": label})
            continue
        signatures = [glyph_signature(font, glyph_set, name) for name in names]
        if any(not any(op in ("lineTo", "qCurveTo", "curveTo") for op, args in outline)
               for outline, metric, hints in signatures):
            errors.append({"kind": "empty_icon", "codepoint": label})
        advances = sorted({metric[0] for outline, metric, hints in signatures})
        details[label] = {"glyphs": sorted(names), "advances": advances}
        if len(advances) != 1 or advances[0] <= 0:
            errors.append({"kind": "invalid_icon_advance", "codepoint": label})
    if len(details) == 2 and details["U+EC81"]["advances"] != details["U+EC82"]["advances"]:
        errors.append({"kind": "inconsistent_icon_advance"})
    return details, errors


def find_fonts(directory):
    result = {}
    for path in Path(directory).rglob("*.ttf"):
        if path.name in result:
            raise ValueError(f"Duplicate font filename: {path.name}")
        result[path.name] = path
    expected = {f"{family}-{style}.ttf" for family in FAMILIES for style in STYLES}
    if set(result) != expected:
        raise ValueError(f"Expected exactly 12 fonts; missing={sorted(expected - result.keys())}, "
                         f"unexpected={sorted(result.keys() - expected)}")
    return result


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_report(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Validate ordinary glyphs and new Nerd Fonts icons in 12 HackGen TTFs.")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    report = {"passed": False, "fonts": [], "errors": []}
    try:
        baseline_paths, candidate_paths = find_fonts(args.baseline), find_fonts(args.candidate)
        for name, baseline_path in sorted(baseline_paths.items()):
            candidate_path = candidate_paths[name]
            with TTFont(baseline_path) as baseline, TTFont(candidate_path) as candidate:
                is_nf = name.split("-")[0].endswith("NF")
                result = compare_fonts(baseline, candidate, include_private=not is_nf,
                                       all_glyphs=not is_nf)
                result.update({"file": name, "baseline_sha256": sha256(baseline_path),
                               "candidate_sha256": sha256(candidate_path)})
                if is_nf:
                    result["icons"], icon_errors = validate_icons(candidate)
                    result["errors"].extend(icon_errors)
                report["fonts"].append(result)
        report["passed"] = all(not font["errors"] for font in report["fonts"])
    except Exception as error:
        report["errors"].append(f"{type(error).__name__}: {error}")
    write_report(args.report, report)
    print(f"Font validation {'passed' if report['passed'] else 'failed'}: {args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
