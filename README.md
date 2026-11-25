# Four-terminal quantum billiard

This project computes coherent transport through a rectangular, spinless
quantum billiard on a square lattice, with one centered lead on each side.
The clean rectangle is an integrable starting point, not itself a chaotic
billiard.

## Setup

The project uses the existing conda environment `gerson`. Install the
dependencies into it:

```powershell
conda env update -n gerson -f environment.yml
```

In VS Code, select the Python interpreter from that environment. Alternatively,
run the following commands from a terminal where conda is available:

```powershell
conda run -n gerson python quantum_billiard.py
conda run -n gerson python -m unittest discover -s tests
```

The script prints the conductance matrix and saves it, the lead order, and a
snapshot of the input parameters to `data\conductance.npz`. The file is
overwritten on each run. Use `--output path\to\results.npz` to save a
different run.

Open [analysis.ipynb](analysis.ipynb) in VS Code, select the `gerson` kernel,
and run its cells to load the results and plot the system with its leads and
the conductance matrix. To use a different output file, change `results_path`
in the notebook. The geometry is rebuilt from the saved parameters rather than
the current TOML file, and the notebook does not recalculate transport.
Alternatively, start JupyterLab with `conda run -n gerson jupyter lab`.

Edit [parameters.toml](parameters.toml) to change the rectangle dimensions,
lead width, hopping, and Fermi energy. Dimensions and lead width are measured
in lattice sites; energy and hopping must use the same units. The lead width
must fit on all four sides without including a corner. Use another parameter
file with `python quantum_billiard.py --config path\to\parameters.toml`.
Rerun the script after editing parameters; the notebook reads the last saved run.

## Model and convention

Each site has onsite energy `4t` and nearest-neighbor hopping `-t`. Leads
have the same lattice and hopping as the rectangle, extend to infinity, and
are ordered **left, right, bottom, top**. The calculated matrix is Kwant's
Landauer–Büttiker conductance matrix in units of `e²/h`, with no spin
degeneracy included. For voltages `V`, currents flowing into the device are
`I = (e²/h) G V`. Off-diagonal entries are `G[i,j] = -T[i,j]` for
transmission from lead `j` to lead `i`; diagonal entries follow from current
conservation. Energies outside the propagating bands can produce zero
conductance.
