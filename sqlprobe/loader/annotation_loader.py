from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SchemaAnnotation:
    object: str | None = None
    join: str | None = None
    semantic: str | None = None
    do_not_use_for: list[str] = field(default_factory=list)
    preferred_for: list[str] = field(default_factory=list)
    required_filter: str | None = None
    notes: str | None = None


def load_annotations(path: str | Path) -> list[SchemaAnnotation]:
    """Load schema annotations from a YAML file.
    Returns empty list if file does not exist."""
    path = Path(path)
    if not path.exists():
        return []
    with open(path) as f:
        data = yaml.safe_load(f)
    annotations = []
    for item in data.get("annotations", []):
        annotations.append(SchemaAnnotation(
            object=item.get("object"),
            join=item.get("join"),
            semantic=item.get("semantic"),
            do_not_use_for=item.get("do_not_use_for", []),
            preferred_for=item.get("preferred_for", []),
            required_filter=item.get("required_filter"),
            notes=item.get("notes"),
        ))
    return annotations
