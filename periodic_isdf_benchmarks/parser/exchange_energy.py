""" Exchange energy printing is hacked into the output
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np


# Returns numpy array, which cannot be serialised
# def parse_exchange_energy(file: Path | str):
#
#     if not Path(file).is_file():
#         raise FileExistsError(f"Can not find {Path(file).as_posix()}")
#
#     # Parse terminal output
#     with open(file=file, mode='r') as fid:
#         text = fid.read()
#
#     pattern = re.compile(
#         r"Elapsed time for SCF step\s+(\d+):.*?"
#         r"exchange energy:\s*([+-]?\d+(?:\.\d*)?(?:[EeDd][+-]?\d+)?)",
#         re.DOTALL,
#     )
#
#     matches = pattern.findall(text)
#
#     exx = np.zeros(shape=(len(matches)))
#     for step, energy in matches:
#         exx[int(step)-1] = float(energy)
#
#     return exx

def parse_exchange_energy(file: Path | str) -> dict[str, list[float]]:
    path = Path(file)

    if not path.is_file():
        raise FileNotFoundError(f"Cannot find {path.as_posix()}")

    text = path.read_text(encoding="utf-8")

    pattern = re.compile(
        r"Elapsed time for SCF step\s+(\d+):.*?"
        r"exchange energy:\s*([+-]?\d+(?:\.\d*)?(?:[EeDd][+-]?\d+)?)",
        re.DOTALL,
    )

    steps: list[int] = []
    energies: list[float] = []

    for step_text, energy_text in pattern.findall(text):
        steps.append(int(step_text))
        energies.append(float(energy_text.replace("D", "E").replace("d", "e")))

    return {
        "scf_step": steps,
        "exchange_energy": energies,
    }
