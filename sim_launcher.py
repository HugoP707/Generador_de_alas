import os
import math
import shutil
import subprocess

# ===============================
#  CONFIGURACIÓN DEL USUARIO
# ===============================

MESH_FILE_1 = "airfoil_simple.su2"

# Valores para barrido paramétrico
AOS = [0, 2, 4, 6, 8]
VELS = [10, 20, 30]

RESULTS_DIR = "results"


# ===============================
#  CREACIÓN DEL CFG BASE
# ===============================
def create_base_cfg(mesh_file):
	cfg = f"""
% ---------------- CFD GENERAL ------------------------------
SOLVER= RANS
MATH_PROBLEM= DIRECT
RESTART_SOL= NO

% ---------------- MALLA
MESH_FILENAME= {mesh_file}

% ---------------- FLUIDO / MODELO FÍSICO
FLUID_MODEL= STANDARD_AIR
GAS_MODEL= AIR-MODEL
SPECIFIC_HEAT_CP= 1004.5
GAS_CONSTANT= 287.05

% ---------------- FLUIDO / ESTADO DE REFERENCIA
%REF_TEMPERATURE= 288.15
%REF_PRESSURE= 101325.0
%REF_DENSITY= 1.225

% ---------------- CONDICIONES DE FLUJO
FREESTREAM_OPTION= VELOCITY_COMPONENTS
FREESTREAM_VELOCITY= ( 10.0, 0.0, 0.0 )

% El ángulo lo aplicamos rotando esta velocidad

% ---------------- TURBULENCIA
KIND_TURB_MODEL= SA

% ---------------- CONDICIONES DE CONTORNO
MARKER_FAR= ( farfield )
% MARKER_WALL= ( wall )
MARKER_WALL= ( main, flap1, flap2 )

% ---------------------- OUTPUT ------------------------------
OUTPUT_FILES= ( HISTORY, PARAVIEW )

% ---------------------- NUMERICOS ------------------------------
CFL_NUMBER= 3.0
MAX_ITER= 2000
CONV_RESIDUAL_MINVAL= -12
"""
	with open("config_base.cfg", "w") as f:
		f.write(cfg)


# ===============================
#  GENERAR CFG PARA CADA CASO
# ===============================
def generate_cfg(aoa_deg, vel, cfg_name):

	# Rotamos la velocidad según el AOA
	aoa_rad = math.radians(aoa_deg)
	vx = vel * math.cos(aoa_rad)
	vy = vel * math.sin(aoa_rad)

	with open("config_base.cfg", "r") as f:
		lines = f.readlines()

	new = []
	for line in lines:
		if "FREESTREAM_VELOCITY" in line:
			new.append(f"FREESTREAM_VELOCITY= ( {vx:.6f}, {vy:.6f}, 0.0 )\n")
		else:
			new.append(line)

	with open(cfg_name, "w") as f:
		f.writelines(new)

# ===============================
#  EJECUCIÓN DE SU2
# ===============================
def run_su2(cfg_name, outdir):
	os.makedirs(outdir, exist_ok=True)

	print(f"\n▶ Ejecutando SU2 con {cfg_name}...")
	subprocess.run(["SU2_CFD", cfg_name], check=True)

	# mover los archivos producidos
	for f in os.listdir("."):
		if (
			f.startswith("history") or
			f.endswith(".vtu") or
			f.endswith(".vtk") or
			f.endswith(".dat") or
			f.endswith(".csv")
		):
			shutil.move(f, os.path.join(outdir, f))


# ===============================
#  MAIN
# ===============================
def main():
	# Comprobación rápida malla
	if not os.path.isfile(MESH_FILE_1):
		raise FileNotFoundError("No se encuentra " + MESH_FILE_1)

	# Crear CFG base si no existe
	# forzar generación por ahora
	if not True: #os.path.isfile("config_base.cfg"):
		print("Generando archivo base: config_base.cfg")
		create_base_cfg(MESH_FILE_1)

	os.makedirs(RESULTS_DIR, exist_ok=True)

	for aoa in AOS:
		for vel in VELS:
			cfg = f"config_AOA{aoa}_VEL{vel}.cfg"
			folder = os.path.join(RESULTS_DIR, f"AOA{aoa}_VEL{vel}")

			generate_cfg(aoa, vel, cfg)
			run_su2(cfg, folder)

	print("\n🎉 Todas las simulaciones han terminado.")


if __name__ == "__main__":
	main()
