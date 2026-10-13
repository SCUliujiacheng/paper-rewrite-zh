"""Conservative visible-fact checks, never a proof of semantic equivalence."""

import json
import re
from collections import Counter
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, Field


class Issue(BaseModel):
    code: str
    severity: Literal["error", "warning"]
    before: str
    after: str


class AuditResult(BaseModel):
    blocked: bool
    issues: list[Issue] = Field(default_factory=list)
    requires_review: Literal[True] = True


_ARABIC = r"[+−-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:[eE][+−-]?\d+)?"
_CHINESE = r"[负負]?[零〇一二两兩三四五六七八九十百千万萬亿億]+(?:点[零〇一二三四五六七八九]+)?"
_EN_INTEGERS = dict(
    enumerate(
        (
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
            "twenty",
        )
    )
)
_EN_VALUE = {word: str(value) for value, word in _EN_INTEGERS.items()}
_EN_INTEGER = r"(?i:\b(?:" + "|".join(_EN_VALUE) + r")\b)"
_UNITS = (
    r"(?:percent|per mille|milligrams?|kilograms?|grams?|milliliters?|liters?|"
    r"millimet(?:er|re)s?|centimet(?:er|re)s?|met(?:er|re)s?|seconds?|minutes?|hours?|"
    r"μg|µg|ug|mg|kg|g|ng|pg|mL|ml|μL|µL|uL|L|mm|cm|km|nm|μm|µm|m|"
    r"ms|s|min|h|Hz|kHz|MHz|GHz|Pa|kPa|MPa|W|kW|MW|V|mV|A|mA|mol|mmol|"
    r"°\s*[CF]|℃|℉|%|％|‰|毫克|千克|微克|纳克|皮克|克|毫升|微升|升|"
    r"毫米|厘米|微米|纳米|米|秒|分钟|小时|"
    r"times?|groups?|reviewers?|participants?|samples?|rows?|beads?|"
    r"年|月|天|日|岁|倍|次|个|例|名|组|项|人|种|篇|份|台|颗|行|枚|艘|段|万元|元)"
    r"(?:[²³]|\^\d+)?(?:\s*/\s*[A-Za-zμµ]+(?:[²³]|\^\d+)?)?(?![A-Za-zμµ])"
)
_NUMBER = re.compile(
    rf"(?:{_ARABIC}|{_CHINESE})\s*(?:至|到|[–—~-])\s*"
    rf"(?:{_ARABIC}|{_CHINESE})(?:\s*{_UNITS})?"
    rf"|{_CHINESE}分之{_CHINESE}(?:\s*{_UNITS})?"
    rf"|{_EN_INTEGER}\s+{_UNITS}"
    rf"|{_ARABIC}(?:\s*{_UNITS})?|(?:百分之|千分之){_CHINESE}"
    rf"|{_CHINESE}\s*{_UNITS}|(?<=[为有共约是至第]){_CHINESE}"
)
_AUTHOR = r"[A-Z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+)*"
_AUTHOR_GROUP = rf"{_AUTHOR}(?:\s*(?:&|and|,)\s*{_AUTHOR})*(?:\s+et\s+al\.)?"
_CITATIONS = re.compile(
    r"\[\s*\d+(?:\s*[,，;；–—-]\s*\d+)*\s*\]"
    r"|\[[^\]\n]*@[\w:.-]+[^\]\n]*\]"
    r"|[（(][^()（）\n]*\b(?:19|20)\d{2}[a-z]?[^()（）\n]*[）)]"
    rf"|\b{_AUTHOR_GROUP}\s*\((?:19|20)\d{{2}}[a-z]?\)"
    r"|[\u4e00-\u9fff]{2,6}(?:等)?\s*[（(](?:19|20)\d{2}[a-z]?[）)]"
)
_URL = re.compile(r"https?://[^\s<>\"'`\[\]（）)。，；：！？]+")
_LATEX = re.compile(
    r"(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$|(?<!\\)\$[^$\n]*?(?<!\\)\$"
    r"|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]"
    r"|\\begin\{([^}]+)\}[\s\S]*?\\end\{\1\}"
)
_CODE = re.compile(
    r"^\s*(`{3,}|~{3,})[^\n]*\n[\s\S]*?^\s*\1\s*$|`+[^`\n]+`+",
    re.MULTILINE,
)
_CONTAINER_PREFIX = re.compile(r"^(?: {0,3}(?:>[ \t]?|(?:[-+*]|\d+[.)])[ \t]+))+")
_COMPARISON = re.compile(
    r">=|<=|==|!=|[><≥≤≠≈]"
    r"|不低于|不高于|不少于|不多于|大于|小于|高于|低于|超过|至少|至多|等于|以上|以下"
    r"|\b(?:greater than|less than|higher than|lower than|at least|at most|"
    r"more than|fewer than|no more than|no less than)\b",
    re.IGNORECASE,
)
_OPERAND = rf"(?:{_ARABIC}(?:\s*{_UNITS})?|[A-Za-z][A-Za-z0-9_]*(?:组|值|指标)?)"
_RELATION = re.compile(
    rf"{_OPERAND}\s*(?:(?:is|was|were)\s+)?(?:{_COMPARISON.pattern})\s*{_OPERAND}",
    re.IGNORECASE,
)
_NEGATION = re.compile(
    r"没有|并非|未曾|未能|无法|不能|不|未|无|否认"
    r"|\b(?:not|no|never|neither|without|cannot|doesn't|didn't|isn't|aren't)\b",
    re.IGNORECASE,
)
_CERTAINTY = re.compile(
    r"可能|或许|也许|似乎|提示|推测|倾向|必然|一定|确定|证明|证实|显然"
    r"|计划|打算|(?<![模虚])拟(?![合人声])"
    r"|\b(?:may|might|could|would|should|possibly|perhaps|suggests?|indicates?|likely|"
    r"certainly|definitely|always|proves?|demonstrates?|establishes?)\b",
    re.IGNORECASE,
)
_PERMISSION = re.compile(r"可以|允许|许可|\b(?:can|allowed|permitted)\b", re.IGNORECASE)
_OBLIGATION = re.compile(r"需要|需(?!求)|必须|应当|\b(?:must|required|requires?)\b", re.IGNORECASE)
_PROVENANCE = re.compile(
    r"占位符?|虚构|编造|模拟数据|合成(?:数据|语料|文本|样例)"
    r"|\b(?:placeholders?|fictional|fabricated|invented|synthetic)\b",
    re.IGNORECASE,
)
_PURPOSE = re.compile(r"\b(?:be|is|are|was|were)\s+used\s+to\b", re.IGNORECASE)


