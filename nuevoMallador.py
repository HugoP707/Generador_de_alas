"""
Multi-airfoil 2D mesh generator (corrected full logic version)
- No argparse
- Only local .dat files
- Arbitrary number of airfoils
- Keeps BL, transfinite and safety checks
"""

import math
from pathlib import Path

from helpers import *

import gmsh

from gmshairfoil2d.airfoil_func import read_airfoil_from_file
from gmshairfoil2d.geometry_def import (
	AirfoilSpline,
	Circle,
	PlaneSurface,
	outofbounds
)

def scale_points(points, scale, origin=(0.0, 0.0)):
	"""
	Scale cloud points with respect to an origin.
	"""
	ox, oy = origin

	scaled = []
	for x, y, z in points:
		xs = ox + scale * (x - ox)
		ys = oy + scale * (y - oy)
		scaled.append((xs, ys, z))

	return scaled

# ==========================================================
# ======================== CONFIG ==========================
# ==========================================================

AIRFOIL_FILES = [
	"tests/alaTest1/main.txt",
	"tests/alaTest1/flap1.txt",
	"tests/alaTest1/flap2.txt",
]

C0 = 0.4
C1 = C0*0.4
C2 = C1*0.5
CUERDAS = [
	C0, C1, C2
]

AOA0 = 10
AOA1 = AOA0 + 40
AOA2 = AOA1 + 35
AOA_LIST = [
	AOA0, AOA1, AOA2
]

GAPS = [gaps_normalizados(C1, AOA0, [-0.1, 0.1]), gaps_normalizados(C2, AOA1, [-0.22, 0.1])]
AIRFOILS = [
	{
		"file": "datos_perfiles/NASA SC(2)-1006 AIRFOIL modified2_4 modified modified_closed_te.dat",
		"scale": C0,
		"aoa": AOA0,
		"translate": (0,0),
		"pivot": 0   # fracción de cuerda
	},
	{
		"file": "datos_perfiles/s1223.dat",
		"scale": C1,
		"aoa": AOA1,
		"translate": -gaps_normalizados(C1, AOA0, [-0.1, 0.1]),
		"pivot": 0
	}
]
AIRFOIL_MESH_SIZE = 0.005
FARFIELD_RADIUS = 10.0
EXT_MESH_SIZE = 0.2

USE_BOUNDARY_LAYER = True
FIRST_LAYER = 1e-5
RATIO = 1.2
NB_LAYERS = 12

APPLY_TRANSFINITE = True

OUTPUT_DIR = "."
FORMAT = "su2"

# ==========================================================


def reorder_points(cloud_points):
	"""Start at LE and clockwise ordering."""
	le = min(p[0] for p in cloud_points)
	for p in cloud_points:
		if p[0] == le:
			start = cloud_points.index(p)

	cloud_points = cloud_points[start:] + cloud_points[:start]

	if cloud_points[1][1] < cloud_points[0][1]:
		cloud_points.reverse()
		cloud_points = cloud_points[-1:] + cloud_points[:-1]

	return cloud_points


def compute_bl_distribution():
	"""Compute cumulative BL thickness exactly like original."""
	d = [FIRST_LAYER]
	for i in range(1, NB_LAYERS):
		d.append(d[-1] - (-d[0]) * RATIO**i)
	return d


def calculate_spline_length(spline):
	pts = spline.point_list
	return sum(
		math.hypot(pts[i].x - pts[i+1].x,
						pts[i].y - pts[i+1].y)
		for i in range(len(pts) - 1)
	)


def apply_transfinite(airfoil):
	"""Apply proportional transfinite like original."""
	l_front = calculate_spline_length(airfoil.front_spline)
	l_upper = calculate_spline_length(airfoil.upper_spline)
	l_lower = calculate_spline_length(airfoil.lower_spline)

	total = l_front + l_upper + l_lower
	total_pts = max(20, int(total / AIRFOIL_MESH_SIZE))

	front_multiplier = 2
	weighted = l_front * front_multiplier + l_upper + l_lower

	n_front = max(15, int((l_front * front_multiplier / weighted) * total_pts))
	n_upper = max(15, int((l_upper / weighted) * total_pts))
	n_lower = max(15, int((l_lower / weighted) * total_pts))

	gmsh.model.mesh.setTransfiniteCurve(
		airfoil.front_spline.tag, n_front, "Bump", 10)
	gmsh.model.mesh.setTransfiniteCurve(
		airfoil.upper_spline.tag, n_upper)
	gmsh.model.mesh.setTransfiniteCurve(
		airfoil.lower_spline.tag, n_lower)


