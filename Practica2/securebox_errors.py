#################################################################################
##### Javier Martinez Rubio javier.martinezrubio@estudiante.uam.es
##### Jorge Santisteban Rivas jorge.santisteban@estudiante.uam.es
#####
#################################################################################

import sys, json



##################################################
## FUNCION: error_code(error)
## INPUT: error - El error del que queremos informar
## OUTPUT: Nada
## DESCRIPCION: Función que imprime por pantalla el error recibido,
##              con algo de información ampliada para ayudar al usuario
###################################################

def error_code(error):

    http_code = error["http_error_code"]
    json_code = error["error_code"]
    description = error["description"]

    print("\nERROR:\nHTTP Code:", http_code,
          "\nJSON Code: " + json_code +
          "\nDescripcion: " + description)

    if json_code == "TOK1":
        print( "Por favor, asegurese de que el token de usuario introducido es correcto.")

    elif json_code == "TOK2":
        print( "Por favor, solicite un nuevo token de usuario.")

    elif json_code == "TOK3":
        print( "Por favor, introduzca la cabecera en un formato correcto")

    elif json_code == "FILE1":
        print( "Por favor, reduzca el tamaño del fichero")

    elif json_code == "FILE2":
        print( "Por favor, asegurese de que el ID introducido es correcto.")

    elif json_code == "FILE3":
        print( "Por favor, elimine otro fichero del servidor antes de subir este.")

    elif json_code == "USER_ID1":
        print( "Por favor, asegurese de que el ID introducido es correcto.")

    elif json_code == "USER_ID2":
        print( "Por favor, introduzca otros credenciales.")

    return
