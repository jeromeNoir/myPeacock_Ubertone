#!/usr/bin/env python
# -*- coding: UTF_8 -*-
# from types import IntType

def cast_int16 (_value):
	_value = int(round(_value))
	if _value > 32767:
		_value = 32767
	elif _value < -32768:
		_value = -32768
	return _value
	
def cast_uint16 (_value):
	_value = int(round(_value))
	if _value < 0:
		_value = 0
	if _value > 65535:
		_value = 65535
	return _value