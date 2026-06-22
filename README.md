# Story Continuity Guard

Story Continuity Guard is a local-first Codex plugin for AI-assisted fiction and agent projects. It helps writers keep character facts and revisions consistent, and helps maintainers detect risky instructions or configuration before running contributed agent files.

The project combines a reusable Codex skill with a deterministic command-line validator. The skill guides evidence-based, read-only review; the validator catches structural problems before creative review begins.

## Why it exists

Long-running AI writing projects often drift: a character's age changes, an old outline silently becomes current again, or an unresolved idea is presented as canon. Story Continuity Guard makes those risks visible through explicit fact labels and immutable revisions.

## Features

- Validates required YAML frontmatter on Markdown story artifacts.
- Enforces allowed document and claim statuses.
- Detects missing `[confirmed]`, `[inferred]`, or `[unresolved]` labels.
- Requires top-level `claim_status: unresolved` when unresolved facts exist.
- Checks revision filename conventions and `supersedes` relationships.
- Produces machine-readable JSON for CI.
- Keeps the audit workflow read-only and local.
- Audits `AGENTS.md`, `SKILL.md`, plugin manifests, and MCP configuration.
- Flags shell-pipe installation, encoded execution, secret-like literals, insecure URLs, and path traversal.

## Quick start

```bash
python scripts/validate_story.py examples
```

Return code `0` means no validation errors were found. Add `--json` for CI-friendly output:

```bash
python scripts/validate_story.py examples --json
```

Audit an agent or Codex project:

```bash
python scripts/audit_agent_config.py .
python scripts/audit_agent_config.py . --format sarif
```

The SARIF output can be consumed by code-scanning systems. Findings are heuristic and should be reviewed by a human; the tool never executes inspected configuration.

Run the tests with only the Python standard library:

```bash
python -m unittest discover -s tests -v
```

## Codex plugin

The plugin manifest lives in `.codex-plugin/plugin.json`. The included `continuity-audit` and `agent-config-security-audit` skills ask Codex to report evidence-backed issues without silently editing source files.

## Artifact contract

Each governed Markdown artifact starts with YAML frontmatter containing:

```yaml
id: episode-01-outline
revision: v1
status: needs-human-review
created_at: 2026-06-22
source_refs: []
claim_status: unresolved
supersedes: null
stale_reason: null
```

Important statements in mixed-certainty documents carry one of three labels: `[confirmed]`, `[inferred]`, or `[unresolved]`.

## Privacy

The validator makes no network requests and has no runtime dependencies outside Python's standard library. Manuscripts stay on the machine where the command runs.

## Contributing

Issues and small, focused pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
