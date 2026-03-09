from typing import Dict, Any, List

from dcvpg.engine.models import ValidationReport


def format_violation_report(report: ValidationReport) -> Dict[str, Any]:
    """Formats a ValidationReport into a structured dict for alerts and API responses."""
    result: Dict[str, Any] = {
        "pipeline_name": report.pipeline_name,
        "contract_name": report.contract_name,
        "contract_version": report.contract_version,
        "status": report.status,
        "rows_processed": report.rows_processed,
        "violations_count": report.violations_count,
        "duration_ms": report.duration_ms,
    }

    if report.violation_details:
        result["violations"] = [
            {
                "field": v.field,
                "violation_type": v.violation_type,
                "rows_affected": v.rows_affected,
                "expected_value": v.expected_value,
                "sample_values": v.sample_values,
            }
            for v in report.violation_details
        ]

    return result


def format_slack_message(report: ValidationReport) -> str:
    """Formats a ValidationReport into a human-readable Slack message."""
    lines = [
        f"*Pipeline:* `{report.pipeline_name}`",
        f"*Contract:* `{report.contract_name}` v{report.contract_version}",
        f"*Status:* {'✅ PASSED' if report.status == 'PASSED' else '❌ FAILED'}",
        f"*Rows Processed:* {report.rows_processed:,}",
        f"*Violations:* {report.violations_count}",
        f"*Duration:* {report.duration_ms}ms",
    ]
    if report.violation_details:
        lines.append("\n*Violation Details:*")
        for v in report.violation_details[:5]:
            lines.append(
                f"  • `{v.field}` → {v.violation_type} "
                f"(rows: {v.rows_affected}, expected: {v.expected_value})"
            )
        if len(report.violation_details) > 5:
            lines.append(f"  … and {len(report.violation_details) - 5} more violations")
    return "\n".join(lines)
