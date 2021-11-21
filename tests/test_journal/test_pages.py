from datetime import date
import pathlib

import pytest

from tembo import PageCreatorOptions, ScopedPageCreator
from tembo import exceptions
from tembo.utils import Success


DATE_TODAY = date.today().strftime("%d-%m-%Y")


def test_create_page_base_path_does_not_exist(tmpdir):
    # arrange
    base_path = str(tmpdir / "nonexistent" / "path")
    options = PageCreatorOptions(
        base_path=base_path,
        page_path="",
        filename="",
        extension="",
        name="",
        user_input=None,
        example=None,
        template_filename=None,
        template_path=None,
    )

    # act
    with pytest.raises(
        exceptions.BasePathDoesNotExistError
    ) as base_path_does_not_exist_error:
        scoped_page = ScopedPageCreator(options).create_page()

    # assert
    assert (
        str(base_path_does_not_exist_error.value)
        == f"Tembo base path of {base_path} does not exist."
    )


@pytest.mark.parametrize("template_path", [(None), ("/nonexistent/path")])
def test_create_page_template_file_does_not_exist(template_path, tmpdir):
    # arrange
    options = PageCreatorOptions(
        base_path=str(tmpdir),
        page_path="some_path",
        filename="some_filename",
        extension="some_extension",
        name="some_name",
        user_input=None,
        example=None,
        template_filename="template.md.tpl",
        template_path=template_path,
    )

    # act
    with pytest.raises(
        exceptions.TemplateFileNotFoundError
    ) as template_file_not_found_error:
        scoped_page = ScopedPageCreator(options).create_page()

    # assert
    if template_path is None:
        assert str(template_file_not_found_error.value) == (
            f"Template file {options.base_path}/.templates/{options.template_filename} does not exist."
        )
    else:
        assert str(template_file_not_found_error.value) == (
            f"Template file {template_path}/{options.template_filename} does not exist."
        )


def test_create_page_already_exists(datadir):
    # arrange
    options = PageCreatorOptions(
        base_path=str(datadir),
        page_path="does_exist",
        filename="some_note",
        extension="md",
        name="some_name",
        user_input=None,
        example=None,
        template_filename=None,
        template_path=None,
    )
    scoped_page_file = (
        pathlib.Path(options.base_path) / options.page_path / options.filename
    ).with_suffix(f".{options.extension}")

    # act
    scoped_page = ScopedPageCreator(options).create_page()
    with pytest.raises(exceptions.ScopedPageAlreadyExists) as page_already_exists:
        result = scoped_page.save_to_disk()

    # assert
    assert scoped_page_file.exists()
    assert str(page_already_exists.value) == f"{scoped_page_file} already exists"
    with scoped_page_file.open("r", encoding="utf-8") as scoped_page_contents:
        assert scoped_page_contents.readlines() == ["this file already exists\n"]


def test_create_page_without_template(tmpdir):
    # arrange
    options = PageCreatorOptions(
        base_path=str(tmpdir),
        page_path="some_path",
        filename="some_filename",
        extension="some_extension",
        name="some_name",
        user_input=None,
        example=None,
        template_filename=None,
        template_path=None,
    )
    scoped_page_file = (
        pathlib.Path(options.base_path) / options.page_path / options.filename
    ).with_suffix(f".{options.extension}")

    # act
    scoped_page = ScopedPageCreator(options).create_page()
    result = scoped_page.save_to_disk()

    # assert
    assert scoped_page_file.exists()
    assert isinstance(result, Success)
    assert result.message == str(scoped_page_file)
    with scoped_page_file.open("r", encoding="utf-8") as scoped_page_contents:
        assert scoped_page_contents.readlines() == []


def test_create_page_with_template(datadir, caplog):
    # arrange
    options = PageCreatorOptions(
        base_path=str(datadir),
        page_path="some_path",
        filename="some_note",
        extension="md",
        name="some_name",
        user_input=None,
        example=None,
        template_filename="some_template_no_tokens.md.tpl",
        template_path=None,
    )
    scoped_page_file = (
        pathlib.Path(options.base_path) / options.page_path / options.filename
    ).with_suffix(f".{options.extension}")

    # act
    scoped_page = ScopedPageCreator(options).create_page()
    result = scoped_page.save_to_disk()

    # assert
    assert scoped_page_file.exists()
    assert isinstance(result, Success)
    assert result.message == str(scoped_page_file)
    with scoped_page_file.open("r", encoding="utf-8") as scoped_page_contents:
        assert scoped_page_contents.readlines() == [
            "scoped page file\n",
            "\n",
            "no tokens",
        ]


@pytest.mark.parametrize(
    "user_input,template_filename,page_contents",
    [
        (None, "some_template_date_tokens.md.tpl", f"some date token: {DATE_TODAY}"),
        (
            ("first_input", "second_input"),
            "some_template_input_tokens.md.tpl",
            "some input tokens second_input first_input",
        ),
        (None, "some_template_name_tokens.md.tpl", "some name token some_name"),
    ],
)
def test_create_tokened_page_tokens_in_template(
    datadir, caplog, user_input, template_filename, page_contents
):
    # arrange
    options = PageCreatorOptions(
        base_path=str(datadir),
        page_path="some_path",
        filename="some_note",
        extension="md",
        name="some_name",
        user_input=user_input,
        example=None,
        template_filename=template_filename,
        template_path=None,
    )
    scoped_page_file = (
        pathlib.Path(options.base_path) / options.page_path / options.filename
    ).with_suffix(f".{options.extension}")

    # act
    scoped_page = ScopedPageCreator(options).create_page()
    result = scoped_page.save_to_disk()

    # assert
    assert scoped_page_file.exists()
    assert isinstance(result, Success)
    assert result.message == str(scoped_page_file)

    with scoped_page_file.open("r", encoding="utf-8") as scoped_page_contents:
        assert scoped_page_contents.readline() == page_contents


