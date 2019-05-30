/////////////////////////////////////////////////////////////////////////////////
///// Javier Martinez Rubio javier.martinezrubio@estudiante.uam.es
///// Jorge Santisteban Rivas jorge.santisteban@estudiante.uam.es
/////
/////////////////////////////////////////////////////////////////////////////////

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include <netinet/in.h>
#include <syslog.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <string.h>
#include <pthread.h>
#include "servidor.h"
#include "daemon.h"


int main() {

        int listenfd;
        pthread_t tid;

        //int daemon;
        // daemon = create_daemon();
        // if(daemon < 0){
        //   syslog(LOG_ERR, "Error demonizando el proceso");
        //   exit(-1);
        // }

        /* Contiene las llamadas a socket(), bind() y listen() */
        listenfd = tcp_listen();


        for ( ; ; ) {

                int * connfd;
                connfd = (int *)malloc(sizeof(int));

                *connfd = accept_connection(listenfd);

                pthread_create(&tid, NULL, &process_request, (void *) connfd);

        }
}
