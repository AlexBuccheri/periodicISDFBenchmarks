""" Benchmark q-independent ISDF

Run like:
python qindependent/parse_result.py "/Users/alexanderbuccheri/Codes/fresh_ocy/testsuite/density_fitting"
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from periodic_isdf_benchmarks.parser.exchange_energy import parse_exchange_energy
from periodic_isdf_benchmarks.parser.profiling import parse_time
from periodic_isdf_benchmarks.parser.parse_inp import parse_octopus_input, Expr


def parse_exchange_results(dir: Path | str):
    """ Parse some well-defined exact exchange results
    :return:
    """
    results = {}

    # Relevant inputs
    inp: dict = parse_octopus_input(dir / "inp")
    results["inp"] = {"ISDFNpoints": inp["ISDFNpoints"],
                      "KPointsGrid": inp["KPointsGrid"][0]}

    # Exact exchange energy, hacked to print to stdout
    results['exchange_energy'] = parse_exchange_energy(dir / "terminal.out")

    # Timing profile
    cumulative_times, self_times = parse_time(dir / "profiling/time.000000")
    results['cumulative_times'] = cumulative_times
    results['self_times'] = self_times

    return results


def json_default(obj):
    if isinstance(obj, Expr):
        return obj.text
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("results.json"))
    args = parser.parse_args()

    results = parse_exchange_results(args.run_dir)

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=json_default)