@pytest.mark.parametrize(
    "user_input,filename,tokened_filename",
    [
        (None, "date_token_{d:%d-%m-%Y}", f"date_token_{DATE_TODAY}"),
        (None, "name_token_{name}", "name_token_some_name"),
        (
            ("first_input", "second input"),
            "input_token_{input1}_{input0}",
            "input_token_second_input_first_input",
        ),
    ],
)
def test_create_tokened_page_tokens_in_filename(
    datadir, caplog, user_input, filename, tokened_filename
):
    # arrange
    options = PageCreatorOptions(
        base_path=str(datadir),
        page_path="some_path",
        filename=filename,
        extension="md",
        name="some_name",
        user_input=user_input,
        example=None,
        template_filename=None,
        template_path=None,
    )
    scoped_page_file = (
        pathlib.Path(options.base_path) / options.page_path / tokened_filename
    ).with_suffix(f".{options.extension}")

    # act
    scoped_page = ScopedPageCreator(options).create_page()
    result = scoped_page.save_to_disk()

    # assert
    assert scoped_page_file.exists()
    assert isinstance(result, Success)
    assert result.message == str(scoped_page_file)


def test_create_tokened_page_input_tokens_preserve_order(datadir, caplog):
    # arrange
    tokened_filename = "input_token_fourth_input_first_input"
    options = PageCreatorOptions(
        base_path=str(datadir),
        page_path="some_path",
        filename="input_token_{input3}_{input0}",
        extension="md",
        name="some_name",
        user_input=("first_input", "second_input", "third_input", "fourth_input"),
        example=None,
        template_filename="some_template_input_tokens_preserve_order.md.tpl",
        template_path=None,
    )
    scoped_page_file = (
        pathlib.Path(options.base_path) / options.page_path / tokened_filename
    ).with_suffix(f".{options.extension}")

    # act
    scoped_page = ScopedPageCreator(options).create_page()
    result = scoped_page.save_to_disk()

    # assert
    assert scoped_page_file.exists()
    assert isinstance(result, Success)
    assert result.message == str(scoped_page_file)
    with scoped_page_file.open(mode="r", encoding="utf-8") as scoped_page_contents:
        assert scoped_page_contents.readline() == "third_input second_input"


@pytest.mark.parametrize(
    "user_input,expected,given",
    [
        (None, 3, 0),
        (("first_input", "second_input"), 3, 2),
        (("first_input", "second_input", "third_input", "fourth_input"), 3, 4),
    ],
)
def test_create_page_mismatched_tokens(tmpdir, user_input, expected, given):
    # arrange
    options = PageCreatorOptions(
        base_path=str(tmpdir),
        page_path="some_path",
        filename="input_token_{input0}_{input1}_{input2}",
        extension="md",
        name="some_name",
        user_input=user_input,
        example=None,
        template_filename=None,
        template_path=None,
    )

    # act
    with pytest.raises(exceptions.MismatchedTokenError) as mismatched_token_error:
        scoped_page = ScopedPageCreator(options).create_page()

    # assert
    assert mismatched_token_error.value.expected == expected
    assert mismatched_token_error.value.given == given


def test_create_page_spaces_in_path(tmpdir, caplog):
    # arrange
    options = PageCreatorOptions(
        base_path=str(tmpdir),
        page_path="some path with a space",
        filename="some filename with a space",
        extension="md",
        name="some_name",
        user_input=None,
        example=None,
        template_filename=None,
        template_path=None,
    )
    scoped_page_file = (
        pathlib.Path(options.base_path)
        / options.page_path.replace(" ", "_")
        / options.filename.replace(" ", "_")
    ).with_suffix(f".{options.extension}")

    # act
    scoped_page = ScopedPageCreator(options).create_page()
    result = scoped_page.save_to_disk()

    # assert
    assert scoped_page_file.exists()
    assert isinstance(result, Success)
    assert result.message == str(scoped_page_file)


def test_create_page_dot_in_extension(tmpdir, caplog):
    # arrange
    options = PageCreatorOptions(
        base_path=str(tmpdir),
        page_path="some_path",
        filename="some_filename",
        extension=".md",
        name="some_name",
        user_input=None,
        example=None,
        template_filename=None,
        template_path=None,
    )
    scoped_page_file = (
        pathlib.Path(options.base_path) / options.page_path / options.filename
    ).with_suffix(f".{options.extension[1:]}")

    # act
    scoped_page = ScopedPageCreator(options).create_page()
    result = scoped_page.save_to_disk()

    # assert
    assert scoped_page_file.exists()
    assert isinstance(result, Success)
    assert result.message == str(scoped_page_file)


def test_create_page_str_representation(tmpdir):
    # arrange
    options = PageCreatorOptions(
        base_path=str(tmpdir),
        page_path="some_path",
        filename="some_filename",
        extension="md",
        name="some_name",
        user_input=None,
        example=None,
        template_filename=None,
        template_path=None,
    )
    scoped_page_file = (
        pathlib.Path(options.base_path) / options.page_path / options.filename
    ).with_suffix(f".{options.extension}")

    # act
    scoped_page = ScopedPageCreator(options).create_page()

    # assert
    assert str(scoped_page) == f"ScopedPage(\"{scoped_page_file}\")"
