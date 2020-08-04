'''module for calculating reaction rate coefficients, automatically generated by eqn_parser'''

##################################################################################################### 
# Python function to hold expressions for calculating rate coefficients # 
#    Copyright (C) 2017  David Topping : david.topping@manchester.ac.uk                             # 
#                                      : davetopp80@gmail.com                                       # 
#    Personal website: davetoppingsci.com                                                           # 
#                                                                                                   # 
#                                                                                                   # 
#                                                                                                   # 
##################################################################################################### 
# File Created at 2020-08-04 15:35:26.548281

import numpy
import PhotolysisRates

def evaluate_rates(RO2, H2O, TEMP, lightm, time, lat, lon, act_flux_path, DayOfYear, M, N2, O2, photo_par_file, Jlen):

	# ------------------------------------------------------------------------	# inputs:
	# M - third body concentration (molecules/cc (air))
	# N2 - nitrogen concentration (molecules/cc (air))
	# O2 - oxygen concentration (molecules/cc (air))
	# RO2: specified by the chemical scheme. eg: subset of MCM
	# H2O, TEMP: given by the user
	# lightm: given by the user and is 0 for lights off and 1 for on
	# reaction rate coefficients and their names parsed in eqn_parser.py 
	# Jlen - number of photolysis reactions
	# calculate generic reaction rate coefficients given by chemical scheme

	# estimate and append photolysis rates
	J = PhotolysisRates.PhotolysisCalculation(time, lat, lon, TEMP, act_flux_path, DayOfYear, photo_par_file, Jlen)

	if lightm == 0:
		J = [0]*len(J)
	rate_values = numpy.zeros(0)
	# reac_coef has been formatted so that python can recognize it
	
	return rate_values
