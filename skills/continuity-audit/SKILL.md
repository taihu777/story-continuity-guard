---
name: continuity-audit
description: Perform a read-only, evidence-based audit of Markdown story artifacts for fact-source, revision, and continuity risks. Use when reviewing character bibles, outlines, scripts, or storyboards before human approval.
---

# Continuity Audit

Audit the user-selected story artifacts without modifying them.

## Workflow

1. Identify the current revision and every declared source reference.
2. Stop with a blocked finding when a required approved source is missing or stale.
3. Compare character identity, desires, permanent traits, temporary state, knowledge, props, time, and location across sources.
4. Distinguish confirmed facts from inferred and unresolved statements.
5. Report each problem with a severity, exact location, expected value, actual value, source evidence, and the smallest safe fix scope.
6. Never rewrite source files, invent canon, or automatically approve an artifact.

Use `scripts/validate_story.py` first when the selected project follows the plugin's artifact contract. Structural validation does not replace creative continuity review.
