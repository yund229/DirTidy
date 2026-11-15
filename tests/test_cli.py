import json

import pytest

from dirtidy.cli import main

RULES = {"Images": [".jpg"], "Docs": [".txt"]}


@pytest.fixture
def rules_file(tmp_path):
    f = tmp_path / "rules.json"
    f.write_text(json.dumps(RULES), encoding="utf-8")
    return f


class TestMain:
    def test_once(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        assert main([str(tmp_path)]) == 0
        assert (tmp_path / "Images" / "a.jpg").exists()

    def test_dry_run_flag(self, tmp_path, capsys):
        (tmp_path / "a.jpg").write_text("a")
        assert main([str(tmp_path), "--dry-run"]) == 0
        assert (tmp_path / "a.jpg").exists()
        assert "planned" in capsys.readouterr().out

    def test_dry_run_shows_planned_moves(self, tmp_path, capsys):
        (tmp_path / "a.jpg").write_text("a")
        main([str(tmp_path), "--dry-run"])
        out = capsys.readouterr().out
        assert "a.jpg" in out and "Images" in out

    def test_nothing_to_tidy(self, tmp_path, capsys):
        assert main([str(tmp_path)]) == 0
        assert "nothing" in capsys.readouterr().out

    def test_custom_rules(self, tmp_path, rules_file):
        (tmp_path / "a.jpg").write_text("a")
        assert main([str(tmp_path), "--rules", str(rules_file)]) == 0
        assert (tmp_path / "Images" / "a.jpg").exists()

    def test_undo(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        main([str(tmp_path)])
        assert main([str(tmp_path), "--undo"]) == 0
        assert (tmp_path / "a.jpg").exists()

    def test_undo_all(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        main([str(tmp_path)])
        (tmp_path / "b.txt").write_text("b")
        main([str(tmp_path)])
        assert main([str(tmp_path), "--undo-all"]) == 0
        assert (tmp_path / "a.jpg").exists()
        assert (tmp_path / "b.txt").exists()

    def test_undo_empty(self, tmp_path, capsys):
        assert main([str(tmp_path), "--undo"]) == 0
        assert "nothing" in capsys.readouterr().out

    def test_missing_folder_arg(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 2

    def test_not_a_folder(self, tmp_path):
        assert main([str(tmp_path / "ghost")]) == 2

    def test_bad_rules_file(self, tmp_path, capsys):
        (tmp_path / "bad.json").write_text("nope", encoding="utf-8")
        assert main([str(tmp_path), "--rules", str(tmp_path / "bad.json")]) == 2

    def test_dump_rules(self, tmp_path):
        out = tmp_path / "my.json"
        assert main(["--dump-rules", str(out)]) == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "Images" in data and ".jpg" in data["Images"]

    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        assert "dirtidy" in capsys.readouterr().out
