#!/usr/bin/python
# -*- coding: UTF-8 -*-

from flask import Flask
from flask_socketio import SocketIO, send, emit
from flask import render_template
import threading
import RPi.GPIO as GPIO
import time

# Association des broches aux devices
BR_LUM = 27
BR_LEDR = 18
BR_LEDB = 24
BR_BUZ = 22


# Temperature
class LightSensor:

    def __init__(self):
        self.light = 0

    # Méthode lecture lumière
    def read_light(self):
        # initialisation de la variable de lumière
        lightcount = 0
        GPIO.setup(BR_LUM, GPIO.OUT)
        GPIO.output(BR_LUM, GPIO.LOW)
        time.sleep(0.1)    # on draine la charge du condensateur
        GPIO.setup(BR_LUM, GPIO.IN)
        # Tant que la broche lit ‘off’ on incrémente notre variable
        while GPIO.input(BR_LUM) == GPIO.LOW:
            lightcount += 1
        self.light = lightcount
        return lightcount

    # Méthode pour activer les diodes selon la lumière
    def diodes(self):
        GPIO.output(BR_LEDB, GPIO.LOW)
        GPIO.output(BR_LEDR, GPIO.LOW)
        if self.light > 200:
            GPIO.output(BR_LEDB, GPIO.HIGH)
        elif self.light < 50:
            GPIO.output(BR_LEDR, GPIO.HIGH)
        return


# Initialisation des devices
def init_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # Initialisation des leds (en mode "sortie")
    GPIO.setup(BR_LEDB, GPIO.OUT)
    GPIO.setup(BR_LEDR, GPIO.OUT)
    # Initialisation du buzzer
    GPIO.setup(BR_BUZ, GPIO.OUT)
    sensor = LightSensor()
    sensor.read_light()
    print("Détecteur de lumière initialisé, L =", sensor.light)
    return sensor


# Boucle de lecture du détecteur de mouvements
def event_loop(lux):
    while True:
        # Acquisition de la lumière et gestion des leds
        lux.read_light()
        lux.diodes()
        # Envoi de la temperature sur socket
        socketio.emit('lumen', lux.light, Broadcast=True)
        time.sleep(1)


app = Flask(__name__)
socketio = SocketIO(app)

sonde = init_gpio()


# Thread qui va permettre à notre fonction de se lancer en parallèle du serveur.
read_events = threading.Thread(target=event_loop, args=(sonde, ))
read_events.start()


@app.route("/")
def index():
    return render_template('index.html')
