'''module to set up particle phase part of box model, calls on init_water_partit to initiate water partitioning with seed particles and wall'''

import numpy as np
import Size_distributions # custom library - see source code
from init_water_partit import init_water_partit
import scipy.constants as si
import ipdb

def pp_intro(y, num_speci, Pybel_objects, TEMP, H2Oi,
			mfp, accom_coeff, y_mw, surfT, 
			DStar_org, RH, num_sb, lowersize, uppersize, pconc, 
			nuc_comp, testf, std, mean_rad, therm_sp,
			Cw, y_dens, Psat, core_diss, kgwt, space_mode, corei, spec_namelist, 
			act_coeff):
	
			
	# inputs -----------------------------------
	# TEMP - temperature (K) in chamber at start of experiment
	# y_mw - molecular weight (g/mol) of components (num_speci, 1)
	# num_sb - number of size bins (excluding wall)
	# lowersize - lowest size bin radius bound (um)
	# uppersize - largest size bin radius bound (um)
	# pconc - starting particle concentration (# particle/cc (air)) - if scalar then
	# gets split between size bins in Size_distributions call, or if an array, elements 
	# are allocated to corresponding size bins
	# nuc_comp - name of the nucleating component
	# testf - test flag to say whether in normal mode (0) or test mode for front.py (1)
	#       or test mode for pp_intro.py
	# std - geometric standard deviation of the particle number concentration 
	# 		(dimensionless)
	# mean_rad - either the mean radius (um) of particles in lognormal number-size 
	#			distribution (in which case pconc should be scalar), or mean radius of
	#			particles where just one size bin present (in which case pconc is also
	#			scalar)
	# Cw - concentration of wall (molecules/cc (air))
	# y_dens - liquid density of components (kg/m3) (num_speci, 1)
	# Psat - saturation vapour pressure of components (molecules/cc (air))
	# core_diss - core dissociation constant
	# kgwt - mass transfer coefficient for vapour-wall partitioning (/s)
	# space_mode - string specifying whether to space size bins logarithmically or 
	# linearly
	# corei - index of component comprising seed particles
	# spec_namelist - names of components noted in chemical scheme file
	# act_coeff - activity coefficient of components
	# ------------------------------------------
	
	if testf==1: # in test mode
		return(0,0,0,0,0,0,0,0,0,0,0,0) # return dummies
	
	# if mean radius not stated explicitly calculate from size ranges (um)
	if mean_rad == -1.0e6 and num_sb>0:
		if lowersize>0.0:
			mean_rad = 10**((np.log10(lowersize)+np.log10(uppersize))/2.0)
		if lowersize == 0.0:
			mean_rad = 10**((np.log10(uppersize))/2.0)
	
	# index of nucleating component
	if len(nuc_comp)>0:
		print('whoop', nuc_comp, nuc_comp[0])
		nuc_compi = spec_namelist.index(nuc_comp[0])
		nuc_comp = np.empty(1, dtype=int)
		nuc_comp[0] = nuc_compi
	
	R_gas = si.R # ideal gas constant (kg.m2.s-2.K-1.mol-1)
	NA = si.Avogadro # Avogadro's number (molecules/mol)
	
	
	if num_sb == 0: # create dummy variables if no size bins
		N_perbin = np.zeros((1,1))
		x = np.zeros((1,1))
		Varr = np.zeros((1,1))
		Vbou = np.zeros((1,1))
		rad0 = np.zeros((1,1))
		Vol0 = np.zeros((1,1))
		rbou = np.zeros((1,1))
		upper_bin_rad_amp = 1.0e6
	
	# create a number concentration for a lognormal distribution (particles/cc (air))
	# this is where gas partitioning to wall set up
	if testf==2:
		print('calling Size_distributions.lognormal')
	# if multiple size bins, this call will assume a lognormal distribution if initial 
	# particle concentration is a scalar, or will assign particles to size bins if
	# initial particle concentration is an array
	if num_sb>1:
		
		# set scale and standard deviation input for lognormal probability distribution 
		# function, following guidance here: 
		# http://all-geo.org/volcan01010/2013/09/how-to-use-lognormal-distributions-in-python/
		scale = np.exp(np.log(mean_rad))
		std = np.log(std)
		loc = 0.0 # no shift
		
		[N_perbin, x, rbou, Vbou, Varr, upper_bin_rad_amp] = Size_distributions.lognormal(num_sb, 
									pconc, std, lowersize, uppersize, loc, scale, 
									space_mode)
