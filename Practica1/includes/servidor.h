/////////////////////////////////////////////////////////////////////////////////
///// Javier Martinez Rubio javier.martinezrubio@estudiante.uam.es
///// Jorge Santisteban Rivas jorge.santisteban@estudiante.uam.es
/////
/////////////////////////////////////////////////////////////////////////////////

#ifndef __SERVIDOR_H__
#define __SERVIDOR_H__


#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include <netinet/in.h>
#include <syslog.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <string.h>


int tcp_listen();
int accept_connection(int sockval);
void * process_request(void * connval);

#endif
