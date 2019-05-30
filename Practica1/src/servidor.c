/////////////////////////////////////////////////////////////////////////////////
///// Javier Martinez Rubio javier.martinezrubio@estudiante.uam.es
///// Jorge Santisteban Rivas jorge.santisteban@estudiante.uam.es
/////
/////////////////////////////////////////////////////////////////////////////////

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include <netinet/in.h>
#include <syslog.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <assert.h>
#include <time.h>
#include <pthread.h>
#include <fcntl.h>
#include <confuse.h>
#include "servidor.h"
#include "picohttpparser.h"

#define st_mtime st_mtim.tv_sec

//Variables globales que utilizaremos para definir la fecha

char *meses[12]={"Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sept", "Oct", "Nov", "Dic"};
char *dias[7]={"Dom","Lun", "Mar", "Mie", "Jue", "Vie", "Sab"};

//Variables globales para el servidor

static char *server_root = NULL;
static long max_clients = 0;
static long listen_port = 0;
static char *server_signature = NULL;

//Tamaño maximo del buffer

#define BUFFSIZE 4096

//////////////////////////////////////////////////////////////////////////
// Estructura para definir los tipos de contenido
//////////////////////////////////////////////////////////////////////////

struct {
  char *ext;
  char *filetype;
} extensions [] = {
  {"txt", "text/plain" },
  {"html","text/html"},
  {"htm", "text/html"},
  {"gif", "image/gif" },
  {"jpeg", "image/jpeg" },
  {"jpg", "image/jpeg" },
  {"mpeg", "video/mpeg" },
  {"mpg",  "video/mpeg"  },
  {"doc",  "application/msword"  },
  {"docx", "application/msword" },
  {"pdf", "application/pdf" },
  {0,0} };


/**
 * Funcion tcp_listen, la cual abre el socket, el bind y se pone a escuchar peticiones
 * @return Identificador del socket
 */

