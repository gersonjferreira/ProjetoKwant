# Quantum Billiard with SVG-Based System Definition

## New Feature: SVG-Based System Definition

The quantum billiard system can now be defined using an SVG (Scalable Vector Graphics) file, providing a visual and flexible way to design complex quantum transport systems.

### Quick Start

1. **Create or modify your SVG file** (`system.svg`):
   - Black regions: Main scattering billiard
   - Blue rectangles: Semi-infinite leads

2. **Run with SVG input**:
   ```bash
   python quantum_billiard.py --config parameters.toml --svg system.svg --output data/conductance.npz
   ```

3. **Or use traditional parameters**:
   ```bash
   python quantum_billiard.py --config parameters.toml --output data/conductance.npz
   ```

## How It Works

### SVG File Structure

The SVG file should contain:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="49mm" height="41.6mm" xmlns="http://www.w3.org/2000/svg">
  <!-- Main billiard region (black polygon or path) -->
  <path style="fill:#000000" d="M ... V ... H ... Z"/>
  
  <!-- Lead 1 (blue rectangle) -->
  <rect x="41.5" y="34.5" width="7" height="12.9" style="fill:#0000ff"/>
  
  <!-- Lead 2 (blue rectangle) -->
  <rect x="83.5" y="34.9" width="7" height="12.9" style="fill:#0000ff"/>
  
  <!-- Lead 3 (vertical, blue rectangle) -->
  <rect x="62.6" y="16.2" width="7" height="12.9" style="fill:#0000ff"/>
  
  <!-- Lead 4 (horizontal, blue rectangle with rotation) -->
  <rect x="47.8" y="-73.2" width="7" height="12.9" 
        style="fill:#0000ff" transform="rotate(90)"/>
</svg>
```

### Color Coding

- **Black (#000000)**: Main scattering region
- **Blue (#0000FF)**: Semi-infinite leads (perfect 1D channels)

### Pixel-to-Sites Mapping

Each pixel in the SVG corresponds to one lattice site:
- Coordinates are automatically extracted from SVG dimensions
- Number of sites = pixel dimensions of each shape
- All coordinates are automatically normalized to start from (0, 0)

### Lead Direction Detection

The code automatically detects lead direction based on rectangle dimensions:
- **Vertical leads**: Height > Width (extend along y-axis)
- **Horizontal leads**: Width > Height (extend along x-axis)
- Lead direction is determined relative to the main system location

## Usage Examples

### Example 1: Using Command Line

```bash
# Calculate conductance with SVG-defined system
python quantum_billiard.py --svg system.svg --output results.npz

# Using custom config file
python quantum_billiard.py --svg system.svg --config myconfig.toml --output results.npz
```

### Example 2: Using Python API

```python
from pathlib import Path
from quantum_billiard import make_system_from_svg
import kwant

# Load system from SVG
svg_path = Path("system.svg")
system = make_system_from_svg(svg_path, hopping=1.0, energy=0.8)

# Calculate scattering matrix
smatrix = kwant.smatrix(system, energy=0.8)

# Get conductance matrix
conductance = smatrix.conductance_matrix()
print(conductance)
```

### Example 3: Testing System Parsing

```bash
# Analyze the parsed system without running full calculation
python test_system_parsing.py

# Output: system_analysis.json with detailed information
```

## File Structure

```
ProjetoKwant/
├── quantum_billiard.py         # Main script with SVG support
├── parameters.toml             # Configuration file (hopping, energy)
├── system.svg                  # System geometry (black region + blue leads)
├── test_system_parsing.py      # Test and validate SVG parsing
├── SVG_SYSTEM_GUIDE.md         # Detailed SVG guide
├── analysis.ipynb              # Analysis notebook
└── data/
    └── conductance.npz         # Output: conductance matrix
```

## Available Commands

### Main Script

```bash
# Show help
python quantum_billiard.py --help

# Key options:
#   --config FILE.toml    Path to parameters file (default: parameters.toml)
#   --svg FILE.svg        Path to SVG system file (optional)
#   --output FILE.npz     Output file (default: data/conductance.npz)
```

### Testing

```bash
# Test SVG parsing without kwant
python test_system_parsing.py

# Output files:
#   - Console: Detailed analysis
#   - system_analysis.json: Structured system information
```

## Parameters

The `parameters.toml` file controls:

```toml
[system]
# Hopping strength (must be positive)
hopping = 1.0

