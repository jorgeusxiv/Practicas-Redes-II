/////////////////////////////////////////////////////////////////////////////////
///// Javier Martinez Rubio javier.martinezrubio@estudiante.uam.es
///// Jorge Santisteban Rivas jorge.santisteban@estudiante.uam.es
/////
/////////////////////////////////////////////////////////////////////////////////


#include <syslog.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include "daemon.h"

int create_daemon(){

  pid_t pid;

  if((pid=fork()) != 0){ //Creamos el proceso hijo y matamos el proceso padre
    exit(-1);
  }

  umask(0); //Cambia el de modo de ficheros
  setlogmask(LOG_UPTO(LOG_INFO)); //Abrimos el system logger
  openlog("Server", LOG_CONS | LOG_PID |LOG_NDELAY, LOG_LOCAL3); //Abrimos una conexion con el system logger
  syslog(LOG_ERR, "Iniciando un nuevo servidor.");

  if(setsid() < 0){ //Hacemos que el hijo sea el lider de sesion
    syslog(LOG_ERR, "Error creando un nuevo SID para el proceso hijo");
    exit(-2);
  }

  if((chdir("/")) < 0){ //Cambiamos el directorio donde estamos trabajando
    syslog(LOG_ERR, "Error cambiando el directorio de trabajo");
    exit(-3);
  }


  syslog(LOG_INFO, "Cerrando descriptores de ficheros");

  close(STDIN_FILENO);
  close(STDOUT_FILENO);
  close(STDERR_FILENO);


  return(0);

}
