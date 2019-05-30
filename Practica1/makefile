CCFLAGS = -Wextra -std=gnu11 -Wall -g


SRC = ./src
INCLIB = ./includes

OBJS =	main_server.o \
		servidor.o \
		daemon.o \
		picohttpparser.o


all : main_server
	rm -f *.o

main_server: $(OBJS)
	gcc $(CCFLAGS) -o server $^ -lpthread -lconfuse

main_server.o:	$(SRC)/main_server.c
	gcc $(CCFLAGS) -I./includes -c $(SRC)/main_server.c

servidor.o:	$(SRC)/servidor.c $(INCLIB)/servidor.h
	gcc $(CCFLAGS) -I./includes -c $(SRC)/servidor.c

daemon.o:	$(SRC)/daemon.c $(INCLIB)/daemon.h
	gcc $(CCFLAGS) -I./includes -c $(SRC)/daemon.c

picohttpparser.o:	$(SRC)/picohttpparser.c $(INCLIB)/picohttpparser.h
	gcc $(CCFLAGS) -I./includes -c $(SRC)/picohttpparser.c



clean:
	rm -f *.o server
