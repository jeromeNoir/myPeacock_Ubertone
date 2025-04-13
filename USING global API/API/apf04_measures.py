#!/usr/bin/env python
# -*- coding: UTF_8 -*-

# @copyright  this code is the property of Ubertone.
# You may use this code for your personal, informational, non-commercial purpose.
# You may not distribute, transmit, display, reproduce, publish, license, create derivative works from, transfer or sell any information, software, products or services based on this code.
# @author Marie Burckbuchler
# @date 20 Aout 2020

from array import *
from struct import calcsize, unpack
from math import sqrt, pi, pow

from .apf_timestamp import decode_timestamp
from .apf04_gain import _convert_code2dB_trunc, convert_code2dB_m, convert_code2dB, calc_gain


# @brief Utilise une frame pour récupérer un profil voulu (format UDT005)
# # une ligne de profil dans raw UDT005 contient
# le raw profile contient un header puis le profil codé
# ce header contient des scalaires qu'il faut aussi enregistrer
# @param _data : le bloc de données binaire
def extract_measures (data, config_hw) :
	size = len(data)
	data_dict = {
		"velocity" : [],
		"amplitude" : [],
		"snr" : [],
		"std" : []
	}
	# Attention, pas de ref à lire à ce stade
	# Lecture du timestamp
	data_dict["timestamp"], offset = decode_timestamp( data )

	head_size = offset
	
	scalars_size = calcsize('hhhhhhhh')
	
	data_dict['pitch'], data_dict['roll'], data_dict['temp'], \
	sound_speed, data_dict['gain_ca0'], data_dict['gain_ca1'], \
	data_dict['noise_g_max'], data_dict['noise_g_mid'] \
	    = unpack('hhhhhhhh', data[head_size:head_size+scalars_size])

	# A few acoustic parameters which are needed for the following calculations
	n_vol = config_hw.n_vol
	c_prf = config_hw.c_prf
	n_avg = config_hw.n_avg
	#r_dvol = to_dict(self.config_hw[self.current_config - 1].config_hw, sound_speed)['r_dvol']
	#r_vol1 = to_dict(self.config_hw[self.current_config - 1].config_hw, sound_speed)['r_vol1']
	blind_ca0 = config_hw.blind_ca0
	blind_ca1 = config_hw.blind_ca1

	if (size-(head_size+scalars_size))/4/2 != n_vol:
		raise Exception('volume number', "expected %d volumes, but profile data contains %d"%(n_vol, ((size-(head_size+scalars_size))/4/2)))

	tab_size = calcsize('h')
	offset = head_size+scalars_size
	for i in range(n_vol):
		data_dict['velocity'].append(unpack('h', data[offset: offset + tab_size])[0])
		offset += calcsize('h')
		data_dict['std'].append(unpack('h', data[offset: offset + tab_size])[0])
		offset += calcsize('h')
		data_dict['amplitude'].append(unpack('h', data[offset: offset + tab_size])[0])
		offset += calcsize('h')
		data_dict['snr'].append(unpack('h', data[offset: offset + tab_size])[0])
		offset += calcsize('h')

	# conversion des valeurs codées:
	# Note: il faut convertir les scalaires après pour avoir les gains tels que pour la conversion du profil d'echo
	conversion_profile(data_dict, sound_speed, n_vol, n_avg, c_prf, data_dict['gain_ca0'], data_dict['gain_ca1'], blind_ca0, blind_ca1)
	#conversion_scalar(scalars_dict)
	#conversion_us_scalar(scalars_us_dict, n_avg, r_dvol, r_vol1)

	return data_dict

def conversion_profile(data_dict, sound_speed, n_vol, n_avg, c_prf, gain_ca0, gain_ca1, blind_ca0, blind_ca1):
	sat = array('f')
	ny_jump = array('f')

	v_ref = 1.25
	fact_code2velocity = sound_speed / (c_prf * 65535.)
	# print("factor code to velocity %f"%fact_code2velocity)
	tab_gain = calc_gain(n_vol, gain_ca0, gain_ca1, blind_ca0, blind_ca1)
	for i in range(n_vol):
		if data_dict['std'][i] < 0:
			ny_jump.append(True)
			data_dict['std'][i] *= -1
		else:
			ny_jump.append(False)
		if data_dict['amplitude'][i] < 0:
			sat.append(True)
			data_dict['amplitude'][i] *= -1
		else:
			sat.append(False)
		data_dict['std'][i] = data_dict['std'][i]*fact_code2velocity
		data_dict['velocity'][i] *= fact_code2velocity
		data_dict['snr'][i] /= 10.
		data_dict['amplitude'][i] *= ((v_ref*2)/4096) / sqrt(n_avg) / tab_gain[i]

def conversion_scalar(data_dict):

	# convert temperature to Kelvin
	data_dict["temp"] += 273.15

	# convert angles to red
	data_dict['pitch'] *= pi/180.
	data_dict['roll'] *= pi/180.

def conversion_us_scalar(self, data_dict, n_avg, r_dvol, r_vol1):

	# convert coded gain to dB and dB/m
	data_dict["a1"] = convert_code2dB_m(data_dict["gain_ca1"], r_dvol)
	del data_dict["gain_ca1"]
	data_dict["a0"] = convert_code2dB(data_dict["gain_ca0"])-data_dict["a1"]*r_vol1
	del data_dict["gain_ca0"]

	# convert coded noise values to V
	v_ref = 1.25
	gain = pow(10, ((_convert_code2dB_trunc(1241)) / 20.)) # gain max
	data_dict["noise_g_high"] = sqrt(data_dict["noise_g_max"]) * ((v_ref*2)/4096) / sqrt(n_avg) / gain
	del data_dict["noise_g_max"]

	gain = pow(10, ((_convert_code2dB_trunc(993)) / 20.)) # gain max - 10dB
	data_dict["noise_g_low"] = sqrt(data_dict["noise_g_mid"]) * ((v_ref*2)/4096) / sqrt(n_avg) / gain
	del data_dict["noise_g_mid"]