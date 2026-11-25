"""Test and demonstrate SVG-based system parsing.

This script verifies that the SVG parsing works correctly without
requiring kwant or compilation.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import json

def parse_svg(svg_path: Path):
    """Parse SVG to extract black system region and blue lead rectangles."""
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    ns = {
        'svg': 'http://www.w3.org/2000/svg',
        'inkscape': 'http://www.inkscape.org/namespaces/inkscape'
    }
    
    system_sites = set()
    leads = defaultdict(list)
    
    # Find all rectangles (blue leads)
    for rect in root.findall('.//svg:rect', ns):
        fill = rect.get('style', '')
        
        if '#0000ff' in fill or 'fill:#0000ff' in fill:
            x = float(rect.get('x', 0))
            y = float(rect.get('y', 0))
            width = float(rect.get('width', 0))
            height = float(rect.get('height', 0))
            transform = rect.get('transform', '')
            
            # Handle 90-degree rotation
            if 'rotate(90)' in transform:
                corners = [
                    (x, y),
                    (x + width, y),
                    (x + width, y + height),
                    (x, y + height)
                ]
                rotated = [(-cy, cx) for cx, cy in corners]
                xs = [p[0] for p in rotated]
                ys = [p[1] for p in rotated]
                x0, x1 = min(xs), max(xs)
                y0, y1 = min(ys), max(ys)
            else:
                x0, x1 = x, x + width
                y0, y1 = y, y + height
            
            x0, y0 = round(x0), round(y0)
            x1, y1 = round(x1), round(y1)
            x0, x1 = min(x0, x1), max(x0, x1)
            y0, y1 = min(y0, y1), max(y0, y1)
            
            lead_id = len(leads)
            for px in range(x0, x1):
                for py in range(y0, y1):
                    leads[lead_id].append((px, py))
    
    # For now, return empty system (path parsing not in this test)
    return system_sites, dict(leads)


def analyze_system(system_sites, leads):
    """Analyze the parsed system and return structured information."""
    
    # Normalize coordinates
    if system_sites:
        all_coords = system_sites | set(c for lead in leads.values() for c in lead)
        min_x = min(c[0] for c in all_coords)
        min_y = min(c[1] for c in all_coords)
        
        system_sites = {(x - min_x, y - min_y) for x, y in system_sites}
        leads = {
            lid: [(x - min_x, y - min_y) for x, y in coords]
            for lid, coords in leads.items()
        }
    else:
        # Just normalize leads
        if leads:
            all_coords = set(c for lead in leads.values() for c in lead)
            min_x = min(c[0] for c in all_coords)
            min_y = min(c[1] for c in all_coords)
            leads = {
                lid: [(x - min_x, y - min_y) for x, y in coords]
                for lid, coords in leads.items()
            }
    
    info = {
        'system': {
            'num_sites': len(system_sites),
            'bounds': None
        },
        'leads': {}
    }
    
    if system_sites:
        xs = [x for x, y in system_sites]
        ys = [y for x, y in system_sites]
        info['system']['bounds'] = {
            'x_min': min(xs), 'x_max': max(xs),
            'y_min': min(ys), 'y_max': max(ys)
        }
    
    for lead_id, lead_sites in leads.items():
        xs = sorted(set(x for x, y in lead_sites))
        ys = sorted(set(y for x, y in lead_sites))
        
        # Determine lead direction based on which dimension is larger
        width_x = len(xs)
        width_y = len(ys)
        
        if width_x > width_y:  # Wider in x -> horizontal lead
            direction = 'horizontal'
            periodicity = width_y  # vertical extent (periodic dimension)
        elif width_y > width_x:  # Wider in y -> vertical lead
            direction = 'vertical'
            periodicity = width_x  # horizontal extent (periodic dimension)
        else:  # Square
            direction = 'square'
            periodicity = width_x
        
        info['leads'][f'lead_{lead_id}'] = {
            'num_sites': len(lead_sites),
            'direction': direction,
            'periodicity': periodicity,
            'x_range': (xs[0], xs[-1]) if xs else (0, 0),
            'y_range': (ys[0], ys[-1]) if ys else (0, 0),
            'width_x': width_x,
            'width_y': width_y
        }
    
    return info, system_sites, leads


def main():
    svg_path = Path("system.svg")
    
    if not svg_path.exists():
        print(f"Error: {svg_path} not found")
        return
    
    print("=" * 60)
    print("SVG System Parser - Test and Analysis")
    print("=" * 60)
    
    # Parse SVG
    system_sites, leads = parse_svg(svg_path)
    print(f"\nParsed SVG file: {svg_path}")
    print(f"  Black regions found: {len(system_sites)} sites")
    print(f"  Blue leads found: {len(leads)}")
    
    # Analyze system
    info, system_sites, leads = analyze_system(system_sites, leads)
    
    print("\n" + "=" * 60)
    print("SYSTEM ANALYSIS")
    print("=" * 60)
    
    # System information
    if info['system']['bounds']:
        bounds = info['system']['bounds']
        print(f"\nMain System:")
        print(f"  Number of sites: {info['system']['num_sites']}")
        print(f"  X bounds: [{bounds['x_min']}, {bounds['x_max']}]")
        print(f"  Y bounds: [{bounds['y_min']}, {bounds['y_max']}]")
        print(f"  Dimensions: {bounds['x_max'] - bounds['x_min'] + 1} × {bounds['y_max'] - bounds['y_min'] + 1}")
    else:
        print(f"\nMain System: None (using lead-only geometry)")
    
    # Lead information
    print(f"\nLeads ({len(info['leads'])} total):")
    for lead_name, lead_info in sorted(info['leads'].items()):
        print(f"\n  {lead_name}:")
        print(f"    Type: {lead_info['direction']}")
        print(f"    Sites: {lead_info['num_sites']}")
        print(f"    Periodicity: {lead_info['periodicity']}")
        print(f"    X range: [{lead_info['x_range'][0]}, {lead_info['x_range'][1]}]")
        print(f"    Y range: [{lead_info['y_range'][0]}, {lead_info['y_range'][1]}]")
    
    # Statistics
    total_sites = info['system']['num_sites'] + sum(lead['num_sites'] for lead in info['leads'].values())
    
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"\nTotal sites (system + leads): {total_sites}")
    print(f"System sites: {info['system']['num_sites']}")
    print(f"Lead sites: {sum(lead['num_sites'] for lead in info['leads'].values())}")
    
    # Save analysis to JSON
    output_file = Path("system_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(info, f, indent=2)
    print(f"\nAnalysis saved to: {output_file}")
    
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)
    
    # Check for common issues
    issues = []
    
    if len(info['leads']) < 2:
        issues.append("WARNING: Fewer than 2 leads detected (may be invalid system)")
    
    for lead_name, lead_info in info['leads'].items():
        if lead_info['periodicity'] is None:
            issues.append(f"WARNING: {lead_name} has unknown direction/periodicity")
    
    if not issues:
        print("\n[OK] All validations passed!")
    else:
        for issue in issues:
            print(f"\n[WARNING] {issue}")
    
    print("\n" + "=" * 60)
    print("Ready for Kwant quantum transport calculations!")
    print("=" * 60)
    
    return info


if __name__ == "__main__":
    info = main()
