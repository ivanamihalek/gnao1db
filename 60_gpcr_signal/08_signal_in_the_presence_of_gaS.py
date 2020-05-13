#!/usr/bin/python3

from bionetgen.literals import *
from bionetgen.tweakables import *
from gnuplot.literals import *
from gnuplot.tweakables import *
from utils.shellutils import *

from math import log10, pow

###############################
'''
# color fading
 	hexcolor = "004c91"
	base_color_rgb =  tuple(int(hexcolor[i:i+2], 16) for i in (0, 2, 4))
	color_rgb = base_color_rgb
	for i in range(1,number_of_runs):
		color_rgb = [min(255,round(c*1.2)) for c in color_rgb]
		hex_color = "#%02x%02x%02x" % (color_rgb[0], color_rgb[1], color_rgb[2])
'''


def write_gnuplot_input(data_table, titles, svg=False):
	colors = ["red", "orange", "yellow", "green", "cyan", "blue", "violet"]
	rootname = data_table.replace(".dat","")
	outname = f"{rootname}.gplt"
	with open(outname, "w") as outf:
		print(styling, file=outf)
		print(axes_signal, file=outf)
		print(labels, file=outf)
		print(set_gnuplot_outfile(rootname, svg=svg), file=outf)
		print("set key top right", file=outf)
		print("set yrange [-30:85]", file=outf)
		column_formatting = [f"plot '{data_table}'  u 1:($2/50*100) t '{titles[0]}'   w lines ls 1"]
		for i in range(1,len(titles)):
			color = colors[i%len(colors)]
			column_formatting.append(f"'' u 1:(${i+2}/50*100)  t '{titles[i]}'  w lines lw 3 lt rgb '{color}'")
		print(", ".join(column_formatting), file=outf)
	return outname

####################################

def add_galpha_s(default_species):
	modified = ""
	for line in default_species.split("\n"):
		line = line.strip()
		if len(line)==0: continue
		if line[:len("Galpha")]=="Galpha":
			modified += "Galpha(GPCR,GnP~GTP~GDP~none,p_site,mut~wt~mutant~s)"
		else:
			modified += line
		modified += "\n"
	return modified


def galpha_s_observables():
	obs  = "Molecules Ga_wt_to_effector @c0:Galpha(GPCR,GnP,p_site!1,mut~wt).Ga_effector(Galpha!1)\n"
	obs += "Molecules Ga_mut_to_effector @c0:Galpha(GPCR,GnP,p_site!1,mut~mutant).Ga_effector(Galpha!1)\n"
	obs += "Molecules Ga_s_to_effector @c0:Galpha(GPCR,GnP,p_site!1,mut~s).Ga_effector(Galpha!1)\n"
	return obs


def write_bngl_input(rootname, o_tweaks, s_tweaks):
	outname = f"{rootname}.bngl"

	empty_pocket_species = ""
	#
	if o_tweaks is None:
		o_type_reaction_rules = ""
	elif type(o_tweaks)==str and o_tweaks == "empty_pocket":
		empty_pocket_species  = galpha_empty_species()
		o_type_reaction_rules = reaction_rules_string(set_default_galpha_reaction_rules("wt")) + \
								reaction_rules_string(empty_pocket_reaction_rules())
	else:
		o_type_reaction_rules = reaction_rules_string(set_default_galpha_reaction_rules("wt")) + \
		                        reaction_rules_string(set_tweaked_reaction_rules("mutant", o_tweaks))

	if s_tweaks is None:
		s_type_reaction_rules = ""
	else:
		s_type_reaction_rules = reaction_rules_string(set_tweaked_reaction_rules("s", s_tweaks))


	with open(outname, "w") as outf:

		model = model_template.format(molecule_types=add_galpha_s(default_molecule_types),
		                              # double the GaS because here we have double GaO (from two genes)
		                              species=default_species + empty_pocket_species + galpha_s_species(factor=2),
		                              observables=default_observables+ galpha_s_observables(),
									  reaction_rules=(default_reaction_rules
									                + o_type_reaction_rules
									                + s_type_reaction_rules))
		outf.write(model)
		outf.write(equilibration_long)
		outf.write(agonist_ping)



	return outname


###############
def run_and_collect(bngl, rootname, o_tweaks, s_tweaks):
	# run simulation
	bngl_input  = write_bngl_input(f"{rootname}", o_tweaks, s_tweaks)
	run_bngl(bngl, bngl_input)
	# make figure (image, plot)
	gdatfile = bngl_input.replace("bngl", "gdat")
	timepoints = []
	with open(gdatfile) as inf:
		for line in inf:
			if line[0]=='#': continue
			field = line.strip().split()
			[go_wt, go_mut, gs] = [float(r) for r in field[-3:]]
			time = float(field[0])
			effector_modulation = go_wt + go_mut - gs
			timepoints.append([time,effector_modulation])
	return timepoints


###############################
def write_timepoints(outnm, timepoints):
	titles = list(timepoints.keys())
	first_title = titles[0]
	number_of_timepoints = len(timepoints[first_title])
	with open(outnm, "w") as outf:
		for t in range(number_of_timepoints):
			outf.write("%f"%timepoints[first_title][t][0]) # time
			for title in titles:
				outf.write("  %.5f"% timepoints[title][t][1]) # values
			outf.write("\n")

