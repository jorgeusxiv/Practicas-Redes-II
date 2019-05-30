
#################################################################################
##### Javier Martinez Rubio javier.martinezrubio@estudiante.uam.es
##### Jorge Santisteban Rivas jorge.santisteban@estudiante.uam.es
#####
#################################################################################

import os

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util.Padding import pad, unpad
from Crypto.Signature import pkcs1_15

#Definimos las constantes que vamos a utilizar
RSA_LEN = 2048
AES_LEN = 16
KEY_LEN = 32


#FUNCIONES DE ENCRIPTACION

###################################################
## FUNCION: encryptAES(msg, key)
## INPUT: msg - El mensaje a encriptar
##        key - La clave simetrica para encriptar
## OUTPUT: El mensaje encriptado
## DESCRIPCION: Función que encripta una cadena de datos utilizando AES
###################################################

def encryptAES(msg, key):
    iv = get_random_bytes(AES_LEN)
    cipher_aes = AES.new(key, AES.MODE_CBC, iv)
    encrypted_msg = iv + cipher_aes.encrypt(pad(msg, AES_LEN))
    return encrypted_msg



###################################################
## FUNCION: encrypt_key(key, public_key)
## INPUT: key - La clave a encriptar
##        public_key - La clave pública con la que encriptar
## OUTPUT: La clave pasada como argumento encriptada
## DESCRIPCION: Función que encripta una cadena de datos (una clave en este caso)
##              utilizando RSA
###################################################

def encrypt_key(key, public_key):
    cipher_RSA = PKCS1_OAEP.new(public_key)
    return cipher_RSA.encrypt(key)



###################################################
## FUNCION: encrypt_message(public_key, message)
## INPUT: public_key - La clave pública con la que encriptar con RSA
##        message - El mensaje a encriptar
## OUTPUT: El mensaje encriptado y correctamente devuelto (iv + clave + mensaje)
## DESCRIPCION: Función que encripta un mensaje con AES y lo devuelve concatenado con la
##              clave encriptada con RSA y el argumento iv
###################################################

def encrypt_message(public_key, message):
    key = get_random_bytes(KEY_LEN)
    encrypted_message = encryptAES(message, key)
    encrypted_key = encrypt_key(key, public_key)
    iv = encrypted_message[:AES_LEN]

    return iv + encrypted_key + encrypted_message[AES_LEN:]



###################################################
## FUNCION: encrypt_file(public_key, file)
## INPUT: public_key - La clave pública con la que encriptar con RSA
##        file - El fichero a encriptar
## OUTPUT: El nombre del fichero encriptado
## DESCRIPCION: Función que encripta el contenido de un fichero con AES y lo
##              devuelve concatenado con la clave encriptada con RSA y el argumento iv
###################################################

def encrypt_file(public_key, fichero):
    print ("-> Abriendo el fichero " + fichero + " para encriptarlo...", end=" ", flush=True)
    try:
        with open(fichero, "rb") as file:
            msg = file.read()
            file.close()
    except EnvironmmenrError:
        print ("-> Error abriendo el fichero " + fichero)
        return None
    print("OK.")
    print ("-> Encriptando el fichero " + fichero + "...")

    encrypted_message = encrypt_message(public_key, msg)

    encrypted_filename = "encrypted_" + fichero

    with open(encrypted_filename, "wb") as file:
        msg = file.write(encrypted_message)
        file.close()

    return encrypted_filename



#FUNCIONES DE FIRMA

###################################################
## FUNCION: create_signature(message)
## INPUT: message - El mensaje del cual se quiere crear la firma
## OUTPUT: La firma creada
## DESCRIPCION: Función que crea una firma a partir de un mensaje dado
###################################################

def create_signature(message):
    hash = SHA256.new(message)
    private_key = RSA.importKey(open("private_key.pem", "r").read())
    #cipher = PKCS1_OAEP.new(private_key)
    sign = pkcs1_15.new(private_key).sign(hash)
    return sign



###################################################
## FUNCION: sign_message(message)
## INPUT: message - El mensaje que se quiere firmar
## OUTPUT: El mensaje firmado
## DESCRIPCION: Función que firma un mensaje dado
###################################################

def sign_message(message):
    signature = create_signature(message)
    return signature + message



###################################################
## FUNCION: sign_file(file)
## INPUT: file - El fichero a firmar
## OUTPUT: El nombre del fichero firmado
## DESCRIPCION: Función que firma un el contenido de un fichero dado
###################################################

def sign_file(fichero):
    print ("-> Abriendo el fichero " + fichero + " para firmarlo...", end=" ", flush=True)
    try:
        with open(fichero, "rb") as file:
            msg = file.read()
            file.close()
    except EnvironmmenrError:
        print ("-> Error abriendo el fichero " + fichero)
        return None
    print("OK.")
    print ("-> Firmando el fichero " + fichero + "...")

    signed_message = sign_message(msg)

    signed_filename = "signed_" + fichero

    with open(signed_filename, "wb") as file:
        msg = file.write(signed_message)
        file.close()

    return signed_filename


