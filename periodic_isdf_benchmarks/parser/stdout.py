import re


def parse_scf_time(string: str) -> dict:
    """ Parse the time taken per SCF iteration from stdout string
    :return: scf_times (in seconds)
    """
    pattern = re.compile(
        r"Elapsed time for SCF step\s+(?P<step>\d+):\s*(?P<time>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    )
    matches = pattern.finditer(string)
    scf_times = {int(m.group("step")): float(m.group("time")) for m in matches}
    return scf_times


def parse_exchange_energy(string: str) -> dict:
    """ Parse the exchange energy per SCF iteration
    NOTE, ONLY works if I add a print statement to v_ks.F90
    :return:
    """
    pattern = re.compile(r'Exact exchange energy\s+([-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)')
    matches = pattern.findall(string)
    return {int(i): float(energy) for i, energy in enumerate(matches)}


def parse_kmeans_iterations(string: str) -> dict:
    """ Parse the number of kmeans iterations per SCF iteration.

    Assumes a complete output, with kmeans initially printing
    when running the initial guess (SCF = 0)

    :return:
    """
    # Match either an SCF cycle header or a KMeans convergence line
    pat = re.compile(r"""
        (?:SCF\ CYCLE\ ITER\ \#\s*(?P<iter>\d+)) |
        (?:Kmeans\ converged\ in\s*(?P<Kmeans>\d+)\s*iterations)
    """, re.VERBOSE | re.IGNORECASE)

    kmeans_itr = {}
    # Kmeans will run for the initial guess, prior to the SCF
    current_iter = 0
    for m in pat.finditer(string):
        if m.group("iter"):
            current_iter = int(m.group("iter"))
        elif m.group("Kmeans"):
            kmeans_itr[current_iter] = int(m.group("Kmeans"))
    return kmeans_itr
