from Generador_de_alas.alas.airfoils import *
from Generador_de_alas.alas.fileio import *
from Generador_de_alas.alas.aleron import *


# Perfiles de ejemplo, importarlos desde la carpeta que sea (en estos casos están en esas
naca642320U, naca642320L = import_airfoil_data("datos_perfiles/javafoilNACA64-2320a0.dat")
naca64AU, naca64AL = import_airfoil_data("datos_perfiles/javafoilNACA64-2320a0.dat")
Fx74U, Fx74L = import_airfoil_data("datos_perfiles/FX74.dat")
s1223U, s1223L = import_airfoil_data("datos_perfiles/s1223.dat")
e423U, e423L = import_airfoil_data("datos_perfiles/e423.dat")

## (Ignorad este comentario)
# Si luego usas normalizarAleron() estas variables serán adimensionales

########################################
# Aquí poned las cuerdas que veais,
# ignorad la forma rara que he usado
# y poned numeros concretos si preferís
########################################

Lc = 1
C0 = Lc*0.75
C1 = C0*0.5
C2 = C1*0.5

print("Cuerdas: ")
print([C0, C1, C2])

AOA0 = -5
AOA1 = AOA0 + 35
AOA2 = AOA1 + 40

print("Ángulos de ataque: ")
print([AOA0, AOA1, AOA2])

# GAPS, los huecos entre los perfiles, si estáis en un editor de texto decente poner el ratón
# encima de la función os pondrá la documentación, sino podeís leerla en lib/aleron.py
GAPS = [gaps_normalizados(C1, AOA0, [-0.2, 0.05]), gaps_normalizados(C2, AOA1, [-0.2, 0.05])]

# Si prefieres usar las coordenadas absolutas puedes hacerlo como:
# pero mi recomendación es usar lo otro.
# GAPS = [[0, 0.2], [0.2, 0.2]]


##################################################################
# A partir de aquí solo hay que tocar si quieres cambiar
# los nombres de los archivos de salida, o añadir/quitar perfiles
##################################################################

main = Airfoil(s1223U, s1223L, {"name": "main"})
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

# TODO: CUIDADO CON setAOA y rotar,
# no fiarse de setAOA, si vas a añadir otro perfil mejor usa rotar !!!!

ala = Alerón([main, flap1, flap2], GAPS, {"name": "RW"})
ala.normalizarAleron()
ala.rotar(ala.AOATotal)
print("Cuerda del alerón: " + str(ala.cuerdaTotal))
print("AOA del alerón: " + str(ala.AOATotal))
for foil in ala.foils:
	print(foil.max_extrados())

ala.plot()
ala.exportar(separadores="\t", comaDec=False, coordz=False, carpeta="tests/alaTest1", sameFile=False, inFileSeparador="\n\n")
# En Javafoil se ponen todos en un archivo y separados por una fila con 9999,9	9999,9
#, inFileSeparador="9999,9\t9999,9\n")