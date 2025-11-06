from datetime import datetime
import os
import re

import numpy as np
from math import sqrt
from scipy.interpolate import interp1d
from scipy.differentiate import derivative
import matplotlib.pyplot as plt

import airfoils
from airfoils import *


def gaps_normalizados(cuerda, aoa, gaps):
	a = np.deg2rad(aoa)
	MatRot = np.array([
		(np.cos(a), -np.sin(a)),
		(np.sin(a),  np.cos(a))
	])

	return np.matmul(MatRot, [cuerda*gaps[0], cuerda*gaps[1]])


class Alerón:
	def __init__(self, foils, gaps=None, meta=None):
		self.foils = foils # Una lista con todos los airfoils del alerón
		self.meta = meta
		self.gaps = [[0, 0] for i in range(0, len(foils)-1)] if gaps == None else gaps
		self.cuerdaTotal = 0
		self.AOATotal = 0

		self.ajustarCoords()

	def ajustarCoords(self):
		currentx, currenty = 0, 0
		for i in range(0, len(self.foils)-1):
			current = self.foils[i]
			print(self.gaps[i][0], self.gaps[i][1])
			currentx += (current.cuerda * np.cos(np.deg2rad(current.aoa))) + self.gaps[i][0]
			currenty += (current.cuerda * np.sin(np.deg2rad(current.aoa))) + self.gaps[i][1]
			self.foils[i+1].translate(currentx, currenty)

		current = self.foils[-1]
		currentx += (current.cuerda * np.cos(np.deg2rad(current.aoa)))
		currenty += (current.cuerda * np.sin(np.deg2rad(current.aoa)))
		self.cuerdaTotal = sqrt(currentx**2 + currenty**2)
		self.AOATotal = np.rad2deg(np.arctan(currenty / currentx))

	def normalizarAleron(self):
		for foil in self.foils:
			foil.escalar(1/self.cuerdaTotal)
			foil.rotar(-self.AOATotal)

	def plot(self, *, show=True, save=False, settings={}):
		"""
		Plot the airfoil and camber line

		Note:
			* 'show' and/or 'save' must be True

		Args:
			:show: (bool) Create an interactive plot
			:save: (bool) Save plot to file
			:settings: (bool) Plot settings

		Plot settings:
			* Plot settings must be a dictionary
			* Allowed keys:

			'points': (bool) ==> Plot coordinate points
			'camber': (bool) ==> Plot camber
			'chord': (bool) ==> Plot chord
			'path': (str) ==> Output path (directory path, must exists)
			'file_name': (str) ==> Full file name

		Returns:
			None or 'file_name' (full path) if 'save' is True
		"""

		fig = plt.figure()
		ax = fig.add_subplot(1, 1, 1)
		ax.set_xlim([0, 1])
		ax.set_xlabel('x')
		ax.set_ylabel('y')
		ax.axis('equal')
		ax.grid()

		for foil in self.foils:
			ax.plot(foil._x_upper, foil._y_upper, '-', color='blue')
			ax.plot(foil._x_lower, foil._y_lower, '-', color='green')

			if settings.get('points', False):
				ax.plot(foil.all_points[0, :], foil.all_points[1, :], '.', color='grey')

			if settings.get('camber', False):
				x = np.linspace(0, 1, int(airfoils.POINTS_AIRFOIL/2))
				ax.plot(x, foil.camber_line(x), '--', color='red')

		if settings.get('chord', False):
			pass

		plt.subplots_adjust(left=0.10, bottom=0.10, right=0.98, top=0.98, wspace=None, hspace=None)

		if show:
			plt.show()

		if save:
			path = settings.get('path', '.')
			file_name = settings.get('file_name', False)

			if not file_name:
				now = datetime.strftime(datetime.now(), format='%F_%H%M%S')
				file_type = 'png'
				file_name = f'airfoils_{now}.{file_type}'

			fig.savefig(os.path.join(path, file_name))
			return file_name

	def exportar(self, separadores=", ", comaDec=False, coordz=True, carpeta=".", sameFile=False, inFileSeparador="\n\n"):
		result = ""
		if not os.path.exists(carpeta):
			os.mkdir(carpeta)

		for foil in self.foils:
			result += foil.exportar(separador=separadores, comaDec=comaDec, coordz=coordz, toFile= not sameFile, filename= carpeta + "/" + str(foil.meta["name"]) + ".txt")
			if sameFile:
				result += inFileSeparador

		result = result[0: -len(inFileSeparador)] # Quitar el ultimo separador (javafoil)

		if sameFile:
			with open(carpeta + "/" + str(self.meta["name"]) + ".txt", "w") as file:
				file.write(result)
