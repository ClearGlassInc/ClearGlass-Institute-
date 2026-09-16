"""Compliance Auto-Scan - detect unencrypted PHI/PII in at-rest files.

This is the Python counterpart of the scheduled PowerShell auditor described in
the design doc: it walks targeted directories, applies a battery of regexes for
common identifiers, and emits :class:`~clearpulse.models.ComplianceFinding`
records with the matched value *masked* so the finding itself never leaks PHI.

It audits at-rest data only and never touches the live FHIR streams.
"""

from __future__ import annotations

import os
import re
from typing import Iterable, Iterator

from clearpulse.models import ComplianceFinding

# Identifier patterns. Kept conservative to limit false positives; the medical
# record number (MRN) pattern is intentionally tunable per site.
PHI_PATTERNS: dict[str, re.Pattern[str]] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "mrn": re.compile(r"\bMRN[:#]?\s?\d{6,10}\b", re.IGNORECASE),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "us_phone": re.compile(r"\b\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}\b"),
}

# File types the scanner inspects as text. Binary office formats (xlsx) require
# openpyxl; they are skipped gracefully when that dependency is absent.
TEXT_EXTENSIONS = {".csv", ".txt", ".json", ".log", ".tsv"}


def mask_snippet(value: str, visible: int = 2) -> str:
    """Mask a matched value, leaving at most ``visible`` trailing characters."""
    stripped = value.strip()
    if len(stripped) <= visible:
        return "*" * len(stripped)
    return "*" * (len(stripped) - visible) + stripped[-visible:]


def severity_from_findings(count: int) -> str:
    """Map the volume of findings in a file to an alert severity."""
    if count >= 100:
        return "CRITICAL"
    if count >= 10:
        return "HIGH"
    if count >= 1:
        return "MEDIUM"
    return "INFO"


class PHIScanner:
    """Scans text and files for unencrypted identifiers."""

    def __init__(self, patterns: dict[str, re.Pattern[str]] | None = None) -> None:
        self.patterns = patterns or PHI_PATTERNS

    def scan_text(self, text: str, *, source: str = "<text>") -> list[ComplianceFinding]:
        findings: list[ComplianceFinding] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            for name, pattern in self.patterns.items():
                for match in pattern.finditer(line):
                    findings.append(ComplianceFinding(
                        file_path=source,
                        pattern_name=name,
                        masked_snippet=mask_snippet(match.group(0)),
                        line_no=line_no,
                    ))
        return findings

    def scan_file(self, path: str) -> list[ComplianceFinding]:
        ext = os.path.splitext(path)[1].lower()
        if ext not in TEXT_EXTENSIONS:
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            return []
        return self.scan_text(text, source=path)

    def scan_directory(self, root: str) -> Iterator[ComplianceFinding]:
        """Recursively yield findings from every supported file under ``root``."""
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                yield from self.scan_file(os.path.join(dirpath, name))

    def scan_paths(self, paths: Iterable[str]) -> list[ComplianceFinding]:
        findings: list[ComplianceFinding] = []
        for path in paths:
            if os.path.isdir(path):
                findings.extend(self.scan_directory(path))
            else:
                findings.extend(self.scan_file(path))
        return findings
