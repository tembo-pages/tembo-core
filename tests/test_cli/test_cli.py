import importlib
import os
import pathlib

import pytest

import tembo.cli
from tembo.cli.cli import list_all, new


def test_new_dry_run(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "success")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir)
    importlib.reload(tembo.cli)
    scope = "some_scope"
    dry_run = "--dry-run"

    # act
    with pytest.raises(SystemExit) as system_exit:
        new([scope, dry_run])

    # assert
    assert system_exit.value.code == 0
    assert (
        capsys.readouterr().out
        == f"[TEMBO] {tmpdir}/some_scope/some_scope.md will be created 🐘\n"
    )

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]


def test_new_success(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "success")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir)
    importlib.reload(tembo.cli)
    scoped_page_file = pathlib.Path(tmpdir / "some_scope" / "some_scope").with_suffix(
        ".md"
    )

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_scope"])

    # assert
    assert scoped_page_file.exists()
    assert system_exit.value.code == 0
    assert capsys.readouterr().out == f"[TEMBO] Saved {scoped_page_file} to disk 🐘\n"

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]


def test_new_success_already_exists(shared_datadir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "success")
    os.environ["TEMBO_BASE_PATH"] = str(shared_datadir)
    importlib.reload(tembo.cli)
    scoped_page_file = pathlib.Path(
        shared_datadir / "some_scope" / "some_scope"
    ).with_suffix(".md")

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_scope"])

    # assert
    assert scoped_page_file.exists()
    assert system_exit.value.code == 0
    assert (
        capsys.readouterr().out == f"[TEMBO] File {scoped_page_file} already exists 🐘\n"
    )

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]


def test_new_scope_not_found(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "success")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir)
    importlib.reload(tembo.cli)
    scoped_page_file = pathlib.Path(tmpdir / "some_scope" / "some_scope").with_suffix(
        ".md"
    )

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_nonexistent_scope"])

    # assert
    assert not scoped_page_file.exists()
    assert system_exit.value.code == 1
    assert (
        capsys.readouterr().out
        == "[TEMBO] Scope some_nonexistent_scope not found in config.yml 🐘\n"
    )

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]


def test_new_empty_config(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "empty")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir)
    importlib.reload(tembo.cli)

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_nonexistent_scope"])

    # assert
    assert system_exit.value.code == 1
    assert (
        capsys.readouterr().out
        == f"[TEMBO] Config.yml found in {shared_datadir}/config/empty is empty 🐘\n"
    )

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]


def test_new_missing_config(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "missing")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir)
    importlib.reload(tembo.cli)

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_nonexistent_scope"])

    # assert
    assert system_exit.value.code == 1
    assert (
        capsys.readouterr().out
        == f"[TEMBO] No config.yml found in {shared_datadir}/config/missing 🐘\n"
    )

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]


def test_new_missing_mandatory_key(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "missing_keys")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir)
    importlib.reload(tembo.cli)

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_scope"])

    # assert
    assert system_exit.value.code == 1
    assert (
        capsys.readouterr().out == "[TEMBO] Key 'filename' not found in config.yml 🐘\n"
    )

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]


@pytest.mark.parametrize(
    "path,message",
    [
        ("success", "[TEMBO] Example for some_scope: tembo new some_scope 🐘\n"),
        ("optional_keys", "[TEMBO] No example in config.yml 🐘\n"),
    ],
)
def test_new_show_example(path, message, shared_datadir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / path)
    importlib.reload(tembo.cli)

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_scope", "--example"])

    # assert
    assert system_exit.value.code == 0
    assert capsys.readouterr().out == message

    # cleanup
    del os.environ["TEMBO_CONFIG"]


def test_new_base_path_does_not_exist(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "success")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir / "nonexistent" / "path")
    importlib.reload(tembo.cli)

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_scope"])

    # assert
    assert system_exit.value.code == 1
    assert (
        capsys.readouterr().out
        == f"[TEMBO] Tembo base path of {tmpdir}/nonexistent/path does not exist. 🐘\n"
    )

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]


def test_new_template_file_does_not_exist(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "missing_template")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir)
    os.environ["TEMBO_TEMPLATE_PATH"] = str(tmpdir)
    importlib.reload(tembo.cli)

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_scope"])

    # assert
    assert (
        capsys.readouterr().out
        == f"[TEMBO] Template file {tmpdir}/some_nonexistent_template.md.tpl does not exist. 🐘\n"
    )
    assert system_exit.value.code == 1

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_TEMPLATE_PATH"]


def test_new_mismatched_tokens_with_example(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "success")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir)
    importlib.reload(tembo.cli)

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_scope", "input0", "input1"])

    # assert
    assert system_exit.value.code == 1
    assert capsys.readouterr().out == "[TEMBO] Your tembo config.yml/template specifies 0 input tokens, you gave 2. Example: tembo new some_scope 🐘\n"

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]


def test_new_mismatched_tokens_without_example(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "success")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir)
    importlib.reload(tembo.cli)

    # act
    with pytest.raises(SystemExit) as system_exit:
        new(["some_scope_no_example", "input0", "input1"])

    # assert
    assert system_exit.value.code == 1
    assert capsys.readouterr().out == "[TEMBO] Your tembo config.yml/template specifies 0 input tokens, you gave 2 🐘\n"

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]


def test_list_all_success(shared_datadir, tmpdir, capsys):
    # arrange
    os.environ["TEMBO_CONFIG"] = str(shared_datadir / "config" / "success")
    os.environ["TEMBO_BASE_PATH"] = str(tmpdir)
    importlib.reload(tembo.cli)
    scoped_page_file = pathlib.Path(tmpdir / "some_scope" / "some_scope").with_suffix(
        ".md"
    )

    # act
    with pytest.raises(SystemExit) as system_exit:
        list_all([])

    # assert
    assert system_exit.value.code == 0
    assert (
        capsys.readouterr().out
        == "[TEMBO] 3 names found in config.yml: 'some_scope', 'some_scope_no_example', 'another_some_scope' 🐘\n"
    )

    # cleanup
    del os.environ["TEMBO_CONFIG"]
    del os.environ["TEMBO_BASE_PATH"]
