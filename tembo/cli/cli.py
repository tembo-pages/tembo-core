"""Submodule which contains the CLI implementation using Click."""

from __future__ import annotations

import pathlib
from typing import Collection

import click

import tembo.cli
from tembo import exceptions
from tembo._version import __version__
from tembo.journal import pages
from tembo.utils import Success

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS, options_metavar="<options>")
@click.version_option(
    __version__,
    "-v",
    "--version",
    prog_name="Tembo",
    message=f"Tembo v{__version__} 🐘",
)
def main():
    """Tembo - an organiser for work notes."""


@click.command(options_metavar="<options>", name="list")
def list_all():
    """List all scopes defined in the config.yml."""
    _all_scopes = [user_scope["name"] for user_scope in tembo.cli.CONFIG.scopes]
    _all_scopes_joined = "', '".join(_all_scopes)
    cli_message(f"{len(_all_scopes)} names found in config.yml: '{_all_scopes_joined}'")
    raise SystemExit(0)


@click.command(options_metavar="<options>")
@click.argument("scope", metavar="<scope>")
@click.argument(
    "inputs",
    nargs=-1,
    metavar="<inputs>",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show the full path of the page to be created without actually saving the page to disk "
    "and exit.",
)
@click.option(
    "--example",
    is_flag=True,
    default=False,
    help="Show the example command in the config.yml if it exists and exit.",
)
def new(scope: str, inputs: Collection[str], dry_run: bool, example: bool):  # noqa
    """
    Create a new page.

    \b
    `<scope>`   The name of the scope in the config.yml.
    \b
    `<inputs>`  Any input token values that are defined in the config.yml for this scope.
                Accepts multiple inputs separated by a space.

    \b
    Example:
        `tembo new meeting my_presentation`
    """
    # check that the name exists in the config.yml
    try:
        _new_verify_name_exists(scope)
    except (
        exceptions.ScopeNotFound,
        exceptions.EmptyConfigYML,
        exceptions.MissingConfigYML,
    ) as tembo_exception:
        cli_message(tembo_exception.args[0])
        raise SystemExit(1) from tembo_exception

    # get the scope configuration from the config.yml
    try:
        config_scope = _new_get_config_scope(scope)
    except exceptions.MandatoryKeyNotFound as mandatory_key_not_found:
        cli_message(mandatory_key_not_found.args[0])
        raise SystemExit(1) from mandatory_key_not_found

    # if --example flag, return the example to the user
    _new_show_example(example, config_scope)

    # if the name is in the config.yml, create the scoped page
    scoped_page = _new_create_scoped_page(config_scope, inputs)

    if dry_run:
        cli_message(f"{scoped_page.path} will be created")
        raise SystemExit(0)

    try:
        result = scoped_page.save_to_disk()
        if isinstance(result, Success):
            cli_message(f"Saved {result.message} to disk")
        raise SystemExit(0)
    except exceptions.ScopedPageAlreadyExists as scoped_page_already_exists:
        cli_message(f"File {scoped_page_already_exists}")
        raise SystemExit(0) from scoped_page_already_exists


def _new_create_scoped_page(config_scope: dict, inputs: Collection[str]) -> pages.Page:
    page_creator_options = pages.PageCreatorOptions(
        base_path=tembo.cli.CONFIG.base_path,
        template_path=tembo.cli.CONFIG.template_path,
        page_path=config_scope["path"],
        filename=config_scope["filename"],
        extension=config_scope["extension"],
        name=config_scope["name"],
        example=config_scope["example"],
        user_input=inputs,
        template_filename=config_scope["template_filename"],
    )
    try:
        return pages.ScopedPageCreator(page_creator_options).create_page()
    except exceptions.BasePathDoesNotExistError as base_path_does_not_exist_error:
        cli_message(base_path_does_not_exist_error.args[0])
        raise SystemExit(1) from base_path_does_not_exist_error
    except exceptions.TemplateFileNotFoundError as template_file_not_found_error:
        cli_message(template_file_not_found_error.args[0])
        raise SystemExit(1) from template_file_not_found_error
    except exceptions.MismatchedTokenError as mismatched_token_error:
        if config_scope["example"] is not None:
            cli_message(
                f"Your tembo config.yml/template specifies {mismatched_token_error.expected}"
                + f" input tokens, you gave {mismatched_token_error.given}. "
                + f'Example: {config_scope["example"]}'
            )
            raise SystemExit(1) from mismatched_token_error
        cli_message(
            f"Your tembo config.yml/template specifies {mismatched_token_error.expected}"
            + f" input tokens, you gave {mismatched_token_error.given}"
        )

        raise SystemExit(1) from mismatched_token_error


def _new_verify_name_exists(scope: str) -> None:
    _name_found = scope in [user_scope["name"] for user_scope in tembo.cli.CONFIG.scopes]
    if _name_found:
        return
    if len(tembo.cli.CONFIG.scopes) > 0:
        # if the name is missing in the config.yml, raise error
        raise exceptions.ScopeNotFound(f"Scope {scope} not found in config.yml")
    # raise error if no config.yml found
    if pathlib.Path(tembo.cli.CONFIG.config_path).exists():
        raise exceptions.EmptyConfigYML(
            f"Config.yml found in {tembo.cli.CONFIG.config_path} is empty"
        )
    raise exceptions.MissingConfigYML(f"No config.yml found in {tembo.cli.CONFIG.config_path}")


def _new_get_config_scope(scope: str) -> dict:
    config_scope = {}
    optional_keys = ["example", "template_filename"]
    for option in [
        "name",
        "path",
        "filename",
        "extension",
        "example",
        "template_filename",
    ]:
        try:
            config_scope.update(
                {
                    option: str(user_scope[option])
                    for user_scope in tembo.cli.CONFIG.scopes
                    if user_scope["name"] == scope
                }
            )
        except KeyError as key_error:
            if key_error.args[0] in optional_keys:
                config_scope.update({key_error.args[0]: None})
                continue
            raise exceptions.MandatoryKeyNotFound(f"Key {key_error} not found in config.yml")
    return config_scope


def _new_show_example(example: bool, config_scope: dict) -> None:
    if example:
        if isinstance(config_scope["example"], str):
            cli_message(f'Example for {config_scope["name"]}: {config_scope["example"]}')
        else:
            cli_message("No example in config.yml")
        raise SystemExit(0)


def cli_message(message: str) -> None:
    """
    Relay a message to the user using the CLI.

    Args:
        message (str): THe message to be displayed.
    """
    click.echo(f"[TEMBO] {message} 🐘")


main.add_command(new)
main.add_command(list_all)
