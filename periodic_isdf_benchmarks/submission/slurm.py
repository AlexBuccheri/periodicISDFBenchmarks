""" Replace this with a fully-fledged slurm python module,
as used in the past
"""

from dataclasses import dataclass, field, fields
from typing import List


module_25c = """module purge
mpsd-modules 25c
module load gcc/13.2.0 openmpi/4.1.6 octopus-dependencies/full
unset CPATH 
unset LIBRARY_PATH
"""

@dataclass
class SlurmConfig:
    executable: str
    job_name: str = field(default="isdf", metadata={"kw": "job-name"})
    time: str = field(default="10:00:00", metadata={"kw": "time"})
    partition: str = field(default="draco-small", metadata={"kw": "partition"})
    nodes: int = field(default=1, metadata={"kw": "nodes"})
    ntasks_per_node: int = field(default=4, metadata={"kw": "ntasks-per-node"})
    cpus_per_task: int = field(default=8, metadata={"kw": "cpus-per-task"})
    exclusive: bool = field(default=True, metadata={"kw": "exclusive", "flag": True})  # flag = no RHS
    pre_script: str = field(default=module_25c)
    stdout: str = field(default="terminal.out")

    def to_sbatch_directives(self) -> List[str]:
        lines: List[str] = []

        for f in fields(self):
            try:
                kw = f.metadata["kw"]
                val = getattr(self, f.name)
                if f.metadata.get("flag", False):
                    if val:
                        lines.append(f"#SBATCH --{kw}")
                else:
                    lines.append(f"#SBATCH --{kw}={val}")
            except KeyError:
                pass

        return lines

    def __str__(self) -> str:
        """
        :return:
        """
        string = """#!/bin/bash

"""
        string += "\n".join(self.to_sbatch_directives())
        string += f"""\n
{self.pre_script}
EXE={self.executable}
OUT={self.stdout}
        
# Work in the submission directory
cd ${{SLURM_SUBMIT_DIR}}

# Set OMP_NUM_THREADS to the number cpu cores per MPI task
export OMP_NUM_THREADS=${{SLURM_CPUS_PER_TASK}}

# $SLURM_NTASKS = n_nodes * ntasks-per-node == total number of MPI processes
orterun -np $SLURM_NTASKS $EXE > $OUT
        """
        return string

