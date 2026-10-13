"""Small, explicit failure pairs; these are not independently human-labelled data."""

import json
from pathlib import Path

import pytest

from paper_rewrite.guards import audit
from paper_rewrite.pipeline import Rewriter


@pytest.mark.parametrize(
    "source,candidate",
    [
        ("Repeated 5 times.", "Repeated five times."),
        ("We used two groups.", "We used 2 groups."),
        ("We used twenty reviewers.", "We used 20 reviewers."),
        ("重复五次。", "重复5次。"),
        ("共有十六颗塑料珠。", "共有16颗塑料珠。"),
        ("We used three groups.", "We used three groups."),
    ],
)
def test_allows_only_supported_equivalent_integer_notation(source, candidate):
    assert audit(source, candidate).issues == []


@pytest.mark.parametrize(
    "source,candidate",
    [
        ("We used two groups.", "We used three groups."),
        ("十六颗塑料珠被分为四组。", "十七颗塑料珠被分为四组。"),
        ("每个棋盘包含八行标记。", "每个棋盘包含九行标记。"),
        ("剂量为5.0 mg。", "剂量为5 mg。"),
        ("Repeated 5 times.", "Repeated more than five times."),
        ("增加5倍。", "增加五倍以上。"),
        ("共有3名评审者。", "共有3组评审者。"),
        ("比例为5%。", "比例为五个百分点。"),
        ("The dose was -5 mg.", "The dose was five mg."),
    ],
)
def test_quantity_coverage_does_not_erase_units_bounds_or_precision(source, candidate):
    assert audit(source, candidate).issues


@pytest.mark.parametrize(
    "source,candidate,code",
    [
        (
            "方案计划使用经参与者确认可以提供的内容。",
            "方案计划使用经参与者确认提供的内容。",
            "permission",
        ),
        ("参与者可以提供记录。", "参与者必须提供记录。", "permission"),
        ("重复引用需要完整保留。", "重复引用已完整保留。", "obligation"),
        ("Participants are permitted to withdraw.", "Participants withdraw.", "permission"),
        ("Researchers must retain the notes.", "Researchers retained the notes.", "obligation"),
        (
            "The figures were invented for testing.",
            "The figures were introduced for testing.",
            "provenance",
        ),
        ("引文均为占位符，本试验为虚构案例。", "本试验为虚构案例。", "provenance"),
        (
            "Practice items would be used to clarify rules.",
            "Practice items would clarify rules.",
            "purpose",
        ),
    ],
)
def test_warns_about_specific_permission_obligation_and_provenance_losses(source, candidate, code):
    issue = next((item for item in audit(source, candidate).issues if item.code == code), None)
    assert issue is not None
    assert issue.severity == "warning"


@pytest.mark.parametrize(
    "source,candidate",
    [
        ("重复引用需要完整保留。", "重复引用需完整保留。"),
        ("参与者可以提供记录。", "参与者允许提供记录。"),
        ("We must retain the notes.", "The notes must be retained."),
        ("We use a canal model.", "A canal model is used."),
        ("我们比较应用方法。", "我们比较分析方法。"),
        (
            "Practice items would be used to clarify rules.",
            "Practice items would be used to clarify the rules.",
        ),
    ],
)
def test_bounded_obligation_equivalences_and_word_boundaries(source, candidate):
    assert audit(source, candidate).issues == []


async def test_recorded_entire_disclaimer_omission_is_withheld_and_visible():
    payload = json.loads(
        Path("artifacts/smoke-qwen-q5-release-2026-10-14.json").read_text(encoding="utf-8")
    )
    case = next(row for row in payload["cases"] if row["id"] == "en-05")["report"]

    class FrozenModel:
        name = "recorded-output-not-live-model"

        async def complete(self, text, seed=0, protected_terms=()):
            return case["output"]

    result = await Rewriter(FrozenModel()).rewrite(case["source"], "en", ["Silver Seed"], 1)
    assert result.output == case["source"]
    assert result.status == "unchanged"
    attempt = result.segments[0].attempts[0]
    assert attempt.text == case["output"]
    assert any(issue.code == "provenance" for issue in attempt.audit.issues)


def test_chinese_sentence_punctuation_ends_url_without_ignoring_unicode_path():
    assert not audit(
        "见https://example.org/path。后文很长。", "见https://example.org/path。简写说明。"
    ).blocked
    assert audit("见https://example.org/中文。", "见https://example.org/英文。").blocked
