from ansys.mapdl.reader import save_as_archive
import pyvista as pv

filename = "to_ansys.msh"
mesh = pv.read_meshio(filename)
mesh.plot()  # optionally plot the mesh
mesh.points /= 1000
save_as_archive("from_gmsh2ansys.cdb", mesh)