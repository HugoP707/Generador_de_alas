import gmsh

# ============================================================
# 1) Función para leer archivo y construir el perfil en OCC
# ============================================================
def import_airfoil(filename, mesh_size=0.002):
	"""
	Carga un archivo con coordenadas y genera:
	- spline del perfil
	- línea de cierre
	- superficie OCC
	Devuelve: surface_tag, lista de curve_tags
	"""

	# ===== Leer archivo =====
	coords = []
	with open(filename, "r") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			parts = line.replace(",", " ").split()
			if len(parts) >= 2:
				x, y = float(parts[0]), float(parts[1])
				coords.append((x, y))

	# ===== Limpiar duplicados =====
	clean = []
	eps = 1e-7
	for x, y in coords:
		if not clean:
			clean.append((x, y))
		else:
			px, py = clean[-1]
			if abs(px - x) > eps or abs(py - y) > eps:
				clean.append((x, y))
	if abs(clean[0][0] - clean[-1][0]) < eps and abs(clean[0][1] - clean[-1][1]) < eps:
		clean.pop()

	# ===== Crear puntos OCC =====
	pt_tags = [gmsh.model.occ.addPoint(x, y, 0, mesh_size) for x, y in clean]

	# ===== Crear spline y línea de cierre =====
	spline = gmsh.model.occ.addSpline(pt_tags)
	closing_line = gmsh.model.occ.addLine(pt_tags[-1], pt_tags[0])

	# ===== Loop y superficie =====
	loop = gmsh.model.occ.addCurveLoop([spline, closing_line])
	surface = gmsh.model.occ.addPlaneSurface([loop])

	return surface, [spline, closing_line]

def add_boundary_layer_to_profile(curve_tags, hwall_n=0.0005, thickness=0.005, ratio=1.2, quads=1):
	"""
	Crea un campo BoundaryLayer sobre un conjunto de curvas (un perfil).
	"""

	bl_field = gmsh.model.mesh.field.add("BoundaryLayer")
	gmsh.model.mesh.field.setNumbers(bl_field, "CurvesList", curve_tags)
	gmsh.model.mesh.field.setNumber(bl_field, "hwall_n", hwall_n)
	gmsh.model.mesh.field.setNumber(bl_field, "thickness", thickness)
	gmsh.model.mesh.field.setNumber(bl_field, "ratio", ratio)
	gmsh.model.mesh.field.setNumber(bl_field, "Quads", quads)
	gmsh.model.mesh.field.setAsBackgroundMesh(bl_field)

	print(f"Boundary layer aplicada a curvas: {curve_tags}")


# ============================================================
# 2) MAIN GMsh
# ============================================================
gmsh.initialize()
gmsh.model.add("multi_airfoil")

airfoil_files = [
	"tests/alaTest1/main.txt",
	"tests/alaTest1/flap1.txt",
	"tests/alaTest1/flap2.txt",
	# puedes agregar más perfiles aquí
]

airfoil_surfaces = []
airfoil_curves = []

# Importamos cada perfil con la función creada
for fname in airfoil_files:
	surf, curves = import_airfoil(fname)
	airfoil_surfaces.append(surf)
	airfoil_curves.append(curves)

gmsh.model.occ.synchronize()

# ==========================
# Capas límites
# ==========================
# TODO: Hacerlo más "personal", es decir, para cada perfil individualmente
for curves in airfoil_curves:
	add_boundary_layer_to_profile(curves, hwall_n=0.005, thickness=0.05, ratio=1.2, quads=1)

gmsh.model.occ.synchronize()
# ============================================================
# 3) Dominio exterior
# ============================================================
L = 2.0
H = 1.0

p1 = gmsh.model.occ.addPoint(-L, -H, 0)
p2 = gmsh.model.occ.addPoint( L, -H, 0)
p3 = gmsh.model.occ.addPoint( L,  H, 0)
p4 = gmsh.model.occ.addPoint(-L,  H, 0)

l1 = gmsh.model.occ.addLine(p1, p2)
l2 = gmsh.model.occ.addLine(p2, p3)
l3 = gmsh.model.occ.addLine(p3, p4)
l4 = gmsh.model.occ.addLine(p4, p1)

outer_loop = gmsh.model.occ.addCurveLoop([l1, l2, l3, l4])
outer_surf = gmsh.model.occ.addPlaneSurface([outer_loop])

gmsh.model.occ.synchronize()

# ============================================================
# 4) Boolean cut con todos los perfiles
# ============================================================
gmsh.model.occ.cut(
	[(2, outer_surf)],
	[(2, s) for s in airfoil_surfaces]
)

gmsh.model.occ.synchronize()

# ============================================================
# 5) Mesh
# ============================================================
gmsh.model.mesh.generate(2)
gmsh.write("multi_airfoil_mesh.msh")
gmsh.fltk.run()
gmsh.finalize()