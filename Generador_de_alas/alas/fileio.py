# Authors:
# * Aaron Dettmann

"""
Import airfoil data from a text file

Developed for Airinnova AB, Stockholm, Sweden.
"""

import re
import numpy as np

# Format identifiers
FORMAT_1 = 'format_1'
FORMAT_2 = 'format_2'

# If x-value deviates from 0 or 1 in this range, it is set to 0 or 1
DATA_TOLERANCE = 1e-3


class FileInputFormatError(Exception):
	"""Raised if file input data is not formatted correctly"""

pass


def import_airfoil_data(file_path):
	"""Read airfoil coordinates from a .dat file.

	Parameters
	----------
	file_path : str or Path
		Path to airfoil data file

	Returns
	-------
	list
		List of unique (x, y, 0) points sorted by original order

	Raises
	------
	FileNotFoundError
		If file does not exist
	ValueError
		If no valid airfoil points found
	"""

	airfoil_points = []
	with open(file_path, 'r') as f:
		for line in f:
			line = line.strip()
			if not line or line.startswith(('#', 'Airfoil')):
					continue
			parts = line.split()
			if len(parts) != 2:
					continue
			try:
					x, y = map(float, parts)
			except ValueError:
					continue
			if x > 1 and y > 1:
					continue
			airfoil_points.append((x, y))

	if not airfoil_points:
		raise ValueError(f"No valid airfoil points found in {file_path}")

	# Split upper and lower surfaces
	try:
		split_index = next(i for i, (x, y) in enumerate(airfoil_points) if x >= 1.0)
	except StopIteration:
		split_index = len(airfoil_points) // 2

	split_index = len(airfoil_points) // 2
	upper_points = airfoil_points[:split_index + 1]
	lower_points = airfoil_points[split_index:]

	# Ensure lower points start from trailing edge
	# if lower_points and lower_points[0][0] == 0.0:
	lower_points = lower_points[::-1]

	# Combine and remove duplicates
	x_up, y_up = zip(*upper_points) if upper_points else ([], [])
	x_lo, y_lo = zip(*lower_points) if lower_points else ([], [])

	x_lo = list(x_lo) + [x_up[0]]
	y_lo = list(y_lo) + [y_up[0]]
	return upper_points, lower_points