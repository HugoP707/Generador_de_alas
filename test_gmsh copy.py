import gmsh
import math
import os

# ===========================
# CONFIG
# ===========================
AIRFOIL_DIR = "tests/alaTest1"           # carpeta con archivos .txt/.dat
MESH_OUT = "multi_airfoil_final.msh"
MESH_SIZE_NEAR = 0.002             # tamaño de malla base cerca del perfil (puntos)
H_WALL_N = 0.001                   # primer espesor boundary layer
BL_THICKNESS = 0.01                # grosor total BL
BL_RATIO = 1.08
BL_QUADS = 1
DIST_REFINEMENT_DISTMAX = 0.1      # zona de refinamiento principal (m)
DIST_REFINEMENT_SIZEMIN = 0.002
DIST_REFINEMENT_SIZEMAX = 0.2
D_TE = 0.01                        # distancia detrás del TE para la curva auxiliar
DOMAIN_L = 10.0
DOMAIN_H = 8.0


# ===========================
# Utilidades
# ===========================
def load_airfoil_file(path):
	coords = []
	with open(path, "r") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			parts = line.replace(",", " ").split()
			if len(parts) < 2:
				continue
			try:
				x = float(parts[0]); y = float(parts[1])
			except:
				continue
			coords.append((x, y))
	# eliminar duplicados consecutivos muy próximos
	clean = []
	eps = 1e-12
	for x, y in coords:
		if not clean or abs(clean[-1][0]-x) > eps or abs(clean[-1][1]-y) > eps:
			clean.append((x, y))
	# si primer==ultimo, quitar el último
	if len(clean) > 1 and abs(clean[0][0]-clean[-1][0]) < eps and abs(clean[0][1]-clean[-1][1]) < eps:
		clean.pop()
	return clean


def find_le_te(coords):
	# LE = índice con menor x (Leading Edge)
	le_idx = min(range(len(coords)), key=lambda i: coords[i][0])
	# rotar coords para que LE quede en 0
	coords = coords[le_idx:] + coords[:le_idx]
	# TE = índice con mayor x
	te_idx = max(range(len(coords)), key=lambda i: coords[i][0])
	return coords, 0, int(len(coords)/2)


def normalize(vx, vy):
	n = math.hypot(vx, vy)
	if n == 0:
		return (0.0, 0.0)
	return (vx / n, vy / n)


# ===========================
# Inicializar Gmsh
# ===========================
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.model.add("multi_airfoil_BL_parallel_TE")

# ===========================
# Cargar archivos de perfiles
# ===========================
airfoil_files = []
for fn in os.listdir(AIRFOIL_DIR):
	if fn.lower().endswith((".txt", ".dat")):
		airfoil_files.append(os.path.join(AIRFOIL_DIR, fn))

airfoil_coords_list = []
for fpath in airfoil_files:
	coords = load_airfoil_file(fpath)
	if len(coords) < 4:
		print(f"Ignorado (pocos puntos): {fpath}")
		continue
	airfoil_coords_list.append((fpath, coords))

if not airfoil_coords_list:
	raise RuntimeError("No se encontraron perfiles en la carpeta 'airfoils'.")


# ===========================
# Crear geometría de perfiles (splines y superficies)
# ===========================
airfoil_surfaces = []     # tags de superficie
airfoil_curve_pairs = []  # por perfil: [extrados_spline_tag, intrados_spline_tag]
te_aux_lines = []         # lines auxiliares creadas (para zona TE)

