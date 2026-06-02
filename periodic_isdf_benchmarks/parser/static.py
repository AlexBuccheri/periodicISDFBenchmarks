"""Parsers for Octopus outputs in the static folder:
* convergence
* forces (TODO)
* info (Most components)
"""
from __future__ import annotations

import re
from pathlib import Path
from io import StringIO

import numpy as np


def convergence_file(workdir: str | Path) -> dict:
    """ Parse convergence file output.

    :param workdir: Root directory of an octopus run
    :return: Dict of convergence info
    """
    wd = Path(workdir)
    convergence_file = wd / "static/convergence"

    try:
        data = np.loadtxt(convergence_file, comments='#')
    except IOError:
        raise IOError(f'{convergence_file.as_posix()} failed to lod')

    serialised_data = {}

    for iscf, row in enumerate(data):
        serialised_data[iscf] = {
            'energy': row[1],
            'energy_diff': row[2],
            'abs_dens': row[3],
            'rel_dens': row[4],
            'abs_ev': row[5],
            'rel_ev': row[6]}

    return serialised_data


def static_forces():
    """ Parse forces file output.
    """
    raise NotImplementedError("Not implemented a parser for static/forces")


def read_info_sections(text: str):
    """Yield (section_name, block_text) tuples from the info file.

    :param text: String of text from info
    :return:
    """
    SECTION_PATTERNS = {
        "Eigenvalues": r"^Eigenvalues \[H\]",
        "Energy": r"^Energy \[H\]:",
        "Dipole": r"^Dipole:\s*\[b\]\s*\[Debye\]",
        "Convergence": r"^Convergence:",
        "Forces": r"^Forces on the ions \[H/b\]",
    }

    pattern = re.compile(
        "|".join(f"({pattern})" for pattern in SECTION_PATTERNS.values()), re.M
    )

    # Find all headers with their start positions
    hits = [(m.lastindex, m.start()) for m in pattern.finditer(text)]
    # Add end sentinel
    hits.append((None, len(text)))

    names = list(SECTION_PATTERNS.keys())
    for (idx, start), (_, end) in zip(hits, hits[1:]):
        yield names[idx - 1], text[start:end].strip()


def static_info_eigenvalues(block: str) -> np.ndarray:
    """ Parse eigenvalues from static/info

    :param block:
    :return: data of shape(Neigenvalues, 3), where each row
    contains [Eigenvalue idx, eigenvalue, occ]
    """
    block = "#" + block
    data = np.loadtxt(StringIO(block), comments='#', usecols=(0, 2, 3))
    return data


def static_info_energy(block: str) -> dict:
    """

    :param block:
    :return:
    """
    lines = block.split('\n')

    results = {'Total': float(lines[1].split('=')[-1]),
               'Free': float(lines[2].split('=')[-1])}

    for line in lines[4:]:
        name, energy = line.split('=')
        results[name.strip()] = float(energy)

    return results


def static_info_dipole(block: str) -> dict:
    """

    :param block: [x,y z] components of [b] and [Debye]
    :return:
    """
    block = "#" + block
    data = np.loadtxt(StringIO(block), comments='#', usecols=(2, 3)).T
    result = {'[b]': data[0, :],
              '[Debye]': data[1, :]}

    return result



def static_info_scf_converged_in(block: str) -> dict:
    pattern = re.compile(r'^SCF\s+converged\s+in\s+(\d+)\s+iteration(?:s)?\b', re.MULTILINE)
    m = pattern.search(block)
    if m:
        return {'SCF converged in': int(m.group(1))}
    else:
        return {'SCF converged in': 'False'}


static_info_parser = {'Eigenvalues': static_info_eigenvalues,
                      'Energy': static_info_energy,
                      'Dipole': static_info_dipole
                      }


def info_file(workdir: str | Path) -> dict:
    """
    Parses:
    * Eigenvalues with occupation (spin ignored)
    * Is Converged
    * Energy components
    * Dipole

    Ignored:
    * Grid
    * Theory level
    * Convergence , as this is in static/convergence
    * Forces, as these are in static/forces

    :return:
    """
    wd = Path(workdir)
    static_info_file = wd / "static/info"

    with open(static_info_file, mode='r') as fid:
        static_info = fid.read()

    results = static_info_scf_converged_in(static_info)
    sections_to_parse = ['Eigenvalues', 'Energy', 'Dipole']

    for name, block in read_info_sections(static_info):
        if name in sections_to_parse:
            results[name] = static_info_parser[name](block)

    return results