def _small_chinese_integer(text: str) -> str | None:
    """Only ordinary unsigned 0..99 forms; not decimal, range or financial notation."""
    digits = {word: value for value, word in enumerate("零一二三四五六七八九")}
    digits.update({"〇": 0, "两": 2, "兩": 2})
    if text in digits:
        return str(digits[text])
    match = re.fullmatch(r"([一二三四五六七八九]?)十([一二三四五六七八九]?)", text)
    if match:
        tens, ones = match.groups()
        return str(digits.get(tens, 1) * 10 + digits.get(ones, 0))
    return None


def _quantities(text: str) -> list[str]:
    values = []
    for match in _NUMBER.finditer(text):
        token = match.group(0)
        english = re.fullmatch(rf"({_EN_INTEGER})\s+({_UNITS})", token)
        chinese = re.fullmatch(rf"({_CHINESE})\s*({_UNITS})", token)
        if english:
            token = _EN_VALUE[english[1].lower()] + english[2]
        elif chinese and (value := _small_chinese_integer(chinese[1])) is not None:
            token = value + chinese[2]
        values.append(re.sub(r"\s+", "", token))
    return values


def _risk_cues(pattern: re.Pattern[str], text: str) -> list[str]:
    # These are lexical hints, not aligned claims. Keep distinct provenance types.
    aliases = {
        "需": "需要",
        "允许": "可以",
        "许可": "可以",
        "占位": "占位符",
        "模拟数据": "合成数据",
    }
    return [aliases.get(token, token) for token in _tokens(pattern, text.lower())]


def _tokens(pattern: re.Pattern[str], text: str, *, compact: bool = False) -> list[str]:
    values = [match.group(0) for match in pattern.finditer(text)]
    return [re.sub(r"\s+", "", value) for value in values] if compact else values


