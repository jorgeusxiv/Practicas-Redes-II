import time
import socket


class servidor_descubrimiento:

    #Puerto servidor
    puertoSD = 8000

    #Tamanio buffer
    tamanioBuffer = 1024

    #Fichero autenticacion
    ficheroAutenticacion = "./conf/autenticacion.dat"

    #Direccion del servidor
    nombreServidor = "vega.ii.uam.es"

    #En primer lugar definimos el constructor

    def __init__(self):
        """Constructor de la clase.

        Parameters
        ----------


        Returns
        -------

        """
        return


    def abrirConexion(self):

        """Funcion para establecer conexion con el servidor de descubrimiento.

        Parameters
        ----------

        Returns
        -------
        ID del socket en caso de conexión aceptada

        """
        #Comprobamos que el campo puerto no este vacio
        if self.puertoSD == None:
            return None

        #Intentamos establecer la conexion
        try:
            socket_id = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_id.settimeout(3)
            socket_id.connect((self.nombreServidor, int(self.puertoSD)))
        except (OSError, ConnectionRefusedError):
            return None

        #Devolvemos el id del socket
        return socket_id

    def cerrarConexion(self, socket_id):

        """Finaliza una conexion dado un socket id.

        Parameters
        ----------
        socket_id :
            Id de la conexion que queremos cerrar.

        Returns
        -------
        respuesta_servidor:
            Respuesta del servidor al cerrar la conexion.

        """

        peticion = "QUIT"
        try:
            socket_id.send(bytes(peticion, 'utf-8'))
            respuesta_servidor = socket_id.recv(self.tamanioBuffer)
            socket_id.close()
        except:
            return None

        return respuesta_servidor


    def registrarUsuario(self, nick, ip_address, port, password):

        """Registra un usuario en el servidor.

        Parameters
        ----------
        nick :
            Nick del usuario a registrar.
        ip_address : type
            Direccion IP del usuario.
        port : type
            Puerto de escucha del usuario.
        password : type
            Contrasenia del usuario.

        Returns
        -------
        OK_WELCOME nick ts si el registro se ha realizado correctamente
        NOK WRONG_PASS si el nick es valido pero la contrasenia es erronea

        """

        #Abrimos la conexion
        socket_usuario = self.abrirConexion()

        if socket_usuario == None:
            return None

        try:
            #Escribimos el mensaje de registro con toda la informacion necesaria
            query = "REGISTER {} {} {} {} V0".format(nick, ip_address, port, password)
            socket_usuario.send(bytes(query,'utf-8'))

            #Recibimos la respuesta del servidor
            buffer = socket_usuario.recv(self.tamanioBuffer)
            respuesta_servidor = buffer.decode('utf-8')
        except:
            return None

        #Cerramos la conexion

        self.cerrarConexion(socket_usuario)

        if respuesta_servidor == "NOK WRONG_PASS":
            return None

        return "OK"



    def queryUsuario(self, nick):
        """A partir del nick de un usuario obtenemos informacion.

        Parameters
        ----------
        nick :
            Nick del usuario del cual obtener informacion.

        Returns
        -------
        None si el usuario no existe, en otro caso una estructura con el
        Nick, direccionIP, puerto y protocolos.

        """

        #Abrimos la conexion
        socket_usuario = self.abrirConexion()

        if socket_usuario == None:
            return None

        try:
            #Creamos la query con el formato QUERY + nick y la enviamos
            query = "QUERY " + nick
            socket_usuario.send(bytes(query, 'utf-8'))

            #Recibimos la respuesta del servidor
            buffer = socket_usuario.recv(self.tamanioBuffer)
            respuesta_servidor = buffer.decode('utf-8')
        except:
            return None

        #Cerramos la conexion

        self.cerrarConexion(socket_usuario)

        #Si no existe el usuario devolvemos el error
        if respuesta_servidor == "NOK USER_UNKNOWN":
            return None
        #En otro caso guardamo s la informacion en un diccionario
        respuesta_parse = respuesta_servidor.split(" ")


        diccionario = {}
        diccionario['nick'] = respuesta_parse[2]
        diccionario['ipAddress'] = respuesta_parse[3]
        diccionario['port'] = respuesta_parse[4]
        diccionario['protocolos'] = respuesta_parse[5]

        return diccionario


    def lista_users(self):
        """Devuelve la lista de usuarios registrados.

        Parameters
        ----------


        Returns
        -------
        Lista de usuarios registrados.

        """

        #Abrimos la conexion
        socket_usuario = self.abrirConexion()

        if socket_usuario == None:
            return None

        try:
            #Creamos la peticion con el formato LIST_USERS
            query = "LIST_USERS"
            socket_usuario.send(bytes(query, 'utf-8'))

            #Recibimos la respuesta del servidor
            buffer = socket_usuario.recv(self.tamanioBuffer)
            respuesta_servidor = buffer.decode('utf-8')
        except:
            return None

        #Si no existe el usuario cerramos la conexion y devolvemos el error
        if respuesta_servidor == "NOK USER_UNKNOWN":
            self.cerrarConexion(socket_usuario)
            return None

        listaSinParsear = respuesta_servidor

        #Necesitamos obtener la lista completa de usuarios, por lo que debemos de seguir leyendo
        #hasta que leamos todos

        totalUsuarios = int(respuesta_servidor.split(" ")[2])
        numUsuariosLeidos = respuesta_servidor.count('#')

        while numUsuariosLeidos < totalUsuarios:
            buffer = socket_usuario.recv(self.tamanioBuffer)
            respuesta_aux = buffer.decode('utf-8')
            numUsuariosLeidos+= respuesta_aux.count('#')
            listaSinParsear += respuesta_aux

        #Ya podemos cerrar la conexión

        self.cerrarConexion(socket_usuario)

        #Parseamos los usuarios leidos
        listaUsuarios = []
        usuarios = listaSinParsear.split("#")

        #Para el primer usuario necesitamos obtenerlo de una manera distinta
        parse_aux = usuarios[0].split(" ")
        listaUsuarios.append(parse_aux[3])

        for usuario in usuarios[1:-1]:
            parse_aux = usuario.split(" ")
            listaUsuarios.append(parse_aux[0])

        return listaUsuarios
