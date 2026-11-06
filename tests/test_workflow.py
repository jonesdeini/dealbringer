import json

import pytest

from dealbringer.cli import main
from dealbringer.history import History
from dealbringer.runner import run
from dealbringer.stores.base import StoreError
from dealbringer.stores.fake import FakeStore


def test_dry_run(tmp_path):
    result = run(FakeStore(tmp_path), dry_run=True)
    assert (result.found, result.previously_clipped, result.skipped) == (4, 1, 3)
    assert result.newly_clipped == result.failed == 0
    assert not (tmp_path / "fake-state.json").exists()


def test_success_and_repeated_run(tmp_path):
    first = run(FakeStore(tmp_path))
    assert (first.newly_clipped, first.previously_clipped, first.skipped) == (2, 1, 1)
    second = run(FakeStore(tmp_path))
    assert (second.newly_clipped, second.previously_clipped, second.skipped) == (0, 3, 1)
    assert not first.errors and not second.errors


@pytest.mark.parametrize("error", [StoreError("private detail"), TimeoutError("private detail")])
def test_partial_failure(tmp_path, monkeypatch, error):
    store = FakeStore(tmp_path)
    original = store.clip

    def clip(offer_id):
        if offer_id == "apples":
            raise error
        original(offer_id)

    monkeypatch.setattr(store, "clip", clip)
    result = run(store)
    assert (result.failed, result.newly_clipped) == (1, 1)
    assert "private detail" not in str(result.errors)


def test_verification_failure(tmp_path, monkeypatch):
    store = FakeStore(tmp_path)
    monkeypatch.setattr(store, "verify", lambda _: False)
    result = run(store)
    assert result.failed == 2
    assert result.newly_clipped == 0


def test_discovery_timeout(tmp_path, monkeypatch):
    store = FakeStore(tmp_path)

    def discover():
        raise TimeoutError("secret")

    monkeypatch.setattr(store, "discover", discover)
    result = run(store)
    assert result.found == 0
    assert result.errors
    assert "secret" not in str(result.errors)


def test_history(tmp_path):
    history = History(tmp_path)
    history.save(run(FakeStore(tmp_path), dry_run=True))
    history.save(run(FakeStore(tmp_path)))
    rows = history.recent()
    assert len(rows) == 2
    assert rows[0]["newly_clipped"] == 2
    assert rows[1]["dry_run"] is True
    assert len(history.recent(1)) == 1


def test_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DEALBRINGER_DATA_DIR", str(tmp_path))
    assert main(["stores"]) == 0
    assert "pending permitted integration" in capsys.readouterr().out
    assert main(["run", "fake", "--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)["newly_clipped"] == 0
    assert main(["run", "fake"]) == 0
    assert json.loads(capsys.readouterr().out)["newly_clipped"] == 2
    assert main(["history"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 2
    assert main(["run", "wegmans"]) == 2
    assert "Milestone 2" in capsys.readouterr().err


def test_cli_corrupt_state(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DEALBRINGER_DATA_DIR", str(tmp_path))
    (tmp_path / "fake-state.json").write_text("invalid")
    assert main(["run", "fake"]) == 2
    assert "Check local data" in capsys.readouterr().err


def test_cli_failed_run_saved(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DEALBRINGER_DATA_DIR", str(tmp_path))

    def clip(self, offer_id):
        raise StoreError("private")

    monkeypatch.setattr(FakeStore, "clip", clip)
    assert main(["run", "fake"]) == 1
    assert json.loads(capsys.readouterr().out)["failed"] == 2
    assert History(tmp_path).recent()[0]["failed"] == 2


def test_cli_unwritable_storage(tmp_path, monkeypatch, capsys):
    path = tmp_path / "file"
    path.write_text("not a directory")
    monkeypatch.setenv("DEALBRINGER_DATA_DIR", str(path))
    assert main(["history"]) == 2
    assert "Check local data" in capsys.readouterr().err
