from pathlib import Path
import sys
import tempfile
import unittest

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.ttLib.tables.ttProgram import Program

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rename_fonts import compare_preserved_tables, rename_font
from validate_fonts import (
    compare_fonts, find_fonts, is_private_use, nerd_selection_ranges,
    selected_nerd_codepoints, validate_icons, validate_nerd_coverage,
)


def make_font():
    builder = FontBuilder(1000, isTTF=True)
    glyphs = {}
    for name in (".notdef", "a", "openai", "claude"):
        pen = TTGlyphPen(None)
        if name != ".notdef":
            pen.moveTo((10, 0))
            pen.lineTo((200, 500))
            pen.lineTo((400, 0))
            pen.closePath()
        glyphs[name] = pen.glyph()
    builder.setupGlyphOrder(list(glyphs))
    builder.setupCharacterMap({0x61: "a", 0xEC81: "openai", 0xEC82: "claude"})
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({name: (500, 10) for name in glyphs})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "HackGen Console NF", "styleName": "Regular",
                           "uniqueFontIdentifier": "HackGenConsoleNF-Regular-1.0",
                           "fullName": "HackGen Console NF Regular",
                           "psName": "HackGenConsoleNF-Regular",
                           "copyright": "HackGen original copyright",
                           "licenseDescription": "Original OFL license"})
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    builder.setupPost()
    builder.setupMaxp()
    return builder.font


def add_variation(font, glyph_name):
    table = CmapSubtable.newSubtable(14)
    table.platformID = 0
    table.platEncID = 5
    table.language = 0
    table.cmap = {}
    table.uvsDict = {0xE0100: [(0x61, glyph_name)]}
    font["cmap"].tables.append(table)


