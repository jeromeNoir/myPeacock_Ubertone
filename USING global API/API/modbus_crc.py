#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @author Stéphane Fischer

def __generate_crc16_table():
	""" Generates a crc16 lookup table
	.. note:: This will only be generated once

	src : pymodbus
	"""
	result = []
	for byte in range(256):
		crc = 0x0000
		for _ in range(8):
			if (byte ^ crc) & 0x0001:
				crc = (crc >> 1) ^ 0xa001
			else: crc >>= 1
			byte >>= 1
		result.append(crc)
	return result

__crc16_table = __generate_crc16_table()


def crc16(data):
	""" Computes a crc16 on the passed in string. For modbus,
	this is only used on the binary serial protocols (in this
	case RTU).
	The difference between modbus's crc16 and a normal crc16
	is that modbus starts the crc value out at 0xffff.
	:param data: The data to create a crc16 of
	:returns: The calculated CRC

	src : pymodbus
	
	vérification du CRC16 (modbus) : 
	https://crccalc.com/
	https://www.lammertbies.nl/comm/info/crc-calculation
	"""
	crc = 0xffff
	for a in data:
		idx = __crc16_table[(crc ^ a) & 0xff]
		crc = ((crc >> 8) & 0xff) ^ idx
	swapped = ((crc << 8) & 0xff00) | ((crc >> 8) & 0x00ff)
	return swapped
