import sys
import signal
TIMEOUT = 1 # seconds
signal.signal(signal.SIGALRM, input)
signal.alarm(TIMEOUT)


try:
    for line in sys.stdin:
        numero = (int(line.split("=")[1].strip()) * 9)/5 + 32
        print("La temperatura en Fahrenheit es: " + str(numero))
except:
    ignorar = True