for fname, coords_raw in airfoil_coords_list:
	# 1) Rotar para LE en índice 0 y detectar TE
	coords, le_idx, te_idx = find_le_te(coords_raw)

	# 2) Construir extrados e intrados garantizando coincidencia exacta en TE y LE
	# Extrados: LE -> TE (inclusive)
	extrados_pts = coords[le_idx:te_idx+1]
	# Intrados: TE -> LE (inclusive) -> tomar desde te_idx hasta end then include coords[0] (LE)
	intrados_pts = coords[te_idx:-1] + [coords[le_idx]]
	"""
	# Forzar coincidencia exacta del punto TE e LE entre extrados e intrados
	if len(extrados_pts) >= 1 and len(intrados_pts) >= 1:
		te_coord = extrados_pts[-1]
		intrados_pts[0] = te_coord   # TE coincide exactamente
		intrados_pts[-1] = extrados_pts[0]  # LE coincide exactamente
	"""
	# 3) Crear puntos OCC y splines
	# Extrados: LE->TE
	ex_pt_tags = [gmsh.model.occ.addPoint(x, y, 0, MESH_SIZE_NEAR) for x, y in reversed(extrados_pts)]
	gmsh.model.occ.synchronize()
	s_ex = gmsh.model.occ.addSpline(ex_pt_tags)

	# Intrados: TE->LE
	in_pt_tags = [gmsh.model.occ.addPoint(x, y, 0, MESH_SIZE_NEAR) for x, y in reversed(intrados_pts)]
	gmsh.model.occ.synchronize()
	s_in = gmsh.model.occ.addSpline(in_pt_tags)

	# 4) Crear curve loop cerrado: [s_ex, s_in]
	# (s_ex end == s_in start == TE, s_in end == s_ex start == LE)
	#try:

	print("No error")
	gmsh.model.occ.synchronize()
	loop_sin = gmsh.model.occ.addCurveLoop([s_in])
	loop_ex = gmsh.model.occ.addCurveLoop([s_ex])
	gmsh.model.occ.synchronize()
	surf = gmsh.model.occ.addPlaneSurface([loop_sin, loop_ex])
	"""
	except Exception as e:
		print("Error")
		# si fallara por seguridad, recurrimos a añadir lines LE/TE explícitas:
		# crear lineas de cierre TE y LE entre puntos correspondientes
		line_te = gmsh.model.occ.addLine(ex_pt_tags[-1], in_pt_tags[0])
		line_le = gmsh.model.occ.addLine(in_pt_tags[-1], ex_pt_tags[0])
		loop = gmsh.model.occ.addCurveLoop([s_ex, line_te, s_in, line_le])
		surf = gmsh.model.occ.addPlaneSurface([loop])
	"""
	airfoil_surfaces.append(surf)
	airfoil_curve_pairs.append((s_ex, s_in))
"""
	# 5) Crear curva auxiliar detrás del TE (sigue la dirección TE)
	# usar últimos dos puntos del extrados para estimar tangente en TE
	if len(extrados_pts) >= 2:
		p_before_te = extrados_pts[-2]
		p_te = extrados_pts[-1]
	else:
		# fallback si pocos puntos
		p_before_te = extrados_pts[0]
		p_te = extrados_pts[-1]

	vec_x = p_te[0] - p_before_te[0]
	vec_y = p_te[1] - p_before_te[1]
	nx, ny = normalize(vec_x, vec_y)
	# aux point: desplazamiento en la misma dirección (hacia fuera)
	aux_x = p_te[0] + nx * D_TE
	aux_y = p_te[1] + ny * D_TE

	pt_te_tag = gmsh.model.occ.addPoint(p_te[0], p_te[1], 0, MESH_SIZE_NEAR)
	pt_aux_tag = gmsh.model.occ.addPoint(aux_x, aux_y, 0, MESH_SIZE_NEAR)
	aux_line = gmsh.model.occ.addLine(pt_te_tag, pt_aux_tag)
	te_aux_lines.append(aux_line)
"""
# sincronizar geometría OCC antes de más operaciones
gmsh.model.occ.synchronize()


# ===========================
# Recombinación de superficies (intentar quads)
# ===========================
for surf in airfoil_surfaces:
	gmsh.model.mesh.setRecombine(2, surf)


# ===========================
# Dominio exterior y booleans
# ===========================
p1 = gmsh.model.occ.addPoint(-DOMAIN_L, -DOMAIN_H, 0)
p2 = gmsh.model.occ.addPoint(DOMAIN_L, -DOMAIN_H, 0)
p3 = gmsh.model.occ.addPoint(DOMAIN_L, DOMAIN_H, 0)
p4 = gmsh.model.occ.addPoint(-DOMAIN_L, DOMAIN_H, 0)

l1 = gmsh.model.occ.addLine(p1, p2)
l2 = gmsh.model.occ.addLine(p2, p3)
l3 = gmsh.model.occ.addLine(p3, p4)
l4 = gmsh.model.occ.addLine(p4, p1)

outer_loop = gmsh.model.occ.addCurveLoop([l1, l2, l3, l4])
outer_surf = gmsh.model.occ.addPlaneSurface([outer_loop])

