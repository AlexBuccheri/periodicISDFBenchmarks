""" Parse the output/s of a all subdirectories for specific file/s
and copy the result back to my local machine
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Dict, List


def match_files(dir: str | Path, names: str | List[str]):
    if isinstance(names, str):
        names = [names]
    matches = []
    for root, _, files in os.walk(dir):
        for fname in files:
            if fname in names:
                p = os.path.join(root, fname)
                matches.append(os.path.relpath(p, dir))
    return matches


FileParser = Dict[str, Callable]


def parse_file_instances(dir: str | Path, pair: FileParser) -> dict:
    """
    Given a root directory, for each key (file) : value (parser)
    pair, iterate through all instances of that file that
    recursively exist in the root directory, parse their contents
    and return

    :param dir: Root directory
    :param pair: Dict of file names and corresponding parsers
    :return:
    """
    results = {}
    for file_name, parser in pair.items():
        # File names prefixed with relative path to dir
        matches = match_files(dir, file_name)
        for match in matches:
            full_file_name = Path(dir, match)
            results[match] = parser(full_file_name)
    return results


if __name__ == "__main__":
    from periodic_isdf_benchmarks.parser.profiling import parse_time

    # App test that can be run on the MPSD cluster
    pair = {"time.000000": parse_time}
    results = parse_file_instances("/home/bucchera/exchange_calcs/isdf/", pair)
    print(results)
