""" Benchmark q-independent ISDF

 python qindependent/generate_inputs.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import numpy as np

from periodic_isdf_benchmarks.input.inp_gen import Quoted, write_octopus_input, cartesian_product

from periodic_isdf_benchmarks.submission.slurm import SlurmConfig


@dataclass(frozen=True)
class SiliconPrimitive:
    a: float = 10.26121
    LatticeParameters: ClassVar[list[float]] = [a, a, a]
    LatticeVectors: ClassVar[list[list[float]]] = [
            [0.0, 0.5, 0.5],
            [0.5, 0.0, 0.5],
            [0.5, 0.5, 0.0]
        ]
    ReducedCoordinates: ClassVar[list[list[float | str]]] = [
            [Quoted("Si"), "0.0", "0.0", "0.0"],
            [Quoted("Si"), "1/4", "1/4", "1/4"]
        ]


if __name__ == "__main__":

    # Debugging
    # Debug = trace  #info
    # HFSingularity = none
    # CheckISDFNpoints = yes
    # MaximumIter = 1

    # Silicon primitive cell ISDF calculation
    system = {
        "Dimensions": 3,
        "PeriodicDimensions": 3,
        "Spacing": "0.20 * angstrom",
        "ExperimentalFeatures": "yes",
        "LatticeParameters": SiliconPrimitive.LatticeParameters,
        "LatticeVectors": SiliconPrimitive.LatticeVectors,
        "ReducedCoordinates": SiliconPrimitive.ReducedCoordinates
    }

    mode = {"CalculationMode": "gs",
        "FromScratch": "yes",
        "RestartWrite": "no",
        "ProfilingMode": "prof_time"}

    isdf_input = {"ACEWithISDF": "yes",
                  "ISDFFreezePoints": "yes",
                  "ISDFRunSerial": "no",
                  "ACERestrictOccupied": "yes"}

    kpoint_input = {"KPointsUseSymmetries": "no",
                    "KPointsUseTimeReversal": "no"}

    scf_and_eigen_input = {"ExtraStates": 3,
                 "ConvRelDens": "1e-7",
                 "Eigensolver": "chebyshev_filter",
                 "FilterPotentials": "filter_none"}

    functional = {"XCFunctional": "hyb_gga_xc_pbeh"}

    base_input = mode | system | isdf_input | kpoint_input | scf_and_eigen_input | functional

    # Want specific numbers of ISDF points with each k-grid
    options = [{"KPointsGrid": [[1, 1, 1]], "ISDFNpoints": [30, 40, 50, 60]},
               {"KPointsGrid": [[2, 2, 2]], "ISDFNpoints": [30, 40, 50, 60, 70, 80]},
               {"KPointsGrid": [[3, 3, 3]], "ISDFNpoints": [60, 80, 100]},
               {"KPointsGrid": [[4, 4, 4]], "ISDFNpoints": [80, 100, 120]}]
               # {"KPointsGrid": [[6, 6, 6]], "ISDFNpoints": [100, 150, 200]}
               # ]
    all_options = []
    for option in options:
        all_options += cartesian_product(option)

    # Base slurm config
    slurm = SlurmConfig(executable = "/home/bucchera/periodic_isdf/octopus/isdf_build/octopus",
                    job_name = "name",
                    partition="bigmem",
                    nodes=1,
                    ntasks_per_node=1,
                    cpus_per_task=1)


    # Create each ISDF job
    root_dir = Path("outputs")

    for opt in all_options:
        # Job subdirectory
        job_name = ("KPointsGrid" +  "".join(str(i) for i in opt["KPointsGrid"])
                    + "_ISDFNpoints" + str(opt["ISDFNpoints"]))

        job_dir = root_dir / Path(job_name)
        job_dir.mkdir(exist_ok=True)

        # Input file
        silicon_input = base_input | opt
        inp_str = write_octopus_input(silicon_input)
        with open(file=job_dir / Path("inp"), mode="w") as fid:
            fid.write(inp_str)

        # Slurm script
        # Modify according to problem size
        slurm.ntasks_per_node = np.prod(opt["KPointsGrid"])
        slurm.job_name = job_name

        with open(file=job_dir / Path("slurm.sh"), mode="w") as fid:
            fid.write(str(slurm))

    # ACE References
    # ACE will run by default for a hybrid functional
    base_input = mode | system | kpoint_input | scf_and_eigen_input | functional

    options = [{"KPointsGrid": [1, 1, 1]},
               {"KPointsGrid": [2, 2, 2]},
               {"KPointsGrid": [3, 3, 3]},
               {"KPointsGrid": [4, 4, 4]}]
               # {"KPointsGrid": [6, 6, 6]}]

    for opt in options:
        # Job subdirectory
        job_name = ("KPointsGrid" +  "".join(str(i) for i in opt["KPointsGrid"])
                    + "_ACE")

        job_dir = root_dir / Path(job_name)
        job_dir.mkdir(exist_ok=True)

        # Input file
        silicon_input = base_input | opt
        inp_str = write_octopus_input(silicon_input)
        with open(file=job_dir / Path("inp"), mode="w") as fid:
            fid.write(inp_str)

        # Slurm script
        # Modify according to problem size
        slurm.ntasks_per_node = np.prod(opt["KPointsGrid"])
        slurm.job_name = job_name

        with open(file=job_dir / Path("slurm.sh"), mode="w") as fid:
            fid.write(str(slurm))
