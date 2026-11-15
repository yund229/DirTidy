from dirtidy.mover import execute_moves, journal_path, plan_moves, read_journal, undo_moves
from dirtidy.rules import DEFAULT_RULES


def tidy(folder):
    return execute_moves(plan_moves(folder, DEFAULT_RULES))


class TestUndoMoves:
    def test_undo_restores_last_batch(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        tidy(tmp_path)
        assert (tmp_path / "Images" / "a.jpg").exists()
        restored = undo_moves(tmp_path)
        assert len(restored) == 1
        assert (tmp_path / "a.jpg").exists()
        assert not (tmp_path / "Images" / "a.jpg").exists()
        assert not (tmp_path / "Images").exists()  # empty category dir removed

    def test_undo_keeps_nonempty_category_dirs(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        tidy(tmp_path)
        (tmp_path / "Images" / "manual.jpg").write_text("kept")  # user's own file
        undo_moves(tmp_path)
        assert (tmp_path / "Images" / "manual.jpg").exists()

    def test_undo_clears_journal_when_empty(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        tidy(tmp_path)
        undo_moves(tmp_path)
        assert not journal_path(tmp_path).exists()

    def test_undo_keeps_older_batches(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        tidy(tmp_path)
        (tmp_path / "b.jpg").write_text("b")
        tidy(tmp_path)
        restored = undo_moves(tmp_path)
        assert [r["src"] for r in restored] == [str(tmp_path / "b.jpg")]
        assert (tmp_path / "b.jpg").exists()
        assert (tmp_path / "Images" / "a.jpg").exists()
        assert len(read_journal(tmp_path)) == 1

    def test_undo_all_restores_everything(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        tidy(tmp_path)
        (tmp_path / "b.pdf").write_text("b")
        tidy(tmp_path)
        restored = undo_moves(tmp_path, all=True)
        assert len(restored) == 2
        assert (tmp_path / "a.jpg").exists()
        assert (tmp_path / "b.pdf").exists()
        assert read_journal(tmp_path) == []

    def test_undo_skips_missing_dst(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        tidy(tmp_path)
        (tmp_path / "Images" / "a.jpg").unlink()  # user deleted it meanwhile
        assert undo_moves(tmp_path) == []
        assert not journal_path(tmp_path).exists()

    def test_undo_resolves_conflict_at_origin(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        tidy(tmp_path)
        (tmp_path / "a.jpg").write_text("new")  # a new file took the spot
        restored = undo_moves(tmp_path)
        assert len(restored) == 1
        assert restored[0]["restored_to"] == str(tmp_path / "a (1).jpg")
        assert (tmp_path / "a (1).jpg").read_text(encoding="utf-8") == "a"
        assert (tmp_path / "a.jpg").read_text(encoding="utf-8") == "new"

    def test_undo_nothing_to_do(self, tmp_path):
        assert undo_moves(tmp_path) == []

    def test_undo_skips_malformed_journal_lines(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        tidy(tmp_path)
        with journal_path(tmp_path).open("a", encoding="utf-8") as fh:
            fh.write("not json\n")
        restored = undo_moves(tmp_path)
        assert len(restored) == 1

    def test_repeated_undos_walk_back_history(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        tidy(tmp_path)
        (tmp_path / "b.jpg").write_text("b")
        tidy(tmp_path)
        undo_moves(tmp_path)
        undo_moves(tmp_path)
        assert (tmp_path / "a.jpg").exists()
        assert (tmp_path / "b.jpg").exists()
        assert read_journal(tmp_path) == []
