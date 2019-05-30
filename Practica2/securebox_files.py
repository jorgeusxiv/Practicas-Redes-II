
#################################################################################
##### Javier Martinez Rubio javier.martinezrubio@estudiante.uam.es
##### Jorge Santisteban Rivas jorge.santisteban@estudiante.uam.es
#####
#################################################################################

import requests
from securebox_errors import *

header = {'Authorization' : "Bearer F31dCeAB047f86c2" }
url = "http://vega.ii.uam.es:8080/api/"


###################################################
## FUNCION: upload_file(file_id)
## INPUT: file_id - El nombre ddel fichero que queremos subir al servidor
## OUTPUT: La respuesta del servidor
##         None si hay algun tipo de error
## DESCRIPCION: Función que sube al servidor un fichero solicitado por el usuario
###################################################

def upload_file(file_id):
    url_upload = url + "files/upload"
    file = open(file_id, "rb")
    args = {'ufile': file}
    try:
        r = requests.post(url_upload, files=args, headers=header)
    except requests.ConnectionError:
        print("ERROR. No es posible establecer conexion")
        return None

    if r.status_code == 200:
        return r.text

    error = json.loads(r.text)
    error_code(error)



##################################################
## FUNCION: download_file(file_id)
## INPUT: file_id - El nombre ddel fichero que queremos descargar del servidor
## OUTPUT: El contenido descargado junto con el nombre del fichero donde se ha
##         descargado, None si hay algun tipo de error
## DESCRIPCION: Función que descarga del servidor un fichero solicitado por el usuario
##              y guarda su contenido en un archivo local
###################################################

def download_file(file_id):
    url_download = url + "files/download"
    args = {'file_id': file_id}
    try:
        r = requests.post(url_download, json=args, headers=header)
    except requests.ConnectionError:
        print("ERROR. No es posible establecer conexion")
        return None, None

    if r.status_code == 200:
        filename = r.headers["Content-disposition"][22:-1]

        file = open("decrypted_" + filename, "wb")
        file.write(r.content)
        file.close()
        return r.content, "decrypted_" + filename


    error = json.loads(r.text)
    error_code(error)


##################################################
## FUNCION: list_files()
## INPUT:
## OUTPUT: La respuesta del servidor
##         None si hay algun tipo de error
## DESCRIPCION: Función que lista los archivos que han sido subidos al
##              servidor por el usuario, mostrando su nombre y su ID
###################################################

def list_files():
    url_list = url + "files/list"
    try:
        r = requests.post(url_list, headers=header)
    except requests.ConnectionError:
        print("ERROR. No es posible establecer conexion")
        return None

    return r.text



##################################################
## FUNCION: delete_file(file_id)
## INPUT: file_id - El ID del fichero que queremos elimiar
## OUTPUT: La respuesta del servidor
##         None si hay algun tipo de error
## DESCRIPCION: Función que elimina del servidor el fichero
##              deseado por el usuario
###################################################

def delete_file(file_id):
    url_delete = url + "files/delete"
    args = {'file_id': file_id}
    try:
        r = requests.post(url_delete, json=args, headers=header)
    except requests.ConnectionError:
        print("ERROR. No es posible establecer conexion")
        return None

    return r.text
