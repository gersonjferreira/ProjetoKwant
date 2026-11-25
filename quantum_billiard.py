"""Four-terminal rectangular quantum billiard and its conductance matrix."""

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import tomllib

import kwant
import numpy as np


LEAD_NAMES = ("left", "right", "bottom", "top")


@dataclass(frozen=True)
class Parameters:
    length: int
    width: int
    lead_width: int
    hopping: float
    energy: float

    def __post_init__(self):
        for name in ("length", "width", "lead_width"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.lead_width > min(self.length, self.width) - 2:
            raise ValueError(
                "lead_width must fit on every side without including corners"
            )
        for name in ("hopping", "energy"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"{name} must be a finite number")
        if self.hopping <= 0:
            raise ValueError("hopping must be positive")


def load_parameters(path: Path) -> Parameters:
    with path.open("rb") as file:
        config = tomllib.load(file)
    return Parameters(**config["system"])


def make_system(params: Parameters):
    lattice = kwant.lattice.square(norbs=1)
    system = kwant.Builder()
    system[
        (lattice(x, y) for x in range(params.length) for y in range(params.width))
    ] = 4 * params.hopping
    system[lattice.neighbors()] = -params.hopping

    horizontal_start = (params.width - params.lead_width) // 2
    vertical_start = (params.length - params.lead_width) // 2
    horizontal_range = range(horizontal_start, horizontal_start + params.lead_width)
    vertical_range = range(vertical_start, vertical_start + params.lead_width)
    leads = (
        ((-1, 0), (lattice(0, y) for y in horizontal_range)),
        ((1, 0), (lattice(params.length - 1, y) for y in horizontal_range)),
        ((0, -1), (lattice(x, 0) for x in vertical_range)),
        ((0, 1), (lattice(x, params.width - 1) for x in vertical_range)),
    )
    for direction, sites in leads:
        lead = kwant.Builder(kwant.TranslationalSymmetry(direction))
        lead[sites] = 4 * params.hopping
        lead[lattice.neighbors()] = -params.hopping
        system.attach_lead(lead)
    return system.finalized()


def conductance_matrix(params: Parameters) -> np.ndarray:
    scattering_matrix = kwant.smatrix(make_system(params), energy=params.energy)
    return scattering_matrix.conductance_matrix()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("parameters.toml"),
        help="path to a TOML parameter file (default: parameters.toml)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("data") / "conductance.npz",
        help="output NPZ file (default: data/conductance.npz; overwritten if present)",
    )
    args = parser.parse_args()
    if args.output.suffix.lower() != ".npz":
        parser.error("--output must have an .npz extension")
    params = load_parameters(args.config)
    matrix = conductance_matrix(params)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        conductance=matrix,
        lead_names=np.array(LEAD_NAMES),
        parameters=json.dumps(asdict(params)),
    )
    print("Lead order:", ", ".join(LEAD_NAMES))
    print(f"Fermi energy: {params.energy:g}")
    print("Conductance matrix G (e^2/h):")
    print(np.array2string(matrix, precision=6, suppress_small=True))
    print(f"Saved results to {args.output}")


if __name__ == "__main__":
    main()