###############################
###############################
###############################
def sanity(bngl, gnuplot, s_tweaks, svg=False):

	rootname = "signal_GaS_sanity"
	outnm = f"{rootname}.dat"

	timepoints = {}

	o_tweaks = {}
	##########################
	#s_tweaks == None --- no GaS
	timepoints["withoutGaS"] = run_and_collect(bngl, rootname, o_tweaks, None)

	# ####
	# s_tweaks == o_tweaks --- equal  => no signal
	timepoints["GaS==GaO"] = run_and_collect(bngl, rootname, o_tweaks, o_tweaks)

	####
	# signal in the presence ow wild-type GaO
	timepoints["weakGaS/GPCR"] = run_and_collect(bngl, rootname,  o_tweaks, s_tweaks)

	write_timepoints(outnm, timepoints)
	gnuplot_input = write_gnuplot_input(outnm, list(timepoints.keys()))

	run_gnuplot(gnuplot, gnuplot_input)
	cleanup(rootname)

	print("sanity run done")


###############################
def effector_interface_scan(bngl, gnuplot, s_tweaks, svg=False):

	rootname = "signal_GaS_effector_if_scan"
	outnm = f"{rootname}.dat"

	kfs = [4.0, 2.0, 1.0, 0.4, 0.2, 0.02, 0.01]
	timepoints = {}

	######
	for kf in kfs:
		o_tweaks = {"effector": [kf, 0.1]}
		title = "effector%.2f"%kf
		timepoints[title] = run_and_collect(bngl, rootname, o_tweaks, s_tweaks)

	##########################
	write_timepoints(outnm, timepoints)
	gnuplot_input = write_gnuplot_input(outnm, list(timepoints.keys()), svg=svg)

	run_gnuplot(gnuplot, gnuplot_input)
	cleanup(rootname)

	print("effector if  run done")
	return


###############################
def catalysis_scan(bngl, gnuplot, s_tweaks, svg=False):
	rootname = "signal_GaS_cat_scan"
	outnm = f"{rootname}.dat"

	kfs = [30.0, 1.0, 0.03, 0.01, 0.003]
	timepoints = {}

	######
	for kf in kfs:
		o_tweaks = {"RGS_as_GAP": [kf, 0.0]}
		title = "cat%.3f"%kf
		timepoints[title] = run_and_collect(bngl, rootname, o_tweaks, s_tweaks)

	##########################
	write_timepoints(outnm, timepoints)
	gnuplot_input = write_gnuplot_input(outnm, list(timepoints.keys()), svg=svg)

	run_gnuplot(gnuplot, gnuplot_input)
	cleanup(rootname)

	print("cat site run done")
	return


###############################
def double_impact_scan(bngl, gnuplot, s_tweaks, svg=False):
	rootname = "signal_GaS_double_impact"
	outnm = f"{rootname}.dat"

	# kfs_catalysis = [30.0, 0.1, 0.003]
	# kfs_effector  = [4.0,  0.2, 0.02]
	kfs_catalysis = [0.3, 0.25, 0.20, 0.15]
	kfs_effector  = [2.0]

	timepoints = {}

	# wild type
	[kfc,kfe] = [30.0, 4.0]
	title = "%.3f/%.2f"%(kfc,kfe)
	o_tweaks = {"RGS_as_GAP": [kfc, 0.0], "effector": [kfe, 0.1] }
	timepoints[title] = run_and_collect(bngl, rootname,  o_tweaks, s_tweaks)

	# mutants
	for kfc in kfs_catalysis:
		for kfe in kfs_effector:
			title = "%.3f/%.2f"%(kfc,kfe)
			o_tweaks = {"RGS_as_GAP": [kfc, 0.0], "effector": [kfe, 0.1] }
			timepoints[title] = run_and_collect(bngl, rootname,  o_tweaks, s_tweaks)

	write_timepoints(outnm, timepoints)

	gnuplot_input = write_gnuplot_input(outnm, list(timepoints.keys()), svg=svg)
	run_gnuplot(gnuplot, gnuplot_input)
	cleanup(rootname)
	print("double impact run done")


###############################
def empty_pocket_scan(bngl, gnuplot, s_tweaks, svg=False):
	rootname = "signal_GaS_empty_pocket"
	outnm = f"{rootname}.dat"

	timepoints = {}

	o_tweaks = {}
	timepoints["wt"] = run_and_collect(bngl, rootname, o_tweaks, s_tweaks)

	timepoints["noGaO"] = run_and_collect(bngl, rootname, None, s_tweaks)

	timepoints["empty"] = run_and_collect(bngl, rootname,  "empty_pocket", s_tweaks)

	##########################
	write_timepoints(outnm, timepoints)

	gnuplot_input = write_gnuplot_input(outnm, list(timepoints.keys()), svg=svg)
	run_gnuplot(gnuplot, gnuplot_input)
	cleanup(rootname)
	print("empty pocket run done")


	pass

###############################
def main():

	bngl    = "/home/ivana/third/bionetgen/BNG2.pl"
	gnuplot = "/usr/bin/gnuplot"
	check_deps([bngl, gnuplot])

	s_tweaks = {"GPCR_activated": [0.01, 0.01], "GPCR_free": [0.01, 0.01]}
	# sanity(bngl, gnuplot, s_tweaks, svg=False)
	# effector_interface_scan(bngl, gnuplot, s_tweaks, svg=False)
	# catalysis_scan(bngl, gnuplot, s_tweaks, svg=False)
	# double_impact_scan(bngl, gnuplot, s_tweaks, svg=False)
	# see comments in 07
	empty_pocket_scan(bngl, gnuplot, s_tweaks, svg=False)


##########################
if __name__=="__main__":
	main()