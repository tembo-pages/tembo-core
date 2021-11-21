"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

PACKAGE_NAME = "tembo"

nav = mkdocs_gen_files.Nav()

for path in sorted(Path(PACKAGE_NAME).glob("**/*.py")):
    module_path = path.relative_to(PACKAGE_NAME).with_suffix("")
    doc_path = path.relative_to(PACKAGE_NAME).with_suffix(".md")
    full_doc_path = Path("code_reference", doc_path)

    parts = list(module_path.parts)
    parts[-1] = f"{parts[-1]}.py"
    nav[parts] = doc_path

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        code_ident = ".".join(module_path.parts)
        print("::: " + PACKAGE_NAME + "." + code_ident, file=fd)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)


with mkdocs_gen_files.open("code_reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
