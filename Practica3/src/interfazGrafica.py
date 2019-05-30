# import the library
from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import sys
import time
import tkinter
import os
import threading
import socket
import signal
import cv2

import servidor_descubrimiento as SD
import moduloTCP as TCP

class interfazGrafica:

    #Inicialiamzos los puertos y la direccion IP
    puerto_TCP = None
    puerto_UDP = None
    dir_ip = None

    #Inicializamos el nick y la contraseña
    nick = None
    password = None

    #Inicializamos el servidor de descubrimiento y configuramos los ficheros y las imagenes necesarios
    servidorD = None
    tcpMOD = None
    fichero_conf = "./conf/usuario.conf"
    imagenEmisor = "./imgs/blanco_pequenio.gif"
    imagenReceptor = "./imgs/blanco_grande.gif"
    rutaVideo = "/videos"

    usuarios = []

    #Flag que indica si estamos en llamada
    call = False
    #Definimos el thread principal que escucha los comandos
    hiloComandos = None


    def __init__(self):
        """Constructor de la interfaz grafica

        Parameters
        ----------


        Returns
        -------
        Inicializamos los atributos necesarios

        """

        #Definimos el nombre de la aplicacion, los tamaños y el color a utilizar
        self.app = gui("CICUTA", "1000x600")
        self.app.setBg("Khaki")
        self.app.setFont(18)
        self.app.setResizable(canResize = False)
        self.nick = None
        self.password = None

        usuario = {}
        #Abrimos el fichero de configuracion para obtener los puertos TCP y UDP del usuario
        try:
            with open(self.fichero_conf,"r") as file:
                for param in file:
                    (name, value) = param.split()
                    usuario[name] = value
            self.puerto_TCP = usuario['puertoTCP']
            self.puerto_UDP = usuario['puertoUDP']


        except:
            return None

        #Conseguimos nuestra IP local
        socketIP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketIP.connect(("vega.ii.uam.es",8000))
        self.dir_ip = socketIP.getsockname()[0]
        socketIP.close()

        #Definimos el servidor de descubrimiento y el modulo TCP

        self.servidorD = SD.servidor_descubrimiento()
        self.tcpMOD = TCP.moduloTCP(ig=self, ipUsuario=self.dir_ip, puertoUsuario=self.puerto_TCP, puertoUDP=self.puerto_UDP)


        self.app.setStopFunction(self.stop)
        signal.signal(signal.SIGINT, self.manejador_cerrar)


    def inicio(self):
        """Inicializa la aplicacion, mostrando la pantalla de Login

        Parameters
        ----------


        Returns
        -------
        """

        self.pantallaLogin()
        self.app.go()

    ###PANTALLAS###

    def pantallaLogin(self):
        """Define la pantalla de login

        Parameters
        ----------


        Returns
        -------

        """

        #Limpiamos la pantalla
        self.app.removeAllWidgets()
        self.app.removeStatusbar()
        self.app.setSticky("")
        self.app.setStretch('Both')

        #Añadimos la imagen y el logo
        self.app.addImage("titulo","./imgs/titulo.gif",0,0)
        self.app.addImage("logo","./imgs/logo.gif",1,0)

        #Añadimos los campos de Nick y Password
        self.app.addLabelEntry("Nick:",2,0)
        self.app.addLabelSecretEntry("Password:",3,0)

        #Asociamos los botones Login y Salir con la funcion que los maneja
        self.app.addButtons(["Login", "Salir"], self.botones)

        #Ponemos el cursos en el campo de Nick
        self.app.setFocus("Nick:")

    def pantallaPrincipal(self):
        """Define la pantalla principal de la aplicacion

        Parameters
        ----------

        Returns
        -------
        """

        #Limpiamos la pantalla
        self.app.removeAllWidgets()
        self.app.removeStatusbar()
        self.app.setSticky("")
        self.app.setStretch('Both')

        #Añadimos las imagenes, y el campo Buscar
        self.camaraEmisor = self.app.addImage("camaraEmisor", self.imagenEmisor, 0, 0, rowspan = 1)
        self.camaraReceptor = self.app.addImage("camaraReceptor", self.imagenReceptor, 0, 1, rowspan = 2)
        self.app.addLabelEntry("Buscar:", 0, 2)

        #Añadimos todos los botones y campos que aparecen en la pantalla
        self.app.addListBox("usuarios", self.usuarios, 1,2)
        self.app.addLabel("usuarioLogin", "Usuario: {}".format(self.nick), 1,0)

        self.app.addButtons(["Buscar","Actualizar"], self.botones, 2,2)
        self.app.addButtons(["Llamar", "Colgar", "Play", "Pausa"], self.botones, 2,1)
        self.app.addButtons(["Logout"], self.botones, 2,0)

        self.app.addButtons(["Enviar video local"], self.botones, 3,0)
        self.app.addOptionBox("FPS", ["FPS->15","FPS->30", "FPS->45"], 3,1)

        self.app.addStatusbar(fields=3)
        self.app.setStatusbar("..", 0)
        self.app.setStatusbar("..", 1)

        self.app.setPollTime(30)
        self.listarUsuarios()

    def botones(self, button):
        """ Gestiona los callbacks de los botones

        Parameters
        ----------
        button :
            Boton cuya funcionalidad queremos gestionar

        Returns
        -------

        """
        #Dependiendo del boton que hayamos recibido, llamamos a una funcion u otra
        if button == "Salir":
            self.app.stop()
        elif button == "Login":
            self.login()
        elif button == "Actualizar":
            self.listarUsuarios()
        elif button == "Buscar":
            self.buscar()
        elif button == "Logout":
            self.logout()
        elif button == "Llamar":
            self.llamar()
        elif button == "Colgar":
            self.colgar()
        elif button == "Pausa":
            self.pausar()
        elif button == "Play":
            self.play()
        elif button == "Enviar video local":
            self.videoLocal()



    ###FUNCIONES AUXILIARES###

    def cambiarFrameEmisor(self, frame):
        """Cambia el frame que se le muestra al emisor

        Parameters
        ----------
        frame :
            Frame que queremos mostrar

        Returns
        -------

        """
        #Cambiamos el frame del emisor
        self.app.setImageData("camaraEmisor", frame, fmt = 'PhotoImage')

    def cambiarFrameReceptor(self, frame):
        """Cambia el frame que se le muestra al emisor

        Parameters
        ----------
        frame :
            Frame que queremos mostrar

        Returns
        -------

        """
        #Cambiamos el frame del receptor
        self.app.setImageData("camaraReceptor", frame, fmt = 'PhotoImage')


    def buscar(self):
        """Gestiona la funcionalidad de la accion buscar

        Parameters
        ----------


        Returns
        -------

        """

        #Obtenemos el usuario que ha sido introducido para ser buscado
        busqueda = self.app.getEntry("Buscar:")
        #Limpiamos la pantalla que muestra los usuarios encontrados
        self.app.clearListBox("usuarios", callFunction=True)

        #Si encontramos algun usuario que coincida, lo insertamos para que se muestre
        for user in self.usuarios:
            if busqueda.lower() in user.lower():
                self.app.addListItem("usuarios", user)

    def listarUsuarios(self):
        """Gestiona la funcionalidad de la accion listar usuarios

        Parameters
        ----------

        Returns
        -------

        """

        #Llamaos a la funcion del servidor de descubrimiento que lista usuarios
        self.usuarios = self.servidorD.lista_users()
        #Limpiamos las pantallas donde los vamos a mostrar
        self.app.clearEntry("Buscar:")
        self.app.clearListBox("usuarios", callFunction=True)

        #Si el nick de un usuario es vacio, lo quitamos de la lista a mostrar
        if self.nick != "" and self.nick != None:
            self.usuarios.remove(self.nick)


        #Vamos recorriendo la lista y mostrando los usuarios
        for user in self.usuarios:
            if user != "":
                self.app.addListItem("usuarios",user)


    def login(self):
        """Gestiona la funcionalidad de la accion login

        Parameters
        ----------

        Returns
        -------

        """

        #Obtenemos el nick y la contraseña introducidas por el usuario
        nick = self.app.getEntry("Nick:")
        password = self.app.getEntry("Password:")

        #Comprobamos que no haya errores en la introduccion de datos
        if nick.count(' ') != 0 or nick.count('#') != 0:
            self.app.errorBox("Login error", "No estan permitidos # ni espacios")
            self.app.setEntry("Nick:","") #Limpiamos el user y la password introducida
            self.app.setEntry("Password:","") #Limpiamos el user y la password introducida
            return
        #Llamamos a la funcion del servidor de descubrimiento que registra un usuario
        registro = self.servidorD.registrarUsuario(nick, self.dir_ip, self.puerto_TCP, password)

        #Si el registro es correcto, entramos en la aplicacion y nos ponemos en modo escucha para recibir peticiones
        if registro == "OK":
            self.nick = nick
            self.password = password
            self.pantallaPrincipal()
            self.end = threading.Event()
            self.hiloComandos = threading.Thread(target=self.tcpMOD.modo_escucha, args=(self.end,))
            self.hiloComandos.setDaemon(True)
            self.hiloComandos.start()
            self.app.go()

        #Si el registro no es correcto, indicamos al usuario que es erroneo
        else:
            self.app.errorBox("Login error", "Contraseña erronea, vuelva a intentarlo")
            self.app.setEntry("Nick:","") #Limpiamos el user y la password introducida
            self.app.setEntry("Password:","") #Limpiamos el user y la password introducida
            return


    def logout(self):
        """Gestiona la funcionalidad de la accion logout

        Parameters
        ----------

        Returns
        -------

        """

        #Si estamos en una llamada, no se puede hacer logout
        if self.call == True:
            self.app.errorBox("Error en logout", "Durante una llamada no puedes hacer logout")
            return

        #Establecemos los atributos de nick y password a None, cerramos los sockets, y mostramos la pantalla de Login
        self.nick = None
        self.password = None
        self.tcpMOD.cerrar_conexion()
        self.tcpMOD = None
        self.pantallaLogin()


    def llamar(self):
        """Gestiona la funcionalidad de la accion de enviar video local

        Parameters
        ----------

        Returns
        -------

        """

        #Obtenemos el usuario al que queremos llamar
        usuarios = self.app.getListBox("usuarios")

        #Si se ha introducido un usuario, obtenemos sus datos
        if usuarios:
            usuario = usuarios[0]
            usuario_data = self.servidorD.queryUsuario(usuario)

            #Si estas en llamada, no se puede establecer otra  conexion
            if self.call:
                self.app.infoBox("Error","Estas en llamada", parent=None)
                return

            #Llamamos al usuario
            self.tcpMOD.peticion_calling(self.nick, usuario_data['ipAddress'], usuario_data['port'])

        #Si no se ha introducido ningun usuario, sale un error
        else:
            self.app.errorBox("ERROR", "Seleccione a un usuario")


    def videoLocal(self):
        """Gestiona la funcionalidad de la accion de enviar video local

        Parameters
        ----------

        Returns
        -------

        """

        #Obtenemos el usuario al que queremos enviar el video
        usuarios = self.app.getListBox("usuarios")

        #Si se ha introducido un usuario, obtenemos la ruta
        if usuarios:
            usuario = usuarios[0]
            #Obtenemos la ruta del video que se quiere enviar
            rutaVideo = os.getcwd() + self.rutaVideo
            video_seleccionado = self.app.openBox(title="Elije el video", dirName=rutaVideo, fileTypes=[('videos','*.mpeg'), ('videos','*.mp4')], asFile=False, parent=None)
            if video_seleccionado == "" or video_seleccionado == ():
                return

            #Obtenemos los datos necesarios(IP y Puerto) del usuario al que queremos enviar el video
            usuario_data = self.servidorD.queryUsuario(usuario)

            #Si estas en llamada, no se puede establecer otra  conexion
            if self.call:
                self.app.infoBox("Error","Estas en llamada", parent=None)
                return

            #Enviamos al usuario el video
            self.tcpMOD.peticion_enviar_video(self.nick, usuario_data['ipAddress'], usuario_data['port'], ruta_video=video_seleccionado)

        #Si no se ha introducido ningun usuario, sale un error
        else:
            self.app.errorBox("Error", "Seleccione a un usuario")



    def colgar(self):
        """Gestiona la funcionalidad de la accion de colgar

        Parameters
        ----------

        Returns
        -------

        """

        #Si hay una llamada activa, colgamos
        if self.call == True:
            self.tcpMOD.peticion_end(self.nick, self.tcpMOD.ipReceptor, self.tcpMOD.puertoReceptorTCP)


    def pausar(self):
        """Gestiona la funcionalidad de la accion de pausar

        Parameters
        ----------

        Returns
        -------

        """

        #Si hay una llamada activa, la pausamos
        if self.call == True:
            self.tcpMOD.peticion_hold(self.nick, self.tcpMOD.ipReceptor, self.tcpMOD.puertoReceptorTCP)


    def play(self):
        """Gestiona la funcionalidad de la accion de reanudar

        Parameters
        ----------

        Returns
        -------

        """

        #Si hay una llamada activa, la reanudamos
        if self.call == True:
            self.tcpMOD.peticion_resume(self.nick, self.tcpMOD.ipReceptor, self.tcpMOD.puertoReceptorTCP)



    def stop(self):
        """Se ejecuta cuando un usuario cierra la aplicacion. Siempre devuelve true

        Parameters
        ----------


        Returns
        -------

        """
        return True


    def manejador_cerrar(self, signal, any):
        """Maneja el cierre de la aplicacion en caso de hacer Ctrl+C o cerrar
           la aplicacion

        Parameters
        ----------
        signal :
            La senial que se maneja
        any :
            Necesario para que signal funcione

        Returns
        -------

        """
        if self.call == True:
            self.colgar()
        sys.exit(0)
