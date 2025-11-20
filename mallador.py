# gen_airfoil_simple.py
# Requisitos: pip install gmsh meshio numpy
import gmsh
import meshio
from gmsh_helpers import *
import os


# ---------------------------
# Configuración (ajusta)
# ---------------------------
airfoil_files = [
	"tests/alaTest1/main.txt",
	"tests/alaTest1/flap1.txt",
	"tests/alaTest1/flap2.txt",
]
airfoil_names = [
	"main",
	"flap1",
	"flap2",
]

output_msh = "airfoil_simple.msh"
output_su2 = "airfoil_simple.su2"
output_cgns = "airfoil_simple.cgns"

all_airfoil_points = [read_profile(file) for file in airfoil_files]

preview_geometria = False

use_circle_farfield = True	# True -> círculo, False -> caja
farfield_radius = 7			# radio del dominio exterior (si usas círculo)
circlex_offset = 2
tunnel_length = 20.0
tunnel_height = 10.0
tunnelx_offset = 5

distanciaMinRefinamiento = 0
distanciaMaxRefinamiento = 4

first_layer_height = 0.001   # altura primera capa BL
bl_ratio = 1.2
espesor_bl = first_layer_height*(3+1)

mesh_size_airfoil = 0.001 # espesor_bl*0.8   # tamaño en el contorno del perfil
mesh_size_close = 0.001
farfield_mesh_size = 0.2         # tamaño lejos del perfil


# ---------------------------
# Inicializar gmsh.geo
# ---------------------------
gmsh.initialize()

airfoils = []

for foil_points, name in zip(all_airfoil_points, airfoil_names):
	print(len(foil_points))
	airfoils.append(
		AirfoilSpline(
			foil_points, mesh_size_airfoil, name)
	)

gmsh.model.geo.synchronize()

for airfoil in airfoils:
	airfoil.gen_skin()

# crear farfield
if use_circle_farfield:
	#ext_domain = gmsh.model.geo.addCircle(0, 0, 0, farfield_radius)
	ext_domain = Circle(0+circlex_offset, 0, 0, radius=farfield_radius,
								mesh_size=farfield_mesh_size)
else:
	ext_domain = Rectangle(0+tunnelx_offset, 0, 0, tunnel_length, tunnel_height,
									mesh_size=farfield_mesh_size)

gmsh.model.geo.synchronize()
surface = PlaneSurface([ext_domain] + airfoils, preview_geom=preview_geometria)
gmsh.model.geo.synchronize()

# crear superficie con agujeros = outer_loop + todos los inner loops
airfoil_curves = []
for airfoil in airfoils:
	curv = [airfoil.upper_spline.tag,
				airfoil.lower_spline.tag]

	airfoil_curves += curv
	# Creates a new mesh field of type 'BoundaryLayer' and assigns it an ID (f).
	f = gmsh.model.mesh.field.add('BoundaryLayer')

	# Add the curves where we apply the boundary layer (around the airfoil for us)
	gmsh.model.mesh.field.setNumbers(f, 'CurvesList', curv)
	gmsh.model.mesh.field.setNumber(f, 'Size', first_layer_height)  # size 1st layer
	gmsh.model.mesh.field.setNumber(f, 'Ratio', bl_ratio)  # Growth ratio
	# Total thickness of boundary layer
	gmsh.model.mesh.field.setNumber(f, 'Thickness', espesor_bl)

	# Forces to use quads and not triangle when =1 (i.e. true)
	gmsh.model.mesh.field.setNumber(f, 'Quads', 1)

	# Enter the points where we want a "fan" (points must be at end on line)(only te for us)
	gmsh.model.mesh.field.setNumbers(
			f, "FanPointsList", [airfoil.te.tag])

	gmsh.model.mesh.field.setAsBoundaryLayer(f)

ext_domain.define_bc()
surface.define_bc()
for airfoil in airfoils:
	airfoil.define_bc()

gmsh.model.geo.synchronize()

# Say we would like to obtain mesh elements with size lc/30 near curve 2 and
# point 5, and size lc elsewhere. To achieve this, we can use two fields:
# "Distance", and "Threshold". We first define a Distance field (`Field[1]') on
# points 5 and on curve 2. This field returns the distance to point 5 and to
# (100 equidistant points on) curve 2.
campoDistancia = gmsh.model.mesh.field.add("Distance")
# gmsh.model.mesh.field.setNumbers(zonaRefinamiento, "PointsList", [5])
gmsh.model.mesh.field.setNumbers(campoDistancia, "CurvesList", airfoil_curves)
gmsh.model.mesh.field.setNumber(campoDistancia, "Sampling", 500)

# We then define a `Threshold' field, which uses the return value of the
# `Distance' field 1 in order to define a simple change in element size
# depending on the computed distances
#
# SizeMax -                     /------------------
#                              /
#                             /
#                            /
# SizeMin -o----------------/
#          |                |    |
#        Point         DistMin  DistMax
zonaRefinamiento = gmsh.model.mesh.field.add("Threshold")
gmsh.model.mesh.field.setNumber(zonaRefinamiento, "InField", campoDistancia)
gmsh.model.mesh.field.setNumber(zonaRefinamiento, "SizeMin", mesh_size_close)
gmsh.model.mesh.field.setNumber(zonaRefinamiento, "SizeMax", farfield_mesh_size)
gmsh.model.mesh.field.setNumber(zonaRefinamiento, "DistMin", distanciaMinRefinamiento)
gmsh.model.mesh.field.setNumber(zonaRefinamiento, "DistMax", distanciaMaxRefinamiento)

gmsh.model.mesh.field.setAsBackgroundMesh(zonaRefinamiento)

gmsh.model.geo.synchronize()

gmsh.option.setNumber("Mesh.SaveAll", 0)
#gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
#gmsh.option.setNumber("Mesh.Points", 1)
#gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)
#gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

# Generate mesh
gmsh.model.mesh.generate(1)
gmsh.model.mesh.generate(2)
gmsh.model.mesh.optimize("Laplace2D", 5) # La librería que he copiado lo usaba, yo no he visto gran diferencia

gmsh.fltk.run()

gmsh.write(output_su2)

gmsh.finalize()