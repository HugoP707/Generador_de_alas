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
