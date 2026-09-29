#!/usr/bin/env python3
"""Generate the `nav:` section for mkdocs.yml from the skill knowledge base.

Reads each domain index (references/<domain>/index.md), extracts its leaf-doc
links in *table order* (that is the curated learning order), and emits a YAML
nav block.  Also includes the site home page and the two root-level docs
(SKILL.md entry / AUTHORING.md author guide).

Usage: python3 scripts/gen-nav.py > nav.yml
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "skills" / "frida"
REFS = DOCS / "references"

# (nav label, directory) — order is the intended learning path.
DOMAINS = [
    ("概念 Concepts", "concepts"),
    ("核心 API Core API", "core-api"),
    ("CLI 工具", "cli"),
    ("Android 实战", "android"),
    ("iOS 实战", "ios"),
    ("配方 Recipes", "recipes"),
    ("指南 Guides", "guides"),
    ("演练手册 Playbooks", "playbooks"),
    ("参考表 Reference", "reference"),
    ("排障 Troubleshooting", "troubleshooting"),
]

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")


def leaf_links(index_md: Path):
    """Yield same-directory leaf filenames from an index table, in order."""
    seen = []
    for line in index_md.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        for _label, target in LINK_RE.findall(line):
            # only same-directory links are leaf docs (no ../)
            if "/" not in target and target != "index.md":
                if target not in seen:
                    seen.append(target)
    return seen


def render_nav():
    lines = ["- 首页: index.md"]
    lines.append("- 入门入口: SKILL.md")
    for label, domain in DOMAINS:
        idx = REFS / domain / "index.md"
        lines.append(f"- {label}:")
        lines.append(f"    - {label} 索引: references/{domain}/index.md")
        for leaf in leaf_links(idx):
            # nav paths are relative to docs_dir (skills/frida/)
            lines.append(f"    - {Path(leaf).stem}: references/{domain}/{leaf}")
    lines.append("- 作者指南: AUTHORING.md")
    return "\n".join(lines)


def inject(cfg_path: Path, nav: str) -> None:
    """Replace the `nav:` block in mkdocs.yml with the generated one, in place."""
    cfg = cfg_path.read_text(encoding="utf-8")
    start = cfg.index("nav:\n")
    cfg_path.write_text(cfg[:start] + "nav:\n" + nav + "\n", encoding="utf-8")


def main():
    nav = render_nav()
    if "--inplace" in sys.argv:
        inject(ROOT / "mkdocs.yml", nav)
        print(f"injected nav ({len(nav.splitlines())} lines) into mkdocs.yml")
    else:
        print(nav)


if __name__ == "__main__":
    main()
