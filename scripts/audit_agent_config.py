#!/usr/bin/env python3
"""Heuristically audit AI-agent configuration without executing it."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


TEXT_NAMES = {"AGENTS.md", "SKILL.md", ".mcp.json", "plugin.json"}
RULES = (
    ("SCG001", "high", re.compile(r"(?:curl|wget)[^\n|]{0,300}\|\s*(?:sh|bash|zsh|powershell|pwsh)\b", re.I), "Remote content is piped directly to a shell."),
    ("SCG002", "high", re.compile(r"(?:invoke-expression|\biex\b|\beval\b).{0,160}(?:base64|frombase64|atob)", re.I), "Encoded content may be executed dynamically."),
    ("SCG003", "high", re.compile(r"(?:api[_-]?key|token|secret|password)\s*[=:]\s*['\"]?(?!\$\{|\$env:|<|your[-_ ])[A-Za-z0-9_./+\-=]{16,}", re.I), "A secret-like literal appears in configuration."),
    ("SCG004", "medium", re.compile(r"http://(?!localhost\b|127\.0\.0\.1\b|\[::1\])", re.I), "Configuration references unencrypted HTTP transport."),
    ("SCG005", "medium", re.compile(r"(?:\.\.[/\\]){2,}"), "A path traverses multiple parent directories."),
    ("SCG006", "medium", re.compile(r"(?:disable|bypass|ignore).{0,80}(?:security|approval|review|sandbox|permission)", re.I), "Instructions appear to suppress a safety or review control."),
)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    path: str
    line: int
    message: str
    evidence: str


def candidate_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    files: list[Path] = []
    for path in target.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.name in TEXT_NAMES:
            files.append(path)
    return sorted(files)


def audit_file(path: Path, root: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    rel = str(path.relative_to(root)) if path != root else path.name
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), 1):
        for rule_id, severity, pattern, message in RULES:
            match = pattern.search(line)
            if match:
                evidence = match.group(0).strip()
                if len(evidence) > 160:
                    evidence = evidence[:157] + "..."
                findings.append(Finding(rule_id, severity, rel, number, message, evidence))
    return findings


def as_sarif(findings: list[Finding]) -> dict:
    rules = {f.rule_id: f for f in findings}
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {"driver": {
                "name": "Story Continuity Guard",
                "informationUri": "https://github.com/taihu777/story-continuity-guard",
                "rules": [{"id": r.rule_id, "shortDescription": {"text": r.message}} for r in rules.values()],
            }},
            "results": [{
                "ruleId": f.rule_id,
                "level": "error" if f.severity == "high" else "warning",
                "message": {"text": f.message},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": f.path.replace("\\", "/")},
                    "region": {"startLine": f.line},
                }}],
            } for f in findings],
        }],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="agent project directory or configuration file")
    parser.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    args = parser.parse_args(argv)
    target = args.target.resolve()
    if not target.exists():
        parser.error(f"target does not exist: {target}")
    root = target if target.is_dir() else target.parent
    findings = [f for path in candidate_files(target) for f in audit_file(path, root)]
    if args.format == "json":
        print(json.dumps([asdict(f) for f in findings], indent=2, ensure_ascii=False))
    elif args.format == "sarif":
        print(json.dumps(as_sarif(findings), indent=2, ensure_ascii=False))
    elif findings:
        for f in findings:
            print(f"{f.severity.upper()} {f.path}:{f.line} {f.rule_id} - {f.message}")
    else:
        print("No heuristic security findings.")
    return 1 if any(f.severity == "high" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
