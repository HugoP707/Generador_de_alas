from Generador_de_alas.alas.airfoils import *
from Generador_de_alas.alas.fileio import *
from Generador_de_alas.alas.aleron import *


# Perfiles de ejemplo, importarlos desde la carpeta que sea (en estos casos están en esas
# Como esto lo copié de otro tío, lo importa como dos curvas, la de extradós e intradós
print(import_airfoil_data("datos_perfiles/javafoilNACA64-2320a0.dat"))
naca642320U, naca642320L = import_airfoil_data("datos_perfiles/javafoilNACA64-2320a0.dat")
naca64AU, naca64AL = import_airfoil_data("datos_perfiles/javafoilNACA64-2320a0.dat")
nasaSC21006U, nasaSC21006L = import_airfoil_data("datos_perfiles/NASA SC(2)-1006 AIRFOIL modified2_4 modified modified_closed_te.dat")
Fx74U, Fx74L = import_airfoil_data("datos_perfiles/FX74.dat")
s1223U, s1223L = import_airfoil_data("datos_perfiles/s1223.dat")
e423U, e423L = import_airfoil_data("datos_perfiles/e423.dat")


##############################
# Elegir los perfiles a usar:
##############################
elem1U, elem1L = nasaSC21006U, nasaSC21006L
elem2U, elem2L = s1223U, s1223L
elem3U, elem3L = e423U, e423L

###############################################################################################
# Por defecto los perfiles los exporta con 120 puntos, independientemente de de los que entren
# además están concentrados los puntos en los bordes de ataque y salida, que es donde queremos
# más precisión (mi mallador no hace mucho caso de esto pero bueno)
# Si quieres cambiar el numero de puntos o el factor de concentración ve a:
# 			/Generador_de_alas/alas/airfoils.py
# Y ahí están definidas las constantes
#
# POINTS_AIRFOIL = 120//2 # (Que sea divisible por dos para no complicar)
# CLUSTERING = 1.2
#
# (Hay que dividir los puntos entre 2 porque usa esos puntos para extradós e intradós)
# (Es chapucero pero me da pereza cambiarlo ya)
###############################################################################################

## (Ignorad este comentario)
# Si luego usas normalizarAleron() estas variables serán adimensionales

########################################
# Aquí poned las cuerdas que veais,
# ignorad la forma "rara" que he usado
# y poned numeros concretos si preferís
########################################
C0 = 0.4
C1 = C0*0.4
C2 = C1*0.5

print("Cuerdas: ")
print([C0, C1, C2])

AOA0 = 7
AOA1 = AOA0 + 33
AOA2 = AOA1 + 33

print("Ángulos de ataque: ")
print([AOA0, AOA1, AOA2])


# Si prefieres usar las coordenadas absolutas puedes hacerlo como:
# pero mi recomendación es usar lo otro.
# GAPS = [[0, 0.2], [0.2, 0.2]]

# GAPS, los huecos entre los perfiles, si estáis en un editor de texto decente poner el ratón
# encima de la función os pondrá la documentación, sino podeís leerla en Generador_de_Alas/alas/aleron.py

# Valores relativos y en ejes de corrdenadas orientados con el perfil anterior
GAPS = [gaps_normalizados(C1, AOA0, [-0.2, 0.2]), gaps_normalizados(C2, AOA1, [-0.22, 0.2])]
# Valores absolutos y en ejes de corrdenadas orientados con el perfil anterio
#GAPS = [gaps_normalizados(C1, AOA0, [-0.2, 0.05], relativos=False), gaps_normalizados(C2, AOA1, [-0.2, 0.05], relativos=False)]
# Valores absolutos y en los ejes de coordenadas normales
#GAPS = [[0.2, 0.1], [0.02, 0.01]]

############################################################################
# A partir de aquí solo hay que tocar los nombres de los perfiles (opcional)
# y la carpeta para exportar al final
############################################################################

main = Airfoil(elem1U, elem1L, {"name": "main"})
main.flip()
main.escalar(C0)
main.setAOA(AOA0)

flap1 = Airfoil(elem2U, elem2L, {"name": "flap1"})
flap1.flip()
flap1.escalar(C1)
flap1.setAOA(AOA1)

flap2 = Airfoil(elem3U, elem3L, {"name": "flap2"})
flap2.flip()
flap2.escalar(C2)
flap2.setAOA(AOA2)

# TODO: CUIDADO CON setAOA y rotar,
# no fiarse de setAOA, si vas a añadir otro perfil mejor usa rotar !!!!
ala = Alerón([main, flap1, flap2], GAPS, {"name": "RW"})
#                                           ^^^^^^^^^ Esto no se usa por ahora, no hace falta cambiarlo

## Estas líneas serían para normalizar el ala (hacerla de longitud unitaria)
## La primera la convierte en longitud 1 y la pone con Ángulo de ataque 0
## La segunda vuelve a colocar el alerón con el ángulo de ataque que tenía
ala.normalizarAleron()
ala.rotar(ala.AOATotal)

print("Cuerda del alerón: " + str(ala.cuerdaTotal))
print("AOA del alerón: " + str(ala.AOATotal))
for foil in ala.foils:
	print(foil.max_extrados())

ala.plot()
#ala.exportar(separadores="\t", comaDec=False, coordz=False, carpeta="tests/alaTest1", sameFile=False, inFileSeparador="\n\n")
# En Javafoil se ponen todos en un archivo y separados por una fila con 9999,9	9999,9
ala.exportarJavaFoil("tests/JavaFoilTests/2/")