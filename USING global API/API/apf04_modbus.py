#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @copyright  this code is the property of Ubertone. 
# You may use this code for your personal, informational, non-commercial purpose. 
# You may not distribute, transmit, display, reproduce, publish, license, create derivative works from, transfer or sell any information, software, products or services based on this code.
# @author Stéphane Fischer, Marie Burckbuchler

import struct # Struct est utilisée pour extraite les données séries  
import serial # Utilisé pour récuperer les donnée vennant de la liaison Série RS485
from sys import platform
import traceback
import logging
from time import time, sleep

from .apf04_exception import apf04_error, apf04_exception
from .modbus_crc import crc16

def hex_print (_bytes):
	""" @brief print a byte array in hexadecimal string
	"""
	print (''.join('%02x'%i for i in _bytes))

class Apf04Modbus ():
	"""	@brief Modbus communication layer
	
	modbus est en big-endian (défaut)
	l'adressage est fait en 16 bits.
	"""
	def __init__(self, _baudrate=None, _dev=None):
		""" @brief Initialisation de la couche communication de l'instrument
		@param _baudrate : vitesse de communication, 57600 bits par seconde par defaut

		_baudrate peut avoir pour valeur 230400 115200 57600 ...
		"""
		# Default device address on modbus
		self.apf04_addr = 0x04

		#la lecture et l'écriture de bloc sont segmentées en blocs de 123 mots 
		# Modbus limite les blocs à un maximum de 123 mots en ecriture et 125 mots en lecture
		self.max_seg_size = 123

		logging.debug("Platform is %s", platform)

		self.usb_device = _dev

		if self.usb_device is None :
			# In case of a *nux system, we can find the port of the APF04 
			# automatically thanks to the serial.tools.list_ports library 
			# and knowing that the RS485 to USB adapter has PID:VID = 0403:6001
			if platform in ["linux","linux2","darwin","cygwin"]: # linux and Mac OS
				import serial.tools.list_ports as lPort
				reslt = lPort.comports()
				for res in reslt:
					#print(res[0], res[2])
					# TODO privilégier une lecture du PID dans RES[2] et créer un dictionnaire des PID reconnus
					if "0403:6001" in res[2] or "1A86:7523" in res[2] or "1486:5523" in res[2] or "1A86:5523" in res[2]: # dongle USB avec et sans alim
						logging.debug("APF04 detected on serial port: %s", res[2])
						self.usb_device = res[0]
					else :
						logging.debug("unknown device detected on serial port: %s (the last found will be selected)"%(res))
						self.usb_device = res[0]

			# for platform == "cygwin" and "win32", the serial port should be modified manually: 
			# for example "/dev/ttyS3" on cygwin or "COM10" on Windows

			if self.usb_device is None : # usb device could not be detected
				logging.critical("USB device cannot be detected automatically, check the wiring or specify the device port.")
				raise apf04_error (1000, "No device port defined.")

		logging.debug("usb_device is at %s with baudrate %s"%(self.usb_device, _baudrate))
		if _baudrate :
			self.connect(_baudrate)

		# In order to reduce serial latency of the linux driver, you may set the ASYNC_LOW_LATENCY flag :
		# setserial /dev/<tty_name> low_latency

		logging.debug("end init")

	def connect (self, _baudrate):
		try :
			# Create an instance of the Peacock's driver at a given baudrate
			self.ser = serial.Serial(self.usb_device, _baudrate, timeout=0.5, \
					bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0)
			# serial timeout is set to 500 ms. This can be changed by setting 
			#   self.ser.timeout to balance between performance and efficiency
		except serial.serialutil.SerialException : 
			raise apf04_error (1005, "Unable to connect to the device.")

	def __del__(self):
		""" @brief close serial port if necessary """
		try : # au cas où le constructeur a planté
			self.ser.close()
		except :
			pass

	def autobaud (self):
		""" @brief automatically detect the baudrate
		@return baudrate if detected, None instead

		If the baudrate is found, the connexion to the device is active
		WARNING : be carefull, this method is not robust, you may try several times to get the baudrate 
		"""
		# Scan available baudrates for the Peacock UVP
		for baudrate in [57600, 115200, 230400, 750000]:
			try:
				logging.debug("try if baudrate = %d"%baudrate)
				self.connect(baudrate)
				# Read the firmware version
				self.read_i16(0)
			except:
				# if failed, the baudrate is wrong
				self.ser.close()

				continue
		
			# if success, the baudrate is correct 
			return baudrate
		
		logging.debug("Fail to detect the baudrate automatically")
		return None
	
	def __check_addr_range(self, _begin, _size):
		""" @brief check if the address range is allowed
		@param _begin : addresse de début en octets
		@param _size : taille du bloc en mots (16 bits)
		"""
		addr_ram_begin =  0x0000
		addr_ram_end =    0x07FF
		addr_reg_action = 0xFFFD # also defined as ADDR_ACTION in apf04_addr_cmd.py

		# adresses des blocs mémoire :
		assert(_begin>=addr_ram_begin)
		if _begin>addr_ram_end:
			assert _begin!=addr_reg_action and _size!=1, "Warning, access at %d, size= %d bytes not allowed"%(_begin, _size)

	def __read__(self, _size, _timeout=0.0):
		""" @brief Low level read method
		@param _size number of bytes to read
		"""
		if _size == 0:
			raise apf04_error(2002, "ask to read null size data." )

		try :
			read_data = b''
			start_time = time()
			# the read of modbus is not interuptible
			while (True):
				read_data += self.ser.read(_size)
				if len (read_data) == _size or time() - start_time > _timeout:
					break

		except serial.serialutil.SerialException:
			#self.log("hardware apparently disconnected")
			#read_data = b''
			raise apf04_error(1010, "Hardware apparently disconnected." )

		if len (read_data) != _size :
			if len (read_data) == 0:
				logging.debug ("WARNING timeout, no answer from device")
				raise apf04_exception(2003, "timeout : device do not answer (please check cable connexion, timeout or baudrate)" )
			else :
				logging.debug ("WARNING, uncomplete answer from device (%d/%d)"%(len (read_data), _size))
				raise apf04_exception(2004, "timeout : uncomplete answer from device (please check timeout or baudrate) (%d/%d)"%(len (read_data), _size))

		return read_data


	############## Read functions ###############################################

	def read_i16 (self, _addr):
		""" @brief Read one word (signed 16 bits)
		@param _addr : data address (given in bytes)
		@return : integer
		"""
		# les données sont transmises en big endian (octet de poids faible en premier)
		return struct.unpack(">h",self.read_seg_16(_addr , 1))[0]


	def read_list_i16(self, _addr, _size):
		""" @brief Read several words (signed 16 bits)
		@param _addr : data address (given in bytes)
		@param _size : number of word to read
		@return : list of integers
		"""
		# TODO utiliser read_buf_i16
		return struct.unpack(">%dh"%_size,self.read_seg_16(_addr , _size))


	# TODO mettre en private
	def read_seg_16(self, _addr, _size):
		""" @brief Low level read (in a single modbus frame)
		@param _addr : data address (given in bytes)
		@param _size : number of word to read
		@return : byte array
		"""
		assert (_size <= self.max_seg_size)  # segment de 125 mots (max en lecture)
		
		logging.debug ("reading %d words at %d"%(_size, _addr))
		# on utilise la fonction modbus 3 pour la lecture des octets
		#self.__check_addr_range(_addr, 2 * _size)

		# request read 
		read_query = struct.pack(">BBHh",self.apf04_addr, 0x03, _addr, _size )
		read_query += struct.pack(">H",crc16 (read_query) )
		#print ("read query = ")
		#hex_print(read_query)
		try :
			self.ser.write(read_query)
		except serial.serialutil.SerialException:
			#self.log("hardware apparently disconnected")
			# TODO traiter les différentes erreurs, se mettre en 3 MBaud sur R0W (bcp de buffer overflow !)
			raise apf04_error(1010, "Hardware apparently disconnected." )

		# read answer
		slave_response = self.__read__(3)

		if slave_response[1] != 3:
			logging.info ("WARNING error while reading %s"%slave_response)

		slave_response += self.__read__(slave_response[2]+2)

		#print ("slave answer = ")
		#hex_print(slave_response)

		# check crc
		#print ("%X"%crc16 (slave_response[0:-2]))
		#print ("%X"%struct.unpack(">H",slave_response[-2:]))
		assert (crc16 (slave_response[0:-2]) == struct.unpack(">H",slave_response[-2:])[0])

		return slave_response[3:-2]


	def read_buf_i16 (self, _addr , _size):
		""" @brief Read buffer 
		@param _addr : data address (given in bytes)
		@param _size : number of word to read
		@return : byte array

		Note : data are transmitted in big endian
		"""
		data = b''
		addr = _addr
		remind = _size
		logging.debug ("reading %d words at %d"%(_size, _addr))
		while remind :
			logging.debug ("remind = %s ; self.max_seg_size = %s ; div : %s"%(remind, self.max_seg_size, remind/self.max_seg_size))
			if remind/self.max_seg_size>=1:
				logging.debug ("read max_seg_size")
				seg_size=self.max_seg_size
			else :
				seg_size = remind
				logging.debug ("read remind")
			data+=self.read_seg_16(addr , seg_size)
			addr+=seg_size #  addr en mots de 16 bits
			remind-=seg_size
		#print( "__Read_buf : %d readed"%(int(addr - _addr)) )
		return data


	############## Write functions ##############################################

	def write_i16 (self, _value, _addr, _timeout=0.0):
		""" @brief Write one word (signed 16 bits)
		@param _value : value of the word
		@param _addr : destination data address (given in bytes)
		"""
		try:
			self.write_buf_i16 ([_value], _addr, _timeout)
		except apf04_exception as ae:
			raise ae # apf04_exception are simply raised upper
		except :
			print(traceback.format_exc())
			raise apf04_error(3000, "write_i16 : FAIL to write 0%04x at %d\n"%(_value, _addr))


	def write_buf_i16 (self, _data, _addr, _timeout=0.0):
		""" @brief Write buffer 
		@param _data : list of words (max size : 123 words)
		@param _addr : data address (given in bytes)
		"""
		# ATTENTION ici on ne gère pas de boucle sur un "write_seg_16" car on n'a pas besoin d'écrire de gros blocs de données
		# segmenter en blocs de 123 mots (max en ecriture)
		assert (len(_data)<=self.max_seg_size)
		try:
			# request read 
			write_query = struct.pack(">BBHhB%sh"%len(_data),self.apf04_addr, 16, _addr, len(_data), 2*len(_data), *_data )
			write_query += struct.pack(">H",crc16 (write_query) )

			try:
				#print (write_query)
				self.ser.write(write_query)
			except serial.serialutil.SerialException:
				logging.error("hardware apparently disconnected")
				raise apf04_error(3004, "write_buf_i16 : hardware apparently disconnected")

			# read answer
			slave_response = self.__read__(2, _timeout)
			# TODO 1 : format de la trame d'erreur et codes d'erreurs effectivement traités
			if slave_response[1] == 16 :
				slave_response += self.__read__(6)
				# TODO sur le principe il faudrait vérifier que le bon nombre de mots a été écrit
			else:
				# TODO traiter les erreurs selon doc 
				size = struct.unpack("B",self.__read__(1))[0]
				print ("size following : %d"%size)
				self.__read__(size)
				print("error while writting")
				print (slave_response)

		except apf04_exception as ae:
			raise ae # apf04_exception are simply raised upper
		except :
			print(traceback.format_exc())
			raise apf04_error(3001, "write_buf_i16 : Fail to write")
