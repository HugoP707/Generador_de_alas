import gmsh
import math
import numpy as np


def import_airfoil(filename, eps=1e-9):
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
				coords.append((x, y, 0))
	"""
	# Eliminar duplicados consecutivos
	clean = []
	for x, y, z in coords:
		if not clean or abs(clean[-1][0]-x) > eps or abs(clean[-1][1]-y) > eps:
			clean.append((x, y, z))
	"""
	clean = coords
	# Si el primer y último son iguales, eliminar el último
	if abs(clean[0][0]-clean[-1][0]) < eps and abs(clean[0][1]-clean[-1][1]) < eps:
		clean.pop()
	
	return clean

"""
def read_profile(path, eps=1e-9):
	pts = []
	with open(path, "r") as f:
		for line in f:
				s = line.strip()
				if not s:
					continue
				parts = s.replace(",", " ").split()
				if len(parts) < 2:
					continue
				x, y = float(parts[0]), float(parts[1])

				pts.append((x, y, 0.0))

	# asegurar cerrado (último = primero)
	if len(pts) > 1 and (abs(pts[0][0] - pts[-1][0]) > eps or abs(pts[0][1] - pts[-1][1]) > eps):
		pts.append(pts[0])

	return pts
"""
def read_profile(path, eps=1e-12):
	return import_airfoil(path, eps)

class Point:
	"""
	A class to represent the point geometrical object of gmsh

	...

	Attributes
	----------
	x : float
		position in x
	y : float
		position in y
	z : float
		position in z
	mesh_size : float
		If mesh_size is > 0, add a meshing constraint
			at that point
	"""

	def __init__(self, x, y, z, mesh_size):

		self.x = x
		self.y = y
		self.z = z
		self.mesh_size = mesh_size
		self.dim = 0

		# create the gmsh object and store the tag of the geometric object
		self.tag = gmsh.model.geo.addPoint(
			self.x, self.y, self.z, self.mesh_size)


class Line:
	"""
	A class to represent the Line geometrical object of gmsh

	...

	Attributes
	----------
	start_point : Point
		first point of the line
	end_point : Point
		second point of the line
	"""

	def __init__(self, start_point, end_point):
		self.start_point = start_point
		self.end_point = end_point

		self.dim = 1

		# create the gmsh object and store the tag of the geometric object
		self.tag = gmsh.model.geo.addLine(
			self.start_point.tag, self.end_point.tag)


class CurveLoop:
	"""
	A class to represent the CurveLoop geometrical object of gmsh
	Curveloop object are an addition entity of the existing line that forms it
	Curveloop must be created when the geometry is in its final layout

	...

	Attributes
	----------
	line_list : list(Line)
		List of Line object, in the order of the wanted CurveLoop and closed
		Possibility to give either the tags directly, or the object Line
	"""

	def __init__(self, line_list):

		self.line_list = line_list
		self.dim = 1
		# generate the Lines tag list to follow
		self.tag_list = [line.tag for line in self.line_list]
		# create the gmsh object and store the tag of the geometric object
		self.tag = gmsh.model.geo.addCurveLoop(self.tag_list)

	def close_loop(self):
		"""
		Method to form a close loop with the current geometrical object. In our case,
		we already have it so just return the tag

		Returns
		-------
		_ : int
			return the tag of the CurveLoop object
		"""
		return self.tag

	def define_bc(self):
		"""
		Method that define the marker of the CurveLoop (when used as boundary layer boundary)
		for the boundary condition
		-------
		"""

		self.bc = gmsh.model.addPhysicalGroup(self.dim, [self.tag])
		self.physical_name = gmsh.model.setPhysicalName(
		self.dim, self.bc, "borde de capa limite")


class Spline:
	"""
	A class to represent the Spine geometrical object of gmsh

	...

	Attributes
	----------
	points_list : list(Point)
		list of Point object forming the Spline
	"""

	def __init__(self, point_list):
		self.point_list = point_list

		# generate the Lines tag list to follow
		self.tag_list = [point.tag for point in self.point_list]
		self.dim = 1
		# create the gmsh object and store the tag of the geometric object
		self.tag = gmsh.model.geo.addSpline(self.tag_list)


