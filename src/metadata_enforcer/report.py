"""Render CheckResult to human-readable stdout."""

from __future__ import annotations

from collections import defaultdict

from metadata_enforcer.validate import CheckResult


def format_report(result: CheckResult) -> str:
    lines: list[str] = []

    if result.errors:
        by_path: dict[str, list] = defaultdict(list)
        for issue in result.errors:
            by_path[issue.path].append(issue)

        for path in sorted(by_path):
            lines.append(path)
            for issue in by_path[path]:
                loc = issue.instance_path or "/"
                lines.append(f"  {loc}: {issue.message}")
            lines.append("")

        files_with_errors = len(by_path)
        issue_count = len(result.errors)
        lines.append(
            f"Checked {result.files_checked} file(s), "
            f"{files_with_errors} with errors ({issue_count} issue(s))"
        )
    else:
        lines.append(f"Checked {result.files_checked} file(s) against {result.schema}")
        lines.append("All good.")

    return "\n".join(lines).rstrip() + "\n"
