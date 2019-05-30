
import queue
import numpy
import socket
import time
import cv2
import math
from PIL import *
from pathlib import *

import interfazGrafica as ig

class moduloUDP:

    #Descriptor necesario para capturar frames
    cap = None

    #Interfaz grafica
    ig = None

    #Atributos de envio

    id_socket_envio = None  #Socket de envio
    ip_destino = 0 #IP destino
    puerto_destino = 0 #Puerto destino

    id_frame = 0 #ID del frame
    FPS = 15 #Fijos para emision de video local, variables para llamadas
    res_Ancho = 640 #Resolucion ancho
    res_Alto = 480 #Resolucion alto
    res_Ancho_df = 300 #Resolucion ancho default
    res_Alto_df = 300 #Resolucion ancho default
    compresion = 40 #Compresion del frame

    ruta_video = None #Ruta del video

    #Atributos de recepcion

    id_socket_recepcion = None
    buffer_recepcion = None

    #Thread para contar el tiempo de la llamada
    hiloTiempoLlamada = None

    def __init__(self,ig, puertoUsuario):
        """Constructor del modulo UDP

        Parameters
        ----------
        ig :
            La interfaz grafica de la aplicacion
        puertoUsuario :
            El puerto local del usuario en el que recibira los datos

        Returns
        -------
        Inicializamos los atributos necesarios

        """

        self.ig = ig

        #Definimos el socket de envio
        self.id_socket_envio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Socket para envio datagramas UDP
        self.id_socket_envio.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

        #Definimos el socket de recepcion
        self.id_socket_recepcion = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Socket para recepcion datagramas UDP
        self.id_socket_recepcion.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.id_socket_recepcion.settimeout(0.6)
        self.id_socket_recepcion.bind(("0.0.0.0",int(puertoUsuario))) #Hacemos bind con el puerto del usuario

        #Definimos el buffer de recepcion segun el id del frame, usando una PriorityQueue
        self.buffer_recepcion = queue.PriorityQueue(self.FPS*2)

    def conf_envio(self, ip_destino, puerto_destino):
        """Configura el socket de envio, (IP y Puerto)

        Parameters
        ----------
        ip_destino :
            Direccion IP del usuario destino
        puerto_destino :
            Numero de puerto del usuario destino

        Returns
        -------

        """

        self.ip_destino = ip_destino
        self.puerto_destino = puerto_destino


    def ajustar_ruta_video(self, ruta, video_flag):
        """Ajusta la ruta del video local que queremos enviar

        Parameters
        ----------
        ruta :
            Ruta del video que queremos enviar
        video_flag :
            Indicador de si se ha seleccionado la opcion
            de envio de video local.

        Returns
        -------

        """

        #Si no se ha seleccionado la opcion, configuramos la ruta None
        if video_flag == 0:
            self.ruta_video = None
            return

        #Si se ha seleccionado, comprobamos que el video existe y configuramos la ruta
        video = Path(ruta)
        if video.is_file():
            self.ruta_video = ruta

        return


    #FUNCIONES PARA ENVIAR VIDEO

    def enviar_frame(self):
        """Crea un frame (de la WebCam o de un video local), lo muestra en la InterfaZ
           Grafica, y lo envia con las cabeceras correspondientes al usuario destino.

        Parameters
        ----------

        Returns
        -------
        None :
            En caso de que se produzca algun error
        Nada :
            En caso contrario

        """

        #Leemos un frame de la WebCam o del video local
        ret, frame = self.cap.read()

        #Comprobamos si se ha leido algun frame, por si ha terminado la llamada y hay que colgar
        if (ret == False) or (frame is None):
            self.ig.colgar()
            return None

        #En caso de llamada normal, fijamos los FPS a los seleccionados por el usuario
        if self.ruta_video is None:
            FPS_new = self.ig.app.getOptionBox("FPS").split("->")[1]
            self.FPS = int(FPS_new)

        #Esperamos el intervalo de tiempo correspondiente a los FPS
        time.sleep(float(1/self.FPS))

        #Ajustamos la resolución del frame, tanto la nuestra como la del destinatario
        #y lo mostramos en la Interfaz
        frame = cv2.resize(frame, (200,200))
        frameDest = cv2.resize(frame, (self.res_Ancho, self.res_Alto))
        cv2_im = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

        #Cambiamos el frame en la InterfaZ Grafica
        self.ig.cambiarFrameEmisor(img_tk)

        #Para enviar por el socket, primero hay que comprimir el frame
        encode_info = [cv2.IMWRITE_JPEG_QUALITY, self.compresion]
        res, frame_comp = cv2.imencode('.jpg', frameDest, encode_info)

        #Comprobamos que se ha comprimido correctamente
        if res == False:
            return None

        frame_comp = frame_comp.tobytes()

        if frame_comp is None:
            return None

        #Creamos las cabeceras, siguiendo el formato indicado
        cabecera = "{}#{}#{}x{}#{}#".format(self.id_frame, time.time(),  self.res_Ancho, self.res_Alto, self.FPS)
        cabecera = bytearray(cabecera.encode())

        #Creamos el frame definitvo, concatenando las cabeceras creadas con el frame obtenido anteriormente
        frame_def = cabecera + frame_comp
        #Aumentamoos en una unidad el id del frame
        self.id_frame+=1
        #Enviamos el frame al Socket

        try:
            self.id_socket_envio.sendto(frame_def, (self.ip_destino, int(self.puerto_destino)))
        except(OSError):
            return

    def transmitir_video_emisor(self, pause, end):
        """Transmite un video, enviando frames al destinatario mientras la llamada no
           no esta ni finalizada ni en pausa.

        Parameters
        ----------
        pause :
            Indicador de si la llamda esta en pausa
        end :
            Indicador de si la llamda ha finalizado

        Returns
        -------

        """

        #Si estamos enviando un video local, capturamos la imagen del video
        if self.ruta_video is not None:
            self.cap = cv2.VideoCapture(self.ruta_video)
            self.FPS = int(self.cap.get(cv2.CAP_PROP_FPS))
        #Si estamos realizando una llamada normal, capturamos la imagen de la WebCam
        else:
            self.cap = cv2.VideoCapture(0)

        #Mientras la llamada no esta finalizada, enviamos el frame al destinatario
        while not end.isSet():
            #Si la llamada esta en pausa, deja  de enviar frames al destinatario
            while pause.isSet():
                if end.isSet():
                    break
            self.enviar_frame()

        #Quitamos nuestra imagen de video de la Interfaz Grafica,
        im = ImageTk.PhotoImage(Image.open(self.ig.imagenEmisor, "r"))
        self.ig.cambiarFrameEmisor(im)

        return


    def finalizar_envio_video(self):
        """Finaliza la emision de video, dejando de leer frames y cerrando los
           sockets de envio y recepcion.

        Parameters
        ----------


        Returns
        -------

        """

        #Dejamos de leer frames
        self.cap.release()

        #Cerramos los sockets de recepcion y de envio
        self.id_socket_envio.close()
        self.id_socket_recepcion.close()

        #Cambiamos el statusbar de la Interfaz Grafica
        self.ig.app.setStatusbar("..",0)




    #FUNCIONES PARA RECIBIR VIDEO

    def obtener_frame(self):
        """Recibe un frame por el socket de recepcion y lo inserta en el buffer de recepcion

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """

        #Recibimos los datos del socket
        try:
            data, ipOrigen = self.id_socket_recepcion.recvfrom(50000)
        except:
            return

        #Vemos que la IP origen sea la que esperamos
        if ipOrigen[0] == self.ip_destino:

            #Cogemos el id del frame de la cabecera
            cabecera = data.split(b"#")

            #Vemos si el buffer de recepcion esta lleno
            if self.buffer_recepcion.full():
                return
            #Insertamos el frame recibido en el buffer de recepcion
            self.buffer_recepcion.put((int(cabecera[0]), data))

        return


    def llenar_buffer_recepcion(self, pause, end):
        """Funcion que va llenando el buffer de recepcion mientras la llamada
           esta activa

        Parameters
        ----------
        pause :
            Indicador de si la llamda esta en pausa
        end :
            Indicador de si la llamda ha finalizado

        Returns
        -------

        """

        #Mientras la llamada no este finalizada
        while not end.isSet():
            #Mientras tampoco este pausada
            while not pause.isSet():

                #Insertamos el frame recibido en el buffer de recepcion
                self.obtener_frame()

                if end.isSet():
                    break
        return




    def imprimir_frame(self):
        """Saca los frames del buffer de recepcion y lo muestra por pantalla,
           descomprimiendolos antes

        Parameters
        ----------


        Returns
        -------

        """

        #Comprobamos si el buffer esta vacio
        if self.buffer_recepcion.empty():
            time.sleep(1) #Esperamos a que le llegue algo
            return

        #Cogemmos el frame del buffer, y obtenemos su cabecera
        data = self.buffer_recepcion.get()
        cabecera_mg = data[1].split(b"#", 4)

        #Cogemos la resolucion
        res_Ancho = int(cabecera_mg[2].split(b"x")[0])
        res_Alto = int(cabecera_mg[2].split(b"x")[1])

        #Tendremos que adaptar la resolución a nuestra pantalla

        #Para ello veremos la diferencia de proporciones y dependiendo del caso la adaptaremos
        if res_Alto >= self.res_Alto_df or res_Ancho > self.res_Ancho_df:
            div1 = res_Alto/self.res_Alto_df
            div2 = res_Ancho/self.res_Ancho_df
        else:
            div1 = self.res_Alto_df/res_Alto
            div2 = self.res_Ancho_df/res_Ancho


        if div1 > 1:
            if div2 > 1:
                if div1 > div2:
                    res_Alto = math.floor(res_Alto/div1)
                    res_Ancho = math.floor(res_Ancho/div1)
                else:
                    res_Alto = math.floor(res_Alto/div2)
                    res_Ancho = math.floor(res_Ancho/div2)
            else:
                res_Alto = math.floor(res_Alto/div1)
                res_Ancho = math.floor(res_Ancho/div1)
        else:
            res_Alto = math.floor(res_Alto/div2)
            res_Ancho = math.floor(res_Ancho/div2)

        FPS = int(cabecera_mg[3])

        #Descomprimimos el frame
        mg_comp = cabecera_mg[4]
        mg_decomp = cv2.imdecode(numpy.frombuffer(mg_comp, numpy.uint8),1)

        #Lo adaptamos a la interfaz
        frame = cv2.resize(mg_decomp, (res_Ancho, res_Alto))
        cv2_im = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

        #Cambiamos el frame en la InterfaZ Grafica
        self.ig.cambiarFrameReceptor(img_tk)

        #Comprobamos como esta el buffer de lleno, y calculamos los nuevos frames necesarios
        if  self.buffer_recepcion.qsize() > self.FPS:
            #Actualizamos la statusbar de la Interfaz Grafica
            self.ig.app.setStatusbar("FPS = " + str(FPS), 0)

        else:
            time.sleep(float(1/(0.5*FPS))) #Si el buffer esta a menos de 50% de su capacidad, reducimos los FPS a la mitad
            #Actualizamos la statusbar de la Interfaz Grafica
            self.ig.app.setStatusbar("FPS = " + str(FPS*0.5), 0)



    def recepcion_frame(self, pause, end):
        """Mientras la llamada este activa, saca los frames del socket de recepcion
           y los muestra por pantalla

        Parameters
        ----------
        pause :
            Indicador de si la llamda esta en pausa
        end :
            Indicador de si la llamda ha finalizado

        Returns
        -------

        """
        #Mientras la llamada este activa
        while not end.isSet():
            #Mientras la llamada tampoco este pausada
            while not pause.isSet():
                self.imprimir_frame() #Imprimimos los frames por pantalla
                if end.isSet():
                    break
            #Vaciamos el buffer
            while not self.buffer_recepcion.empty():
                    self.buffer_recepcion.get()

        #Una vez la llamada ha finalizado, quitamos la imagen del otro usuario de la Interfaz
        im = ImageTk.PhotoImage(Image.open(self.ig.imagenReceptor, "r"))
        self.ig.cambiarFrameReceptor(im)
        #Finalizamos la emision de video
        self.finalizar_envio_video()

        return
