""" Parsers
"""
from pathlib import Path
import pandas as pd


def read_profiling_time(root: Path | str):
    """

    :param root:
    :return:
    """
    if not Path(root).is_dir():
        raise NotADirectoryError

    profiling = Path(root) / Path("profiling/time.000000")

    table = pd.read_table(
        profiling,
        sep=r"\s+",
        names=[
            "TAG",
            "CUM NUM_CALLS",
            "CUM TOTAL_TIME",
            "CUM TIME_PER_CALL",
            "CUM MIN_TIME",
            "CUM MFLOPS",
            "CUM MBYTES/S",
            "CUM %TIME",
            "|",
            "SELF TOTAL_TIME",
            "SELF TIME_PER_CALL",
            "SELF MFLOPS",
            "SELF MBYTES/S",
            "SELF %TIME",
        ],
        skiprows=4,
        index_col="TAG",
        usecols=lambda x: x != "|",
    )
    return table


def read_profiling_time_as_dict(root: Path | str) -> dict:
    """

    :param root:
    :return:
    """
    if not Path(root).is_dir():
        raise NotADirectoryError

    prof = read_profiling_time(root).to_dict()
    new_prof = {'CUMULATIVE': {}, 'SELF': {}}

    for key, val in prof.items():
        top_key, lower_key = str(key).split()
        if top_key == 'CUM': top_key += 'ULATIVE'
        new_prof[top_key] = {lower_key: val}

    return new_prof
