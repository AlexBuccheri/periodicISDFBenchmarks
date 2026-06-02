""" Generate an Octopus inp from a python dict
"""
from __future__ import annotations

import copy
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def is_row_like(x: Any) -> bool:
    return isinstance(x, (list, tuple))


def render_block(key: str, value: list | tuple) -> str:
    lines = [f"%{key}"]

    if len(value) == 0:
        lines.append("%")
        return "\n".join(lines)

    # Nested list/tuple: several rows.
    if all(is_row_like(row) for row in value):
        rows = value
    else:
        # Flat list: one row.
        rows = [value]

    for row in rows:
        lines.append(" | ".join(render_atom(x) for x in row))

    lines.append("%")
    return "\n".join(lines)


def write_octopus_input(options: dict[str, Any]) -> str:
    lines: list[str] = []

    for key, value in options.items():
        if isinstance(value, (list, tuple)):
            lines.append(render_block(key, value))
        else:
            lines.append(f"{key} = {render_atom(value)}")

    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class Quoted:
    text: str

    def __init__(self, text: Any):
        object.__setattr__(self, "text", str(text))

    def render(self) -> str:
        escaped = self.text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'


def render_atom(x: Any) -> str:
    if isinstance(x, Quoted):
        return x.render()

    if isinstance(x, Path):
        return Quoted(x).render()

    if isinstance(x, bool):
        return "yes" if x else "no"

    if isinstance(x, int):
        return str(x)

    if isinstance(x, float):
        return format(x, ".16g")

    if isinstance(x, str):
        return x

    raise TypeError(f"Cannot render Octopus value of type {type(x).__name__}: {x!r}")


def apply_patch(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    out.update(patch)
    return out


def cartesian_product(matrix: dict):
    """ Create all combinations of options, where the dict
    keys define the options and the values define the
    specific values that the optionals should take.

    Expects a dict of the form:

    {'Eigensolver': ['rmmdiis', 'chebyshev_filter'],
     'EigensolverTolerance':['1e-7']}

    with no nesting of containers in values.
    If a value is not in list, every

    :param matrix:
    :return:
    """
    # Get all possible combinations
    combinations = list(itertools.product(*matrix.values()))

    # Create a list of dictionaries by pairing each key with its corresponding value from the combinations
    all_option_permutations = [{key: value for key, value in zip(matrix.keys(), combination)} for combination in
                               combinations]

    return all_option_permutations


def generate_input_files(
    base_options: dict[str, Any],
    matrix: dict[str, list[Any] | Any],
) -> tuple[list[str], list[dict[str, Any]]]:

    inputs = []
    configs = []

    for patch in cartesian_product(matrix):
        options = apply_patch(base_options, patch)
        inputs.append(write_octopus_input(options))
        configs.append(patch)

    return inputs, configs