# cortar perfiles fuera del dominio
gmsh.model.occ.cut([(2, outer_surf)], [(2, s) for s in airfoil_surfaces])
gmsh.model.occ.synchronize()


# ===========================
# Aplicar boundary layers por separado a extrados e intrados
# ===========================
for s_ex, s_in in airfoil_curve_pairs:
	add_field = gmsh.model.mesh.field.add  # shortcut
	# Extrados
	bl1 = add_field("BoundaryLayer")
	gmsh.model.mesh.field.setNumbers(bl1, "CurvesList", [s_ex])
	gmsh.model.mesh.field.setNumber(bl1, "hwall_n", H_WALL_N)
	gmsh.model.mesh.field.setNumber(bl1, "thickness", BL_THICKNESS)
	gmsh.model.mesh.field.setNumber(bl1, "ratio", BL_RATIO)
	gmsh.model.mesh.field.setNumber(bl1, "Quads", BL_QUADS)
	gmsh.model.mesh.field.setAsBoundaryLayer(bl1)
	# Intrados
	bl2 = add_field("BoundaryLayer")
	gmsh.model.mesh.field.setNumbers(bl2, "CurvesList", [s_in])
	gmsh.model.mesh.field.setNumber(bl2, "hwall_n", H_WALL_N)
	gmsh.model.mesh.field.setNumber(bl2, "thickness", BL_THICKNESS)
	gmsh.model.mesh.field.setNumber(bl2, "ratio", BL_RATIO)
	gmsh.model.mesh.field.setNumber(bl2, "Quads", BL_QUADS)
	gmsh.model.mesh.field.setAsBoundaryLayer(bl2)


# ===========================
# Zona de refinamiento principal (Distance + Threshold)
# ===========================
all_profile_curves = []
for pair in airfoil_curve_pairs:
	all_profile_curves.extend(pair)

dist_main = gmsh.model.mesh.field.add("Distance")
gmsh.model.mesh.field.setNumbers(dist_main, "EdgesList", all_profile_curves)

th_main = gmsh.model.mesh.field.add("Threshold")
gmsh.model.mesh.field.setNumber(th_main, "InField", dist_main)
gmsh.model.mesh.field.setNumber(th_main, "SizeMin", DIST_REFINEMENT_SIZEMIN)
gmsh.model.mesh.field.setNumber(th_main, "SizeMax", DIST_REFINEMENT_SIZEMAX)
gmsh.model.mesh.field.setNumber(th_main, "DistMin", 0.0)
gmsh.model.mesh.field.setNumber(th_main, "DistMax", DIST_REFINEMENT_DISTMAX)
"""
# ===========================
# Campos Threshold para curvas auxiliares TE
# ===========================
te_threshold_fields = []
for aux_line in te_aux_lines:
	dist_te = gmsh.model.mesh.field.add("Distance")
	gmsh.model.mesh.field.setNumbers(dist_te, "EdgesList", [aux_line])
	th_te = gmsh.model.mesh.field.add("Threshold")
	gmsh.model.mesh.field.setNumber(th_te, "InField", dist_te)
	# zona muy cercana al TE
	gmsh.model.mesh.field.setNumber(th_te, "SizeMin", DIST_REFINEMENT_SIZEMIN)
	gmsh.model.mesh.field.setNumber(th_te, "SizeMax", max(DIST_REFINEMENT_SIZEMIN, DIST_REFINEMENT_SIZEMAX/4.0))
	gmsh.model.mesh.field.setNumber(th_te, "DistMin", 0.0)
	gmsh.model.mesh.field.setNumber(th_te, "DistMax", D_TE)
	te_threshold_fields.append(th_te)
"""
# ===========================
# Combinar campos (Min) y activar como fondo
# ===========================
fields_to_min = [th_main] #+ te_threshold_fields
min_field = gmsh.model.mesh.field.add("Min")
gmsh.model.mesh.field.setNumbers(min_field, "FieldsList", fields_to_min)
gmsh.model.mesh.field.setAsBackgroundMesh(min_field)

# ===========================
# Generar la malla 2D
# ===========================
gmsh.model.mesh.generate(2)
gmsh.write(MESH_OUT)
print("Malla escrita en:", MESH_OUT)
gmsh.fltk.run()
gmsh.finalize()