class FontValidationTests(unittest.TestCase):
    def test_identical_font_passes(self):
        result = compare_fonts(make_font(), make_font(), include_private=True, all_glyphs=True)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["checked_codepoints"], 3)

    def test_private_use_boundaries(self):
        for value in (0xE000, 0xF8FF, 0xF0000, 0xFFFFD, 0x100000, 0x10FFFD):
            self.assertTrue(is_private_use(value))
        for value in (0xDFFF, 0xF900, 0xEFFff, 0xFFFFE, 0x10FFFE):
            self.assertFalse(is_private_use(value))

    def test_ordinary_outline_metrics_and_hints_are_checked(self):
        baseline, candidate = make_font(), make_font()
        candidate["glyf"]["a"].coordinates[0] = (11, 0)
        candidate["hmtx"]["a"] = (501, 10)
        candidate["glyf"]["a"].program = Program()
        candidate["glyf"]["a"].program.fromBytecode([0])
        candidate["hhea"].ascent += 1
        kinds = {item["kind"] for item in compare_fonts(baseline, candidate)["errors"]}
        self.assertEqual(kinds, {"outline", "advance_or_lsb", "glyph_hinting", "font_metric"})

    def test_private_use_change_is_excluded_only_when_requested(self):
        baseline, candidate = make_font(), make_font()
        candidate["glyf"]["openai"].coordinates[0] = (11, 0)
        self.assertEqual(compare_fonts(baseline, candidate)["errors"], [])
        self.assertTrue(compare_fonts(baseline, candidate, include_private=True)["errors"])

    def test_missing_ordinary_character_fails(self):
        baseline, candidate = make_font(), make_font()
        for table in candidate["cmap"].tables:
            table.cmap.pop(0x61, None)
        self.assertEqual(compare_fonts(baseline, candidate)["errors"],
                         [{"kind": "missing_codepoint", "codepoint": "U+0061"}])

    def test_icon_presence_outline_and_advances(self):
        font = make_font()
        self.assertEqual(validate_icons(font, 500)[1], [])
        font["hmtx"]["openai"] = (1000, 10)
        self.assertIn({"kind": "inconsistent_icon_advance"}, validate_icons(font, 500)[1])
        font["glyf"]["claude"] = TTGlyphPen(None).glyph()
        self.assertIn({"kind": "empty_icon", "codepoint": "U+EC82"}, validate_icons(font, 500)[1])
        for table in font["cmap"].tables:
            table.cmap.pop(0xEC81, None)
        self.assertIn({"kind": "missing_icon", "codepoint": "U+EC81"}, validate_icons(font, 500)[1])

    def test_icons_with_equal_but_incorrect_advances_fail(self):
        for expected in (540, 618):
            errors = validate_icons(make_font(), expected)[1]
            self.assertEqual(len(errors), 2)
            self.assertTrue(all(error["kind"] == "unexpected_icon_advance" for error in errors))

    def test_nerd_coverage_uses_source_cmap_intersection_with_selection(self):
        selections = nerd_selection_ranges('''select_nerd_symbols="
  # Selected icons
  SelectMore(0uEC81, 0uEC83)
  SelectMore(0u2665)
"
other_symbols="
  SelectMore(0u61)
"
''')
        expected = selected_nerd_codepoints(make_font(), selections)
        self.assertEqual(expected, {0xEC81, 0xEC82})
        candidate = make_font()
        self.assertEqual(validate_nerd_coverage(candidate, expected)[1], [])
        for table in candidate["cmap"].tables:
            table.cmap.pop(0xEC82, None)
        details, errors = validate_nerd_coverage(candidate, expected)
        self.assertEqual(details, {"expected_codepoints": 2, "present_codepoints": 1})
        self.assertEqual(errors, [{"kind": "missing_nerd_codepoint", "codepoint": "U+EC82"}])

    def test_unknown_nerd_selection_syntax_fails(self):
        with self.assertRaisesRegex(ValueError, "Unsupported Nerd Fonts selection"):
            nerd_selection_ranges('select_nerd_symbols="\n  ${another_selection}\n"\n')

    def test_variation_outline_is_checked_even_when_glyph_has_private_mapping(self):
        baseline, candidate = make_font(), make_font()
        add_variation(baseline, "openai")
        add_variation(candidate, "openai")
        candidate["glyf"]["openai"].coordinates[0] = (11, 0)
        result = compare_fonts(baseline, candidate)
        self.assertEqual(result["checked_variation_sequences"], 1)
        self.assertEqual(result["errors"], [{"kind": "outline", "codepoint": "U+0061 U+E0100"}])

    def test_missing_variation_sequence_fails(self):
        baseline, candidate = make_font(), make_font()
        add_variation(baseline, None)
        self.assertEqual(compare_fonts(baseline, candidate)["errors"],
                         [{"kind": "missing_variation_sequence", "codepoint": "U+0061 U+E0100"}])

    def test_default_variation_uses_default_cmap_glyph(self):
        baseline, candidate = make_font(), make_font()
        add_variation(baseline, None)
        add_variation(candidate, "a")
        self.assertEqual(compare_fonts(baseline, candidate)["errors"], [])

    def test_raw_table_and_head_field_changes_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory) / "source.ttf", Path(directory) / "target.ttf"
            font = make_font()
            font.save(source)
            font["post"].underlinePosition -= 1
            font["head"].flags ^= 1
            font.save(target)
            with TTFont(source) as baseline, TTFont(target) as candidate:
                errors = compare_preserved_tables(baseline, candidate)
            self.assertIn({"kind": "table_bytes_changed", "table": "post"}, errors)
            self.assertTrue(any(error["kind"] == "head_field_changed"
                                and error["field"] == "flags" for error in errors))

    def test_rename_preserves_shapes_metrics_and_legal_names(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "HackGenConsoleNF-Regular.ttf"
            target = Path(directory) / "AmenoConsoleNF-Regular.ttf"
            make_font().save(source)
            result = rename_font(source, target)
            self.assertEqual(result["errors"], [])
            with TTFont(target) as font:
                self.assertEqual(font["name"].getDebugName(1), "Ameno Console NF")
                self.assertEqual(font["name"].getDebugName(6), "AmenoConsoleNF-Regular")
                self.assertEqual(font["name"].getDebugName(0), "HackGen original copyright")
                self.assertEqual(font["name"].getDebugName(13), "Original OFL license")

    def test_missing_build_outputs_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Expected exactly 12 fonts"):
                find_fonts(directory)


if __name__ == "__main__":
    unittest.main()
