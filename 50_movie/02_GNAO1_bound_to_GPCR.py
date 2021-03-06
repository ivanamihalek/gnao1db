#!  /usr/local/bin/pymol -qc
'''
[* 02] (We see the GPCR in the clump representation in the mebrane with G-tetramer docked.
Camera moves down to focus on G-tetramer.
'''

# to tfm in pymol https://pymolwiki.org/index.php/Transform_selection
# to get the tfm needed: copy object by hand, than follow this to get the tfm
# see here https://pymolwiki.org/index.php/Get_object_matrix
# print(tfm) to have ti spit on the commandline in gui
import sys
from time import time

from utils.pymol_constants import *

from utils.pymol_pieces import *
from utils.pheno_scene_views import *
from utils.utils import *

frames_home = "/home/ivana/projects/gnao1db/50_movie/movie"


@cmd.extend
def sequence():

	# careful: starting production mode with gui can freeze teh desktop
	production = (sys.argv[1] == '-qc')

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
	all_structures = ["GPCR", "gnao-gpcr", "gbeta", "ggamma", "lipid", "substrate"]
	load_structures(structure_home, structure_filename, all_structures)
	make_GDP("substrate", "substrate-GDP")
	# move the GTP out of the cat pocket - we'll return it later
	# as we are re-creatin the process of activation
	# cmd.transform_selection("substrate", GTP_tfm)
	cmd.bg_color("white")

	if production: # run without gui

		cmd.remove("ggamma and resi 52-62") # disordered tail creates a hole in rendered surface
		for structure  in ["GPCR", "gnao-gpcr", "gbeta", "ggamma"]:
			clump_representation([structure], mol_color[structure], structure)
		style_substrate("substrate-GDP", mol_color["substrate-GDP"])
		style_lipid("lipid")

		# interpolate to the view from below - makes pngs
		frame_offset = 1
		frame_offset = view_interpolate(sequence_02_view[0], sequence_02_view[1], frame_basename,
		                                number_of_frames=32, frameno_offset=frame_offset, easing_type=("sine", "inout"))


	else: # run from gui

		for struct in ["GPCR", "gnao-gpcr", "gbeta", "ggamma"]:
			cmd.show_as("cartoon", struct)


	print("done in %d secs" %(time()-time0))

	return


###################################
sequence()