###################################################
## FUNCION: verify_sign(sign, message, public_key)
## INPUT: sign - La firma a verificar
##        message - El mensaje con el que verificar la firma
##        public_key : La clave pública del usuario que quiere
##                     verificar la firma
## OUTPUT: True en caso de que sea correcta, False en caso contrario
## DESCRIPCION: Función que aplica el hash al mensaje y comprueba que sse corresponde con
##              la firma recibida
###################################################

def verify_sign(sign, message, public_key):

    hash = SHA256.new(message)

    try:
        pkcs1_15.new(public_key).verify(hash, sign)
    except (TypeError, ValueError):
        return False

    return True




#FUNCIONES DE FIRMA Y ENCRIPTACION

###################################################
## FUNCION: sign_encrypt_message(public_key, message)
## INPUT: public_key - La clave publica con la que encriptar
##        message - El mensaje a firmar y encriptar
## OUTPUT: El mensaje correctamente firmado y encriptado
## DESCRIPCION: Función que firma primero, y encripta despues un mensaje pasado como argumento
###################################################

def sign_encrypt_message(public_key, message):

    print ("-> Firmando...", end = " ", flush = True)
    signed_message = sign_message(message)
    print ("-> OK. Firmado correctamente.")
    print ("-> Encriptando...", end = " ", flush = True)
    encrypted_message = encrypt_message(public_key, signed_message)
    print ("-> OK. Encriptado correctamente.")
    return encrypted_message




###################################################
## FUNCION: sign_encrypt_file(public_key, fichero)
## INPUT: public_key - La clave publica con la que encriptar
##        fichero - El fichero cuyo contenido queremos encriptar
## OUTPUT: EL contenido del fichero correctamente firmado y encriptado
## DESCRIPCION: Función que firma primero, y encripta despues el contenido de
##              un fichero pasado como argumento
###################################################

def sign_encrypt_file(public_key, fichero):

    print ("-> Abriendo el fichero " + fichero + " para firmarlo y encriptarlo...")
    try:
        with open(fichero, "rb") as file:
            msg = file.read()
            file.close()
    except EnvironmmenrError:
        print ("-> Error abriendo el fichero " + fichero)
        return None

    print ("-> Firmando y encriptando el fichero " + fichero + "...")

    encrypted_message = sign_encrypt_message(public_key, msg)

    encrypted_filename = "signed_encrypted_" + fichero

    with open(encrypted_filename, "wb") as file:
        msg = file.write(encrypted_message)
        file.close()

    return encrypted_filename




#FUNCIONES DE DESENCRIPTACION

###################################################
## FUNCION: decryptAES(msg, key, iv)
## INPUT: msg - El mensaje a desencriptar
##        key - La clave simétrica para desencriptar
##        iv - Argumento necesario para AES
## OUTPUT: EL mensaje dessencriptado
## DESCRIPCION: Función que desencripta una cadena de datos utilizando AES
###################################################

def decryptAES(msg, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_msg = unpad(cipher.decrypt(msg), AES_LEN)
    return decrypted_msg



###################################################
## FUNCION: decrypt_key(encrypted_key, private_key)
## INPUT: encrypted_key - La clave a desencriptar
##        private_key - La clave privada con la que desencriptar
## OUTPUT: La clave pasada como argumento dessencriptada
## DESCRIPCION: Función que desencripta una cadena de datos (una clave en este caso)
##              utilizando RSA
###################################################

def decrypt_key(encrypted_key, private_key):
    cipher = PKCS1_OAEP.new(RSA.importKey(private_key))
    decrypted_key = cipher.decrypt(encrypted_key)
    return decrypted_key



###################################################
## FUNCION: decrypt_message(encrypted_message, public_key)
## INPUT: encrypted_message - El mensaje a desencriptar
##        public_key - La clave publica a utilizar con RSA
## OUTPUT: El mensaje desencriptado si la firma es correcta,
##         None en caso contrario
## DESCRIPCION: Función que se encarga de todo el proceso de desencriptado:
##              desencriptar la clave, validar la firma y desencriptar con AES
###################################################

def decrypt_message(encrypted_message, public_key):

    print ("-> Descifrando fichero...", end=" ", flush=True)

    iv = encrypted_message[:AES_LEN]
    encrypted_key = encrypted_message[AES_LEN:256+16]
    encrypted_data = encrypted_message[256+16:]

    key = decrypt_key(encrypted_key, open("private_key.pem", "rb").read())
    encrypted_sign_message = decryptAES(encrypted_data, key, iv)
    print ("OK.")

    sign = encrypted_sign_message[:256]
    message = encrypted_sign_message[256:]

    print ("-> Verificando firma...", end=" ", flush=True)
    if verify_sign(sign, message, public_key) == True:
        print("OK.")
        return message

    else:
        print ("ERROR. Fichero no confiable. La firma no es válida.")
        return None
