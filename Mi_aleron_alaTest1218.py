from Generador_de_alas.alas.airfoils import *
from Generador_de_alas.alas.fileio import *
from Generador_de_alas.alas.aleron import *


# Perfiles de ejemplo, importarlos desde la carpeta que sea (en estos casos están en esas
# Como esto lo copié de otro tío, lo importa como dos curvas, la de extradós e intradós
# print(import_airfoil_data("datos_perfiles/javafoilNACA64-2320a0.dat"))
naca642320U, naca642320L = import_airfoil_data("datos_perfiles/javafoilNACA64-2320a0.dat")
naca64AU, naca64AL = import_airfoil_data("datos_perfiles/javafoilNACA64-2320a0.dat")
nasaSC21006U, nasaSC21006L = import_airfoil_data("datos_perfiles/NASA SC(2)-1006 AIRFOIL modified2_4 modified modified_closed_te.dat")
naca16_3_014U, naca16_3_014L = import_airfoil_data("datos_perfiles/naca 16-3014.dat")

jkk145145U, jkkL145145L = import_airfoil_data("datos_perfiles/joukovsky145145.dat")

Fx74U, Fx74L = import_airfoil_data("datos_perfiles/FX74.dat")
s1223U, s1223L = import_airfoil_data("datos_perfiles/s1223.dat")
s1223RTLU, s1223RTLL = import_airfoil_data("datos_perfiles/S1223 RTL.dat")
e423U, e423L = import_airfoil_data("datos_perfiles/e423.dat")

naca1313U, naca1313L = import_airfoil_data("datos_perfiles/nacasxx_en50_13_en20/13.dat")
naca1314U, naca1314L = import_airfoil_data("datos_perfiles/nacasxx_en50_13_en20/14.dat")
naca1315U, naca1315L = import_airfoil_data("datos_perfiles/nacasxx_en50_13_en20/15.dat")
naca1316U, naca1316L = import_airfoil_data("datos_perfiles/nacasxx_en50_13_en20/16.dat")
naca1317U, naca1317L = import_airfoil_data("datos_perfiles/nacasxx_en50_13_en20/17.dat")

##############################
# Elegir los perfiles a usar:
##############################
# elem0U, elem0L = None
elem1U, elem1L = naca1313U, naca1313L
elem2U, elem2L = naca1317U, naca1317L
elem3U, elem3L = naca1317U, naca1317L
elem4U, elem4L = naca1317U, naca1317L

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
C0 = None
C1 = 1
C2 = C1*2/3
C3 = C2*2/3
C4 = C3*2/3

print("Cuerdas: ")
print([C1, C2, C3, C4])

AOA1 = -10
AOA2 = AOA1 + 25
AOA3 = AOA2 + 30
AOA4 = AOA3 + 5

print("Ángulos de ataque: ")
print([AOA1, AOA2, AOA3, AOA4])


# Si prefieres usar las coordenadas absolutas puedes hacerlo como:
# pero mi recomendación es usar lo otro.
# GAPS = [[0, 0.2], [0.2, 0.2]]

# GAPS, los huecos entre los perfiles, si estáis en un editor de texto decente poner el ratón
# encima de la función os pondrá la documentación, sino podeís leerla en Generador_de_Alas/alas/aleron.py

# Valores relativos y en ejes de corrdenadas orientados con el perfil anterior
GAPS = [
			gaps_normalizados(C2, AOA1, [-0.55, 0.15]),
			gaps_normalizados(C3, AOA2, [-0.55, 0.15]),
			gaps_normalizados(C4, AOA3, [-0.5, 0.3])
		]

print("Huecos entre perfiles: ")
print(GAPS)
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
main.escalar(C1)
main.setAOA(AOA1)

flap1 = Airfoil(elem2U, elem2L, {"name": "flap1"})
flap1.flip()
flap1.escalar(C2)
flap1.setAOA(AOA2)

flap2 = Airfoil(elem3U, elem3L, {"name": "flap2"})
flap2.flip()
flap2.escalar(C3)
flap2.setAOA(AOA3)

flap3 = Airfoil(elem4U, elem4L, {"name": "flap3"})
flap3.flip()
flap3.escalar(C4)
flap3.setAOA(AOA4)

# TODO: CUIDADO CON setAOA y rotar,
# no fiarse de setAOA, si vas a añadir otro perfil mejor usa rotar !!!!
ala = Alerón([main, flap1, flap2, flap3], GAPS, {"name": "RW"})
#                                           ^^^^^^^^^ Esto no se usa por ahora, no hace falta cambiarlo

## Estas líneas serían para normalizar el ala (hacerla de longitud unitaria)
## La primera la convierte en longitud 1 y la pone con Ángulo de ataque 0
## La segunda vuelve a colocar el alerón con el ángulo de ataque que tenía
ala.normalizarAleron()
# ala.rotar(-ala.AOATotal)

print("Cuerda del alerón: " + str(ala.cuerdaTotal))
print("AOA del alerón: " + str(ala.AOATotal))
for foil in ala.foils:
	print(foil.max_extrados())

ala.plot()
ala.exportar(separadores="\t", comaDec=False, coordz=False, carpeta="tests/alaTest1218", sameFile=False, inFileSeparador="\n\n")
# En Javafoil se ponen todos en un archivo y separados por una fila con 9999,9	9999,9
ala.exportarJavaFoil("tests/JavaFoilTests/1218/")