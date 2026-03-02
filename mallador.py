# gen_airfoil_simple.py
# Requisitos: pip install gmsh meshio numpy
#import os
import gmsh
#import meshio
from Generador_de_alas.mallador.gmsh_helpers import *


# ---------------------------
# Configuración (ajusta)
# ---------------------------
# Archivos de los perfiles colocados
airfoil_files = [
	"tests/alaTest1/main.txt",
   "tests/alaTest1/flap1.txt",
   "tests/alaTest1/flap2.txt",
]
# Nombres de las boundaries de cada perfil (mismo orden que los archivos)
# (el farfield se exporta como "farfield")
airfoil_names = [
   "main",
   "flap1",
   "flap2",
]

# Nombre del archibo de la malla
output_msh = "airfoil_simple.msh"
output_su2 = "airfoil_simple.su2"
output_cgns = "airfoil_simple.cgns"
output_file = output_su2

all_airfoil_points = [read_profile(file) for file in airfoil_files]

##############
## SETTINGS ##
##############
mallaCuadrada = False

# Más que nada para revisar cosas, no hace falta si no te da errores
preview_geometria = False


###########################################################
### SETTINGS DEL FARFIELD ###
###########################################################
use_circle_farfield = True	# True -> círculo, False -> caja
farfield_radius = 6			# radio del dominio exterior (si usas círculo)
circlex_offset = 2			# adelantar el perfil dentro del circulo

tunnel_length = 12.0
tunnel_height = 5.0
tunnelx_offset = 2			#adelantar el perfil dentro de la caja


###########################################################
## SETTINGS CAPA LÍMITE
###########################################################
first_layer_height = 1.1e-5   # altura primera capa BL
bl_ratio = 1.2
espesor_bl = 4.5e-3             # Espesor total


##########################################################
## SETTINGS REFINAMIENTO
##########################################################
# Cambiar esta no es importante, en todo caso mesh_size_close
mesh_size_airfoil = 0.001   # tamaño en el contorno del perfil

# SizeMax -                     /------------------
#                              /
#                             /
#                            /
# SizeMin -o----------------/
#          |                |    |
#        Point         DistMin  DistMax

distanciaMinRefinamiento = 0.02
distanciaMaxRefinamiento = farfield_radius * 1

mesh_size_close =  0.001 # espesor_bl * 1.2  # tamaño cerca del ala
farfield_mesh_size = 0.33      # tamaño lejos del ala

mesh_size_estela = 0.1
###########################################################

#########################################
# A partir de aquí no hay que tocar nada
#########################################

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

if mallaCuadrada:
	gmsh.model.geo.mesh.setRecombine(2, surface.tag)

gmsh.model.geo.synchronize()


# crear superficie con agujeros = outer_loop + todos los inner loops
airfoil_curves = []
for airfoil in airfoils:
   curv = [airfoil.upper_spline.tag,
            airfoil.lower_spline.tag,
            airfoil.closing_line.tag
            ]

   airfoil_curves += curv
   # Creates a new mesh field of type 'BoundaryLayer' and assigns it an ID (f).
   f = gmsh.model.mesh.field.add('BoundaryLayer')

   gmsh.model.mesh.field.setNumbers(
         f, "FanPointsList", [airfoil.le.tag] + [airfoil.te.tag])
                        # airfoil.le.tag + i for i in range(-2, 2)
   #gmsh.model.mesh.field.setNumber(
   #   f, "BoundaryLayerFanElements", 20)
   # Add the curves where we apply the boundary layer (around the airfoil for us)
   gmsh.model.mesh.field.setNumbers(f, 'CurvesList', curv)
   gmsh.model.mesh.field.setNumber(f, 'Size', first_layer_height)  # size 1st layer
   gmsh.model.mesh.field.setNumber(f, 'Ratio', bl_ratio)  # Growth ratio
   # Total thickness of boundary layer
   gmsh.model.mesh.field.setNumber(f, 'Thickness', espesor_bl)

   # Forces to use quads and not triangle when =1 (i.e. true)
   gmsh.model.mesh.field.setNumber(f, 'Quads', 1)

   # Enter the points where we want a "fan" (points must be at end on line)(only te for us)
   gmsh.model.mesh.field.setAsBoundaryLayer(f)

ext_domain.define_bc()
surface.define_bc()

# estela = Line(airfoils[-1].te, Point(tunnel_length, 0, 0, mesh_size_estela))
# estela.define_bc()

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
gmsh.model.mesh.field.setNumbers(campoDistancia, "CurvesList", airfoil_curves)# + [estela.tag])
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

# balls = []
# for airfoil in airfoils:
#    ball = gmsh.model.mesh.field.add("Ball")
#    gmsh.model.mesh.field.setNumber(ball, "XCenter", airfoil.le.x)
#    gmsh.model.mesh.field.setNumber(ball, "YCenter", airfoil.le.y)
#    gmsh.model.mesh.field.setNumber(ball, "ZCenter", airfoil.le.z)
#    gmsh.model.mesh.field.setNumber(ball, "Radius", 0.01)   # radio de influencia
#    gmsh.model.mesh.field.setNumber(ball, "VIn", mesh_size_close / 2)    # tamaño mínimo dentro
#    #gmsh.model.mesh.field.setNumber(ball, "VOut", 0.01)     # tamaño fuera

#    #gmsh.model.mesh.field.setAsBackgroundMesh(ball)
#    ball2 = gmsh.model.mesh.field.add("Ball")
#    gmsh.model.mesh.field.setNumber(ball2, "XCenter", airfoil.te.x)
#    gmsh.model.mesh.field.setNumber(ball2, "YCenter", airfoil.te.y)
#    gmsh.model.mesh.field.setNumber(ball2, "ZCenter", airfoil.te.z)
#    gmsh.model.mesh.field.setNumber(ball2, "Radius", 0.02)   # radio de influencia
#    gmsh.model.mesh.field.setNumber(ball2, "VIn", mesh_size_close / 2)    # tamaño mínimo dentro
#    #gmsh.model.mesh.field.setNumber(ball, "VOut", 0.01)     # tamaño fuera

#    balls.append(ball)
#    balls.append(ball2)

combined = gmsh.model.mesh.field.add("Min")
gmsh.model.mesh.field.setNumbers(combined, "FieldsList", [zonaRefinamiento])# + balls)
gmsh.model.mesh.field.setAsBackgroundMesh(combined)

gmsh.model.geo.synchronize()


gmsh.option.setNumber("Mesh.SaveAll", 0)
gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
#gmsh.option.setNumber("Mesh.Points", 1)
#gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)
#gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
gmsh.option.setNumber("Mesh.Algorithm", 8)          # frontal-delaunay (+ robusto en BL)
# Disable all automatic characteristic length sources
gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", 0)
gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 0)
gmsh.option.setNumber("Mesh.CharacteristicLengthExtendFromBoundary", 0)

# Let the background mesh field (that we will create) define the sizes
#gmsh.option.setNumber("Mesh.LcMin", 1e-9)   # safety
#gmsh.option.setNumber("Mesh.LcMax", 1e9)


# Generate mesh
gmsh.model.mesh.generate(1)
gmsh.model.mesh.generate(2)
gmsh.model.mesh.optimize("Netgen")
gmsh.model.mesh.optimize("Laplace2D", 5) # La librería que he copiado lo usaba, yo no he visto gran diferencia

# gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
gmsh.write(output_file)

gmsh.fltk.run()


gmsh.finalize()