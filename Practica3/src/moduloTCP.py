
import socket
import time
import cv2
import threading


from PIL import *
from appJar import *

import servidor_descubrimiento as SD
import moduloUDP as UDP

class moduloTCP:

    #Declaramos el servidor de descubrimiento, las direcciones IP y el puerto del usuario

    servidorD = None
    ipUsuario = None
    ipDestino = None
    puertoUsuario = None

    #Declaramos tambien los sockets de envio y de recepcion

    id_socket_envio = None
    id_socket_recepcion = None
    peticiones = 5

    #Necesitaremos además el módulo UDP

    udpMOD = None

    #Variables para threads

    end = None
    pause = None
    timeHilo = None
    video_flag = None

    def __init__(self, ig, ipUsuario, puertoUsuario, puertoUDP):
        """Constructor del modulo TCP.

        Parameters
        ----------
        ig :
            Interfaz grafica que utilizaremos.
        ipUsuario : type
            IP del usuario.
        puertoUsuario : type
            Puerto TCP del usuario.
        puertoUDP : type
            Puerto UDP del usuario.

        Returns
        -------
        Inicializamos todas las variables necesarias para el modulo TCP.

        """

        self.puertoUsuario = puertoUsuario
        self.ipUsuario = ipUsuario
        self.puertoUDP = puertoUDP
        self.ig = ig

        #Inicializamos el socket de recepcion

        self.id_socket_recepcion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.id_socket_recepcion.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.id_socket_recepcion.bind(('', int(self.puertoUsuario)))
        self.id_socket_recepcion.listen(self.peticiones)

        self.servidorD = SD.servidor_descubrimiento()

    #Funciones de envio de peticiones


    def peticion(self, peticion, ipDestino, puertoDestino):
        """Función que se encarga de abrir el socket de envio y enviar la peticion recibida.

        Parameters
        ----------
        peticion :
            Peticion a enviar.
        ipDestino :
            IP destino.
        puertoDestino :
            Puerto destino.

        Returns
        -------
        OK si la petición se ha enviado correctamente, error en otro caso.

        """

        #Abrimos el socket para enviar la peticion
        self.id_socket_envio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #Intentamos conectarnos al socket de envio para enviar la peticion
        try:
            self.id_socket_envio.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            self.id_socket_envio.settimeout(10)
            self.id_socket_envio.connect((ipDestino, int(puertoDestino)))
            self.id_socket_envio.settimeout(None)
        except(OSError, ConnectionRefusedError, ValueError):

            self.ig.app.errorBox("Error de conexion", "Error de conexion")
            if self.ig.call == True:
                self.end.set()
                self.ig.call = False
            self.ig.app.setStatusbar("..",1)
            return "error"

        #Mandamos la peticion y cerramos la conexion

        self.id_socket_envio.send(peticion.encode('utf-8'))
        self.id_socket_envio.close()

        return "OK"

    def peticion_calling(self, nick, ipDestino, puertoDestino):
        """Definimos la peticion CALLING.

        Parameters
        ----------
        nick :
            Nick del usuario que realiza la llamada.
        ipDestino :
            IP destino.
        puertoDestino :
            Puerto destino.

        Returns
        -------
        Volvemos si ha habido un fallo enviando la peticion.

        """

        #Definimos la peticion que queremos enviar

        peticion = "CALLING {} {}".format(nick, self.puertoUDP)


        self.ig.app.setStatusbar("Iniciando llamada",1)

        #Enviamos la peticion al IP y puerto destino
        ans = self.peticion(peticion, ipDestino, puertoDestino)

        #Si nos devuelve error return
        if ans == "error":
            return

    def peticion_enviar_video(self, nick, ipDestino, puertoDestino, ruta_video):
        """Definimos la peticion CALLING (igual que la de arriba) pero hecha para enviar un video local.

        Parameters
        ----------
        nick :
            Nick del usuario que realiza la llamada.
        ipDestino :
            IP destino.
        puertoDestino :
            Puerto destino.
        ruta_video :
            Ruta dl video local a enviar

        Returns
        -------
        Volvemos si ha habido un fallo enviando la peticion.

        """

        #Definimos la peticion que queremos enviar

        peticion = "CALLING {} {}".format(nick, self.puertoUDP)


        self.ig.app.setStatusbar("Iniciando llamada",1)

        #Enviamos la peticion al IP y puerto destino
        ans = self.peticion(peticion, ipDestino, puertoDestino)

        #Si nos devuelve error return
        if ans == "error":
            return
        #Ponemos el flag de video a 1 e indicamos el directorio del video local que queremos enviar

        self.video_flag = 1
        self.ruta_video = ruta_video



    def peticion_hold(self, nick, ipDestino, puertoDestino):
        """Definimos la peticion HOLD, que pausa un video.

        Parameters
        ----------
        nick :
            Nick del usuario que realiza la llamada.
        ipDestino :
            IP destino.
        puertoDestino :
            Puerto destino.

        Returns
        -------
        Volvemos si ha habido un fallo enviando la peticion.

        """

        #Definimos la peticion que queremos enviar
        peticion = "CALL_HOLD {}".format(nick)
        self.ig.app.setStatusbar("Llamada en pausa",1)

        #Enviamos la peticion al IP y puerto destino
        ans = self.peticion(peticion, ipDestino, puertoDestino)

        #Si nos devuelve error return
        if ans == "error":
            return

        #Ponemos el "semaforo" de pausa a 1
        self.pause.set()

    def peticion_resume(self, nick, ipDestino, puertoDestino):
        """Definimos la peticion RESUME, que reanuda la comunicacion.

        Parameters
        ----------
        nick :
            Nick del usuario que realiza la llamada.
        ipDestino :
            IP destino.
        puertoDestino :
            Puerto destino.

        Returns
        -------
        Volvemos si ha habido un fallo enviando la peticion.

        """

        #Definimos la peticion que queremos realizar
        peticion = "CALL_RESUME {}".format(nick)
        self.ig.app.setStatusbar("Llamada activa", 1)

        #Realizamos la peticion al IP y Puero Destino
        ans = self.peticion(peticion, ipDestino, puertoDestino)

        if ans == "error":
            return

        #Ponemos el "semaforo" de pausa a 0
        self.pause.clear()

    def peticion_end(self, nick, ipDestino, puertoDestino):
        """Definimos la peticion END, que finaliza una comunciacion.

        Parameters
        ----------
        nick :
            Nick del usuario que realiza la llamada.
        ipDestino :
            IP destino.
        puertoDestino :
            Puerto destino.

        Returns
        -------
        Volvemos si ha habido un fallo enviando la peticion.

        """

        #Definimos la peticion que queremos realizar
        peticion = "CALL_END {}".format(nick)
        self.ig.app.setStatusbar("...", 1)

        #Realizamos la peticion al IP y Puero Destino
        ans = self.peticion(peticion, ipDestino, puertoDestino)

        if ans == "error":
            return

        #Ponemos el "semaforo" de end a 1 y ponemos el estado de la llamada en False
        self.end.set()
        self.ig.call = False

    #Funciones de recepcion de peticiones

    def peticion_call_accepted(self, nick, ipDestino, puertoDestino):
        """Definimos la peticion CALL_ACCEPTED, que se envia para aceptar una llamada.

        Parameters
        ----------
        nick :
            Nick del usuario que realiza la llamada.
        ipDestino :
            IP destino.
        puertoDestino :
            Puerto destino.

        Returns
        -------
        Volvemos si ha habido un fallo enviando la peticion.

        """

        #Enviamos que la llamada ha sido aceptada
        peticion = "CALL_ACCEPTED {} {}".format(nick, self.puertoUDP)
        self.ig.app.setStatusbar("Llamada activa", 1)

        #Recibimos la respuesta
        ans = self.peticion(peticion, ipDestino, puertoDestino)

        if ans == "error":
            return

    def peticion_call_denied(self, nick, ipDestino, puertoDestino):
        """Definimos la peticion CALL_DENIED, que se envia para rechazar una llamada.

        Parameters
        ----------
        nick :
            Nick del usuario que realiza la llamada.
        ipDestino :
            IP destino.
        puertoDestino :
            Puerto destino.

        Returns
        -------
        Volvemos si ha habido un fallo enviando la peticion.

        """

        #Enviamos que la llamada ha sido aceptada
        peticion = "CALL_DENIED {}".format(nick)

        #Recibimos la respuesta
        ans = self.peticion(peticion, ipDestino, puertoDestino)

        if ans == "error":
            return

    def peticion_call_busy(self, ipDestino, puertoDestino):
        """Definimos la peticion CALL_BUSY, que se envia para indicar que el usuario al que llamamos está
           en otra llamada.

        Parameters
        ----------
        nick :
            Nick del usuario que realiza la llamada.
        ipDestino :
            IP destino.
        puertoDestino :
            Puerto destino.

        Returns
        -------
        Volvemos si ha habido un fallo enviando la peticion.

        """

        #Enviamos que la llamada ha sido aceptada
        peticion = "CALL_BUSY"

        #Recibimos la respuesta
        ans = self.peticion(peticion, ipDestino, puertoDestino)

        if ans == "error":
            return


    #Manejadores de todas las posibles peticiones que un usuario puede recibir


    def manejador_calling(self, nick, puertoDestino):
        """Maneja la recepcion de la petición CALLING.

        Parameters
        ----------
        nick : type
            Nick del usuatio de la peticion.
        puertoDestino : type
            Puerto destino.

        Returns
        -------
        Inicializamos todos los hilos necesario para la correcta recepcion de la peticion.

        """
        #Obtenemos los datos del usuario mediante la funcion queryUsuario

        nick_data = self.servidorD.queryUsuario(nick)

        if self.ig.call == True:
            #Si esta en llamada enviamos la peticion de ocupado
            self.peticion_call_busy(nick_data['ipAddress'], nick_data['port'])
        else:
            #Creamos un pop-up para aceptar la llamada
            popup = "Llamada de {} ¿Acepta la llamada?".format(nick)
            ans = self.ig.app.yesNoBox("Llamada", popup, parent=None)

            #Si la respuesta es NO, enviamos una peticion de cancelar la llamada
            if ans == False:
                self.peticion_call_denied(self.ig.nick ,nick_data['ipAddress'], nick_data['port'])
            elif ans == True:
                #Cambiamos el estado de la llamada
                self.ig.app.setStatusbar("Llamada activa", 1)
                #Enviamos la peticion de llamada aceptada
                self.peticion_call_accepted(self.ig.nick ,nick_data['ipAddress'], nick_data['port'])

                #Definimos los atributos del receptor de video
                self.puertoReceptorUDP = puertoDestino
                self.nickReceptor = nick
                self.ipReceptor = nick_data['ipAddress']
                self.puertoReceptorTCP = nick_data['port']

                #Ponemos el estado de la llamada a True
                self.ig.call = True

                #Definimos el modulo UDP y los eventos de END y de PAUSE
                self.udpMOD = UDP.moduloUDP(self.ig, self.puertoUDP)
                self.udpMOD.conf_envio(nick_data['ipAddress'], puertoDestino)
                self.pause = threading.Event()
                self.end = threading.Event()

                #Inicializamos los 3 hilos de las funciones UDP definidas en el paquete UDP
                self.hiloVideoEmisor = threading.Thread(target = self.udpMOD.transmitir_video_emisor, args = (self.pause, self.end))
                self.hiloRecibirVideo = threading.Thread(target = self.udpMOD.llenar_buffer_recepcion, args = (self.pause, self.end))
                self.hiloMostrarVideo = threading.Thread(target = self.udpMOD.recepcion_frame, args = (self.pause, self.end))
                #Inicializamos el hilo que muestra la duracion de la llamada
                self.hiloTiempoLlamada = threading.Thread(target = self.tiempo_llamada, args = (self.pause, self.end))

                #Demonizamos los hilos y los iniciamos
                self.hiloVideoEmisor.setDaemon(True)
                self.hiloRecibirVideo.setDaemon(True)
                self.hiloMostrarVideo.setDaemon(True)
                self.hiloTiempoLlamada.setDaemon(True)

                self.hiloVideoEmisor.start()
                self.hiloRecibirVideo.start()
                self.hiloMostrarVideo.start()
                self.hiloTiempoLlamada.start()


    def manejador_hold(self):
        """Si estamos en llamada nos ponemos en pausa.

        Parameters
        ----------

        Returns
        -------


        """

        if self.ig.call == True:
            self.ig.app.setStatusbar("Pausa",1)
            self.pause.set()

    def manejador_resume(self):
        """Si estamos en llamada quitamos la pausa.

        Parameters
        ----------

        Returns
        -------

        """

        if self.ig.call == True:
            self.ig.app.setStatusbar("Llamada activa",1)
            self.pause.clear()

    def manejador_end(self):
        """Si estamos en llamada, ponemos el "semaforo" end a 1 y el flag de llamada a 0.

        Parameters
        ----------

        Returns
        -------

        """
        if self.ig.call == True:
            self.ig.app.setStatusbar("...",1)
            self.end.set()
            self.ig.call = False


    def manejador_call_busy(self):
        """Creamos un POP-UP que indique que la persona que queremos llamar esta ocupada.

        Parameters
        ----------

        Returns
        -------

        """

        popup = "La persona a la que esta intentando llamar esta ocupada en estos momentos. Intentelo de nuevo mas tarde"
        self.ig.app.infoBox("Llamada rechazada", popup, parent=None)
        self.ig.app.setStatusbar("...",1)

    def manejador_call_denied(self,nick):
        """Creamos un POP-UP que indique que la persona que queremos llamar ha rechazado la llamada.

        Parameters
        ----------
        nick :
            Nick del usuario que ha rechazado la llamada.

        Returns
        -------

        """

        popup = "{} ha rechazado tu llamada".format(nick)
        self.ig.app.infoBox("Llamada rechazada", popup, parent=None)
        self.ig.app.setStatusbar("...",1)


    def manejador_call_accepted(self, nick, puertoDestino):
        """Maneja la recepcion de la petición CALLING ACCEPTED.

        Parameters
        ----------
        nick : type
            Nick del usuatio de la peticion.
        puertoDestino : type
            Puerto destino.

        Returns
        -------
        Inicializamos todos los hilos necesario para la correcta recepcion de la peticion.

        """
        #Si ya estamos en llamada simplemente volvemos

        if self.ig.call == True:
            return
        else:
            #En otro caso, obtenemos los datos del usuario

            nick_data = self.servidorD.queryUsuario(nick)
            popup = "Llamada aceptada de {}".format(nick)
            self.ig.app.infoBox("Llamada", popup,parent=None)

            #Ponemos el estado de la barra a "Llamada"
            self.ig.app.setStatusbar("Llamada activa",1)
            self.ig.call = True

            #Definimos los atributos del receptor de video
            self.puertoReceptorUDP = puertoDestino
            self.nickReceptor = nick
            self.ipReceptor = nick_data['ipAddress']
            self.puertoReceptorTCP = nick_data['port']

            #Definimos el modulo UDP y los eventos de END y de PAUSE
            self.udpMOD = UDP.moduloUDP(self.ig, self.puertoUDP)
            self.udpMOD.conf_envio(nick_data['ipAddress'], puertoDestino)

            #Si la bandera de video esta a 1, indicamos que queremos transmitir el video local

            if self.video_flag == 1:
                self.udpMOD.ajustar_ruta_video(self.ruta_video, self.video_flag)
            elif self.video_flag == 0:
                self.udpMOD.ajustar_ruta_video(None, self.video_flag)

            #Definimos los eventos de END y de PAUSE

            self.pause = threading.Event()
            self.end = threading.Event()

            #Inicializamos los 3 hilos de las funciones UDP definidas en el paquete UDP
            self.hiloVideoEmisor = threading.Thread(target = self.udpMOD.transmitir_video_emisor, args = (self.pause, self.end))
            self.hiloRecibirVideo = threading.Thread(target = self.udpMOD.llenar_buffer_recepcion, args = (self.pause, self.end))
            self.hiloMostrarVideo = threading.Thread(target = self.udpMOD.recepcion_frame, args = (self.pause, self.end))
            #Inicializamos el hilo que muestra la duracion de la llamada
            self.hiloTiempoLlamada = threading.Thread(target = self.tiempo_llamada, args = (self.pause, self.end))

            #Demonizamos los hilos y los iniciamos
            self.hiloVideoEmisor.setDaemon(True)
            self.hiloRecibirVideo.setDaemon(True)
            self.hiloMostrarVideo.setDaemon(True)
            self.hiloTiempoLlamada.setDaemon(True)

            self.hiloVideoEmisor.start()
            self.hiloRecibirVideo.start()
            self.hiloMostrarVideo.start()
            self.hiloTiempoLlamada.start()

    #Funciones para recibir y procesar las peticiones


    def modo_escucha(self, end):
        """Nos ponemos en escucha continua mediante la funcion accept para recibir peticiones.

        Parameters
        ----------
        end :
            Semaforo END.

        Returns
        -------
        Procesamos la peticiones que vamos recibiendo

        """


        while not end.isSet():

            #Nos ponemos en modo escucha en el socket de recepcion
            conn, address = self.id_socket_recepcion.accept()

            txt = conn.recv(1024)

            #Cuando recibimos una peticion la procesamos

            if txt:
                self.procesar_peticion(txt.decode('utf-8'))


    def procesar_peticion(self, txt):
        """Procesamos una peticion que recibimos.

        Parameters
        ----------
        txt :
            Peticion a procesar.

        Returns
        -------
        Dependiendo de la peticion que recibamos la manejamos de distinta manera.

        """

        split = txt.split(" ")

        #Cogemos el primer elemento de la peticion que es el que nos indicará su tipo
        peticion = split[0]

        if peticion == "CALLING":

            self.manejador_calling(split[1], split[2])

        elif peticion == "CALL_RESUME":

            self.manejador_resume()

        elif peticion == "CALL_END":

            self.manejador_end()

        elif peticion == "CALL_HOLD":

            self.manejador_hold()

        elif peticion == "CALL_ACCEPTED":

            self.manejador_call_accepted(split[1], split[2])

        elif peticion == "CALL_BUSY":

            self.manejador_call_busy()

        elif peticion == "CALL_DENIED":

            self.manejador_call_denied(split[1])

    #Funcion auxiliar para indicar la duracion de una llamada

    def tiempo_llamada(self, pause, end):
        """Funcion que indica la duracion de la llamada a tiempo real.

        Parameters
        ----------
        pause :
            Semaforo de pausa.
        end :
            Semaforo de end.

        Returns
        -------
        Vamos cambiando en la StatusBar la duracion de la llamada

        """

        segundos = 00
        minutos = 00
        horas = 00

        while not end.isSet():

            while pause.isSet():
                if end.isSet():
                    break
            #Vamos contando de 1 en 1 los segundos y lo pasamos al formato de horas, minutos y segundos
            time.sleep(1)
            segundos+=1
            if segundos == 60:
                segundos = 0
                minutos += 1
                if minutos == 60:
                    minutos = 0
                    horas += 1

            tiempo = "Duracion de llamada:   {:02}:{:02}:{:02}".format(horas, minutos, segundos)
            self.ig.app.setStatusbar(tiempo, 2)

        self.ig.app.setStatusbar("...",2)


    def cerrar_conexion(self):
        """Cerramos el socket de recepcion.

        Parameters
        ----------


        Returns
        -------

        """

        #Cerramos el socket de recepcion
        self.id_socket_recepcion.close()