class Circle:
	"""
	A class to represent a Circle geometrical object, composed of many arcCircle object of gmsh

	...

	Attributes
	----------
	xc : float
		position of the center in x
	yc : float
		position of the center in y
	zc : float
		position in z
	radius : float
		radius of the circle
	mesh_size : float
		determine the mesh resolution and how many segment the
		resulting circle will be composed of
	"""

	def __init__(self, xc, yc, zc, radius, mesh_size):
		# Position of the disk center
		self.xc = xc
		self.yc = yc
		self.zc = zc

		self.radius = radius
		self.mesh_size = mesh_size
		self.dim = 1

		# create multiples ArcCircle to merge in one circle

		# first compute how many points on the circle (for the meshing to be alined with the points)
		self.distribution = math.floor(
			(np.pi * 2 * self.radius) / self.mesh_size)
		realmeshsize = (np.pi * 2 * self.radius)/self.distribution

		# Create the center of the circle
		center = Point(self.xc, self.yc, self.zc, realmeshsize)

		# Create all the points for the circle
		points = []
		for i in range(0, self.distribution):
			angle = 2 * np.pi / self.distribution * i
			p = Point(self.xc+self.radius*math.cos(angle), self.yc+self.radius *
							math.sin(angle), self.zc, realmeshsize)
			points.append(p)
		# Add the first point last for continuity when creating the arcs
		points.append(points[0])

		# Create arcs between two neighbouring points to create a circle
		self.arcCircle_list = [
			gmsh.model.geo.addCircleArc(
					points[i].tag,
					center.tag,
					points[i+1].tag,
			)
			for i in range(0, self.distribution)
		]

		# Remove the duplicated points generated by the arcCircle
		gmsh.model.geo.synchronize()
		gmsh.model.geo.removeAllDuplicates()

	def close_loop(self):
		"""
		Method to form a close loop with the current geometrical object

		Returns
		-------
		_ : int
			return the tag of the CurveLoop object
		"""
		return gmsh.model.geo.addCurveLoop(self.arcCircle_list)

	def define_bc(self):
		"""
		Method that define the marker of the circle
		for the boundary condition
		-------
		"""

		self.bc = gmsh.model.addPhysicalGroup(self.dim, self.arcCircle_list)
		self.physical_name = gmsh.model.setPhysicalName(
			self.dim, self.bc, "farfield")

	def rotation(self, angle, origin, axis):
		"""
		Method to rotate the object Circle
		...

		Parameters
		----------
		angle : float
			angle of rotation in rad
		origin : tuple
			tuple of point (x,y,z) which is the origin of the rotation
		axis : tuple
			tuple of point (x,y,z) which represent the axis of rotation
		"""
		[
			gmsh.model.geo.rotate(
					[(self.dim, arccircle)],
					*origin,
					*axis,
					angle,
			)
			for arccircle in self.arcCircle_list
		]

	def translation(self, vector):
		"""
		Method to translate the object Circle
		...

		Parameters
		----------
		direction : tuple
			tuple of point (x,y,z) which represent the direction of the translation
		"""
		[
			gmsh.model.geo.translate([(self.dim, arccircle)], *vector)
			for arccircle in self.arcCircle_list
		]


class Rectangle:
	"""
	A class to represent a rectangle geometrical object, composed of 4 Lines object of gmsh

	...

	Attributes
	----------
	xc : float
		position of the center in x
	yc : float
		position of the center in y
	z : float
		position in z
	dx: float
		length of the rectangle along the x direction
	dy: float
		length of the rectangle along the y direction
	mesh_size : float
		attribute given for the class Point
	"""

	def __init__(self, xc, yc, z, dx, dy, mesh_size):

		self.xc = xc
		self.yc = yc
		self.z = z

		self.dx = dx
		self.dy = dy

		self.mesh_size = mesh_size
		self.dim = 1
		# Generate the 4 corners of the rectangle
		self.points = [
			Point(self.xc - self.dx / 2, self.yc -
					self.dy / 2, z, self.mesh_size),
			Point(self.xc + self.dx / 2, self.yc -
					self.dy / 2, z, self.mesh_size),
			Point(self.xc + self.dx / 2, self.yc +
					self.dy / 2, z, self.mesh_size),
			Point(self.xc - self.dx / 2, self.yc +
					self.dy / 2, z, self.mesh_size),
		]
		gmsh.model.geo.synchronize()

		# Generate the 4 lines of the rectangle
		self.lines = [
			Line(self.points[0], self.points[1]),
			Line(self.points[1], self.points[2]),
			Line(self.points[2], self.points[3]),
			Line(self.points[3], self.points[0]),
		]

		gmsh.model.geo.synchronize()

	def close_loop(self):
		"""
		Method to form a close loop with the current geometrical object

		Returns
		-------
		_ : int
			return the tag of the CurveLoop object
		"""
		return CurveLoop(self.lines).tag

	def define_bc(self):
		"""
		Method that define the different markers of the rectangle for the boundary condition
		self.lines[0] => wall_bot
		self.lines[1] => outlet
		self.lines[2] => wall_top
		self.lines[3] => inlet
		-------
		"""

		self.bc_in = gmsh.model.addPhysicalGroup(
			self.dim, [self.lines[3].tag], tag=-1)
		gmsh.model.setPhysicalName(self.dim, self.bc_in, "inlet")

		self.bc_out = gmsh.model.addPhysicalGroup(
			self.dim, [self.lines[1].tag])
		gmsh.model.setPhysicalName(self.dim, self.bc_out, "outlet")

		self.bc_wall = gmsh.model.addPhysicalGroup(
			self.dim, [self.lines[0].tag, self.lines[2].tag]
		)
		gmsh.model.setPhysicalName(self.dim, self.bc_wall, "wall")

		self.bc = [self.bc_in, self.bc_out, self.bc_wall]


