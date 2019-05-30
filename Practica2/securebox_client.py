
#################################################################################
##### Javier Martinez Rubio javier.martinezrubio@estudiante.uam.es
##### Jorge Santisteban Rivas jorge.santisteban@estudiante.uam.es
#####
#################################################################################

"""SecureBox.

    Usage:
      securebox_client.py --create_id <nombre> <email> [<alias>]
      securebox_client.py --search_id <cadena>
      securebox_client.py --delete_id <id>
      securebox_client.py --upload <fichero> --dest_id <id>
      securebox_client.py --list_files
      securebox_client.py --download <id_fichero>  --source_id <id>
      securebox_client.py --delete_file <id_fichero>
      securebox_client.py --encrypt <fichero> --dest_id <id>
      securebox_client.py --sign <fichero>
      securebox_client.py --enc_sign <fichero> --dest_id <id>
      securebox_client.py (-h | --help)

    Options:
      -h --help       Mostrar ventana de ayuda
      --create_id     Registra nueva identidad para un usuario con nombre nombre ,email y alias (opcional)
      --search_id     Busca un usuario cuyo nombre o correo electrónico contenga cadena.
      --delete_id     Borra la identidad con ID <id> registrada en el sistema.
      --upload        Envia un fichero a otro usuario, cuyo ID es especificado.
      --source_id     ID del emisor del fichero.
      --dest_id       ID del receptor del fichero.
      --list_files    Lista todos los ficheros pertenecientes al usuario
      --download      Recupera un fichero cuyo ID es especificado
      --delete_file    Borra un fichero del sistema.
      --encrypt       Cifra un fichero.
      --sign          Firma un fichero.
      --enc_sign      Firma y encripta un fichero.
"""


from docopt import docopt
from securebox_files import *
from securebox_encrypt import *
from securebox_users import *
import sys
import time
import json

if __name__ == '__main__':
    args = docopt(__doc__)

##CREATE ID

    if args['--create_id']:

        nombre = args['<nombre>']
        email = args['<email>']

        if args['<alias>']:
            alias = args['<alias>']
            salida = create_id(nombre, email,  alias)

        else:
            salida = create_id(nombre, email)

        if salida == None:
            sys.exit(1)

##SEARCH ID

    elif args['--search_id']:

        cadena = args['<cadena>']
        print("-> Buscando usuario " + cadena + " en el servidor...", end = " ",flush=True)
        salida = search_id(cadena)

        if salida:
            print("-> OK.")

            users = json.loads(salida)
            if len(users) == 0:
                print("-> No se ha encontrado ningun usuario con esos datos.")
                sys.exit(1)

            elif len(users) == 1:
                print("-> 1 usuario encontrado:")

            else:
                print("->", len(users), " usuarios encontrados:")

            count = 1
            for user in users:
                if user["nombre"] == None:
                    user["nombre"] = ""
                if user["email"] == None:
                    user["email"] = ""
                if user["userID"] == None:
                    user["userID"] = ""

                print("-> [",count,"]  Nombre: " + user["nombre"] + ",  Email: " + user["email"] + ",  ID: " + user["userID"])
                count+=1
        else:
            sys.exit(1)
##DELETE ID


    elif args['--delete_id']:

        print("-> Solicitando borrado de la identidad #" + args['<id>'] + " ...", end = " ", flush=True)
        salida = delete_id(args['<id>'])

        if salida:
            print("-> OK.")

            id = json.loads(salida)
            print("-> Identidad con ID#" + id["userID"] + " borrada correctamente.")

            print("-> Eliminando la clave privada...", end = " ", flush=True)

            if os.path.exists("private_key.pem"):
                os.remove("private_key.pem")
                print("-> OK. Clave privada borrada satisfactoriamente.")
        else:
            sys.exit(1)


