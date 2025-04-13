#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @copyright  this code is the property of Ubertone. 
# You may use this code for your personal, informational, non-commercial purpose. 
# You may not distribute, transmit, display, reproduce, publish, license, create derivative works from, transfer or sell any information, software, products or services based on this code.
# @author Stéphane Fischer

from datetime import datetime
import struct
import logging

from .apf04_modbus import Apf04Modbus
from .apf04_addr_cmd import *
from .apf04_config_hw import ConfigHw
from .apf_timestamp import encode_timestamp
from .apf04_exception import apf04_exception

# TODO gérer ici les erreur spécifiques au HW

class Apf04Driver (Apf04Modbus):
	""" @brief gère l'instrument APF04
	"""
	# TODO : tester la com dans un init par une lecture de la version 
	def __init__(self, _baudrate, _f_sys, _dev=None):
		self.f_sys=_f_sys
		Apf04Modbus.__init__(self, _baudrate, _dev)

	def new_config (self):
		"""  @brief create an empty config
		"""
		# TODO pourrait aussi s'appeler create_config ou empty_config @marie : un avis ?
		return ConfigHw(self.f_sys)

	def read_config (self, _id_config=0):
		""" @brief lecture des paramètres d'une configuration
		    @param _id_config : identifiant de la configuration [0..2] (par défaut la config n°1/3) 
				
				principalement utilisé pour relire la config après un check_config
				"""
		self.config = ConfigHw(self.f_sys)
		self.config.id_config = _id_config
		#	tous les paramètres des settings sont en signé
		self.config.from_list(self.read_list_i16(ADDR_CONFIG+_id_config*OFFSET_CONFIG, SIZE_CONFIG)) # en mots
		return self.config
	
	# TODO .to_list() à faire par l'appelant ? APF04Driver ne connait pas config_hw ou passer config_hw en self.config (actuellement au niveau au dessus) ?
	def write_config (self, _config, _id_config):
		""" @brief écriture des paramètres d'une configuration
		    @param _config : configuration (de type ConfigHw)
		    @param _id_config : identifiant de la configuration [0..2]
		"""
		logging.debug("%s"%(_config.to_list()))
		self.write_buf_i16(_config.to_list(), ADDR_CONFIG+_id_config*OFFSET_CONFIG)

	# DEFINI LA CONFIG 0 UTILISEE PAR L'APPAREIL
	# _config = [0..2]
	def select_config (self, _id_config):
		logging.debug("selecting config %d [0..N-1]"%(_id_config))
		self.write_i16(_id_config, ADDR_CONFIG_ID)

	def read_version (self):
		""" @brief Lecture des versions C et VHDL
		"""
		self.version_vhdl = self.read_i16(ADDR_VERSION_VHDL)
		self.version_c = self.read_i16(ADDR_VERSION_C)
		logging.debug("Version VHDL=%s", self.version_vhdl)
		logging.debug("Version C=%s", self.version_c)
		if self.version_c < 45:
			print ("WARNING firmware version %d do not provide noise measurements in profile's header" % self.version_c)
			self.model = 0
			self.year = 2018
			self.serial_num = 0
		else :
			model_year = self.read_i16(ADDR_MODEL_YEAR)
			self.model = (model_year & 0xFF00)>>8
			self.year = 2000 + (model_year & 0x00FF)

			if self.model == 0x01 :
				logging.debug("Model is Peacock UVP")
			else :
				logging.info("Warning, model (id %s) is not defined"%self.model)	
			logging.debug("Year of production = %s", self.year)
			
			self.serial_num = self.read_i16(ADDR_SERIAL_NUM)
			logging.debug("Serial number=%s", self.serial_num)
		
		return self.version_vhdl, self.version_c

	def write_sound_speed (self, sound_speed=1480, sound_speed_auto=False):
		""" @brief Writing of the sound speed global parameter in RAM
		"""
		addr_ss_auto = ADDR_SOUND_SPEED_AUTO
		addr_ss_set = ADDR_SOUND_SPEED_SET
		# fix for firmware prior to 45
		if self.version_c < 45:
			addr_ss_auto -= 2
			addr_ss_set -= 2

		if sound_speed_auto:
			self.write_i16(1, addr_ss_auto)
		else:
			self.write_i16(0, addr_ss_auto)
			self.write_i16(sound_speed, addr_ss_set)
