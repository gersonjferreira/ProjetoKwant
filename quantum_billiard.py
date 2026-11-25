"""Four-terminal rectangular quantum billiard and its conductance matrix."""

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import re
import tomllib
import xml.etree.ElementTree as ET

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


NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
COLORS = {
    "#000000": "black", "#000": "black", "black": "black",
    "#0000ff": "blue", "#00f": "blue", "blue": "blue",
}


def _transform_matrix(text: str) -> np.ndarray:
    """Convert an SVG transform attribute into a 3x3 affine matrix."""
    matrix = np.eye(3)
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", text or ""):
        a = [float(v) for v in NUMBER.findall(args)]
        step = np.eye(3)
        if name == "translate":
            step[:2, 2] = (a[0], a[1] if len(a) > 1 else 0.0)
        elif name == "scale":
            step[0, 0], step[1, 1] = a[0], a[1] if len(a) > 1 else a[0]
        elif name == "rotate":
            c, s = math.cos(math.radians(a[0])), math.sin(math.radians(a[0]))
            step[:2, :2] = [[c, -s], [s, c]]
            if len(a) == 3:
                pre, post = np.eye(3), np.eye(3)
                pre[:2, 2], post[:2, 2] = (-a[1], -a[2]), (a[1], a[2])
                step = post @ step @ pre
        elif name == "matrix":
            step[:2, :] = np.array(a).reshape(3, 2).T
        elif name == "skewX":
            step[0, 1] = math.tan(math.radians(a[0]))
        elif name == "skewY":
            step[1, 0] = math.tan(math.radians(a[0]))
        else:
            raise ValueError(f"Unsupported SVG transform: {name}")
        matrix = matrix @ step
    return matrix


def _path_subpaths(d: str) -> list:
    """Flatten an SVG path (M L H V C S Q T Z, absolute or relative) to polygons."""
    tokens = re.findall(r"[A-Za-z]|" + NUMBER.pattern, d)
    subpaths, current = [], []
    pos = start = np.zeros(2)
    last_ctrl, last_cmd = None, ""
    i, cmd = 0, ""

    def take(count):
        nonlocal i
        values = [float(v) for v in tokens[i:i + count]]
        i += count
        return values

    def bezier(points, steps=16):
        t = np.linspace(0, 1, steps + 1)[1:, None]
        pts = [np.asarray(p) for p in points]
        while len(pts) > 1:
            pts = [(1 - t) * p + t * q for p, q in zip(pts[:-1], pts[1:])]
        return list(pts[0])

    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                if current:
                    subpaths.append(current)
                current, pos, last_ctrl, last_cmd = [], start, None, "z"
                continue
        rel = cmd.islower()
        c = cmd.upper()
        base = pos if rel else np.zeros(2)
        if c == "M":
            if current:
                subpaths.append(current)
            pos = start = base + take(2)
            current = [pos]
            cmd = "l" if rel else "L"
            last_ctrl = None
        elif c == "L":
            pos = base + take(2)
            current.append(pos)
            last_ctrl = None
        elif c == "H":
            pos = np.array([take(1)[0] + (pos[0] if rel else 0.0), pos[1]])
            current.append(pos)
            last_ctrl = None
        elif c == "V":
            pos = np.array([pos[0], take(1)[0] + (pos[1] if rel else 0.0)])
            current.append(pos)
            last_ctrl = None
        elif c in "CS":
            if c == "C":
                p1 = base + take(2)
            else:
                p1 = 2 * pos - last_ctrl if last_cmd in ("C", "S") else pos
            p2 = base + take(2)
            end = base + take(2)
            current.extend(bezier([pos, p1, p2, end]))
            pos, last_ctrl = end, p2
        elif c in "QT":
            if c == "Q":
                p1 = base + take(2)
            else:
                p1 = 2 * pos - last_ctrl if last_cmd in ("Q", "T") else pos
            end = base + take(2)
            current.extend(bezier([pos, p1, end]))
            pos, last_ctrl = end, p1
        else:
            raise ValueError(f"Unsupported SVG path command: {cmd}")
        last_cmd = c
    if current:
        subpaths.append(current)
    return [np.array(p) for p in subpaths if len(p) > 2]


def _fill_color(element) -> str | None:
    style = dict(
        item.split(":", 1)
        for item in element.get("style", "").split(";")
        if ":" in item
    )
    fill = style.get("fill", element.get("fill", "")).strip().lower()
    return COLORS.get(fill)


