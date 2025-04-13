#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @copyright  this code is the property of Ubertone. 
# You may use this code for your personal, informational, non-commercial purpose. 
# You may not distribute, transmit, display, reproduce, publish, license, create derivative works from, transfer or sell any information, software, products or services based on this code.
# @author Stéphane Fischer


## Adresses et commandes de l'APF04

# numéro de commande d'inaction (tourne en boucle en attendant une commande) 
CMD_NULL = 0 
# numéro de commande pour l'arrêt de l'action en cours 
CMD_STOP = 1 
# numéro de commande mode bloquant 
CMD_PROFILE_BLOCKING = 3 
# numéro de commande mode non bloquant 
CMD_PROFILE_NON_BLOCKING = 4 
# numéro de commande mesure avec remontée des IQ 
CMD_PROFILE_IQ = 6 
# numéro de commande démarrage du mode auto 
CMD_START_AUTO = 2 
# numéro de commande verification de la configuration courante 
CMD_CHECK_CONFIG = 5 
# numéro de commande de réinitialisation du settings
CMD_INIT_SETTINGS = 7
# mesure de niveau 
CMD_MEAS_LEVEL = 20 
# numéro de commande pour un test de LED 
CMD_TEST_LED = 190 
# numéro de commande pour une mesure de température + pitch + roll 
CMD_TEST_I2C = 195 

ADDR_ACTION = 0xFFFD

ADDR_VERSION_C    = 0x0000
ADDR_VERSION_VHDL = 0xFFFE
ADDR_MODEL_YEAR   = 0x0001
ADDR_SERIAL_NUM   = 0x0002

ADDR_SOUND_SPEED_AUTO = 0x0004
ADDR_SOUND_SPEED_SET  = 0x0005

#Adresse contenant l'adresse de la configuration de séquencement ultrasons demandée par Modbus. Elle est suivie par les 3 config partagées avec Modbus.
ADDR_CONFIG_ID = 0x0010
#Adresse de départ de la zone contenant les config
ADDR_CONFIG =    0x0011
#Décallage entre chaque config
OFFSET_CONFIG = 20
SIZE_CONFIG =   17

# ----- Mesures Sensors -----
#Adresse du tanguage moyen mesuré (à destination du Modbus)
ADDR_TANGAGE = 0x0058
#Adresse du roulis moyen mesuré (à destination du Modbus)
ADDR_ROULIS = 0x0059
#Adresse de la température moyenne mesurée (à destination du Modbus)
ADDR_TEMP_MOY = 0x005A

# ---- En-tête des profils ----
ADDR_SOUND_SPEED = 0x005B
ADDR_GAIN_CA0 = 0x005C
ADDR_GAIN_CA1 = 0x005D

#Adresse des profils de vitesse et amplitude
ADDR_PROFILE_HEADER = 0x0058 # adresse du tangage, 1er sensor
SIZE_PROFILE_HEADER = 8
ADDR_PROFILE_DATA = 0x0060 # le début des données