#JN 22.04.2021:
#read the sound speed from the board to convert the config param to setting param
	def read_sound_speed (self, sound_speed_auto=False):
		""" @brief Reading of the sound speed global parameter from RAM
		"""
		addr_ss_auto = ADDR_SOUND_SPEED_AUTO
		addr_ss_set = ADDR_SOUND_SPEED_SET
		# fix for firmware prior to 45
		if self.version_c < 45:
			addr_ss_auto -= 2
			addr_ss_set -= 2

		if sound_speed_auto:
			sound_speed=self.read_i16(addr_ss_auto)
		else:
			sound_speed=self.read_i16(addr_ss_set)

		return sound_speed 
	def __action_cmd__(self, _cmd, _timeout=0.0):
		""" @brief generic action function 
		send a command asking for a given action. Unless specific case,
		the function is released when the action is finished. The timeout 
		should be set consequently. """
		try:
			self.write_i16(_cmd, ADDR_ACTION, _timeout)
		except apf04_exception as ae:
			logging.info("apf04_exception catched with command %s with timeout %e"%(_cmd, _timeout))
			raise ae

	def act_stop (self):
		""" @brief Stop the measurement (only in non blocking mode)"""
		self.__action_cmd__(CMD_STOP, 5.0)

	def act_meas_I2C (self):
		""" @brief Make one measure of pitch, roll and temp. Those values are then updated in the RAM.
		"""
		self.__action_cmd__(CMD_TEST_I2C, 2.0)

	def act_test_led (self):
		self.__action_cmd__(CMD_TEST_LED, 1.5)
		# timeout set to 1.5 seconds to let the Led blink
		
	def act_meas_IQ (self):
		self.__action_cmd__(CMD_PROFILE_IQ) # TODO timeout
		
	def act_meas_profile (self, _timeout=0.):
		""" @brief start to measure a block of profils
		    @param _timeout maximum delay to get an answer from the board 
		"""
		# get UTC timestamp just before strating the measurements
		self.timestamp_profile = datetime.utcnow()

		logging.debug ("setting timeout to %f"%_timeout)
		self.__action_cmd__(CMD_PROFILE_BLOCKING, _timeout)
		
		
	def act_check_config (self):
		self.__action_cmd__(CMD_CHECK_CONFIG, 0.2)

	def act_start_auto_mode (self):
		self.__action_cmd__(CMD_START_AUTO) # TODO timeout

	def read_temp (self):
		return self.read_i16(ADDR_TEMP_MOY)

	def read_pitch (self):
		return self.read_i16(ADDR_TANGAGE)
		
	def read_profile (self, _n_vol):
		logging.debug("timestamp: %s"%self.timestamp_profile)

		#logging.debug("pitch: %s, roll: %s,"%(self.read_i16(ADDR_TANGAGE), self.read_i16(ADDR_ROULIS)))
		#logging.debug("pitch: %s, roll: %s, temps: %s, sound_speed: %s, ca0: %s, ca1: %s"%(self.read_i16(ADDR_TANGAGE), self.read_i16(ADDR_ROULIS), self.read_i16(ADDR_TEMP_MOY), self.read_i16(ADDR_SOUND_SPEED), self.read_i16(ADDR_GAIN_CA0), self.read_i16(ADDR_GAIN_CA1)))
		data_list = self.read_buf_i16(ADDR_PROFILE_HEADER, SIZE_PROFILE_HEADER + _n_vol*4) 

		logging.debug("processing+transfert delay = %fs"%(datetime.utcnow()-self.timestamp_profile).total_seconds())

		# on passe en litte endian (les données initiales sont en big endian)
		# traitement < 1ms pour 50 cellules sur macbook pro
		data_packed = struct.pack('<%sh'%int(len(data_list)/2), \
			*struct.unpack('>%sh'%int(len(data_list)/2), data_list))
		logging.debug("pack string = '%s'"%'>%sh'%int(len(data_list)/2))

		logging.debug("processing+transfert+swap delay = %fs"%(datetime.utcnow()-self.timestamp_profile).total_seconds())

		return encode_timestamp(self.timestamp_profile) + data_packed