def _rasterize(polygons: list, pixel_size: float) -> set:
    """Pixels whose centers lie inside the polygons (even-odd rule)."""
    stacked = np.vstack(polygons)
    i0, j0 = np.floor(stacked.min(axis=0) / pixel_size).astype(int)
    i1, j1 = np.ceil(stacked.max(axis=0) / pixel_size).astype(int)
    ii, jj = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1), indexing="ij")
    px = (ii.ravel() + 0.5) * pixel_size
    py = (jj.ravel() + 0.5) * pixel_size
    inside = np.zeros(px.shape, dtype=bool)
    for poly in polygons:
        x1, y1 = poly[:, 0], poly[:, 1]
        x2, y2 = np.roll(x1, -1), np.roll(y1, -1)
        for ax, ay, bx, by in zip(x1, y1, x2, y2):
            if ay == by:
                continue
            crosses = (ay > py) != (by > py)
            x_at = ax + (py - ay) * (bx - ax) / (by - ay)
            inside ^= crosses & (px < x_at)
    return set(zip(ii.ravel()[inside].tolist(), jj.ravel()[inside].tolist()))


def parse_svg(svg_path: Path, pixel_size: float = 1.0) -> tuple[set, list]:
    """Read the system (black) and leads (blue) from an SVG file.

    Shapes are rasterized onto a grid where one pixel of `pixel_size` SVG user
    units is one lattice site; group/element transforms are honoured. Pixel
    coordinates are (column, row) with the row growing downwards.

    Returns (system_pixels, [lead_pixels, ...]).
    """
    black, blue = [], []

    def walk(element, matrix):
        tag = element.tag.split("}")[-1]
        if tag == "defs":
            return
        matrix = matrix @ _transform_matrix(element.get("transform", ""))
        if tag == "rect":
            x, y = float(element.get("x", 0)), float(element.get("y", 0))
            w, h = float(element.get("width")), float(element.get("height"))
            polys = [np.array([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])]
        elif tag == "path":
            polys = _path_subpaths(element.get("d", ""))
        else:
            polys = None
        if polys:
            color = _fill_color(element)
            if color:
                moved = [(p @ matrix[:2, :2].T) + matrix[:2, 2] for p in polys]
                (black if color == "black" else blue).append(moved)
        for child in element:
            walk(child, matrix)

    walk(ET.parse(svg_path).getroot(), np.eye(3))
    system = set()
    for polys in black:
        system |= _rasterize(polys, pixel_size)
    return system, [_rasterize(polys, pixel_size) for polys in blue]


def make_system_from_svg(svg_path: Path, hopping: float, energy: float,
                         pixel_size: float = 1.0):
    """Build a Kwant system from an SVG file.

    The black area is the scattering region and each blue rectangle is a
    semi-infinite lead that is periodic along the rectangle's narrow side, so
    the lead cross-section is its long side. The end of the rectangle that
    lies farther from the black area is where the lead extends to infinity.
    One SVG pixel is one lattice site.
    """
    system_px, lead_px = parse_svg(svg_path, pixel_size)
    if not system_px:
        raise ValueError("No black region found in SVG")
    if not lead_px:
        raise ValueError("No blue lead rectangles found in SVG")

    # Kwant's y axis points up, so flip rows to keep the picture orientation.
    flip = lambda sites: {(i, -j) for i, j in sites}
    system_sites = flip(system_px)

    leads = []
    for px in lead_px:
        sites = flip(px)
        xs = [x for x, _ in sites]
        ys = [y for _, y in sites]
        nx, ny = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        if len(sites) != nx * ny:
            raise ValueError("Blue lead shapes must be (axis-aligned) rectangles")
        if nx == ny:
            raise ValueError("Blue lead rectangles must have distinct side lengths")
        axis = 0 if nx < ny else 1  # narrow side = periodicity direction
        coords = np.array(sorted(sites))
        middle = (coords[:, axis].min() + coords[:, axis].max()) / 2
        low = sum(1 for s in sites if s in system_sites and s[axis] < middle)
        high = sum(1 for s in sites if s in system_sites and s[axis] > middle)
        if low == high:
            raise ValueError("Cannot tell which end of a lead faces the system")
        sign = -1 if low < high else 1
        direction = (sign, 0) if axis == 0 else (0, sign)
        edge = coords[:, axis].min() if sign < 0 else coords[:, axis].max()
        cell = [tuple(s) for s in coords if s[axis] == edge]
        leads.append((sites, direction, cell))
        system_sites |= sites

    lattice = kwant.lattice.square(norbs=1)
    system = kwant.Builder()
    for site in system_sites:
        system[lattice(*site)] = 4 * hopping
    system[lattice.neighbors()] = -hopping

    for _, direction, cell in leads:
        lead = kwant.Builder(kwant.TranslationalSymmetry(direction))
        for site in cell:
            lead[lattice(*site)] = 4 * hopping
        lead[lattice.neighbors()] = -hopping
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
        "--svg",
        type=Path,
        help="path to SVG file defining the system (if provided, overrides config parameters)",
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
    
    if args.svg:
        # Build system from SVG
        params = load_parameters(args.config)
        scattering_matrix = kwant.smatrix(
            make_system_from_svg(args.svg, params.hopping, params.energy),
            energy=params.energy
        )
        matrix = scattering_matrix.conductance_matrix()
    else:
        # Build system from parameters
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
