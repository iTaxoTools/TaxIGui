#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Update README.md version strings before a release"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def update_readme(gui_version: str, taxi2_version: str) -> None:
    readme = ROOT / "README.md"
    content = readme.read_text(encoding="utf-8")
    content = re.sub(r"v\d+\.\d+\.\d+", gui_version, content)
    content = re.sub(r"TaxI_\d+\.\d+\.\d+", f"TaxI_{taxi2_version}", content)
    content = re.sub(r"TaxI\d+\.\d+\.\d+", f"TaxI{taxi2_version}", content)
    readme.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {Path(__file__).name} <gui-version> <taxi2-version>")
        print(f"Example: python {Path(__file__).name} 0.3.0 2.2.3")
        sys.exit(1)

    gui_arg = sys.argv[1]
    if not re.fullmatch(r"\d+\.\d+\.\d+", gui_arg):
        print(f"Error: expected GUI version like 0.3.0, got {gui_arg!r}")
        sys.exit(1)
    gui_version = f"v{gui_arg}"

    taxi2_version = sys.argv[2]
    if not re.fullmatch(r"\d+\.\d+\.\d+", taxi2_version):
        print(f"Error: expected TaxI2 version like 2.2.3, got {taxi2_version!r}")
        sys.exit(1)

    update_readme(gui_version, taxi2_version)
    print(f"Updated README.md: TaxIGui {gui_version}, TaxI2 {taxi2_version}")
