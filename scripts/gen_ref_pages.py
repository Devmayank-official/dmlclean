# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Generate the code reference pages for DMLClean documentation.

This script is used by mkdocs-gen-files plugin to automatically
generate API documentation pages from Python source files.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from pathlib import Path

import mkdocs_gen_files

# Navigation object for building the navigation tree
nav = mkdocs_gen_files.Nav()

# Root directory for source code
src_root = Path("src")

# Iterate over all Python files in the source directory
for path in sorted(src_root.rglob("*.py")):
    # Get the module path relative to src/
    module_path = path.relative_to(src_root).with_suffix("")
    doc_path = path.relative_to(src_root).with_suffix(".md")
    full_doc_path = Path("api", doc_path)

    # Handle __init__.py and __main__.py files
    parts = tuple(module_path.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue  # Skip __main__.py files

    # Add to navigation
    nav[parts] = doc_path.as_posix()

    # Generate the documentation page
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        # Get the full module identifier
        identifier = ".".join(parts)
        
        # Write the mkdocstrings directive
        fd.write(f"::: {identifier}\n")
        fd.write("    handler: python\n")
        fd.write("    options:\n")
        fd.write("      show_source: false\n")
        fd.write("      show_root_heading: true\n")
        fd.write("      show_category_heading: true\n")
        fd.write("      merge_init_into_class: true\n")
        fd.write("      docstring_style: google\n")
        fd.write("      show_submodules: true\n")

    # Set the edit path for the generated file
    mkdocs_gen_files.set_edit_path(full_doc_path, path)

# Generate the navigation index file
with mkdocs_gen_files.open("api/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())

print("✓ Generated API reference pages successfully")
