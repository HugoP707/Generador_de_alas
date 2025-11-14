import gmsh

# ==============================
# Función para importar un perfil
# ==============================
def import_airfoil(filename, mesh_size=0.002):
	"""
	Carga un archivo con coordenadas y genera:
	- spline del perfil
	- línea de cierre
	- superficie OCC
	Devuelve: surface_tag, lista de curve_tags
	"""
	# Leer archivo
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

	# Eliminar duplicados consecutivos
	clean = []
	eps = 1e-7
	for x, y in coords:
		if not clean or abs(clean[-1][0]-x) > eps or abs(clean[-1][1]-y) > eps:
			clean.append((x, y))

	# Si el primer y último son iguales, eliminar el último
	if abs(clean[0][0]-clean[-1][0]) < eps and abs(clean[0][1]-clean[-1][1]) < eps:
		clean.pop()

	# Crear puntos OCC
	pt_tags = [gmsh.model.occ.addPoint(x, y, 0, mesh_size) for x, y in clean]

	# Crear spline y línea de cierre
	spline = gmsh.model.occ.addSpline(pt_tags)
	closing_line = gmsh.model.occ.addLine(pt_tags[-1], pt_tags[0])

	# Loop y superficie
	loop = gmsh.model.occ.addCurveLoop([spline, closing_line])
	surface = gmsh.model.occ.addPlaneSurface([loop])

	return surface, [spline, closing_line]


# ==================================
# Función para aplicar boundary layer
# ==================================
def add_boundary_layer_to_profile(curve_tags, hwall_n=0.001, thickness=0.01, ratio=1.2, quads=1):
	"""
	Aplica un campo BoundaryLayer a un perfil (lista de curvas).
	"""
	bl_field = gmsh.model.mesh.field.add("BoundaryLayer")
	gmsh.model.mesh.field.setNumbers(bl_field, "CurvesList", curve_tags)
	gmsh.model.mesh.field.setNumber(bl_field, "hwall_n", hwall_n)
	gmsh.model.mesh.field.setNumber(bl_field, "thickness", thickness)
	gmsh.model.mesh.field.setNumber(bl_field, "ratio", ratio)
	gmsh.model.mesh.field.setNumber(bl_field, "Quads", quads)

	# Activar correctamente como boundary layer
	gmsh.model.mesh.field.setAsBoundaryLayer(bl_field)
	print(f"Boundary layer aplicada a curvas: {curve_tags}")


# ===========================
# Inicio del programa principal
# ===========================
gmsh.initialize()
gmsh.model.add("multi_airfoil_BL")

# -------------------
# Archivos de perfiles
# -------------------
airfoil_files = [
	"tests/alaTest1/main.txt",
	"tests/alaTest1/flap1.txt",
	"tests/alaTest1/flap2.txt",
	# puedes agregar más perfiles aquí
]

mesh_size = 0.002
airfoil_surfaces = []
airfoil_curves = []

# Importar perfiles
for fname in airfoil_files:
	surf, curves = import_airfoil(fname, mesh_size)
	airfoil_surfaces.append(surf)
	airfoil_curves.append(curves)

gmsh.model.occ.synchronize()

# ===========================
# Dominio exterior
# ===========================
L = 10.0
H = 8.0

p1 = gmsh.model.occ.addPoint(-L, -H, 0)
p2 = gmsh.model.occ.addPoint(L, -H, 0)
p3 = gmsh.model.occ.addPoint(L, H, 0)
p4 = gmsh.model.occ.addPoint(-L, H, 0)

l1 = gmsh.model.occ.addLine(p1, p2)
l2 = gmsh.model.occ.addLine(p2, p3)
l3 = gmsh.model.occ.addLine(p3, p4)
l4 = gmsh.model.occ.addLine(p4, p1)

outer_loop = gmsh.model.occ.addCurveLoop([l1, l2, l3, l4])
outer_surf = gmsh.model.occ.addPlaneSurface([outer_loop])

# Restar los perfiles del dominio
gmsh.model.occ.cut([(2, outer_surf)], [(2, s) for s in airfoil_surfaces])
gmsh.model.occ.synchronize()

# ===========================
# Aplicar boundary layers a cada perfil
# ===========================
for curves in airfoil_curves:
	add_boundary_layer_to_profile(
		curves,
		hwall_n=0.00001,   # primer espesor
		thickness=0.002,  # grosor total
		ratio=1.2,
		quads=1
	)

# ===========================
# Zona de refinamiento alrededor de todos los perfiles
# ===========================
all_curves = [c for curves in airfoil_curves for c in curves]

dist_field = gmsh.model.mesh.field.add("Distance")
gmsh.model.mesh.field.setNumbers(dist_field, "EdgesList", all_curves)

threshold_field = gmsh.model.mesh.field.add("Threshold")
gmsh.model.mesh.field.setNumber(threshold_field, "InField", dist_field)
gmsh.model.mesh.field.setNumber(threshold_field, "SizeMin", 0.0005)   # muy fino cerca
gmsh.model.mesh.field.setNumber(threshold_field, "SizeMax", 0.02)    # grande lejos
gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", 0)     # tamaño mínimo desde 0
gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", 5)     # zona fina se extiende solo hasta 0.1 unidades

# Activar el campo de refinamiento
gmsh.model.mesh.field.setAsBackgroundMesh(threshold_field)
#gmsh.model.mesh.field.setAsBackgroundMesh(dist_field)
# --- Generar malla ---
gmsh.model.mesh.generate(2)
gmsh.write("airfoil_BL_quads.msh")
gmsh.fltk.run()
gmsh.finalize()