class AirfoilSpline:
	"""
	A class to represent and airfoil as a CurveLoop object formed with Splines
	...

	Attributes
	----------
	point_cloud : list(list(float))
		List of points forming the airfoil in the order,
		each point is a list containing in the order
		its position x,y,z
	mesh_size : float
		attribute given for the class Point, (Note that a mesh size larger
		than the resolution given by the cloud of points
		will not be taken into account --> Not implemented)
	name : str
		name of the marker that will be associated to the airfoil
		boundary condition
	"""

	def __init__(self, point_cloud, mesh_size,  name):

		self.name = name
		self.dim = 1
		self.mesh_size = mesh_size

		# Generate Points object from the point_cloud
		self.points = [
			Point(point_cord[0], point_cord[1], point_cord[2], mesh_size)
			for point_cord in point_cloud
		]

		# Find leading and trailing edge location
		# in points array
		self.te_idx = 0									# max(self.points, key=attrgetter("x"))
		self.le_idx = (len(self.points) - 1) // 2		# min(self.points, key=attrgetter("x"))

		self.te = self.points[self.te_idx]
		self.le = self.points[self.le_idx]
		print("Total points: " + str(len(self.points)))
		print("Leading edge index: " + str(self.le_idx))

		print(len(self.points))
		print("Margins: ")
		print(self.te_idx, ":", self.le_idx+1)
		print(self.le_idx, ":", len(self.points)+1)
		print(len(self.points[self.te_idx:self.le_idx+1]) + len(self.points[self.le_idx:len(self.points)+1]))

	def gen_skin(self):
		"""
		self.lower_spline = Spline(
			self.points[self.te_idx:self.le_idx+1]
		)

		# create a spline from the trailing edge to the up down point (down part)
		self.upper_spline = Spline(
			self.points[self.te_idx:self.le_idx]
		)

		self.closing_line = Spline([self.points[self.te_idx], self.points[-1]])
		"""
		"""
		Method to generate the three splines forming the foil, Only call this function when the points
		of the airfoil are in their final position
		-------
		"""
		# Find the first point after 0.049 in the upper band lower spline
		# create a spline from the up middle point to the trailing edge (up part)
		self.upper_spline = Spline(
			self.points[0: self.le_idx + 1])

		# create a spline from the trailing edge to the up down point (down part)
		self.lower_spline = Spline(
			self.points[self.le_idx:]
		)

		self.closing_line = Line(
			self.points[len(self.points)-1], self.points[0]
		)
		with open("testing.txt", "w") as file:
			for point in self.points:
				file.write("{0},{1},{2}\n".format(point.x,point.y,point.z))

	def close_loop(self):
		"""
		Method to form a close loop with the current geometrical object

		Returns
		-------
		_ : int
			return the tag of the CurveLoop object
		"""
		self.close_loop_tag = CurveLoop([self.upper_spline, self.lower_spline, self.closing_line]).tag
		return self.close_loop_tag

	def define_bc(self):
		"""
		Method that define the marker of the airfoil for the boundary condition
		-------
		"""
		print("Line tags: ")
		print([
			self.upper_spline.tag,
			self.lower_spline.tag,
			self.closing_line.tag
		])

		self.bc = gmsh.model.addPhysicalGroup(
			self.dim, [self.upper_spline.tag,
							self.lower_spline.tag,
							self.closing_line.tag]
		)
		gmsh.model.setPhysicalName(self.dim, self.bc, self.name)


class PlaneSurface:
	"""
	A class to represent the PlaneSurface geometrical object of gmsh

	...

	Attributes
	----------
	geom_objects : list(geom_object)
		List of geometrical object able to form closedloop,
		First the object will be closed in ClosedLoop
		the first curve loop defines the exterior contour; additional curve loop
		define holes in the surface domaine

	"""

	def __init__(self, geom_objects):

		self.geom_objects = geom_objects
		# close_loop() will form a close loop object and return its tag
		self.tag_list = []
		for geom_object in self.geom_objects:
			self.tag_list.append(
				geom_object.close_loop()
			)
			print("bien")

		self.dim = 2

		print(self.tag_list)
		gmsh.fltk.run()
		# create the gmsh object and store the tag of the geometric object
		self.tag = gmsh.model.geo.addPlaneSurface(self.tag_list)

	def define_bc(self):
		"""
		Method that define the domain marker of the surface
		-------
		"""
		self.ps = gmsh.model.addPhysicalGroup(self.dim, [self.tag])
		gmsh.model.setPhysicalName(self.dim, self.ps, "fluido")
