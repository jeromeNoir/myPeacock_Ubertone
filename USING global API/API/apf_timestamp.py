#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @copyright  this code is the property of Ubertone.
# You may use this code for your personal, informational, non-commercial purpose.
# You may not distribute, transmit, display, reproduce, publish, license, create derivative works from, transfer or sell any information, software, products or services based on this code.
# @author Stéphane Fischer

from datetime import datetime, timezone, timedelta
from time import mktime
from struct import pack, unpack, calcsize

# temps ZERO (Ubertone Epoch)
UBT_EPOCH = datetime(2020, 1, 1, tzinfo=timezone.utc)

def encode_timestamp(_datetime):
	"""Encode timestamp in words

	Args:
		_datetime: timestap

	Returns:
		bytearray representing the encoded timestamp
	  
	  ubertone's epoch :
	  - 01/01/2020 starting from version 2.01
	"""
	
	timestamp = mktime(_datetime.timetuple()) + _datetime.microsecond/1e6 - mktime(UBT_EPOCH.timetuple())
	#       timestamp (epoch)    2*int16  Epoch en secondes MSB + LSB (*)
	#       timestamp extension  int16    En millisecondes
	
	# DIRECTIVE WARNING : attention à ne pas mélanger int16 et int32. En effet la machine est susceptible d'aligner les données sur 32 bits.
	#   du coup un pack "hih" vas donner le premier short (16 bits) suivi par 0x0000 puis le second entier (int32) !!!
	# TODO forcer l'endianness ?
	return pack("hhh", int((int(timestamp)>>15)&0x0000FFFF), int(int(timestamp)&0x00007FFF),\
										  int(1000.*(timestamp%1)))

def decode_timestamp(_encoded_datetime):
	"""Extract timestamp from a byte array

	Args:
		_encoded_datetime: 

	Returns:
		timestamp and offset
	"""
	timestamp_size = calcsize('hhh')
	nsec_pF, nsec_pf, msec = unpack('hhh', _encoded_datetime[0:timestamp_size])
	return UBT_EPOCH+timedelta(seconds=(int(nsec_pF)<<15)|nsec_pf, milliseconds=msec), timestamp_size
