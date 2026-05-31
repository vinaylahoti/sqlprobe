from sqlprobe.loader.annotation_loader import SchemaAnnotation


def build_annotation_context(annotations: list[SchemaAnnotation]) -> str:
    """
    Returns a formatted string block for injection into judge prompt.
    Returns empty string if annotations list is empty.

    Format:
    Schema annotations:
    - transactions.amount: Gross transaction value before refunds.
      [do_not_use_for: revenue reporting, ARR, MRR]
    - transactions.net_revenue: Recognized revenue net of refunds.
      [preferred_for: revenue reporting, P&L analysis]
    - accounts.is_test: Must always be filtered.
      [required_filter: = false]
    - join transactions → accounts: Always inner join.
    """
    if not annotations:
        return ""
    lines = ["Schema annotations:"]
    for ann in annotations:
        label = ann.object if ann.object else f"join {ann.join}"
        semantic_text = ann.semantic or ""
        lines.append(f"- {label}: {semantic_text}")
        if ann.do_not_use_for:
            lines.append(f"  [do_not_use_for: {', '.join(ann.do_not_use_for)}]")
        if ann.preferred_for:
            lines.append(f"  [preferred_for: {', '.join(ann.preferred_for)}]")
        if ann.required_filter:
            lines.append(f"  [required_filter: {ann.required_filter}]")
        if ann.notes:
            lines.append(f"  [notes: {ann.notes}]")
    return "\n".join(lines)
