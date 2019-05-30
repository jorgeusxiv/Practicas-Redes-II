

#################################################################################
##### Javier Martinez Rubio javier.martinezrubio@estudiante.uam.es
##### Jorge Santisteban Rivas jorge.santisteban@estudiante.uam.es
#####
#################################################################################

import requests
from Crypto.PublicKey import RSA
import os
import json
from securebox_errors import *

header = {'Authorization' : "Bearer F31dCeAB047f86c2" }
url = "http://vega.ii.uam.es:8080/api/"

RSA_LEN = 2048

###################################################
## FUNCION: generate_RSA_key()
## INPUT:
## OUTPUT: La clave pública generada
## DESCRIPCION: Función que genera una clave RSA, devolviendo la pública
##              e insertando la privada en un fichero
###################################################

def generate_RSA_key():
    key = RSA.generate(RSA_LEN)

    print("-> Generando par de claves RSA de 2048 bits...", end = " ",flush=True)

    with open("private_key.pem", "wb") as file:
        file.write(key.export_key())
        file.close()

    print("-> OK.")
    return key.publickey().export_key()



###################################################
## FUNCION: create_id()
## INPUT: nombre - El nombre con el que se registrará al usuario
##        email - El email con el que se registrará al usuario
##        alias - El alias con el que se registrará el usuario (Opcional)
## OUTPUT: La respuesta del servidor
##         None si hay error de conexion
## DESCRIPCION: Función que registra un nuevo usuario con los datos especificados,
##              generando a su vez un par de claves , pública y privada, las cuales
##              almacenará, respectivamente, en el servidor y en un fichero local
###################################################

def create_id(nombre, email, alias = None):
    url_register = url + "users/register"
    public_key = generate_RSA_key()
    args = {'nombre': nombre, 'email': email, 'alias' : alias, 'publicKey': public_key}

    try:
        r = requests.post(url_register, json=args, headers=header)
    except requests.ConnectionError:
        print("ERROR. No es posible establecer conexion")
        return None


    r2 = search_id(nombre)
    users = json.loads(r2)
    id = None
    ts_max = 0

    for user in users:
        ts_aux = user["ts"]
        if float(ts_aux) > ts_max:
            ts_max = float(ts_aux)
            id = user["userID"]

    print("-> Usuario con nombre " + nombre + " e ID " + id + " registrado correctamente")
    return r.text




###################################################
## FUNCION: get_public_key(id)
## INPUT: id - El identificador del usuario cuya clave pública solicitamos
## OUTPUT: La clave pública
##         None si hay error de conexion
## DESCRIPCION: Función que busca la clave pública de un usuario especificado por parametro
###################################################

def get_public_key(id):

    url_public_key = url + "users/getPublicKey"
    args = {'userID': id}

    try:
        r = requests.post(url_public_key, json=args, headers=header)
    except requests.ConnectionError:
        print("ERROR. No es posible establecer conexion")
        return None

    if r.status_code == 200:
        data = json.loads(r.text)
        public_key = data["publicKey"]

        return public_key

    error = json.loads(r.text)
    error_code(error)

    return None



###################################################
## FUNCION: search_id(cadena)
## INPUT: cadena - Los datos que utilizamos para buscar a un usuario
## OUTPUT: La respuesta del servidor
##         None si hay algun tipo de error
## DESCRIPCION: Función que permite encontrar un usuario del que sólo sabemos su nombre o correo
###################################################

def search_id(cadena):

    url_search = url + "users/search"
    args = {'data_search': cadena}
    try:
        r = requests.post(url_search, json=args, headers=header)
    except requests.ConnectionError:
        print("ERROR. No es posible establecer conexion")
        return None

    if r.status_code == 200:
        return r.text

    error = json.loads(r.text)
    error_code(error)

    return None



###################################################
## FUNCION: delete_id(id)
## INPUT: id - El ID del usuario que queremos eliminar
## OUTPUT: La respuesta del servidor
##         None si hay error de conexion
## DESCRIPCION: Función que elimina una identidad si esta ha sido creada por el usuario
###################################################

def delete_id(id):
    url_delete = url + "users/delete"
    args = {'userID': id}
    try:
        r = requests.post(url_delete, json=args, headers=header)
    except requests.ConnectionError:
        print("ERROR. No es posible establecer conexion")
        return None

    return r.text
