import time

from dirtidy.watcher import snapshot, watch


class TestSnapshot:
    def test_lists_files_and_dirs(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        (tmp_path / "sub").mkdir()
        snap = snapshot(tmp_path)
        assert "a.jpg" in snap
        assert "sub/" in snap

    def test_changes_when_file_added(self, tmp_path):
        before = snapshot(tmp_path)
        (tmp_path / "a.jpg").write_text("a")
        assert snapshot(tmp_path) != before

    def test_changes_when_file_modified(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        first = snapshot(tmp_path)
        time.sleep(0.05)
        (tmp_path / "a.jpg").write_text("b")
        assert snapshot(tmp_path) != first


class TestWatch:
    def test_initial_pass_and_change_pass(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        (tmp_path / "b.jpg").write_text("b")
        batches: list[list[dict]] = []
        calls = {"n": 0}

        def should_stop():
            calls["n"] += 1
            if calls["n"] == 1:
                # appear during the first poll interval so the watcher
                # observes a change and runs a second pass
                (tmp_path / "c.jpg").write_text("c")
                return False
            return calls["n"] >= 5

        watch(
            tmp_path,
            {"Images": (".jpg",)},
            interval=0.01,
            should_stop=should_stop,
            on_batch=batches.append,
        )

        assert (tmp_path / "Images" / "a.jpg").exists()
        assert (tmp_path / "Images" / "b.jpg").exists()
        assert (tmp_path / "Images" / "c.jpg").exists()
        # initial pass moved 2 files; the change pass moved the file that
        # appeared during polling
        assert [len(b) for b in batches] == [2, 1]

    def test_dry_run_does_not_move(self, tmp_path):
        (tmp_path / "a.jpg").write_text("a")
        watch(
            tmp_path,
            {"Images": (".jpg",)},
            dry_run=True,
            should_stop=lambda: True,
        )
        assert (tmp_path / "a.jpg").exists()
        assert not (tmp_path / "Images").exists()
