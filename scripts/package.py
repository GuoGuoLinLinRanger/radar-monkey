"""Build dist/tight-job-tailor.skill and dist/radar-monkey-extension.zip.

    python scripts/package.py

A .skill file is just a zip with the skill folder at its root, which is what Claude expects
when you upload it under Settings > Capabilities > Skills.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def zip_dir(src: Path, out: Path, prefix: str = "") -> int:
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if f.is_file() and not any(p.startswith(".") for p in f.relative_to(src).parts):
                z.write(f, Path(prefix) / f.relative_to(src))
                n += 1
    return n


def check_skill(folder: Path) -> str:
    text = (folder / "SKILL.md").read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SystemExit(f"{folder}/SKILL.md is missing its --- frontmatter ---")
    name = re.search(r"^name:\s*(.+)$", m.group(1), re.M)
    desc = re.search(r"^description:\s*(.+)$", m.group(1), re.M)
    if not name or not desc:
        raise SystemExit(f"{folder}/SKILL.md needs name: and description: in its frontmatter")
    if name.group(1).strip() != folder.name:
        raise SystemExit(f"skill name '{name.group(1).strip()}' must match its folder name '{folder.name}'")
    return name.group(1).strip()


def main() -> None:
    DIST.mkdir(exist_ok=True)
    for folder in sorted((ROOT / "packages").iterdir()):
        if (folder / "SKILL.md").exists():
            name = check_skill(folder)
            n = zip_dir(folder, DIST / f"{name}.skill", prefix=name)
            print(f"dist/{name}.skill  ({n} files)")
    version = json.loads((ROOT / "extension" / "manifest.json").read_text())["version"]
    n = zip_dir(ROOT / "extension", DIST / "radar-monkey-extension.zip")
    print(f"dist/radar-monkey-extension.zip  (v{version}, {n} files)")


if __name__ == "__main__":
    main()
