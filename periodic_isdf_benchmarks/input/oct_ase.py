""" Interoperability with Atomic Simulation Environment (ASE)
"""
import ase
import numpy as np
import scipy

from octoprepy.oct_units import angstrom_to_bohr, bohr_to_angstrom


def unit_vector(a):
    return np.asarray(a) / scipy.linalg.norm(a)


def lattice_angles_from_vectors(lattice_vectors):
    """
    Should a) test and b) reimplement with matrix ops
    """
    n_dim = len(lattice_vectors)

    assert (
        n_dim == 3
    ), "Calculation of angles between lattice vectors only coded for 3D systems"

    lattice_angles = []
    for i in range(0, n_dim):
        j = (i + 1) % n_dim
        angle = np.arccos(
            np.dot(
                unit_vector(lattice_vectors[i]),
                unit_vector(lattice_vectors[j]),
            )
        )
        lattice_angles.append(np.degrees(angle))

    return lattice_angles


def parse_oct_structure_to_atoms(options: dict) -> ase.atoms.Atoms:
    """

    Cannot handle any symbolic constants
    ASSUMES default Octopus units: Bohr, degrees, etc
    """
    # If not present, assume molecule (consistent with Octopus default)
    periodic_dims = options.get('PeriodicDimensions', 0)
    pbc = np.zeros(3)
    for i in range(periodic_dims):
        pbc[i] = 1
    pbc.astype(bool)

    # Coordinates or ReducedCoordinates
    keys = set(list(options))
    coord_key = list(keys.intersection({'Coordinates', 'ReducedCoordinates'}))
    assert len(coord_key) == 1, 'More than one coordinate definition key in input file'
    coord_key = coord_key[0]

    # Removing the encapsulating quotes
    species = [entry[0][1:-1] for entry in options[coord_key]]
    # TODO Consider an origin shift
    positions = []
    for entry in options[coord_key]:
        positions.append([r * bohr_to_angstrom for r in entry[1:]])

    keyword_map = {'Coordinates': 'positions', 'ReducedCoordinates': 'scaled_positions'}
    kwargs = {'symbols': species, keyword_map[coord_key]: positions, 'pbc': pbc}
    atoms = ase.atoms.Atoms(**kwargs)

    # LatticeParameters
    if any(pbc):
        # NOTE this immediately breaks as soon as symbolic notation is used
        constants_and_angles = options['LatticeParameters']

        if len(constants_and_angles) == 2:
            constants, angles = constants_and_angles
        else:
            constants = constants_and_angles
            lattice_vectors = options.get("LatticeVectors", None)
            assert lattice_vectors is not None, "LatticeVectors not defined in input, but required"
            angles = lattice_angles_from_vectors(lattice_vectors)

        atoms.set_cell(constants + angles, scale_atoms=False)

    return atoms


def ase_fully_periodic_atoms_to_oct_dict(atoms: ase.atoms.Atoms, origin_shift=False) -> dict:
    """

    """
    assert all(atoms.get_pbc()), "ASE atoms is not fully periodic"
    input = {}

    # LatticeParameters
    constants_and_angles = atoms.cell.cellpar()
    ndim = int(0.5 * len(constants_and_angles))
    input['LatticeParameters'] = [[c * angstrom_to_bohr for c in constants_and_angles[0:ndim]],
                                  constants_and_angles[ndim:].tolist()
                                  ]
    # ReducedCoordinates
    fractional_origin = np.full(ndim, 0.5) if origin_shift else np.zeros(shape=ndim)
    positions = np.asarray(atoms.get_scaled_positions()) - fractional_origin
    species = atoms.get_chemical_symbols()
    n_atoms = len(species)
    input["ReducedCoordinates"] = [[f'"{species[ia]}"'] + positions[ia].tolist() for ia in range(0, n_atoms)]

    return input


def ase_molecular_atoms_to_oct_dict(atoms: ase.atoms.Atoms, add_box=False) -> dict:
    """
    # Defines finite lattice vectors for all dimensions
    # lattice_params = np.asarray(input['LatticeParameters'])
    # mask = np.where(lattice_params <= numerically_zero)[0]
    # minimum_length = 0.5 * np.min(lattice_params[lattice_params > numerically_zero])
    # for i in mask:
    #     input['LatticeParameters'][i] = minimum_length

    """
    assert not any(atoms.get_pbc()), "ASE atoms is contains at least one periodic dimension"
    input = {}

    # Coordinates
    species = atoms.get_chemical_symbols()
    positions = np.asarray(atoms.get_positions()) * angstrom_to_bohr
    n_atoms = len(species)
    input['Coordinates'] = [[f'"{species[ia]}"'] + positions[ia].tolist() for ia in range(0, n_atoms)]

    # Optional lattice vectors
    numerically_zero = 1.e-6
    lattice = atoms.get_cell().array
    zero_lattice_vectors = np.all(np.abs(lattice) <= numerically_zero, axis=1)

    if all(zero_lattice_vectors) and add_box:
        ndims = positions.shape[1]
        constants = [2 * (np.max(positions[:, i]) - np.min(positions[:, i])) for i in range(ndims)]
        input['LatticeVectors'] = [[constants[0], 0., 0.], [0., constants[1], 0.], [0., 0., constants[2]]]

    return input


def ase_partially_periodic_atoms_oct_dict(atoms, centre_origin=True):
    """Convert ASE Atoms instance to Octopus input dict

     When PeriodicDimensions < 3, such as surfaces.

    In Octopus, the grid is always centered on the origin. Atomic positions need to be translated
    to be consistent with this. If atoms are too close to one side of the simulation box in the
    non-periodic direction the code may well not converge.

    :param atoms: Atoms instance.
    :return: input_string: Structure substring
    """
    assert any(atoms.get_pbc()), 'Atoms object must have at least one periodic dimension'
    input = {}

    # LatticeParameters
    constants_and_angles = atoms.cell.cellpar()
    ndim = int(0.5 * len(constants_and_angles))
    constants = constants_and_angles[0:ndim]
    input['LatticeParameters'] = [c * angstrom_to_bohr for c in constants]

    # LatticeVectors (row-wise in ASE, and in Octopus input)
    lattice = atoms.get_cell().array * angstrom_to_bohr
    origin = np.zeros(ndim)
    if centre_origin:
        # Centre the origin of the atomic positions on the centre of the lattice
        origin = 0.5 * np.sum(lattice, axis=0)

    input['LatticeVectors'] = [v / constants[i] for i, v in enumerate(lattice)]
    input['LatticeVectors'] = [v.tolist() for v in input['LatticeVectors']]

    # Coordinates
    species = atoms.get_chemical_symbols()
    positions = np.asarray(atoms.get_positions()) * angstrom_to_bohr - origin
    n_atoms = len(species)
    input['Coordinates'] = [[f'"{species[ia]}"'] + positions[ia].tolist() for ia in range(0, n_atoms)]

    return input


def ase_atoms_to_oct_dict(atoms: ase.atoms.Atoms, centre_origin=True) -> dict:
    """

    """
    # Fully periodic
    if all(atoms.get_pbc()):
        return ase_fully_periodic_atoms_to_oct_dict(atoms)

    # Molecular
    elif not any(atoms.get_pbc()):
        return ase_molecular_atoms_to_oct_dict(atoms)

    # Partially periodic
    else:
        return ase_partially_periodic_atoms_oct_dict(atoms, centre_origin=centre_origin)
