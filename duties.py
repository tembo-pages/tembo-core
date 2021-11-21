from __future__ import annotations

import importlib
import os
import pathlib
import re
import shutil
import sys
from io import StringIO
from typing import List, Optional, Pattern
from urllib.request import urlopen

from duty import duty

PACKAGE_NAME = "tembo"


@duty(post=["export"])
def update_deps(ctx, dry: bool = False):
    """
    Update the dependencies using Poetry.

    Args:
        ctx: The context instance (passed automatically).
        dry (bool, optional) = If True will update the `poetry.lock` without updating the
            dependencies themselves. Defaults to False.

    Example:
        `duty update_deps dry=False`
    """
    dry_run = "--dry-run" if dry else ""
    ctx.run(
        ["poetry", "update", dry_run],
        title=f"Updating poetry deps {dry_run}",
    )


@duty
def test(ctx):
    """
    Run tests using pytest.

    Args:
        ctx: The context instance (passed automatically).
    """
    pytest_results = ctx.run(["pytest", "-v"], pty=True)
    print(pytest_results)


@duty
def coverage(ctx):
    """
    Generate a coverage report and save to XML and HTML.

    Args:
        ctx: The context instance (passed automatically).

    Example:
        `duty coverage`
    """
    ctx.run(["coverage", "run", "--source", PACKAGE_NAME, "-m", "pytest"])
    res = ctx.run(["coverage", "report"], pty=True)
    print(res)
    ctx.run(["coverage", "html"])
    ctx.run(["coverage", "xml"])


@duty
def bump(ctx, version: str = "patch"):
    """
    Bump the version using Poetry and update _version.py.

    Args:
        ctx: The context instance (passed automatically).
        version (str, optional) = poetry version flag. Available options are:
            patch, minor, major. Defaults to patch.

    Example:
        `duty bump version=major`
    """

    # bump with poetry
    result = ctx.run(["poetry", "version", version])
    new_version = re.search(r"(?:.*)(?:\s)(\d+\.\d+\.\d+)$", result)
    print(new_version.group(0))

    # update _version.py
    version_file = pathlib.Path(PACKAGE_NAME) / "_version.py"
    with version_file.open("w", encoding="utf-8") as version_file:
        version_file.write(
            f'"""Module containing the version of {PACKAGE_NAME}."""\n\n' + f'__version__ = "{new_version.group(1)}"\n'
        )
    print(f"Bumped _version.py to {new_version.group(1)}")


@duty
def build(ctx):
    """
    Build with poetry and extract the setup.py and copy to project root.

    Args:
        ctx: The context instance (passed automatically).

    Example:
        `duty build`
    """

    repo_root = pathlib.Path(".")

    # build with poetry
    result = ctx.run(["poetry", "build"])
    print(result)

    # extract the setup.py from the tar
    extracted_tar = re.search(r"(?:.*)(?:Built\s)(.*)", result)
    tar_file = pathlib.Path(f"./dist/{extracted_tar.group(1)}")
    shutil.unpack_archive(tar_file, tar_file.parents[0])

    # copy setup.py to repo root
    extracted_path = tar_file.parents[0] / os.path.splitext(tar_file.stem)[0]
    setup_py = extracted_path / "setup.py"
    shutil.copyfile(setup_py, (repo_root / "setup.py"))

    # cleanup
    shutil.rmtree(extracted_path)


@duty
def release(ctx, version: str = "patch") -> None:
    """
    Prepare package for a new release.

    Will run bump, build, export. Manual running of publish is required afterwards.

    Args:
        ctx: The context instance (passed automatically).
        version (str): poetry version flag. Available options are: patch, minor, major.
    """
    print(ctx.run(["duty", "bump", f"version={version}"]))
    ctx.run(["duty", "build"])
    ctx.run(["duty", "export"])


@duty
def export(ctx):
    """
    Export the dependencies to a requirements.txt file.

    Args:
        ctx: The context instance (passed automatically).

    Example:
        `duty export`
    """
    requirements_content = ctx.run(
        [
            "poetry",
            "export",
            "-f",
            "requirements.txt",
            "--without-hashes",
        ]
    )
    requirements_dev_content = ctx.run(
        [
            "poetry",
            "export",
            "-f",
            "requirements.txt",
            "--without-hashes",
            "--dev",
        ]
    )

    requirements = pathlib.Path(".") / "requirements.txt"
    requirements_dev = pathlib.Path(".") / "requirements_dev.txt"

    with requirements.open("w", encoding="utf-8") as req:
        req.write(requirements_content)

    with requirements_dev.open("w", encoding="utf-8") as req:
        req.write(requirements_dev_content)


