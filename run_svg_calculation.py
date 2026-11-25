#!/usr/bin/env python
"""Quick start script to run SVG-based quantum billiard calculation and open analysis."""

import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 70)
    print("SVG-Based Quantum Billiard - Quick Start")
    print("=" * 70)
    print()
    
    # Step 1: Validate SVG
    print("Step 1: Validating SVG system...")
    result = subprocess.run([sys.executable, "test_system_parsing.py"], cwd=Path.cwd())
    if result.returncode != 0:
        print("Warning: SVG validation had issues, but continuing...")
    print()
    
    # Step 2: Run calculation
    print("Step 2: Running quantum transport calculation...")
    print("Command: python quantum_billiard.py --svg system.svg --output data/conductance.npz")
    print()
    
    result = subprocess.run(
        [sys.executable, "quantum_billiard.py", "--svg", "system.svg", "--output", "data/conductance.npz"],
        cwd=Path.cwd()
    )
    
    if result.returncode == 0:
        print()
        print("=" * 70)
        print("✓ Calculation complete!")
        print("=" * 70)
        print()
        print("Results saved to: data/conductance.npz")
        print()
        print("Next steps:")
        print("  1. Open analysis.ipynb in Jupyter")
        print("  2. Run all cells to see results and visualizations")
        print("  3. Modify system.svg and re-run for different geometries")
        print()
        print("To open Jupyter:")
        print("  jupyter notebook analysis.ipynb")
        print()
    else:
        print()
        print("Error: Calculation failed")
        print("Make sure:")
        print("  1. Kwant is installed")
        print("  2. system.svg exists")
        print("  3. parameters.toml is configured")
        sys.exit(1)

if __name__ == "__main__":
    main()
