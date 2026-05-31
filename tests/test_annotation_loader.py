from pathlib import Path

from sqlprobe.annotations.prompt_builder import build_annotation_context
from sqlprobe.loader.annotation_loader import load_annotations


REPO_ROOT = Path(__file__).parent.parent
ANNOTATIONS_PATH = REPO_ROOT / "schema" / "annotations.yaml"


def test_load_annotations_returns_list():
    annotations = load_annotations(ANNOTATIONS_PATH)

    assert isinstance(annotations, list)
    assert len(annotations) >= 4


def test_object_annotation_fields():
    annotations = load_annotations(ANNOTATIONS_PATH)
    amount_annotation = next(
        ann for ann in annotations if ann.object == "transactions.amount"
    )

    assert amount_annotation.semantic is not None
    assert len(amount_annotation.semantic) > 0
    assert "revenue reporting" in amount_annotation.do_not_use_for


def test_join_annotation_fields():
    annotations = load_annotations(ANNOTATIONS_PATH)
    join_annotation = next(ann for ann in annotations if ann.join is not None)

    assert join_annotation.notes is not None


def test_required_filter_parsed():
    annotations = load_annotations(ANNOTATIONS_PATH)
    test_account_annotation = next(
        ann for ann in annotations if ann.object == "accounts.is_test"
    )

    assert test_account_annotation.required_filter == "= false"


def test_missing_file_returns_empty_list():
    missing_path = REPO_ROOT / "schema" / "nonexistent.yaml"

    assert load_annotations(missing_path) == []


def test_build_annotation_context_nonempty():
    annotations = load_annotations(ANNOTATIONS_PATH)

    context = build_annotation_context(annotations)

    assert "Schema annotations:" in context
    assert "transactions.amount" in context
    assert "transactions.net_revenue" in context


def test_build_annotation_context_empty_list():
    assert build_annotation_context([]) == ""


def test_build_annotation_context_includes_required_filter():
    annotations = load_annotations(ANNOTATIONS_PATH)

    context = build_annotation_context(annotations)

    assert "required_filter" in context
