#!/usr/bin/env python3
"""Validate revision and claim metadata in Markdown story artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


REQUIRED_FIELDS = (
    "id", "revision", "status", "created_at", "source_refs",
    "claim_status", "supersedes", "stale_reason",
)
ALLOWED_STATUS = {"draft", "needs-human-review", "approved", "superseded"}
ALLOWED_CLAIMS = {"confirmed", "inferred", "unresolved"}
CLAIM_TAG = re.compile(r"\[(confirmed|inferred|unresolved)\]")
REVISION_FILE = re.compile(r"-v(\d+)\.md$")


@dataclass(frozen=True)
class Finding:
    path: str
    code: str
    message: str
    severity: str = "error"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    raw, body = text[4:end], text[end + 5:]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("'\"")
    return data, body


def validate_file(path: Path, root: Path) -> list[Finding]:
    rel = str(path.relative_to(root))
    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    findings: list[Finding] = []

    if not meta:
        return [Finding(rel, "frontmatter.missing", "Missing or malformed YAML frontmatter.")]

    for field in REQUIRED_FIELDS:
        if field not in meta:
            findings.append(Finding(rel, "frontmatter.field", f"Missing required field: {field}."))

    if meta.get("status") not in ALLOWED_STATUS:
        findings.append(Finding(rel, "status.invalid", "status is not an allowed value."))
    if meta.get("claim_status") not in ALLOWED_CLAIMS:
        findings.append(Finding(rel, "claim_status.invalid", "claim_status is not an allowed value."))

    revision = meta.get("revision", "")
    match = REVISION_FILE.search(path.name)
    if revision and (not match or revision != f"v{match.group(1)}"):
        findings.append(Finding(rel, "revision.filename", "revision must match the -vN.md filename suffix."))

    tags = CLAIM_TAG.findall(body)
    if "unresolved" in tags and meta.get("claim_status") != "unresolved":
        findings.append(Finding(rel, "claim_status.unresolved", "An unresolved body claim requires top-level claim_status: unresolved."))

    important_lines = [
        line for line in body.splitlines()
        if line.strip() and not line.lstrip().startswith(("#", "```", "|", "- [", ">"))
    ]
    if important_lines and not tags:
        findings.append(Finding(rel, "claim_tag.missing", "Body contains content but no claim certainty labels.", "warning"))

    if revision == "v1" and meta.get("supersedes") not in {"null", "~", ""}:
        findings.append(Finding(rel, "supersedes.initial", "The first revision must use supersedes: null."))
    return findings


def markdown_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() == ".md" else []
    return sorted(p for p in target.rglob("*.md") if ".git" not in p.parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="Markdown file or project directory")
    parser.add_argument("--json", action="store_true", help="emit JSON findings")
    args = parser.parse_args(argv)
    target = args.target.resolve()
    if not target.exists():
        parser.error(f"target does not exist: {target}")
    root = target if target.is_dir() else target.parent
    findings = [f for path in markdown_files(target) for f in validate_file(path, root)]
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2, ensure_ascii=False))
    elif findings:
        for finding in findings:
            print(f"{finding.severity.upper()} {finding.path}: {finding.code} - {finding.message}")
    else:
        print("No validation findings.")
    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
