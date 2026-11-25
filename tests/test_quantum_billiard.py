import unittest
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import kwant
import numpy as np

from quantum_billiard import Parameters, conductance_matrix, load_parameters, make_system


class BilliardTests(unittest.TestCase):
    def setUp(self):
        self.params = Parameters(length=16, width=12, lead_width=4, hopping=1, energy=1)

    def test_leads_and_conductance(self):
        system = make_system(self.params)
        self.assertEqual(len(system.leads), 4)
        self.assertEqual(system.graph.num_nodes, self.params.length * self.params.width)
        expected_interfaces = (
            {(0, y) for y in range(4, 8)},
            {(15, y) for y in range(4, 8)},
            {(x, 0) for x in range(6, 10)},
            {(x, 11) for x in range(6, 10)},
        )
        for interface, expected in zip(system.lead_interfaces, expected_interfaces):
            self.assertEqual({tuple(system.sites[index].tag) for index in interface}, expected)
        matrix = conductance_matrix(self.params)
        self.assertEqual(matrix.shape, (4, 4))
        np.testing.assert_allclose(matrix.sum(axis=0), 0, atol=1e-10)
        np.testing.assert_allclose(matrix.sum(axis=1), 0, atol=1e-10)
        np.testing.assert_allclose(matrix, matrix.T, atol=1e-10)
        self.assertTrue(np.all(np.diag(matrix) > 0))
        self.assertTrue(np.all(matrix[~np.eye(4, dtype=bool)] <= 0))
        scattering = kwant.smatrix(system, energy=self.params.energy)
        for outgoing in range(4):
            for incoming in range(4):
                if outgoing != incoming:
                    self.assertAlmostEqual(
                        matrix[outgoing, incoming],
                        -scattering.transmission(outgoing, incoming),
                    )

    def test_invalid_lead_width(self):
        with self.assertRaisesRegex(ValueError, "without including corners"):
            Parameters(length=10, width=8, lead_width=7, hopping=1, energy=1)

    def test_default_configuration_loads(self):
        path = Path(__file__).resolve().parents[1] / "parameters.toml"
        params = load_parameters(path)
        self.assertEqual(conductance_matrix(params).shape, (4, 4))

    def test_script_saves_custom_run(self):
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "results.npz"
            config = Path(directory) / "input.toml"
            config.write_text(
                "[system]\nlength = 16\nwidth = 12\nlead_width = 4\n"
                "hopping = 1.0\nenergy = 1.0\n",
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, str(project / "quantum_billiard.py"),
                 "--config", str(config), "--output", str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            with np.load(output, allow_pickle=False) as results:
                params = Parameters(**json.loads(results["parameters"].item()))
                self.assertEqual(params, self.params)
                self.assertEqual(results["lead_names"].tolist(),
                                 ["left", "right", "bottom", "top"])
                np.testing.assert_allclose(results["conductance"], conductance_matrix(params))


if __name__ == "__main__":
    unittest.main()