@duty
def publish(ctx, password: str):
    """
    Publish the package to pypi.org.

    Args:
        ctx: The context instance (passed automatically).
        password (str): pypi.org password.

    Example:
        `duty publish password=$my_password`
    """
    dist_dir = pathlib.Path(".") / "dist"
    rm_result = rm_tree(dist_dir)
    print(rm_result)

    publish_result = ctx.run(["poetry", "publish", "-u", "dtomlinson", "-p", password, "--build"])
    print(publish_result)


@duty(silent=True)
def clean(ctx):
    """
    Delete temporary files.

    Args:
        ctx: The context instance (passed automatically).
    """
    ctx.run("rm -rf .mypy_cache")
    ctx.run("rm -rf .pytest_cache")
    ctx.run("rm -rf tests/.pytest_cache")
    ctx.run("rm -rf build")
    ctx.run("rm -rf dist")
    ctx.run("rm -rf pip-wheel-metadata")
    ctx.run("rm -rf site")
    ctx.run("rm -rf coverage.xml")
    ctx.run("rm -rf pytest.xml")
    ctx.run("rm -rf htmlcov")
    ctx.run("find . -iname '.coverage*' -not -name .coveragerc | xargs rm -rf")
    ctx.run("find . -type d -name __pycache__ | xargs rm -rf")
    ctx.run("find . -name '*.rej' -delete")


@duty
def format(ctx):
    """
    Format code using Black and isort.

    Args:
        ctx: The context instance (passed automatically).
    """
    res = ctx.run(["black", "--line-length=99", PACKAGE_NAME], pty=True, title="Running Black")
    print(res)

    res = ctx.run(["isort", PACKAGE_NAME])
    print(res)


@duty(pre=["check_code_quality", "check_types", "check_docs", "check_dependencies"])
def check(ctx):
    """
    Check the code quality, check types, check documentation builds and check dependencies for vulnerabilities.

    Args:
        ctx: The context instance (passed automatically).
    """


@duty
def check_code_quality(ctx):
    """
    Check the code quality using prospector.

    Args:
        ctx: The context instance (passed automatically).
    """
    ctx.run(["prospector", PACKAGE_NAME], pty=True, title="Checking code quality with prospector")


@duty
def check_types(ctx):
    """
    Check the types using mypy.

    Args:
        ctx: The context instance (passed automatically).
    """
    ctx.run(["mypy", PACKAGE_NAME], pty=True, title="Checking types with MyPy")


@duty
def check_docs(ctx):
    """
    Check the documentation builds successfully.

    Args:
        ctx: The context instance (passed automatically).
    """
    ctx.run(["mkdocs", "build"], title="Building documentation")


@duty
def check_dependencies(ctx):
    """
    Check dependencies with safety for vulnerabilities.

    Args:
        ctx: The context instance (passed automatically).
    """
    for module in sys.modules:
        if module.startswith("safety.") or module == "safety":
            del sys.modules[module]

    importlib.invalidate_caches()

    from safety import safety
    from safety.formatter import report
    from safety.util import read_requirements

    requirements = ctx.run(
        "poetry export --dev --without-hashes",
        title="Exporting dependencies as requirements",
        allow_overrides=False,
    )

    def check_vulns():
        packages = list(read_requirements(StringIO(requirements)))
        vulns = safety.check(packages=packages, ignore_ids="41002", key="", db_mirror="", cached=False, proxy={})
        output_report = report(vulns=vulns, full=True, checked_packages=len(packages))
        print(vulns)
        if vulns:
            print(output_report)

    ctx.run(
        check_vulns,
        stdin=requirements,
        title="Checking dependencies",
        pty=True,
    )


def _latest(lines: List[str], regex: Pattern) -> Optional[str]:
    for line in lines:
        match = regex.search(line)
        if match:
            return match.groupdict()["version"]
    return None


def _unreleased(versions, last_release):
    for index, version in enumerate(versions):
        if version.tag == last_release:
            return versions[:index]
    return versions