# Fermi energy for transport calculation
energy = 0.8

# These are ignored when using --svg flag:
# length = 40
# width = 30
# lead_width = 10
```

## Key Functions

### `parse_svg(svg_path: Path) -> tuple[set, dict]`
Parses SVG file and extracts:
- Black region as system sites
- Blue rectangles as leads
Returns normalized coordinates and lead information

### `make_system_from_svg(svg_path: Path, hopping: float, energy: float)`
Builds a Kwant system from SVG:
- Creates square lattice with specified hopping
- Adds leads with translational symmetry
- Returns finalized Kwant system ready for transport calculations

### `parse_path_to_pixels(path_data: str) -> set`
Converts SVG path commands to pixel coordinates
- Supports M, L, H, V, Z commands
- Uses Bresenham line rasterization
- Implements scanline fill algorithm

### `fill_polygon(vertices: list, boundary_pixels: set) -> set`
Fills a polygon region using scanline algorithm
- Guarantees complete fill of interior
- Returns set of all interior + boundary pixels

## Creating SVG Files

### Using Inkscape (Recommended)

1. Create shapes with desired geometry
2. Set fill colors:
   - Black (#000000) for main region
   - Blue (#0000FF) for leads
3. Export as "Plain SVG" format
4. Verify in text editor that fill colors are correct

### Using Python/Matplotlib

```python
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

fig, ax = plt.subplots(figsize=(8, 6))

# Main billiard (black polygon)
billiard_verts = [(10, 10), (60, 10), (60, 50), (40, 50), (40, 30), (10, 30)]
billiard = Polygon(billiard_verts, facecolor='black', edgecolor='black')
ax.add_patch(billiard)

# Left lead (blue rectangle)
left_lead = Rectangle((0, 25), 10, 10, facecolor='blue', edgecolor='blue')
ax.add_patch(left_lead)

# Right lead (blue rectangle)
right_lead = Rectangle((70, 25), 10, 10, facecolor='blue', edgecolor='blue')
ax.add_patch(right_lead)

# Bottom lead (blue rectangle)
bottom_lead = Rectangle((30, 0), 10, 10, facecolor='blue', edgecolor='blue')
ax.add_patch(bottom_lead)

ax.set_xlim(-5, 85)
ax.set_ylim(-5, 60)
ax.set_aspect('equal')
plt.savefig('system.svg', format='svg', bbox_inches='tight')
```

## Troubleshooting

### "No black region found in SVG"
- Verify fill color is exactly #000000 (pure black)
- Check style attribute: `style="fill:#000000"`

### "No blue lead rectangles found in SVG"
- Verify fill color is exactly #0000ff (pure blue)
- Ensure rectangles (not paths) are used for leads
- Check style attribute: `style="fill:#0000ff"`

### Wrong number of sites
- Verify SVG viewBox coordinates
- Check that units are in pixels
- In Inkscape: File > Document Properties > Units: px

### Lead direction incorrect
- Ensure leads are rectangular with clear width/height ratio
- Avoid diagonal or complex shapes for leads
- Use simple geometric rectangles only

### Coordinate issues with rotated leads
- Rotation transformation (rotate(90)) is automatically handled
- Ensure rotation is exactly 90 degrees
- Coordinates are normalized after rotation

## Validation

Run the test script to validate your SVG:

```bash
python test_system_parsing.py
```

This will:
1. Parse the SVG
2. Extract system geometry and leads
3. Identify lead directions and periodicities
4. Check for common issues
5. Generate `system_analysis.json` with detailed information

## Performance Notes

- System size depends on SVG pixel dimensions
- Larger systems require more memory
- Kwant calculation time scales with system size
- For large systems (>1000 sites total), consider computational resources

## References

- **Kwant Project**: https://kwant-project.org/
- **SVG Specification**: https://www.w3.org/TR/SVG2/
- **Inkscape**: https://inkscape.org/

## Citation

If you use this code in research, please cite:

```bibtex
@software{kwant2024,
  author = {Groth, Christoph and Wimmer, Michael and others},
  title = {Kwant: A software package for quantum transport},
  year = {2024},
  url = {https://kwant-project.org/}
}
```

## License

Same as the original Kwant project
