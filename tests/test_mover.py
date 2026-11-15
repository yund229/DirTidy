import json
from pathlib import Path

from dirtidy.mover import (
    execute_moves,
    journal_path,
    plan_moves,
    read_journal,
    run_once,
    unique_destination,
)
from dirtidy.rules import DEFAULT_RULES


def make(folder, *names):
    for name in names:
        (folder / name).write_text(name, encoding="utf-8")


class TestPlanMoves:
    def test_basic_plan(self, tmp_path):
        make(tmp_path, "a.jpg", "b.pdf", "c.zip")
        plans = plan_moves(tmp_path, DEFAULT_RULES)
        assert [(p.src.name, p.category) for p in plans] == [
            ("a.jpg", "Images"),
            ("b.pdf", "Documents"),
            ("c.zip", "Archives"),
        ]

    def test_dst_in_category_dir(self, tmp_path):
        make(tmp_path, "a.jpg")
        (plan,) = plan_moves(tmp_path, DEFAULT_RULES)
        assert plan.dst == tmp_path / "Images" / "a.jpg"

    def test_skips_directories(self, tmp_path):
        (tmp_path / "Images").mkdir()
        (tmp_path / "Images" / "nested.jpg").write_text("x")
        assert plan_moves(tmp_path, DEFAULT_RULES) == []

    def test_skips_hidden_files(self, tmp_path):
        make(tmp_path, ".hidden.jpg")
        assert plan_moves(tmp_path, DEFAULT_RULES) == []

    def test_skips_journal(self, tmp_path):
        journal_path(tmp_path).write_text("", encoding="utf-8")
        assert plan_moves(tmp_path, DEFAULT_RULES) == []

    def test_skips_unmatched(self, tmp_path):
        make(tmp_path, "Makefile", "weird.xyz")
        assert plan_moves(tmp_path, DEFAULT_RULES) == []

    def test_skips_category_dirs_even_if_file_named_so(self, tmp_path):
        make(tmp_path, "Images")  # a *file* named like a category dir
        assert plan_moves(tmp_path, DEFAULT_RULES) == []

    def test_conflict_gets_numbered_name(self, tmp_path):
        (tmp_path / "Images").mkdir()
        make(tmp_path / "Images", "a.jpg")
        make(tmp_path, "a.jpg")
        (plan,) = plan_moves(tmp_path, DEFAULT_RULES)
        assert plan.dst == tmp_path / "Images" / "a (1).jpg"

    def test_conflict_increments(self, tmp_path):
        (tmp_path / "Images").mkdir()
        make(tmp_path / "Images", "a.jpg", "a (1).jpg")
        make(tmp_path, "a.jpg")
        (plan,) = plan_moves(tmp_path, DEFAULT_RULES)
        assert plan.dst == tmp_path / "Images" / "a (2).jpg"


class TestUniqueDestination:
    def test_free_name_untouched(self, tmp_path):
        dst = tmp_path / "x.txt"
        assert unique_destination(dst) == dst

    def test_taken_name_numbered(self, tmp_path):
        (tmp_path / "x.txt").write_text("a")
        assert unique_destination(tmp_path / "x.txt") == tmp_path / "x (1).txt"

    def test_no_extension(self, tmp_path):
        (tmp_path / "x").write_text("a")
        assert unique_destination(tmp_path / "x") == tmp_path / "x (1)"


class TestExecuteMoves:
    def test_moves_files_and_creates_dirs(self, tmp_path):
        make(tmp_path, "a.jpg", "b.pdf")
        plans = plan_moves(tmp_path, DEFAULT_RULES)
        execute_moves(plans)
        assert (tmp_path / "Images" / "a.jpg").exists()
        assert (tmp_path / "Documents" / "b.pdf").exists()
        assert not (tmp_path / "a.jpg").exists()

    def test_dry_run_moves_nothing(self, tmp_path):
        make(tmp_path, "a.jpg")
        entries = execute_moves(plan_moves(tmp_path, DEFAULT_RULES), dry_run=True)
        assert entries == []
        assert (tmp_path / "a.jpg").exists()
        assert not (tmp_path / "Images").exists()

    def test_empty_plans_noop(self, tmp_path):
        assert execute_moves([]) == []

    def test_journals_batch(self, tmp_path):
        make(tmp_path, "a.jpg", "b.pdf")
        entries = execute_moves(plan_moves(tmp_path, DEFAULT_RULES))
        stored = read_journal(tmp_path)
        assert stored == entries
        assert {e["category"] for e in stored} == {"Images", "Documents"}
        for entry in stored:
            assert entry["src"] == str(tmp_path / Path(entry["src"]).name)
            assert entry["time"]

    def test_journal_is_valid_jsonl(self, tmp_path):
        make(tmp_path, "a.jpg")
        execute_moves(plan_moves(tmp_path, DEFAULT_RULES))
        lines = journal_path(tmp_path).read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["category"] == "Images"

    def test_run_once(self, tmp_path):
        make(tmp_path, "a.jpg", "no-match.xyz")
        entries = run_once(tmp_path, DEFAULT_RULES)
        assert len(entries) == 1
        assert (tmp_path / "Images" / "a.jpg").exists()