def update_changelog(
    inplace_file: str,
    marker: str,
    version_regex: str,
    commit_style: str,
    planned_tag: str,
    last_released: str,
) -> None:
    """
    Update the given changelog file in place.
    Arguments:
        inplace_file: The file to update in-place.
        marker: The line after which to insert new contents.
        version_regex: A regular expression to find currently documented versions in the file.
        template_url: The URL to the Jinja template used to render contents.
        commit_style: The style of commit messages to parse.
    """
    from git_changelog.build import Changelog
    from jinja2.sandbox import SandboxedEnvironment

    env = SandboxedEnvironment(autoescape=False)
    template = env.from_string(changelog_template())
    changelog = Changelog(".", style=commit_style)

    if len(changelog.versions_list) == 1:
        last_version = changelog.versions_list[0]
        print(last_version.planned_tag)
        if last_version.planned_tag is None:
            planned_tag = planned_tag
            last_version.tag = planned_tag
            last_version.url += planned_tag
            last_version.compare_url = last_version.compare_url.replace("HEAD", planned_tag)

    with open(inplace_file, "r") as changelog_file:
        lines = changelog_file.read().splitlines()

    # last_released = _latest(lines, re.compile(version_regex))
    last_released = last_released
    print(last_released)
    if last_released:
        changelog.versions_list = _unreleased(changelog.versions_list, last_released)
    rendered = template.render(changelog=changelog, inplace=True)
    lines[lines.index(marker)] = rendered

    with open(inplace_file, "w") as changelog_file:  # noqa: WPS440
        changelog_file.write("\n".join(lines).rstrip("\n") + "\n")


# @duty
def changelog(planned_tag, last_released):
    """
    Update the changelog in-place with latest commits.
    Arguments:
        ctx: The context instance (passed automatically).
    """
    # print(
    #     ctx.run(
    #         update_changelog,
    #         kwargs={
    #             "inplace_file": "CHANGELOG.md",
    #             "marker": "<!-- insertion marker -->",
    #             "version_regex": r"^## \[v?(?P<version>[^\]]+)",
    #             "commit_style": "angular",
    #         },
    #         title="Updating changelog",
    #         pty=True,
    #     )
    # )

    update_changelog(
        inplace_file="CHANGELOG.md",
        marker="<!-- insertion marker -->",
        version_regex=r"^## \[v?(?P<version>[^\]]+)",
        commit_style="angular",
        planned_tag=planned_tag,
        last_released=last_released
    )




def rm_tree(directory: pathlib.Path):
    """
    Recursively delete a directory and all its contents.

    Args:
        directory (pathlib.Path): The directory to delete.
    """
    for child in directory.glob("*"):
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)
    directory.rmdir()


def changelog_template() -> str:
    return """
{% if not inplace -%}
# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

{% endif %}<!-- insertion marker -->
{% macro render_commit(commit) -%}
- {{ commit.style.subject|default(commit.subject) }} ([{{ commit.hash|truncate(7, True, '') }}]({{ commit.url }}) by {{ commit.author_name }}).
{%- if commit.text_refs.issues_not_in_subject %} References: {% for issue in commit.text_refs.issues_not_in_subject -%}
{% if issue.url %}[{{ issue.ref }}]({{ issue.url }}){%else %}{{ issue.ref }}{% endif %}{% if not loop.last %}, {% endif -%}
{%- endfor -%}{%- endif -%}
{%- endmacro -%}

{%- macro render_section(section) -%}
### {{ section.type or "Misc" }}
{% for commit in section.commits|sort(attribute='author_date',reverse=true)|unique(attribute='subject') -%}
{{ render_commit(commit) }}
{% endfor %}
{%- endmacro -%}

{%- macro render_version(version) -%}
{%- if version.tag or version.planned_tag -%}
## [{{ version.tag or version.planned_tag }}]({{ version.url }}){% if version.date %} - {{ version.date }}{% endif %}

<small>[Compare with {{ version.previous_version.tag|default("first commit") }}]({{ version.compare_url }})</small>
{%- else -%}
## Unrealeased

<small>[Compare with latest]({{ version.compare_url }})</small>
{%- endif %}

{% for type, section in version.sections_dict|dictsort -%}
{%- if type and type in changelog.style.DEFAULT_RENDER -%}
{{ render_section(section) }}
{% endif -%}
{%- endfor -%}
{%- endmacro -%}

{% for version in changelog.versions_list -%}
{{ render_version(version) }}
{%- endfor -%}
    """


if __name__ == "__main__":
    changelog("1.0.1", "1.0.0")