def main():

	if len(AIRFOIL_FILES) != len(AOA_LIST):
		raise ValueError("AIRFOIL_FILES and AOA_LIST must match.")

	gmsh.initialize()

	airfoils = []

	for config in AIRFOILS:

		# 1️⃣ Leer y reordenar
		pts = read_airfoil_from_file(config["file"])
		pts = reorder_points(pts)

		# 2️⃣ Escalar antes de crear geometría
		pts = scale_points(
			pts,
			config["scale"],
			origin=(0.0, 0.0)
		)

		# 3️⃣ Crear spline
		af = AirfoilSpline(
			pts,
			AIRFOIL_MESH_SIZE,
			name=Path(config["file"]).stem,
			is_flap=False
		)

		# 4️⃣ Rotación
		pivot_fraction = config.get("pivot", 0.25)
		pivot_x = pivot_fraction * config["scale"]

		aoa_rad = config["aoa"] * math.pi / 180

		af.rotation(
			aoa_rad,
			(pivot_x, 0.0, 0.0),
			(0, 0, 1)
		)

		# 5️⃣ Traslación (usa método interno correcto)
		dx, dy = config["translate"]
		af.translation((dx, dy, 0))

		# 6️⃣ Generar splines
		af.gen_skin()

		airfoils.append(af)

	gmsh.model.geo.synchronize()

	# ======================================================
	# Boundary layer preparation
	# ======================================================
	if USE_BOUNDARY_LAYER:
		d = compute_bl_distribution()
		total_bl = d[-1]

		# Safety check like original
		for af in airfoils:
			outofbounds(af, None, FARFIELD_RADIUS, total_bl)
	else:
		d = [0]

	# ======================================================
	# External domain
	# ======================================================
	farfield = Circle(
		0.5, 0, 0,
		radius=FARFIELD_RADIUS,
		mesh_size=EXT_MESH_SIZE
	)

	gmsh.model.geo.synchronize()

	surface = PlaneSurface([farfield] + airfoils)

	gmsh.model.geo.synchronize()
	gmsh.fltk.run()
	# ======================================================
	# Boundary layer field
	# ======================================================
	if USE_BOUNDARY_LAYER:

		curves = []
		fan_points = []

		for af in airfoils:
			curves += [
					af.upper_spline.tag,
					af.lower_spline.tag,
					af.front_spline.tag
			]
			fan_points.append(af.te.tag)

		f = gmsh.model.mesh.field.add("BoundaryLayer")
		gmsh.model.mesh.field.setNumbers(f, "CurvesList", curves)
		gmsh.model.mesh.field.setNumber(f, "Size", FIRST_LAYER)
		gmsh.model.mesh.field.setNumber(f, "Ratio", RATIO)
		gmsh.model.mesh.field.setNumber(f, "Thickness", d[-1])
		gmsh.model.mesh.field.setNumber(f, "Quads", 1)
		gmsh.model.mesh.field.setNumbers(f, "FanPointsList", fan_points)

		gmsh.model.mesh.field.setAsBoundaryLayer(f)

	# ======================================================
	# Transfinite
	# ======================================================
	if APPLY_TRANSFINITE and USE_BOUNDARY_LAYER:
		for af in airfoils:
			apply_transfinite(af)

		coef = max(10, min(25, 15 * 0.01 / AIRFOIL_MESH_SIZE))
		gmsh.option.setNumber("Mesh.BoundaryLayerFanElements", coef)

	# ======================================================
	# Mesh options
	# ======================================================
	gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)
	gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

	# ======================================================
	# Generate mesh
	# ======================================================
	gmsh.model.mesh.generate(2)
	gmsh.model.mesh.optimize("Laplace2D", 5)

	# ======================================================
	# Save
	# ======================================================
	output = Path(OUTPUT_DIR, "mesh_multi_airfoil." + FORMAT)
	gmsh.write(str(output))
	gmsh.fltk.run()
	gmsh.finalize()

	print(f"Mesh written to {output}")


if __name__ == "__main__":
	main()