int tcp_listen() {

  //En primer lugar tenemos que parsear el fichero .conf para poder obtener la ruta de los ficheros del servidor
  //, el numero maximo de clientes de la conexion, el puerto donde escuchara y el nombre del servidor.

  cfg_opt_t opts[] = {
    CFG_SIMPLE_STR("server_root", &server_root),
    CFG_SIMPLE_INT("max_clientes", &max_clients),
    CFG_SIMPLE_INT("listen_port", &listen_port),
    CFG_SIMPLE_STR("server_signature", &server_signature),
    CFG_END()
  };
  cfg_t *cfg;
  /* set default value for the server option */
  server_root = strdup("gazonk");
  server_signature = strdup("/");
  cfg = cfg_init(opts, 0);
  cfg_parse(cfg, "server.conf");
  printf("Server root: %s\n", server_root);
  printf("Max clients: %ld\n", max_clients);
  printf("Listen port: %ld\n",listen_port);
  printf("Server name: %s\n",server_signature);


  int sockval;
  struct sockaddr_in Direccion;

  //Abrimos el socket
  syslog(LOG_INFO, "Creando el socket");
  if((sockval = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    syslog(LOG_ERR, "Error creando el socket");
    exit(-1);
  }

  //Guardamos en la estructura la informacion del socket
  Direccion.sin_family=AF_INET;
  Direccion.sin_port=htons(listen_port);
  Direccion.sin_addr.s_addr=htonl(INADDR_ANY);
  bzero((void*)&(Direccion.sin_zero),8);

  //Hacemos el bind
  syslog (LOG_INFO, "Haciendo el binding");
  if (bind (sockval, (struct sockaddr*)&Direccion, sizeof(Direccion))<0){
    syslog(LOG_ERR, "Error haciendo el binding");
    exit(-2);
 }

 //Hacemos el listen
 syslog (LOG_INFO, "Escuchando conexiones");
 if (listen (sockval, max_clients)<0){
   syslog(LOG_ERR, "Error escuchando");
   exit(-3);
 }

 return sockval;
}

/**
 * Función que realiza el accept en una conexión
 * @param  sockval Identificador del socket
 * @return         Identificador de la conexion
 */
int accept_connection(int sockval) {

  int desc;
  socklen_t len;
  struct sockaddr Conexion;
  len = sizeof(Conexion);

  //Aceptamos la conexion
  if ((desc = accept(sockval, &Conexion, &len))<0){
    syslog(LOG_ERR, "Error aceptando conexion");
    exit(-1);
  }

  return desc;

}

/**
 * Funcion que procesa peticiones, en nuestro GET, POST y OPTIONS
 * @param  Identificador de la conexion de la peticion
 * @return
 */

void * process_request(void * connval) {

  int c = *((int *)connval);

  free(connval);

  //Variables para el parseo de la peticion

  char buffer[4096];
  const char *method, *path;
  int pret, minor_version,i;
  long len;
  struct phr_header headers[500];
  size_t buflen = 0, prevbuflen = 0, method_len, path_len, num_headers;
  ssize_t rret;

  //Variables para el tiempo y la fecha de modificacion

  time_t t;
  struct tm *tm;
  struct stat fileStat;

  //Variables para las cabeceras y los scripts

  t=time(NULL);
  tm=localtime(&t);
  int file_id;
  char *fstr;
  char path2[BUFFSIZE];
  char path_spt[BUFFSIZE]; //path para el script
  char path_head[BUFFSIZE]; //path para la cabecera
  char path_copy[BUFFSIZE];
  char *script;
  struct tm *last_mod;
  char *qdetector1, *qdetector2;


  //Respuesta del script
  char script_response[BUFFSIZE];

  //En primer lugar tenemos que parsear la cabecera de la peticion utilizando la libreria picohttpparser

  while (1) {
    /* read the request */
    while ((rret = read(c, buffer + buflen, sizeof(buffer) - buflen)) == -1)
        ;
    if (rret <= 0){
      memset(buffer,0,strlen(buffer)); //Limpiamos el buffer y enviamos un error 400
      sprintf(buffer,"HTTP/1.1 400 Forbidden\nContent-Length: 88\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>400 Forbidden</title>\n</head><body>\n<h1>Forbidden</h1></body></html>\n");
      send(c, buffer, BUFFSIZE, 0);
      close(c);
      pthread_exit(NULL);
    }
    prevbuflen = buflen;
    buflen += rret;
    /* Parseamos la peticion con phr_parse_request de picohttpparser */
    num_headers = sizeof(headers) / sizeof(headers[0]);
    pret = phr_parse_request(buffer, buflen, &method, &method_len, &path, &path_len,
                             &minor_version, headers, &num_headers, prevbuflen);


    if (pret > 0)
        break; /* successfully parsed the request */
    else if (pret == -1){
      memset(buffer,0,strlen(buffer)); //Limpiamos el buffer y enviamos un error 400
      sprintf(buffer,"HTTP/1.%d 400 Forbidden\nContent-Length: 88\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>400 Forbidden</title>\n</head><body>\n<h1>Forbidden</h1></body></html>\n",minor_version);
      send(c, buffer, BUFFSIZE, 0);
      close(c);
      pthread_exit(NULL);
    }
    /* request is incomplete, continue the loop */
    assert(pret == -2);
    if (buflen == sizeof(buffer)){
      memset(buffer,0,strlen(buffer));//Limpiamos el buffer y enviamos un error 400
      sprintf(buffer,"HTTP/1.%d 400 Forbidden\nContent-Length: 88\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>400 Forbidden</title>\n</head><body>\n<h1>Forbidden</h1></body></html>\n",minor_version);
      send(c, buffer, BUFFSIZE, 0);
      close(c);
      pthread_exit(NULL);
    }

  }

  //Tenemos que concatenar el path que obtenemos al parsear con la raiz de los ficheros del servidor

  strcpy(path2,server_root);
  strncat(path2,path,path_len);
  path_len+=strlen(server_root); //Aumentamos el tamanio del path tras haberlo concatenado

  //Cuando tenemos peticiones POST (no POST/GET), los argumentos se encuentran en el cuerpo, por lo que tendremos que obtenerlos y concatenarlos con el path para
  //procesar todas las peticiones de igual manera

  if((!strncmp(method,"POST ",4) || !strncmp(method,"post ",4)) && !(strstr(path,"?"))){

    char *sch;
    char body1[BUFFSIZE];
    char body2[BUFFSIZE];
    char *stopper= "\n\r";
    char post_args[BUFFSIZE];

    //Llegamos hasta el final de los headers utilizando el stopper

    sch = strstr(buffer,stopper);
    strcpy(body1, sch);

    //Además tenemos que eliminar los saltos de línea de sobra, por lo que únicamente nos interesa
    //a partir de la 3º posicion
    for(i=0;body1[i]!='\0';i++)
     {
     body2[i] = body1[i+3];
      }

    strcpy(post_args,body2);

    //Tenemos que llegar a un url igual al que recibe una peticion GET para analizar todas las peticiones
    //de la misma manera, por lo que concatenamos todo con una ? que lo separe

    strcat(path2,"?");
    path_len+=1;
    strcat(path2,post_args);
    path_len+=strlen(post_args);


  }

  //Si el path esta vacio ponemos por defecto un path con el index.html

    if(!strncmp(path2,"./htmlfiles/",path_len)){
      strcat(path2,"index.html");
      path_len+=10;
    }

    strcpy(path_spt,path2);

    //Veamos si lo que tenemos es un script y, si lo es, lo procesamos

    script=strtok(path_spt,"?");

    //Hemos implementado que ejecute scripts de python y de php

    if(!strcmp(script+strlen(script)-3,".py") || !strcmp(script+strlen(script)-4,".php")){

      int pid;
      int fd1[2], fd2[2];
      char *token;
      char *arguments[BUFFSIZE];
      char path_p1[BUFFSIZE]=".";
      char path_p2[BUFFSIZE], path_aux[BUFFSIZE];
      char interpreter[20];
      int len;

      strcpy(path_aux, path2);

      //Parseamos los argumentos para ejecutar con execvp el script de manera correcta

      token = strtok(path_aux, ".");

      strcpy(path_p2, token);
      strcat(path_p1,path_p2);
      strcat(path_p1,".");
      token = strtok(NULL, "?");

      strcpy(interpreter, token);
      strcat(path_p1,interpreter);

      //Identificamos cual va a ser el interprete del script
      arguments[0] = interpreter;
      arguments[1] = path_p1;
      arguments[2] = strtok(NULL,"?");
      if(arguments[2] == NULL){
        memset(buffer,0,strlen(buffer));//Limpiamos el buffer y enviamos un error 400
        sprintf(buffer,"HTTP/1.%d 400 Forbidden\nContent-Length: 88\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>400 Forbidden</title>\n</head><body>\n<h1>Forbidden</h1></body></html>\n",minor_version);
        send(c, buffer, BUFFSIZE, 0);
        close(c);
        pthread_exit(NULL);
      }
      arguments[3]=NULL;


        //Creamos los pipe

        if(pipe(fd1)<0 || pipe(fd2)<0){
          memset(buffer,0,strlen(buffer));
          sprintf(buffer,"HTTP/1.%d 400 Forbidden\nContent-Length: 88\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>400 Forbidden</title>\n</head><body>\n<h1>Forbidden</h1></body></html>\n",minor_version);
          send(c, buffer, BUFFSIZE, 0);
          close(c);
          pthread_exit(NULL);
        }


        //Hacemos un fork para ejecutar los scripts

        if((pid=fork()) < 0){
          memset(buffer,0,strlen(buffer));
          sprintf(buffer,"HTTP/1.%d 400 Forbidden\nContent-Length: 88\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>400 Forbidden</title>\n</head><body>\n<h1>Forbidden</h1></body></html>\n",minor_version);
          send(c, buffer, BUFFSIZE, 0);
          close(c);
          pthread_exit(NULL);
        }

        //Proceso hijo que ejecuta el script

        if(pid == 0){

          close(fd1[1]);
          dup2(fd1[0],0);
          close(fd2[0]);
          dup2(fd2[1],1);

          if(!strcmp(interpreter,"py")){
            strcpy(interpreter, "python3");
            arguments[0] = interpreter;
          }
          //Ejecutamos el script mediante la funcion execvp

          if(execvp(interpreter,arguments) <0) {
            memset(buffer,0,strlen(buffer));
            sprintf(buffer,"HTTP/1.%d 400 Forbidden\nContent-Length: 88\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>400 Forbidden</title>\n</head><body>\n<h1>Forbidden</h1></body></html>\n",minor_version);
            send(c, buffer, BUFFSIZE, 0);
            close(c);
            pthread_exit(NULL);
          }

          exit(0);

        }

        //Proceso padre que escribe los argumentos en la tuberia

        if(pid > 0){

          len = strlen(*arguments);
          if(!strcmp(interpreter,"py")){
          len+=1;
          }
          close(fd1[0]);
          for(int x=2; x<len; x++) {
            write(fd1[1],arguments[x], strlen(arguments[x]));
            write(fd1[1], "\n", 1);
          }


          wait(NULL);

          close(fd2[1]);
          if(read(*fd2,script_response, BUFFSIZE) == -1){
              memset(buffer,0,strlen(buffer));
              sprintf(buffer,"HTTP/1.%d 400 Forbidden\nContent-Length: 88\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>400 Forbidden</title>\n</head><body>\n<h1>Forbidden</h1></body></html>\n",minor_version);
              send(c, buffer, BUFFSIZE, 0);
              close(c);
              pthread_exit(NULL);

          }

        }


    }

    //Ahora debemos obtener unicamente el path del fichero, sin argumentos, por lo que tenemos que copiar en path_head esa url

    strcpy(path_copy,path2);
    qdetector1 = strstr(path2,"?");
    if(qdetector1 == NULL){
      strcpy(path_head,path2);
    }else{
      qdetector2 = strtok(path_copy, "?");
      strcpy(path_head, qdetector2);
    }
    //Ponemos la nueva longitud del path

    path_len = strlen(path_head);

    //Definimos la estructura que nos dara la fecha de ultima modificacion

    if(stat(path_head,&fileStat) < 0){
      memset(buffer,0,strlen(buffer));
      sprintf(buffer,"HTTP/1.%d 404 Not Found\nContent-Length: 112\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>404 Not Found</title>\n</head><body>\n<h1>Not Found</h1>\n Recurso no encontrado\n</body></html>\n",minor_version);
      send(c, buffer, BUFFSIZE, 0);
      close(c);
      pthread_exit(NULL);
    }

    //Sacamos la fecha de ultima modificacion

    last_mod = gmtime(&fileStat.st_mtim.tv_sec);

    //Comprobamos si el metodo es OPTIONS, donde simplemente devolvemos los metodos que aceptamos

    if(!strncmp(method,"OPTIONS ",7) || !strncmp(method,"options ",7)){
      memset(buffer,0,strlen(buffer));
      sprintf(buffer,"HTTP/1.%d 200 OK\nAllow: OPTIONS, GET, POST\nDate: %s, %d %s %d %d:%d:%d\nServer:%s\nLast-Modified:%d/%d/%d\nContent-Lenght:%d\r\n\r\n"
      ,minor_version, dias[tm->tm_wday], tm->tm_mday, meses[tm->tm_mon], tm->tm_year + 1900, tm->tm_hour,tm->tm_min ,tm->tm_sec,server_signature,last_mod->tm_mday,last_mod->tm_mon+1,last_mod->tm_year + 1900,0);
      write(c,buffer, strlen(buffer));
      close(c);
      pthread_exit(NULL);

    }

    fstr = (char *)0;

    //Si tenemos un script para ejecutar creamos un txt donde volcamos lo devuelto anteriormente y abrimos el fichero

    if(strstr(path2,"?")){

      fstr = "text/plain";

      len = strlen(script_response);

      file_id = open("./txts/script.txt",O_RDWR | O_CREAT | O_TRUNC,S_IRWXU | S_IRWXG | S_IRWXO);
      write (file_id, script_response, strlen(script_response));
      close(file_id);
      file_id = open("./txts/script.txt", O_RDONLY);


    }else{//En otro caso tenemos que ver si nosotros soportamos la extension del fichero a procesar, para además poder averiguar el content-type y el content Lenght

      for(i=0;extensions[i].ext != 0; i++){
        len=strlen(extensions[i].ext);
        if(!strncmp(path_head+path_len-len,extensions[i].ext,len)){ // Si encontramos el tipo que queremos pasamos el filetype

          fstr = extensions[i].filetype;
          break;
        }
      }

      if(fstr == 0){
        memset(buffer,0,strlen(buffer));
        sprintf(buffer,"HTTP/1.%d 400 Forbidden\nContent-Length: 88\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>400 Forbidden</title>\n</head><body>\n<h1>Forbidden</h1></body></html>\n",minor_version);
        send(c, buffer, BUFFSIZE, 0);
        close(c);
        pthread_exit(NULL);
      }

      if((file_id = open(path_head, O_RDONLY))== -1){
        memset(buffer,0,strlen(buffer));
        sprintf(buffer,"HTTP/1.%d 404 Not Found\nContent-Length: 112\nConnection: close\nContent-Type: text/html\n\n<html><head>\n<title>404 Not Found</title>\n</head><body>\n<h1>Not Found</h1>\n Recurso no encontrado\n</body></html>\n",minor_version);
        send(c, buffer, BUFFSIZE, 0);
        close(c);
        pthread_exit(NULL);
      }

      //Veamos la longitud del fichero

      len = lseek(file_id,0,SEEK_END);
      lseek(file_id,0,SEEK_SET);


    } //Finalmente devolvemos el mensaje de OK con los datos demandados: Fecha, Servidor, Last_modified y Content_length
    memset(buffer,0,strlen(buffer));
    sprintf(buffer,"HTTP/1.%d 200 OK\nDate: %s, %d %s %d %d:%d:%d\nServer:%s\nLast-Modified:%d/%d/%d\nContent-Lenght:%ld\nContent-Type:%s\r\n\r\n"
    ,minor_version, dias[tm->tm_wday], tm->tm_mday, meses[tm->tm_mon], tm->tm_year + 1900, tm->tm_hour,tm->tm_min ,tm->tm_sec,server_signature,last_mod->tm_mday,last_mod->tm_mon+1,last_mod->tm_year + 1900,len,fstr);
    write(c,buffer, strlen(buffer));

    //Ahora enviamos el fichero
    while((rret = read(file_id,buffer,BUFFSIZE)) > 0){
      write(c,buffer,rret);
    }
    sleep(1);

    close(c);
    close(file_id);
    pthread_exit(NULL);


  return NULL;

}
