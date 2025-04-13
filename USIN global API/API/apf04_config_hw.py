#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @copyright  this code is the property of Ubertone.
# You may use this code for your personal, informational, non-commercial purpose.
# You may not distribute, transmit, display, reproduce, publish, license, create derivative works from, transfer or sell any information, software, products or services based on this code.
# @author Marie Burckbuchler, Stéphane Fischer

import logging
from math import ceil

from .apf04_gain import convert_dB_m2code, convert_code2dB_m, convert_code2dB, convert_dB2code, APF04_CODE_MAX_APPLIED
#from .ap_exception import ap_protocol_error
from .apf_type import cast_int16, cast_uint16

#ap_protocol_error(3300, "Warning: v_min has to be in [-Nyquist_Range, 0].")

class ConfigHw ():
	# @brief To instantiate an object of this class, you can give no parameter to get attributes set to zero, or you can give a settings, the ID of the config and the sound_speed to use.
	# TODO (san 21/04/2020) il serait surement plus approprié, plus propre (et plus compact) de stocker la configHW dans un dict 
	#      accompagné d'une liste donnant l'ordre des valeurs en mémoire :
	#      order = ['div_f0', 'n_tir', 'c_prf', 'n_em', 'n_vol', 'c_vol1', 'c_dvol' ...]  
	def __init__(self, _f_sys):
		
		logging.debug("f_sys = %.1e"%_f_sys)
		self.f_sys = _f_sys
		
		self.div_f0 = 0
		self.n_tir = 0
		self.c_prf = 0
		self.n_em = 0
		self.n_vol = 0
		self.c_vol1 = 0
		self.c_dvol = 0
		self.gain_ca0 = 0
		self.gain_ca1 = 0
		self.tr = 0
		self.phi_min = 0
		self.method = 0
		self.reserved1 = 0
		self.reserved2 = 0
		self.n_avg = 0
		self.blind_ca0 = 0
		self.blind_ca1 = 0

	#JN:
	#date: 22.04.2021
	#mods: _sound_speed is now given by _config_dict['soundspeed']	
	def set(self, _config_data, _sound_speed=1480, _gain_blind_zone=None):
		"""
		docstring
		"""
		if type(_config_data) is dict :
			logging.debug ("call from_dict")
			#old code
			#self.from_dict(_config_data, _sound_speed, _gain_blind_zone)
			#new code
			self.from_dict(_config_data, _gain_blind_zone)
		elif type(_config_data) is list :
			logging.debug ("call from_dict")
			self.from_list(_config_data)
		else :
			logging.info("wrong data type for _config_data")
		
		return self


	# @brief Chargement des paramètres d'une configuration acoustique
	# On rétrocalcule à chaque fois la valeur en paramètre utilisateur par rapport au paramètre hardware (pour prendre en compte les modifications dues à des cast etc, lorsqu'il y a interdépendance entre paramètres.)
	# @param _data : ref sur objet de la classe data donnant accès aux configs et au sound speed et à la fréquency système.
	# @param meas_ultrasound_key : clé de la configuration en cours.
	# appelé uniquement par le constructeur

	#JN:
	#date: 22.04.2021
	#mods: _sound_speed is now given by _config_dict['soundspeed']
	#old code
	#def from_dict(self, _config_dict, _sound_speed=1480, _gain_blind_zone=None):
	#


	def from_dict(self, _config_dict, _sound_speed=1480, _gain_blind_zone=None):
		#JN:get sound speed from the configuration dictionnary directly
		_sound_speed=_config_dict['soundspeed']
		#
		logging.debug("start import dict")
		#JN old Code: self.div_f0 = cast_int16(self.f_sys / _config_dict['f0'] -1)
		self.div_f0 = cast_int16(self.f_sys / _config_dict['f_emission'] -1)
		
		f0 = self.f_sys / (self.div_f0+1)

		self.c_prf = cast_int16(f0 / _config_dict['prf'])
		#prf = _config_dict['f0']/self.c_prf
		prf = _config_dict['f_emission']/self.c_prf

		#JN: OLD code: self.n_tir = cast_int16(_config_dict['n_ech'])
		self.n_tir = cast_int16(_config_dict['nb_emission_per_profile'])

		#JN:
		#date: 22.04.2021: 
		#mods: n_em is set directly and r_em is recalculated.  
		# comment the initial code -> replace with new

		#old code
		# if _config_dict['gate_size'] == 0:
		# 	self.n_em = cast_int16(0)
		# else:
		# 	self.n_em = cast_int16(round(2./_sound_speed * f0 *_config_dict['gate_size']))
		# 	if self.n_em == 0:
		# 		self.n_em = cast_int16(1)

		#new code
		if _config_dict['nb_cycles_per_emission']>self.c_prf/20:
			self.n_em = cast_int16(self.c_prf/20)
			print('number of emission is too large, set to n_em_max=%i'%cast_int16(self.c_prf/20))
		else:
			self.n_em = cast_int16(_config_dict['nb_cycles_per_emission'])
		#
		print (_sound_speed)
		r_em = _sound_speed/(2.*f0)*self.n_em

		#self.n_vol = cast_int16(_config_dict['n_vol'])
		self.n_vol = cast_int16(_config_dict['nb_gates'])

		#self.c_vol1 = cast_uint16(2./_sound_speed * f0 * (_config_dict['r_vol1'] - r_em/2.))
		self.c_vol1 = cast_uint16(2./_sound_speed * f0 * (_config_dict['position_first_gate'] - r_em/2.))
		r_vol1 = _sound_speed/(2.*f0)*self.c_vol1 + r_em/2.

		#JN:
		#date:22.04.2021
		#mods: since setting n_em, r_em not known a priori. Change r_dvol from resolution to overlap
		#r_dvol=0.5 means r_dvol=0.5xr_em (50% overlap)
		#r_dvol=1 means r_dvol=r_em (no overlap)
		#r_dvol=2 means r_dvol=2xr_em (no overlap)

		#old code
		#self.c_dvol = cast_int16(2./_sound_speed * f0 *_config_dict['gate_distance'])

		#new code
		self.c_dvol = cast_int16(2./_sound_speed * f0 *_config_dict['overlap']*r_em)
		#


		c_dvol_min =int(ceil(0.75e-6 * f0 + 1))
		if self.c_dvol < c_dvol_min: # constraint from APF04 hardware
			self.c_dvol = cast_int16(c_dvol_min)
		r_dvol = _sound_speed/(2.*f0)*self.c_dvol
		
		self.gain_ca1 = cast_int16(convert_dB_m2code(_config_dict['gain_function']['a1'], r_dvol))
		a1 = convert_code2dB_m(self.gain_ca1, r_dvol)

		if _gain_blind_zone :
			self.blind_ca1 = cast_int16(convert_dB_m2code(_gain_blind_zone['a1_max'], r_dvol))
		else :
			self.blind_ca1 = 0
	#	Pour a1 max, on ne rétrocalcule pas dans le const, puisque c'est un const et que cette valeur n'est utile que quelques lignes plus loin dans le calcul du ca0_max.
		a1_max = convert_code2dB_m(self.blind_ca1, r_dvol)
		
		r_ny = _sound_speed*prf/(2*f0)
		self.phi_min = cast_int16(_config_dict['v_min']*65535/(2*r_ny))

		self.gain_ca0 = cast_int16(convert_dB2code(_config_dict['gain_function']['a0'] + r_vol1*a1))
		if _gain_blind_zone :
			self.blind_ca0 = cast_int16(convert_dB2code(_gain_blind_zone['a0_max'] + r_vol1 * a1_max))
		else :
			self.blind_ca0 = APF04_CODE_MAX_APPLIED

		# on a vu plus simple comme écriture ...
		self.tr = cast_int16(int(''.join(ele for ele in _config_dict['tr_out'] if ele.isdigit())))-1

		if _config_dict['method'] == "ppc_cont":
			self.burst_mode = False
		else:	# Donc method == "corr_ampl"
			self.burst_mode = True
		self.phase_coding = _config_dict['phase_coding']
		self.static_echo_filter = _config_dict['static_echo_filter']
		self.gain_auto = _config_dict['gain_function']['auto']
		
		# Pour retourner choisir le paramètres methode traitement, remplacer la dernière parenthèse par un 2 ou un 0.
		if(self.gain_auto == True):
			logging.debug("gain auto is set")
			# +2048 pour activer l'I2C (pour firmware >C51)
			self.method = cast_int16(512 + (cast_int16(self.static_echo_filter)<<8) + (cast_int16(self.phase_coding)<<2) + cast_int16(self.burst_mode) + (cast_int16(self.burst_mode)<<1))
		else:
			logging.debug("gain is set to manual")
			self.method = cast_int16(0 + (cast_int16(self.static_echo_filter)<<8) + (cast_int16(self.phase_coding)<<2) + cast_int16(self.burst_mode) + (cast_int16(self.burst_mode)<<1))

		#JN: Old Code: self.n_avg = cast_int16(_config_dict['n_profile'])
		self.n_avg = cast_int16(_config_dict['nb_profile_average'])

		self.reserved1 = 0
		self.reserved2 = 0
		
	# @brief Chargement des paramètres à partir d'un tableau lu dans le Hardware
	# @param _param_table : tableau des valeurs dans l'ordre indiqué ci-dessous. cf. aussi dt_protocole de l'APF04.
	def from_list(self, _param_table):
		logging.debug("start import list")
		if len(_param_table)==17:
			self.div_f0 = _param_table[0]
			self.n_tir = _param_table[1]
			self.c_prf = _param_table[2]
			self.n_em = _param_table[3]
			self.n_vol = _param_table[4]
			self.c_vol1 = _param_table[5]
			self.c_dvol = _param_table[6]
			self.gain_ca0 = _param_table[7]
			self.gain_ca1 = _param_table[8]
			self.tr = _param_table[9]
			self.phi_min = _param_table[10]
			self.method = _param_table[11]
			self.n_avg = _param_table[14]
			self.blind_ca0 = _param_table[15]
			self.blind_ca1 = _param_table[16]

			# Other useful parameters (coded in method bits array) :
			if (self.method & 0x0001) == 0:
				self.burst_mode = False
			else:
				self.burst_mode = True
			# en self.method & 0x0002, il y a l'indication de méthode traitement.
			if (self.method & 0x0004) == 0:
				self.phase_coding = False
			else:
				self.phase_coding = True
			if (self.method & 0x0100) == 0:
				self.static_echo_filter = False
			else:
				self.static_echo_filter = True
			if (self.method & 0x0200) == 0:
				self.gain_auto = False
			else:
				self.gain_auto = True
		#else :
		#	logging.info("WARNING")
		# TODO raise error
	
	# @brief Update the config with the current config_hw.
	# @param _sound_speed: information of the sound speed

	#OLD CODE STEPHANE
	# def to_dict(self, _sound_speed):
	# 	# TODO si div_f0 : pas initialisé -> ERROR
	# 	config = {}
	# 	f0_ = (self.f_sys/(self.div_f0+1))
	# 	config['f0'] = f0_
	# 	config['tr_out'] = 'tr'+str(self.tr+1)
	# 	config['prf'] = f0_/self.c_prf
	# 	config['r_vol1'] = _sound_speed*((self.c_vol1+self.n_em/2.)/f0_)/2.
	# 	config['r_dvol'] = _sound_speed*(self.c_dvol/f0_)/2.
	# 	config['n_vol'] = self.n_vol
	# 	config['r_em'] = _sound_speed*(self.n_em/f0_)/2.
	# 	config['n_ech'] = self.n_tir
	# 	if self.burst_mode:
	# 		config['method'] = "corr_ampl"
	# 	else:
	# 		config['method'] = "ppc_cont"
	# 	# en self.method & 0x0002, il y a l'indication de méthode traitement.
	# 	if self.phase_coding:
	# 		config['phase_coding'] = True
	# 	else:
	# 		config['phase_coding'] = False
	# 	if self.static_echo_filter:
	# 		config['static_echo_filter'] = True
	# 	else:
	# 		config['static_echo_filter'] = False
	# 	config['gain_function'] = {}
	# 	if self.gain_auto:
	# 		config['gain_function']['auto'] = True
	# 	else:
	# 		config['gain_function']['auto'] = False
	# 	config['n_profile'] = self.n_avg
		
	# 	rdvol = _sound_speed*(self.c_dvol/f0_)/2.
	# 	rvol1 = _sound_speed*((self.c_vol1+self.n_em/2.)/f0_)/2.

	# 	a1 = convert_code2dB_m(self.gain_ca1, rdvol)
	# 	config['gain_function']['a0'] = convert_code2dB(self.gain_ca0)-a1*rvol1
	# 	config['gain_function']['a1'] = a1

	# 	config['v_min'] = 2*_sound_speed*config['prf']*self.phi_min/(2*65535*f0_)
	# 	return config
	def to_dict(self, _sound_speed):
		# TODO si div_f0 : pas initialisé -> ERROR
		config = {}
		f0_ = (self.f_sys/(self.div_f0+1))
		config['soundspeed']=_sound_speed
		config['f_emission'] = f0_
		config['tr_out'] = 'tr'+str(self.tr+1)
		config['prf'] = f0_/self.c_prf

		#JN:
		#date: 22.04.2021: 
		#mods: add n_em to dict config.  
		#new code
		config['nb_cycles_per_emission'] = self.n_em
		config['overlap']=self.c_dvol/self.n_em
		#

		config['nb_emission_per_profile'] = self.n_tir
		config['position_first_gate'] = _sound_speed*((self.c_vol1+self.n_em/2.)/f0_)/2.
		config['gate_distance'] = _sound_speed*(self.c_dvol/f0_)/2.
		config['nb_gates'] = self.n_vol
		config['gate_size'] = _sound_speed*(self.n_em/f0_)/2.

		if self.burst_mode:
			config['method'] = "corr_ampl"
		else:
			config['method'] = "ppc_cont"
		# en self.method & 0x0002, il y a l'indication de méthode traitement.
		if self.phase_coding:
			config['phase_coding'] = True
		else:
			config['phase_coding'] = False
		if self.static_echo_filter:
			config['static_echo_filter'] = True
		else:
			config['static_echo_filter'] = False
		config['gain_function'] = {}
		if self.gain_auto:
			config['gain_function']['auto'] = True
		else:
			config['gain_function']['auto'] = False
		config['nb_profile_average'] = self.n_avg
		
		rdvol = _sound_speed*(self.c_dvol/f0_)/2.
		rvol1 = _sound_speed*((self.c_vol1+self.n_em/2.)/f0_)/2.

		a1 = convert_code2dB_m(self.gain_ca1, rdvol)
		config['gain_function']['a0'] = convert_code2dB(self.gain_ca0)-a1*rvol1
		config['gain_function']['a1'] = a1

		config['v_min'] = 2*_sound_speed*config['prf']*self.phi_min/(2*65535*f0_)
		return config
	
	def get_bloc_duration(self):
		#TODO san 27/09/2017 attention ça augmente si n_vol> 100
		return self.n_tir * (self.n_avg) * (self.div_f0 + 1) * self.c_prf / self.f_sys


	# @brief Affichage du paramétrage en cours.
	def print_config_hw(self):
		logging.debug("div_F0 = %s", self.div_f0)
		logging.debug("n_tir = %s", self.n_tir)
		logging.debug("c_PRF = %s", self.c_prf)
		logging.debug("n_Em = %s", self.n_em)
		logging.debug("n_vol = %s", self.n_vol)
		logging.debug("c_vol1 = %s", self.c_vol1)
		logging.debug("c_dvol = %s", self.c_dvol)
		logging.debug("CA0_dac = %s", self.gain_ca0)
		logging.debug("CA1_dac = %s", self.gain_ca1)
		logging.debug("CA0_max_dac = %s", self.blind_ca0)
		logging.debug("CA1_max_dac = %s", self.blind_ca1)
		logging.debug("Cs_Tr = %s", self.tr)
		logging.debug("phi_min = %s", self.phi_min)
		logging.debug("Methode = %s", self.method)
		logging.debug("n_avg = %s", self.n_avg)
		# logging.debug("gain auto : %s", self.gain_auto)
		# logging.debug("static_echo_fiter : %s", self.static_echo_filter)
		# logging.debug("burst_mode : %s", self.burst_mode)
		# logging.debug("phase_coding : %s", self.phase_coding)


	def to_list(self):
		buf=[]
		buf.append(self.div_f0)
		buf.append(self.n_tir)
		buf.append(self.c_prf)
		buf.append(self.n_em)
		buf.append(self.n_vol)
		buf.append(self.c_vol1)
		buf.append(self.c_dvol)
		buf.append(self.gain_ca0)
		buf.append(self.gain_ca1)
		buf.append(self.tr)
		buf.append(self.phi_min)
		buf.append(self.method)
		buf.append(self.reserved1)
		buf.append(self.reserved2)
		buf.append(self.n_avg)
		buf.append(self.blind_ca0)
		buf.append(self.blind_ca1)
		return buf
	

	def __str__(self): 
		return str(self.__dict__)


	def __eq__(self, other):
		if not isinstance(other, type(self)):
			logging.info("NOT IMPLEMENTED")
			return NotImplemented
		
		return ((self.div_f0, self.tr, self.method, self.c_prf, self.phi_min, self.n_tir, self.c_vol1, self.c_dvol, self.n_em, self.n_vol, self.reserved1, self.reserved2, self.n_avg, self.gain_ca0, self.gain_ca1, self.blind_ca0, self.blind_ca1) == (other.div_f0, other.tr, other.method, other.c_prf, other.phi_min, other.n_tir, other.c_vol1, other.c_dvol, other.n_em, other.n_vol, other.reserved1, other.reserved2, other.n_avg, other.gain_ca0, other.gain_ca1, other.blind_ca0, other.blind_ca1))


	def __ne__(self, other):
		return not self == other
