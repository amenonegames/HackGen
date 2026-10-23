from pathlib import Path
import sys
import tempfile
import unittest

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.ttProgram import Program

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rename_fonts import rename_font
from validate_fonts import compare_fonts, find_fonts, is_private_use, validate_icons


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
        self.assertEqual(validate_icons(font)[1], [])
        font["hmtx"]["openai"] = (1000, 10)
        self.assertIn({"kind": "inconsistent_icon_advance"}, validate_icons(font)[1])
        font["glyf"]["claude"] = TTGlyphPen(None).glyph()
        self.assertIn({"kind": "empty_icon", "codepoint": "U+EC82"}, validate_icons(font)[1])
        for table in font["cmap"].tables:
            table.cmap.pop(0xEC81, None)
        self.assertIn({"kind": "missing_icon", "codepoint": "U+EC81"}, validate_icons(font)[1])

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
