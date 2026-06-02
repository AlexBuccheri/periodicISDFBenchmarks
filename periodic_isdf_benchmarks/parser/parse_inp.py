from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Expr:
    """Unevaluated Octopus expression, e.g. 1/4 or 0.20 * angstrom."""
    text: str

    def __str__(self) -> str:
        return self.text


_int_re = re.compile(r"^[+-]?\d+$")

_float_re = re.compile(
    r"""
    ^[+-]?
    (?:
        (?:\d+\.\d*) |
        (?:\.\d+) |
        (?:\d+)
    )
    (?:[eE][+-]?\d+)?
    $
    """,
    re.VERBOSE,
)

_ident_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def strip_comment(line: str) -> str:
    """Strip # comments, ignoring # inside double quotes."""
    in_quote = False
    escaped = False

    for i, ch in enumerate(line):
        if ch == "\\" and not escaped:
            escaped = True
            continue

        if ch == '"' and not escaped:
            in_quote = not in_quote

        if ch == "#" and not in_quote:
            return line[:i]

        escaped = False

    return line


def split_unquoted_pipe(line: str) -> list[str]:
    """Split a row on |, ignoring | inside double quotes."""
    parts: list[str] = []
    start = 0
    in_quote = False
    escaped = False

    for i, ch in enumerate(line):
        if ch == "\\" and not escaped:
            escaped = True
            continue

        if ch == '"' and not escaped:
            in_quote = not in_quote

        if ch == "|" and not in_quote:
            parts.append(line[start:i].strip())
            start = i + 1

        escaped = False

    parts.append(line[start:].strip())
    return parts


def parse_quoted_string(text: str) -> str:
    """Parse a simple double-quoted string."""
    inner = text[1:-1]
    return inner.replace(r"\"", '"').replace(r"\\", "\\")


def parse_atom(text: str) -> Any:
    text = text.strip()

    if text == "":
        return ""

    if text.startswith('"') and text.endswith('"'):
        return parse_quoted_string(text)

    lower = text.lower()

    if lower in {"yes", "true"}:
        return True

    if lower in {"no", "false"}:
        return False

    if _int_re.match(text):
        return int(text)

    if _float_re.match(text):
        return float(text)

    # Keep bare identifiers as strings:
    # gs, prof_time, filter_none, hyb_gga_xc_pbeh, a, angstrom, etc.
    if _ident_re.match(text):
        return text

    # Keep arithmetic/expression-like values unevaluated:
    # 1/4, 0.20 * angstrom, a + b, etc.
    return Expr(text)


def parse_block_row(line: str) -> list[Any]:
    fields = split_unquoted_pipe(line)

    # Most Octopus blocks use | separators. Fall back to whitespace-separated
    # fields if no pipe is present.
    if len(fields) == 1:
        fields = line.split()

    return [parse_atom(field) for field in fields]


def parse_octopus_input(file: Path | str) -> dict[str, Any]:
    """
    Parse an Octopus input file into a flat dictionary.

    Scalar assignments become ordinary values:

        CalculationMode = gs
        ISDFNpoints = 55

    Blocks become list-of-row lists:

        %KPointsGrid
          2 | 1 | 1
        %

    returns:

        {
            "CalculationMode": "gs",
            "ISDFNpoints": 55,
            "KPointsGrid": [[2, 1, 1]],
        }
    """
    text = Path(file).read_text(encoding="utf-8")

    parsed: dict[str, Any] = {}

    current_block: str | None = None
    current_rows: list[list[Any]] = []

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = strip_comment(raw_line).strip()

        if not line:
            continue

        if current_block is not None:
            if line == "%":
                parsed[current_block] = current_rows
                current_block = None
                current_rows = []
            else:
                current_rows.append(parse_block_row(line))
            continue

        if line.startswith("%"):
            current_block = line[1:].strip()

            if not current_block:
                raise ValueError(f"Empty block name at line {lineno}")

            if current_block in parsed:
                raise ValueError(f"Duplicate key/block {current_block!r} at line {lineno}")

            current_rows = []
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()

            if not key:
                raise ValueError(f"Empty key at line {lineno}")

            if key in parsed:
                raise ValueError(f"Duplicate key/block {key!r} at line {lineno}")

            parsed[key] = parse_atom(value)
            continue

        raise ValueError(f"Cannot parse line {lineno}: {raw_line!r}")

    if current_block is not None:
        raise ValueError(f"Unclosed block %{current_block}")

    return parsed
