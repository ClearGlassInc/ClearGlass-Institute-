#!/usr/bin/env python3
"""Deterministic GitHub Actions workflow auditor.

The read-only, no-LLM half of the Workflow Repair Agent. It enforces the
security baseline documented in ``.github/WORKFLOW_AGENT.md`` and exits non-zero
on any ERROR-level finding, so it works as a real CI guard as well as a local
pre-flight check::

    python3 .github/scripts/audit_workflows.py

Checks (ERROR fails the build; WARN is informational):

* ERROR  YAML fails to parse.
* ERROR  A workflow has no top-level ``permissions`` block (token would inherit
         the repository default, which may be write-all).
* ERROR  Any ``uses:`` pins a mutable ref: ``@master`` / ``@main`` / ``@latest``.
* ERROR  A third-party action (owner not ``actions``/``github``) is not pinned
         to a 40-hex commit SHA.
* WARN   ``pull_request_target`` trigger is present (review for token exposure).

Depends only on PyYAML; install with ``pip install pyyaml``.
"""

from __future__ import annotations

import glob
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - the workflow installs PyYAML first
    print("ERROR: PyYAML is required (pip install pyyaml).", file=sys.stderr)
    sys.exit(2)

WORKFLOW_GLOBS = (".github/workflows/*.yml", ".github/workflows/*.yaml")
FIRST_PARTY_OWNERS = {"actions", "github"}
MUTABLE_REFS = {"master", "main", "latest"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _iter_uses(doc: dict):
    """Yield every ``uses:`` reference in a parsed workflow (steps + reusable)."""
    for job in (doc.get("jobs") or {}).values():
        if not isinstance(job, dict):
            continue
        if isinstance(job.get("uses"), str):      # reusable workflow call
            yield job["uses"]
        for step in job.get("steps") or []:
            if isinstance(step, dict) and isinstance(step.get("uses"), str):
                yield step["uses"]


def audit_file(path: str) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for one workflow file."""
    errors: list[str] = []
    warnings: list[str] = []
    try:
        with open(path, encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        return [f"{path}: YAML parse error: {exc}"], []
    if not isinstance(doc, dict):
        return [f"{path}: not a mapping at the top level"], []

    # 'on' parses to the boolean True under YAML 1.1; accept either key.
    triggers = doc.get("on", doc.get(True))
    if isinstance(triggers, (dict, list)):
        names = list(triggers) if isinstance(triggers, (dict, list)) else [triggers]
        if "pull_request_target" in names:
            warnings.append(f"{path}: uses pull_request_target - review token exposure")

    if "permissions" not in doc:
        errors.append(f"{path}: missing top-level 'permissions' (default to read-only)")

    for ref in _iter_uses(doc):
        if ref.startswith("./") or ref.startswith("docker://"):
            continue  # local composite action / container - not a tag/SHA pin
        name, _, version = ref.partition("@")
        if not version:
            errors.append(f"{path}: action '{ref}' is not pinned to any ref")
            continue
        if version.lower() in MUTABLE_REFS:
            errors.append(f"{path}: action '{ref}' pins a mutable ref '@{version}'")
            continue
        owner = name.split("/", 1)[0]
        if owner not in FIRST_PARTY_OWNERS and not SHA_RE.match(version):
            errors.append(
                f"{path}: third-party action '{ref}' must be pinned to a commit "
                f"SHA, not '@{version}'")
    return errors, warnings


def main() -> int:
    paths = sorted({p for pattern in WORKFLOW_GLOBS for p in glob.glob(pattern)})
    if not paths:
        print("No workflow files found under .github/workflows/.")
        return 0

    all_errors: list[str] = []
    all_warnings: list[str] = []
    print(f"Inspected {len(paths)} workflow file(s):")
    for path in paths:
        errors, warnings = audit_file(path)
        status = "FAIL" if errors else ("WARN" if warnings else "OK")
        print(f"  [{status}] {path}")
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    for warning in all_warnings:
        print(f"WARN  {warning}")
    for error in all_errors:
        print(f"ERROR {error}")

    if all_errors:
        print(f"\nAudit failed: {len(all_errors)} error(s), "
              f"{len(all_warnings)} warning(s).")
        return 1
    print(f"\nAudit passed: 0 errors, {len(all_warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