# 		print(rbou)
# 		ipdb.set_trace()
		if testf==2:
			print('finished with Size_distributions.lognormal')
		
	if num_sb == 1:
		N_perbin = np.array((pconc)) # (# particles/cc (air))
		x = np.zeros(1)
		
		meansize = mean_rad # mean radius of this size bin (um)
		
		x[0] = meansize
		# extend uppersize to reduce chance of particles growing beyond this
		upper_bin_rad_amp = 1.0e6
		uppersize = uppersize*upper_bin_rad_amp
		# volume bounds of size bin (um3)
		Vbou = np.array(((lowersize**3.0)*(4.0/3.0)*np.pi, 
						(uppersize**3.0)*(4.0/3.0)*np.pi))
		# volume of single particle (um3)
		Varr = np.zeros((1,1))
		Varr[0] = (meansize**3.0)*(4.0/3.0)*np.pi
		# radius bounds of size bin (um)
		rbou = ((Vbou*3.0)/(4.0*np.pi))**(1.0/3.0)
	
	# set first volume and radius bound to zero, thereby allowing shrinkage to zero in the 
	# smallest bin
	# remember initial first radius bound for saving
	rbou00 = rbou[0]

	Vbou[0] = 0.0
	rbou[0] = 0.0 # this reversed in saving.py back to rbou00
	
	
	if num_sb>0:
		# remember the radii (um) and volumes (um3) at size bin centre before water 
		# partitioning
		rad0 = np.zeros((len(x)))
		rad0[:] = x[:]
		Vol0 = np.zeros((len(Varr)))
		Vol0[:] = Varr[:]
	
	num_sb += 1 # add one to size bin number to account for wall

	# append particle-phase concentrations of species to y (molecules/cc (air))
	# note, there's a very small amount of each species in the particle phase to
	# prevent nan errors later on
	y = np.append(y, np.ones((num_sb*num_speci))*1.0e-40)
	
	# molar volume (multiply y_dens by 1e-3 to convert from kg/m3 to g/cc and give
	# MV in units cc/mol)
	MV = (y_mw/(y_dens*1.0e-3)).reshape(num_speci, 1)
	Vperbin = ((N_perbin*(4.0/3.0)*np.pi*x**3.0))
	
	if sum(pconc)>0.0: # account for seed material concentration
	
		# core concentration in size bins (molecules/cc (air)):
		# core mass concentration in each size bin (molecules/cc (air))
		y[num_speci+corei:(num_speci*(num_sb)+corei):num_speci] = ((y_dens[corei]*1.0e-3)*
								(Varr*1.0e-12*N_perbin)*(1.0/y_mw[corei])*NA)
	
	if testf==2:
		print('calling init_water_partit.py')

	# allow water to equilibrate with particles and walls
	[y, Varr, x, N_perbin] = init_water_partit(x, y, H2Oi, Psat, mfp, num_sb, num_speci, 
					accom_coeff, y_mw, surfT, R_gas, TEMP, NA, y_dens, 
					N_perbin, DStar_org, RH, core_diss, Varr, Vbou, Vol0, MV,
					therm_sp, Cw, pconc, kgwt, corei, act_coeff)

	if testf==2:
		print('finished with init_water_partit.py')
	
	# print mass concentration of particles (scale y_dens by 1e-3 to convert from kg/m3
	# to g/cm3)
	if num_sb>0:
		mass_conc = 0.0
		for i in range(num_sb-1): # as size bin now account for wall too
			mass_conc += sum((y_dens[:, 0]*1.0e-3)*((y[num_speci*(i+1):num_speci*(i+2)]/si.N_A)*MV[:,0]))
			mass_conc -= (y_dens[int(H2Oi), 0]*1.0e-3)*((y[num_speci*(i+1)+int(H2Oi)]/si.N_A)*MV[int(H2Oi), 0])
		mass_conc = mass_conc*1.0e12 # convert from g/cc (air) to ug/m3 (air)
		if mass_conc < 1.0e-10:
			mass_conc = 0.0
		print(str('Total dry (no water) mass concentration of particles at start of simulation is ' + str(mass_conc) + ' ug/m3 (air)'))
	else:
		print('No particle size bins detected, simulation will not include particles')
	return(y, N_perbin, x, Varr, Vbou, rad0, Vol0, rbou, MV, num_sb, nuc_comp, rbou00, 
			upper_bin_rad_amp)