##UPLOAD FILE

    elif args['--upload']:

        id_receptor = args["<id>"]
        file = args["<fichero>"]

        public_key_aux = get_public_key(id_receptor)

        if public_key_aux == None:
            print("-> Error buscando la clave pública del receptor.")
            sys.exit(1)

        public_key  = RSA.import_key(public_key_aux)


        encrypted_file = sign_encrypt_file(public_key, file)

        if encrypted_file == None:
            sys.exit(1)

        print("-> Subiendo fichero a servidor...", end = " ", flush=True)
        salida = upload_file(encrypted_file)
        os.remove(encrypted_file)

        if salida:
            print("-> OK.")

            file_id = json.loads(salida)

            print("Subida realizada correctamente, ID del fichero: ", file_id["file_id"])

        else:
            sys.exit(1)


##LIST FILES

    elif args['--list_files']:

        salida = list_files()

        if salida:
            list_files = json.loads(salida)

            num_files = list_files["num_files"]
            files = list_files["files_list"]

            if num_files == 0:
                print("-> No se ha encontrado ningun archivo perteneciente a este usuario.")
                sys.exit(1)

            elif num_files == 1:
                print("-> 1 fichero encontrado:")

            else:
                print("->", num_files, " ficheros encontrados:")

            count = 1
            for file in files:
                if file["fileName"] == None:
                    file["fileName"] = ""
                if file["fileID"] == None:
                    file["fileID"] = ""

                print("-> [",count,"]  " + file["fileName"] + ",  ID: " + file["fileID"])
                count+=1
        else:
            sys.exit(1)

##DOWNLOAD FILE

    elif args['--download']:

        file = args['<id_fichero>']
        id_source = args['<id>']

        print("Descargando fichero de SecureBox...", end=" ", flush=True)
        encrypted_data, filename = download_file(file)

        if encrypted_data:

            print("OK.")
            print("->", len(encrypted_data), " bytes descargados correctamente.")
            print("-> Recuperando clave pública de ID",id_source, "...", end=" ", flush=True)
            public_key_aux = get_public_key(id_source)

            if public_key_aux == None:
                print("-> Error buscando la clave pública del receptor.")
                sys.exit(1)

            public_key  = RSA.import_key(public_key_aux)
            print("OK.")

            decrypted_data = decrypt_message(encrypted_data, public_key)

            if decrypted_data == None:
                print("-> Error descifrando el archivo.")
                sys.exit(1)

            try:
                with open(filename, "wb") as file:
                    file.write(decrypted_data)
                    file.close()
            except EnvironmmenrError:
                    print ("-> Error abriendo el fichero para escribir" + fichero)
                    sys.exit(1)

            print("Fichero " + filename[10:] + " descargado y verificado correctamente. Guardado en " + filename)

        else:
            sys.exit(1)

##DELETE FILE

    elif args['--delete_file']:

        file = args['<id_fichero>']

        print("-> Solicitando borrado del fichero con  ID#" + file + " ...", end = " ", flush=True)
        salida = delete_file(file)

        if salida:
            print("-> OK.")
            id = json.loads(salida)
            print("-> Fichero con ID#" + id["file_id"] + " borrado correctamente.")
        else:
            sys.exit(1)


##ENCRYPT FILE

    elif args['--encrypt']:

        file = args['<fichero>']
        id_receptor = args['<id>']

        public_key_aux = get_public_key(id_receptor)

        if public_key_aux == None:
            print("-> Error buscando la clave pública del receptor.")
            sys.exit(1)

        public_key  = RSA.import_key(public_key_aux)


        encrypted_file = encrypt_file(public_key, file)

        if encrypted_file == None:
            sys.exit(1)

        print("-> Fichero encriptado correctamente en " + encrypted_file)




##SIGN FILE

    elif args['--sign']:

        file = args['<fichero>']

        signed_file = sign_file(file)

        print("-> Fichero firmado correctamente en " + signed_file)



##SIGN-ENCRYPT FILE

    elif args['--enc_sign']:

        file = args['<fichero>']
        id_receptor = args['<id>']

        public_key_aux = get_public_key(id_receptor)

        if public_key_aux == None:
            print("-> Error buscando la clave pública del receptor.")
            sys.exit(1)

        public_key  = RSA.import_key(public_key_aux)


        encrypted_file = sign_encrypt_file(public_key, file)

        if encrypted_file == None:
            sys.exit(1)

        print("-> Fichero encriptado correctamente en " + encrypted_file)
