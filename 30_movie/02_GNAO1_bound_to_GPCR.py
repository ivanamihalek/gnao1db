#!  /usr/local/bin/pymol -qc
'''
[* 02] (We see the GPCR in the clump representation in the mebrane with G-tetramer docked.
Camera moves down to focus on G-tetramer.
'''

# to tfm in pymol https://pymolwiki.org/index.php/Transform_selection
# to get the tfm needed: copy object by hand, than follow this to get the tfm
# see here https://pymolwiki.org/index.php/Get_object_matrix
# print(tfm) to have ti spit on the commandline in gui


from time import time

from utils.pymol_pieces import *
from utils.pymol_constants import *
from utils.pheno_scene_views import *
from utils.utils import *

frames_home = "/home/ivana/projects/gnao1db/30_movie/movie"

ac_tfm = (0.9867311120033264, -0.011104182340204716, -0.16198275983333588,
          -137.9303598023693, 0.004471524152904749, 0.9991387128829956,
          -0.04125393182039261, -17.250826810116003, 0.16230133175849915,
           0.039982229471206665, 0.985930860042572, 35.708624462858666,
           0.0, 0.0, 0.0, 1.0)

@cmd.extend
def sequence():

	production = True

	dirname = "02_gpcr"
	frame_basename = "seq02frm"

	time0 = time()

	for dep in [structure_home, frames_home]:
		if not os.path.exists(dep):
			print(dep, "not found")
			return

	subdir_prep(frames_home, dirname)
	pymol_chdir("{}/{}".format(frames_home, dirname))

	# the initial scene containing the GPCR-bound G-trimer
	all_structures = ["GPCR", "gnao-gpcr", "gbeta", "ggamma", "AC", "lipid", "substrate"]
	load_structures(structure_home, structure_filename, all_structures)
	cmd.transform_selection("AC", ac_tfm)
	make_GDP("substrate", "substrate_GDP")
	# move the GTP out of the cat pocket - we'll return it later
	# as we are re-creatin the process of activation
	# cmd.transform_selection("substrate", GTP_tfm)
	cmd.bg_color("white")

	if production: # run without gui

		# for struct in ["GPCR", "gnao-gpcr", "gbeta", "ggamma", "AC"]:
		# 	cmd.show_as("cartoon", struct)
		clump_representation(["GPCR"], "orange", "GPCR")
		clump_representation(["gnao-gpcr"], "lightblue", "gnao-gpcr")
		clump_representation(["gbeta"], "magenta", "gbeta")
		cmd.remove("ggamma and resi 52-62") # disordered tail creates a hole in rendered surface
		clump_representation(["ggamma"], "palegreen", "ggamma")
		clump_representation(["substrate_GDP"], "marine", "substrate_GDP", small_molecule=True)

		style_lipid("lipid")

		frame_offset = 0
		cmd.set_view(sequence_02_view[0])
		cmd.png(frame_basename + str(frame_offset).zfill(3), width=1920, height=1080, ray=True)
		# interpolate to the view from below - makes pngs
		frame_offset += 1
		frame_offset = view_interpolate(sequence_02_view[0], sequence_02_view[1], frame_basename,
		                                number_of_frames=15, frameno_offset=frame_offset)


	else: # run from gui

		for struct in ["GPCR", "gnao-gpcr", "gbeta", "ggamma", "AC"]:
			cmd.show_as("cartoon", struct)


	print("done in %d secs" %(time()-time0))

	return


###################################
sequence()
