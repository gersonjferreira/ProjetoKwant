# SVG-Based System Definition Guide

## Overview

The quantum billiard system can now be defined using an SVG file, allowing for flexible and visual system design. The code reads the SVG and constructs a tight-binding model based on pixel coordinates.

## SVG Format Specification

### Color Coding

- **Black (#000000)**: Defines the main scattering region. Any filled black area in the SVG becomes the quantum billiard system.
- **Blue (#0000FF)**: Defines semi-infinite leads (perfect one-dimensional channels). Each blue rectangle becomes a lead.

### Key Properties

1. **Pixel Coordinates**: The number of lattice sites corresponds to the pixel dimensions of the SVG elements.
   - Each pixel = one lattice site in the tight-binding model
   - Coordinates are automatically normalized to start from (0, 0)

2. **Lead Periodicity**: Blue rectangles represent leads with:
   - Periodicity along the narrow dimension of the rectangle
   - Semi-infinite extension along the direction perpendicular to the rectangle
   - Automatic detection of lead direction (horizontal or vertical)

3. **Transformations**: Supported SVG transformations include:
   - Rotation (90-degree rotation for leads is handled automatically)
   - Translation (all coordinates are normalized)

## Example SVG Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="49mm" height="41.6mm" viewBox="0 0 49 41.6" xmlns="http://www.w3.org/2000/svg">
  <g>
    <!-- Main scattering region (black) -->
    <path style="fill:#000000" d="M 45.3,32.1 V 50.9 H 86.6 V 13.2 H 66.6 v 19.1 z"/>
    
    <!-- Left lead (blue) -->
    <rect x="41.5" y="34.5" width="7" height="12.9" style="fill:#0000ff"/>
    
    <!-- Right lead (blue) -->
    <rect x="83.5" y="34.9" width="7" height="12.9" style="fill:#0000ff"/>
    
    <!-- Bottom lead (blue) -->
    <rect x="62.6" y="16.2" width="7" height="12.9" style="fill:#0000ff"/>
    
    <!-- Top lead (blue, rotated 90 degrees) -->
    <rect x="47.8" y="-73.2" width="7" height="12.9" style="fill:#0000ff" transform="rotate(90)"/>
  </g>
</svg>
```

## Usage

### Command Line

#### Using SVG-based system:
```bash
python quantum_billiard.py --config parameters.toml --svg system.svg --output data/conductance.npz
```

#### Using traditional parameters:
```bash
python quantum_billiard.py --config parameters.toml --output data/conductance.npz
```

### Python API

```python
from pathlib import Path
from quantum_billiard import make_system_from_svg
import kwant

svg_path = Path("system.svg")
hopping = 1.0
energy = 0.8

system = make_system_from_svg(svg_path, hopping, energy)
scattering_matrix = kwant.smatrix(system, energy=energy)
conductance = scattering_matrix.conductance_matrix()
```

## Implementation Details

### SVG Parsing (`parse_svg` function)

1. **Reads the SVG file** using Python's `xml.etree.ElementTree`
2. **Identifies blue rectangles** as leads:
   - Extracts x, y, width, height attributes
   - Handles 90-degree rotations by computing rotated bounding box
   - Converts to integer pixel coordinates
   - Stores lead sites as list of (x, y) tuples
3. **Identifies black paths** as the main system:
   - Uses path rasterization to convert SVG paths to pixels
   - Applies scanline fill algorithm to fill polygon regions
4. **Normalizes all coordinates** to start from (0, 0)

### Path Rasterization (`parse_path_to_pixels` function)

Converts SVG path commands (M, L, H, V, Z, etc.) to pixel coordinates using:
- Bresenham line rasterization for outline
- Scanline fill algorithm for interior

Supported SVG path commands:
- **M/m**: Moveto (absolute/relative)
- **L/l**: Lineto (absolute/relative)
- **H/h**: Horizontal lineto (absolute/relative)
- **V/v**: Vertical lineto (absolute/relative)
- **Z/z**: Closepath
- **C/c**, **S/s**, **Q/q**, **T/t**, **A/a**: Curved paths (basic support)

### System Construction (`make_system_from_svg` function)

1. **Parses the SVG** to get system sites and lead sites
2. **Creates Kwant lattice** (square lattice with 1 orbital per site)
3. **Adds main system**:
   - Each site has energy 4*hopping (on-site energy)
   - Nearest-neighbor hopping with strength -hopping
4. **Attaches leads**:
   - Automatically determines lead direction (up, down, left, right)
   - Creates lead with translational symmetry in the appropriate direction
   - Adds hopping to neighboring sites within the lead
5. **Finalizes the system** for use with Kwant solvers

### Lead Direction Detection

The code determines lead direction by analyzing the rectangular bounds:
- **Vertical lead** (single x coordinate): extends along y-direction
  - Direction: (+1, 0) if right of system, (-1, 0) if left
- **Horizontal lead** (single y coordinate): extends along x-direction
  - Direction: (0, +1) if above system, (0, -1) if below

## Creating Your Own SVG

### Using Inkscape (Recommended)

1. **Draw shapes**:
   - Use black rectangles or paths for the main billiard region
   - Use blue rectangles for leads
2. **Set colors**:
   - Black: RGB(0, 0, 0) or #000000
   - Blue: RGB(0, 0, 255) or #0000FF
3. **Position accurately**:
   - Measure carefully to ensure leads connect to the billiard edge
   - Each pixel unit corresponds to one lattice site
4. **Export as SVG**:
   - Choose "Plain SVG" for maximum compatibility

### Using Python/matplotlib

```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots()

# Main billiard region (black)
billiard = patches.Polygon([(10, 10), (60, 10), (60, 50), (10, 50)], 
                           closed=True, fill=True, facecolor='black')
ax.add_patch(billiard)

# Left lead (blue)
lead = patches.Rectangle((0, 25), 10, 10, fill=True, facecolor='blue')
ax.add_patch(lead)

ax.set_xlim(-5, 70)
ax.set_ylim(0, 60)
ax.set_aspect('equal')
plt.savefig('system.svg', format='svg')
```

## Validation and Debugging

### Check parsed system:

```python
from quantum_billiard import parse_svg
from pathlib import Path

svg_path = Path("system.svg")
system_sites, leads = parse_svg(svg_path)

print(f"System sites: {len(system_sites)}")
print(f"System bounds: x=[{min(x for x,y in system_sites)}, {max(x for x,y in system_sites)}]")
print(f"              y=[{min(y for x,y in system_sites)}, {max(y for x,y in system_sites)}]")

print(f"\nLeads: {len(leads)}")
for lead_id, lead_sites in leads.items():
    xs = sorted(set(x for x, y in lead_sites))
    ys = sorted(set(y for x, y in lead_sites))
    print(f"  Lead {lead_id}: {len(lead_sites)} sites")
    print(f"    x range: [{xs[0]}, {xs[-1]}]")
    print(f"    y range: [{ys[0]}, {ys[-1]}]")
```

## Parameters

The `parameters.toml` file still controls:
- **hopping**: Nearest-neighbor hopping strength (must be positive)
- **energy**: Fermi energy for the scattering calculation
- **length, width, lead_width**: Ignored when using SVG input

Example `parameters.toml`:
```toml
[system]
hopping = 1.0
energy = 0.8

# These are ignored when using --svg flag
length = 40
width = 30
lead_width = 10
```

## Tips and Best Practices

1. **Lead Connection**: Ensure lead rectangles overlap or touch the main billiard region for proper connection.
2. **Square Lattice**: The code assumes a square lattice. All dimensions should use the same units.
3. **Pixel Precision**: For accurate models, use integer pixel coordinates. The code will round floats to nearest integer.
4. **Lead Symmetry**: Leads should have constant width perpendicular to their extension direction.
5. **Avoid Noise**: Complex or noisy SVG paths may produce unexpected results. Keep shapes simple and geometric.

## Troubleshooting

### "No black region found in SVG"
- Ensure the main billiard region is colored with #000000 (pure black)
- Check that the fill style includes `fill:#000000`

### "No blue lead rectangles found in SVG"
- Ensure leads are colored with #0000FF (pure blue)
- Check that rectangles use `style="fill:#0000ff"`

### Wrong number of sites
- Verify that SVG coordinates are in pixels (1 unit = 1 site)
- Check the viewBox and width/height attributes
- Ensure units are properly set in Inkscape (File > Document Properties > Units: px)

### Incorrect lead direction
- Leads must have distinct x or y ranges (not mixed)
- For rotated rectangles, ensure the rotation is 90 degrees and handled correctly
- Check that leads are aligned with system edges
