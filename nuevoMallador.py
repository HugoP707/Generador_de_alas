"""
Simplified multi-airfoil 2D mesh generator using GMSH.
- Configuration via variables inside the script
- Airfoils only from local .dat files
- Arbitrary number of airfoils supported
"""

import math
from pathlib import Path
import gmsh

from gmshairfoil2d.airfoil_func import read_airfoil_from_file
from gmshairfoil2d.geometry_def import AirfoilSpline, Circle, PlaneSurface


# ==========================================================
# ===================== CONFIGURATION ======================
# ==========================================================

# List of airfoil files (local .dat)
AIRFOIL_FILES = [
	"tests\\alaTest1\\main.txt",
	"tests\\alaTest1\\flap1.txt",
	"tests\\alaTest1\\flap2.txt",
]

# Rotation angles for each airfoil [deg]
AOA_LIST = [0, 0, 0]

# Mesh parameters
AIRFOIL_MESH_SIZE = 0.01
FARFIELD_RADIUS = 10.0
FARFIELD_MESH_SIZE = 0.2

# Boundary layer parameters
USE_BOUNDARY_LAYER = True
FIRST_LAYER_HEIGHT = 3e-5
GROWTH_RATIO = 1.2
NB_LAYERS = 30

# Output
OUTPUT_DIRECTORY = "."
MESH_FORMAT = "su2"

# ==========================================================


def reorder_points(cloud_points):
	"""Ensure airfoil starts at LE and is clockwise."""
	le = min(p[0] for p in cloud_points)
	for p in cloud_points:
		if p[0] == le:
			start = cloud_points.index(p)

	cloud_points = cloud_points[start:] + cloud_points[:start]

	if cloud_points[1][1] < cloud_points[0][1]:
		cloud_points.reverse()
		cloud_points = cloud_points[-1:] + cloud_points[:-1]

	return cloud_points


def compute_bl_thickness(first_layer, ratio, n_layers):
	"""Compute total boundary layer thickness."""
	d = [first_layer]
	for i in range(1, n_layers):
		d.append(d[-1] - (-d[0]) * ratio**i)
	return d[-1]


def apply_boundary_layer(airfoils):
	"""Apply boundary layer field to all airfoils."""
	f = gmsh.model.mesh.field.add("BoundaryLayer")

	curves = []
	fan_points = []

	for af in airfoils:
		curves += [
			af.upper_spline.tag,
			af.lower_spline.tag,
			af.front_spline.tag,
		]
		fan_points.append(af.te.tag)

	total_thickness = compute_bl_thickness(
		FIRST_LAYER_HEIGHT, GROWTH_RATIO, NB_LAYERS
	)

	gmsh.model.mesh.field.setNumbers(f, "CurvesList", curves)
	gmsh.model.mesh.field.setNumber(f, "Size", FIRST_LAYER_HEIGHT)
	gmsh.model.mesh.field.setNumber(f, "Ratio", GROWTH_RATIO)
	gmsh.model.mesh.field.setNumber(f, "Thickness", total_thickness)
	gmsh.model.mesh.field.setNumber(f, "Quads", 1)
	gmsh.model.mesh.field.setNumbers(f, "FanPointsList", fan_points)

	gmsh.model.mesh.field.setAsBoundaryLayer(f)


def main():

	if len(AIRFOIL_FILES) != len(AOA_LIST):
		raise ValueError("AIRFOIL_FILES and AOA_LIST must have same length")

	gmsh.initialize()

	airfoils = []

	# ======================================================
	# Create airfoils
	# ======================================================
	k12s = []

	for file_path, aoa_deg in zip(AIRFOIL_FILES, AOA_LIST):

		cloud_points = read_airfoil_from_file(file_path)
		cloud_points = reorder_points(cloud_points)

		airfoil = AirfoilSpline(
			cloud_points,
			AIRFOIL_MESH_SIZE,
			name=Path(file_path).stem,
			# is_flap=True,
		)

		aoa_rad = -aoa_deg * math.pi / 180
		# airfoil.rotation(aoa_rad, (0.5, 0, 0), (0, 0, 1))
		airfoil.gen_skin()
		airfoils.append(airfoil)

	gmsh.model.geo.synchronize()

	# ======================================================
	# External circular domain
	# ======================================================
	farfield = Circle(
		0.5, 0, 0,
		radius=FARFIELD_RADIUS,
		mesh_size=FARFIELD_MESH_SIZE
	)

	gmsh.model.geo.synchronize()

	# Create surface (subtract airfoils from farfield)
	surface = PlaneSurface([farfield] + airfoils)

	gmsh.model.geo.synchronize()

	# ======================================================
	# Boundary layer
	# ======================================================
	if USE_BOUNDARY_LAYER:
		apply_boundary_layer(airfoils)

	# Mesh options
	gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)
	gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

	# Generate mesh
	gmsh.model.mesh.generate(2)
	gmsh.model.mesh.optimize("Laplace2D", 5)

	# ======================================================
	# Save mesh
	# ======================================================
	output_name = "mesh_multi_airfoil." + MESH_FORMAT
	mesh_path = Path(OUTPUT_DIRECTORY, output_name)

	gmsh.write(str(mesh_path))
	gmsh.finalize()

	print(f"Mesh saved to: {mesh_path}")


if __name__ == "__main__":
	main()