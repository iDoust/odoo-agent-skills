"""Validate the vendor-neutral Agent Skills core."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SUPPORTED_VERSIONS = ("17", "18", "19")
REQUIRED_SKILLS = (
    "odoo-development",
    "odoo-debug",
    "odoo-review",
    "odoo-security",
    "odoo-test",
    "odoo-upgrade",
    "odoo-doodba",
    "odoo-query",
    "odoo-token-killer",
)
FORBIDDEN_CORE_TERMS = (
    "claude",
    "claude_",
    "subagent",
    "task tool",
    "codex cli",
    ".claude-plugin",
)
FORBIDDEN_SLASH_COMMAND = re.compile(r"(?<![\w.])/odoo-(?!bin\b)", re.IGNORECASE)
LINK_PATTERN = re.compile(r"\[[^]]+\]\(([^)]+)\)")
GENERATED_CORE_DIRS = frozenset({"__pycache__", ".venv", "target", ".pytest_cache", ".mypy_cache"})


def _frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None

    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip().strip('"\'')
    return values


def _core_files(root: Path) -> list[Path]:
    files = []
    for directory in (root / "skills", root / "references"):
        if directory.is_dir():
            files.extend(
                path
                for path in directory.rglob("*")
                if path.is_file()
                and not any(part in GENERATED_CORE_DIRS for part in path.parts)
                and path.suffix != ".pyc"
            )
    return sorted(files)


def _check_links(path: Path, root: Path) -> list[str]:
    errors = []
    for target in LINK_PATTERN.findall(path.read_text(encoding="utf-8")):
        target = target.split("#", 1)[0].split("?", 1)[0].strip()
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.is_file() or root.resolve() not in resolved.parents:
            errors.append(f"broken local link: {path.relative_to(root)} -> {target}")
    return errors


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    skills_root = root / "skills"
    versions_root = root / "references" / "versions"

    if (root / ".claude-plugin").exists():
        errors.append("root .claude-plugin is not allowed in the universal core")

    for version in SUPPORTED_VERSIONS:
        path = versions_root / f"{version}.md"
        if not path.is_file():
            errors.append(f"missing version reference: references/versions/{version}.md")

    if not skills_root.is_dir():
        errors.append("missing skills directory")
    else:
        for skill_name in REQUIRED_SKILLS:
            if not (skills_root / skill_name / "SKILL.md").is_file():
                errors.append(f"missing required skill: skills/{skill_name}/SKILL.md")
        for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                errors.append(f"missing SKILL.md: {skill_file.relative_to(root)}")
                continue
            metadata = _frontmatter(skill_file.read_text(encoding="utf-8"))
            if metadata is None:
                errors.append(f"invalid frontmatter: {skill_file.relative_to(root)}")
                continue
            if not metadata.get("name") or not metadata.get("description"):
                errors.append(f"frontmatter requires name and description: {skill_file.relative_to(root)}")
            elif metadata["name"] != skill_dir.name:
                errors.append(f"skill name does not match directory: {skill_file.relative_to(root)}")

    for path in _core_files(root):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for term in FORBIDDEN_CORE_TERMS:
            if term in lowered:
                errors.append(f"vendor coupling in core: {path.relative_to(root)} contains {term!r}")
        if FORBIDDEN_SLASH_COMMAND.search(text):
            errors.append(f"vendor coupling in core: {path.relative_to(root)} contains a slash command")
        errors.extend(_check_links(path, root))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).parent.parent)
    args = parser.parse_args()
    errors = validate_repository(args.root)
    if errors:
        print("Validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print("Agent Skills core is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
