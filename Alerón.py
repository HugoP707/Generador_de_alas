from lib.airfoils import *
from lib.fileio import *
from lib.aleron import *


# Perfiles de ejemplo
naca642320U, naca642320L = import_airfoil_data("airfoils/javafoilNACA64-2320a0.dat")
naca64AU, naca64AL = import_airfoil_data("airfoils/javafoilNACA64-2320a0.dat")
Fx74U, Fx74L = import_airfoil_data("airfoils/FX74.dat")
s1223U, s1223L = import_airfoil_data("airfoils/s1223.dat")
e423U, e423L = import_airfoil_data("airfoils/e423.dat")

## Si luego usas normalizarAleron() estas variables serán adimensionales
C0 = 1
C1 = C0 * 1/3
C2 = C0 * 1/4
AOA0 = 0
AOA1 = AOA0 + 30
AOA2 = AOA1 + 50
print("Ángulos de ataque: ")
print([AOA0, AOA1, AOA2])

main = Airfoil(Fx74U, Fx74L, {"name": "main"})
main.flip()
main.escalar(C0)
main.setAOA(AOA0)

flap1 = Airfoil(s1223U, s1223L, {"name": "flap1"})
flap1.flip()
flap1.escalar(C1)
flap1.setAOA(AOA1)

flap2 = Airfoil(s1223U, s1223L, {"name": "flap2"})
flap2.flip()
flap2.escalar(C2)
flap2.setAOA(AOA2)

# GAPS = [[C1*-0.25, C1*0.01], [C2*-0.25, C2*0.01]]
GAPS = [gaps_normalizados(C1, AOA0, [-0.2, 0.1]), gaps_normalizados(C2, AOA1, [-0.15, 0.1])]
ala = Alerón([main, flap1, flap2], GAPS, {"name": "RW"})
# ala.normalizarAleron()
print("Cuerda del alerón: " + str(ala.cuerdaTotal))
print("AOA del alerón: " + str(ala.AOATotal))
for foil in ala.foils:
	print(foil.max_extrados())

ala.plot()
ala.exportar(separadores="\t", comaDec=False, coordz=False, carpeta="tests/alaTest1", sameFile=False) #, inFileSeparador="9999,9\t9999,9\n")
