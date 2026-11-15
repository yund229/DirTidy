import json

import pytest

from dirtidy.rules import DEFAULT_RULES, category_for, load_rules


class TestCategoryFor:
    def test_image(self):
        assert category_for("photo.jpg", DEFAULT_RULES) == "Images"

    def test_case_insensitive(self):
        assert category_for("REPORT.PDF", DEFAULT_RULES) == "Documents"

    def test_installer(self):
        assert category_for("setup.EXE", DEFAULT_RULES) == "Installers"

    def test_archive(self):
        assert category_for("backup.7z", DEFAULT_RULES) == "Archives"

    def test_video(self):
        assert category_for("clip.mkv", DEFAULT_RULES) == "Videos"

    def test_audio(self):
        assert category_for("song.flac", DEFAULT_RULES) == "Audio"

    def test_font(self):
        assert category_for("Roboto.ttf", DEFAULT_RULES) == "Fonts"

    def test_code(self):
        assert category_for("app.py", DEFAULT_RULES) == "Code"

    def test_unknown_ext(self):
        assert category_for("data.xyz123", DEFAULT_RULES) is None

    def test_no_ext(self):
        assert category_for("Makefile", DEFAULT_RULES) is None

    def test_hidden_file(self):
        assert category_for(".gitignore", DEFAULT_RULES) is None

    def test_first_match_wins(self):
        rules = {"A": (".jpg",), "B": (".jpg",)}
        assert category_for("a.jpg", rules) == "A"

    def test_custom_category(self):
        rules = {"Work": (".docx",)}
        assert category_for("spec.docx", rules) == "Work"


class TestLoadRules:
    def test_default_copy_is_independent(self):
        rules = load_rules()
        assert rules is not DEFAULT_RULES
        assert rules == DEFAULT_RULES

    def test_load_from_json(self, tmp_path):
        f = tmp_path / "rules.json"
        f.write_text(json.dumps({"Stuff": [".AAA", ".bbb"]}), encoding="utf-8")
        rules = load_rules(f)
        assert rules == {"Stuff": (".aaa", ".bbb")}

    def test_exts_normalized_to_lowercase(self, tmp_path):
        f = tmp_path / "rules.json"
        f.write_text(json.dumps({"X": [".PNG"]}), encoding="utf-8")
        assert load_rules(f) == {"X": (".png",)}

    def test_replaces_defaults(self, tmp_path):
        f = tmp_path / "rules.json"
        f.write_text(json.dumps({"Only": [".bin"]}), encoding="utf-8")
        assert category_for("photo.jpg", load_rules(f)) is None

    def test_invalid_json_raises(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{oops", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_rules(f)

    def test_wrong_shape_raises(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text(json.dumps({"A": "not-a-list"}), encoding="utf-8")
        with pytest.raises(ValueError):
            load_rules(f)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(OSError):
            load_rules(tmp_path / "nope.json")