def _summary(tokens: list[str]) -> str:
    return json.dumps(dict(Counter(tokens)), ensure_ascii=False, sort_keys=True)


def _nested_code(text: str) -> list[str]:
    """Recognize container fences while preserving the original code verbatim."""
    lines = text.splitlines(keepends=True)
    blocks: list[str] = []
    cursor = 0
    while cursor < len(lines):
        line = lines[cursor]
        if not _CONTAINER_PREFIX.match(line):
            cursor += 1
            continue
        content = _CONTAINER_PREFIX.sub("", line).lstrip(" \t")
        opening = re.match(r"(`{3,}|~{3,})", content)
        if not opening:
            cursor += 1
            continue
        marker = opening.group(1)
        closing = re.compile(rf"{re.escape(marker[0])}{{{len(marker)},}}[ \t]*")
        end = cursor + 1
        while end < len(lines):
            content = _CONTAINER_PREFIX.sub("", lines[end]).lstrip(" \t").rstrip("\r\n")
            end += 1
            if closing.fullmatch(content):
                break
        blocks.append("".join(lines[cursor:end]))
        cursor = end
    return blocks


def _malformed(text: str) -> bool:
    stripped = text.strip()
    if not stripped or any(ord(char) < 32 and char not in "\r\n\t" for char in text):
        return True
    if re.match(r"(?:<!doctype|<html\b|<body\b|<script\b)", stripped, re.IGNORECASE):
        return True
    if re.match(
        r"(?:here (?:is|are) (?:the |a )?(?:rewritten|revised)|"
        r"(?:改写|修改|润色)(?:后的)?(?:文本|版本|结果)[：:])",
        stripped,
        re.IGNORECASE,
    ):
        return True
    if stripped.startswith(("{", "[")):
        try:
            return isinstance(json.loads(stripped), (dict, list))
        except json.JSONDecodeError:
            return stripped.startswith('{"')
    return False


def audit(source: str, candidate: str, protected_terms: list[str] | None = None) -> AuditResult:
    """Compare visible facts; warn about lexical polarity and modality occurrence shifts.

    The rules intentionally reject some harmless notation changes. They cannot verify
    argument meaning, citation placement, or arbitrary entity/value associations.
    Proposal markers are lexical counts: synonyms or omitted repeated modals can
    trigger review warnings without proving that the meaning changed.
    """
    issues: list[Issue] = []
    if not source.strip() or _malformed(candidate):
        issues.append(
            Issue(code="invalid_output", severity="error", before=source, after=candidate)
        )

    checks: list[tuple[str, Callable[[str], list[str]]]] = [
        ("numbers", _quantities),
        (
            "comparisons",
            lambda text: (
                _tokens(_COMPARISON, text, compact=True) + _tokens(_RELATION, text, compact=True)
            ),
        ),
        ("citations", lambda text: _tokens(_CITATIONS, text, compact=True)),
        ("urls", lambda text: [value.rstrip(".,;:，。；：！!") for value in _tokens(_URL, text)]),
        ("latex", lambda text: _tokens(_LATEX, text)),
        ("code", lambda text: _tokens(_CODE, text) + _nested_code(text)),
        (
            "protected_terms",
            lambda text: [
                term
                for term in dict.fromkeys(protected_terms or [])
                if term
                for _ in range(text.count(term))
            ],
        ),
    ]
    for code, extract in checks:
        before, after = extract(source), extract(candidate)
        if Counter(before) != Counter(after):
            issues.append(
                Issue(code=code, severity="error", before=_summary(before), after=_summary(after))
            )
    for code, pattern in (
        ("negation", _NEGATION),
        ("certainty", _CERTAINTY),
        ("permission", _PERMISSION),
        ("obligation", _OBLIGATION),
        ("provenance", _PROVENANCE),
        ("purpose", _PURPOSE),
    ):
        before, after = _risk_cues(pattern, source), _risk_cues(pattern, candidate)
        if Counter(before) != Counter(after):
            issues.append(
                Issue(code=code, severity="warning", before=_summary(before), after=_summary(after))
            )
    return AuditResult(blocked=any(issue.severity == "error" for issue in issues), issues=issues)
