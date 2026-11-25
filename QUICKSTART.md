# Quick Start: SVG-Based Quantum Billiard Systems

## 5-Minute Quick Start

### 1. Prepare Your SVG File

Ensure your `system.svg` has:
- **Black regions** (#000000) for the main billiard
- **Blue rectangles** (#0000ff) for semi-infinite leads

Each pixel = 1 lattice site

### 2. Set Parameters

Edit `parameters.toml`:
```toml
[system]
hopping = 1.0      # Hopping strength
energy = 0.8       # Fermi energy
```

### 3. Run Calculation

```bash
python quantum_billiard.py --svg system.svg --output data/conductance.npz
```

### 4. Check Results

Output: `conductance.npz` with:
- `conductance`: 4×4 conductance matrix
- `lead_names`: Order of leads
- `parameters`: Configuration used

## Understanding the Output

The conductance matrix shows transmission and reflection between leads:
- Diagonal elements: Reflection (should be close to 0 for ballistic transport)
- Off-diagonal elements: Transmission between different leads
- Units: e²/h (quantum of conductance)

## Common SVG Shapes

### Four-Terminal Billiard
```
  Lead (top)
       ↓
  ┌─────────┐
  │         │  
L │  Black  │ R
  │  Billiard│  
  │         │  
  └─────────┘
       ↑
   Lead (bottom)
```

### More Complex Geometry
You can create:
- Rectangular billiards
- T-shaped regions
- Complex polygons
- Multiple isolated leads

## Tips

1. **Keep SVG simple**: Use basic rectangles and polygons
2. **Check colors carefully**: 
   - Black must be #000000 (not gray)
   - Blue must be #0000ff (not other colors)
3. **Align leads properly**: They should touch or overlap the main region
4. **Test first**: Use `test_system_parsing.py` to validate

## Analyze Your System

```bash
python test_system_parsing.py
```

This creates `system_analysis.json` showing:
- Number of sites per region
- Lead directions and periodicities
- Coordinate ranges
- Validation warnings

## Next Steps

For detailed information, see:
- `SVG_SYSTEM_GUIDE.md`: Complete specification
- `README_SVG_FEATURES.md`: Full feature documentation
- `analysis.ipynb`: Example analysis of results
