import sys
import signal
TIMEOUT = 1 # seconds
signal.signal(signal.SIGALRM, input)
signal.alarm(TIMEOUT)


try:
    for line in sys.stdin:
        name = line.split("=")[1].strip().replace("+"," ")
        print("Hola " + name + "!")
except:
    ignorar = True
