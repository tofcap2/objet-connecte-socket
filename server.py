#!/usr/bin/python
# -*- coding: UTF-8 -*-

from flask import Flask
from flask_socketio import SocketIO, send, emit
from flask import render_template
import threading
import os
import RPi.GPIO as GPIO
import time

# Association des broches aux devices
BR_MVT = 17
BR_LEDR = 18
BR_LEDB = 24
BR_BUZ = 22


# Temperature
class TemperatureSensor:

    def __init__(self, code):
        self.address = code
        # Chemin du fichier contenant la température (remplacer par votre valeur trouvée précédemment)
        self.device_file = '/sys/bus/w1/devices/' + code + '/w1_slave'
        self.temperatureC = 0
        self.temperatureF = 0

    # Méthode qui lit dans le fichier température
    def read_temp_raw(self):
        f = open(self.device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    #  Méthode qui lit la temperature en Celsius
    def read_temp(self):
        lines = self.read_temp_raw()
        # Tant que la première ligne ne vaut pas 'YES', on attend 0,2s
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.read_temp_raw()
        # On cherche le '=' dans la seconde ligne du fichier
        equals_pos = lines[1].find('t=')
        # Si le '=' est trouvé, on converti ce qu'il y a après le '=' en degrés Celsius
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            self.temperatureC = round(temp_c, 2)
            self.temperatureF = round(self.convertCtoF(temp_c), 2)
            return 0

    #  Méthode qui converti la temperature en Fahrenheit
    def convertCtoF(self, tc):
        return tc * 9 / 5 + 32

    # Méthode pour activer les diodes selon T°
    def diodes(self):
        GPIO.output(BR_LEDB, GPIO.LOW)
        GPIO.output(BR_LEDR, GPIO.LOW)
        if self.temperatureC < 15:
            print("Blue led On")
            GPIO.output(BR_LEDB, GPIO.HIGH)
        elif self.temperatureC > 30:
            print("red led on")
            GPIO.output(BR_LEDR, GPIO.HIGH)
        return


# Initialisation des devices
def init_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # Initialisation du détecteur de mouvements
    # Initialisation de notre GPIO 17 pour recevoir un signal
    # Contrairement à nos LEDs avec lesquelles on envoyait un signal
    GPIO.setup(BR_MVT, GPIO.IN)
    # Initialisation des leds (en mode "sortie")
    GPIO.setup(BR_LEDB, GPIO.OUT)
    GPIO.setup(BR_LEDR, GPIO.OUT)
    # Initialisation du buzzer
    GPIO.setup(BR_BUZ, GPIO.OUT)
    # Initialisation des broches pour le sensor de température
    os.system('modprobe w1-gpio')  # Allume le module 1wire
    os.system('modprobe w1-therm')  # Allume le module Temperature
    #
    sensor = TemperatureSensor('28-01131b7af492')
    sensor.read_temp()
    print("Sonde de température initialisée, T° =", sensor.temperatureC)
    return sensor


# Boucle de lecture du détecteur de mouvements
def event_loop(thermo):
    previousstate = 0
    while True:
        # Acquisition de la température et gestion leds
        thermo.read_temp()
        thermo.diodes()
        # Envoi de la temperature sur socket
        socketio.emit('temperature', [thermo.temperatureC, thermo.temperatureF], Broadcast=True)
        # Lecture du détecteur de mouvements
        currentstate = GPIO.input(BR_MVT)
        # Si le capteur est déclenché
        if currentstate == 1 and previousstate == 0:
            GPIO.output(BR_LEDB, GPIO.HIGH)
            # GPIO.output(BR_LEDR, GPIO.HIGH)
            # GPIO.output(BR_BUZ, GPIO.HIGH)     # <--- Désactivation du buzzer
            print("    Mouvement détecté !")
            socketio.emit('alert', False, Broadcast=True)
            # En enregistrer l'état
            previousstate = 1
        # Si le capteur s'est stabilisé
        elif currentstate == 0 and previousstate == 1:
            GPIO.output(BR_LEDB, GPIO.LOW)
            # GPIO.output(BR_LEDR, GPIO.LOW)
            # GPIO.output(BR_BUZ, GPIO.LOW)      # <--- Désactivation du buzzer
            print("    Prêt")
            socketio.emit('alert', True, Broadcast=True)
            previousstate = 0
        # On attends 10ms
        time.sleep(0.01)


app = Flask(__name__)
socketio = SocketIO(app)

sonde = init_gpio()


# Thread qui va permettre à notre fonction de se lancer en parallèle du serveur.
read_events = threading.Thread(target=event_loop, args=(sonde, ))
read_events.start()


@app.route("/")
def index():
    return render_template('index.html')
