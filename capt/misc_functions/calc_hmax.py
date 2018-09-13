import numpy
import itertools
from scipy.special import comb
from capt.misc_functions.mapping_matrix import get_mappingMatrix, covMap_superFast
from capt.map_functions.covMap_fromMatrix import covMap_fromMatrix
from capt.misc_functions.make_pupil_mask import make_pupil_mask
from matplotlib import pyplot; pyplot.ion()
from capt.roi_functions.gamma_vector import gamma_vector

def calc_hmax(pupil_mask, n_subap, gs_pos, tel_diam, air_mass):
	"""Calculates minimum and maximum h_max for a given GS asterism
	- determining altitudes which are visible within across covariance map separations.
	This code DOES NOT take into account the profile projected by the GS asterism 
	i.e. assumes maximum separation distance is tel_diam.

	Parameters:
		pupil_mask (ndarray): shwfs mask.
		n_subap (ndarray): no. of sub-apertures within each shwfs.
		gs_pos (ndarray): GS asterism in telescope FoV.
		tel_diam (float): telescope diameter.
		air_mass (float): observation's air mass.

	Returns:
		float: minimum GS asterism h_max.
		float: maximum GS asterism h_max."""

	nx_subap = pupil_mask.shape[0]
	w = tel_diam/nx_subap
	# grid = numpy.ones((n_subap[0], n_subap[0]))
	# mm, mmc, md = get_mappingMatrix(pupil_mask, grid)
	# c_map = covMap_superFast((2*nx_subap)-1, grid, mm, mmc, md)
	# blank_c_map = c_map.copy() * 0

	minAlt = 1e20
	maxAlt = 0.
	combs = int(comb(gs_pos.shape[0], 2, exact=True))
	selector = numpy.array((range(gs_pos.shape[0])))
	selector = numpy.array((list(itertools.combinations(selector, 2)))) 
	for i in range(combs):
		gs_pos0 = gs_pos[selector[i, 0]]
		gs_pos1 = gs_pos[selector[i, 1]]
		# gs_pos_comb = numpy.array((gs_pos0, gs_pos1))
		# vector, b, theta = gamma_vector(blank_c_map, 'False', gs_pos_comb, 0, 0)
		# vector_subaps = c_map[vector[0,:,0], vector[0,:,1]]
		# tot_vector_subaps = vector_subaps.sum()
		# pyplot.imshow(b)
		
		sep_sq = (gs_pos0-gs_pos1)**2
		sep = numpy.sqrt(numpy.sum(sep_sq))
		sep *= (1/3600.) * (numpy.pi/180.)

		maxObsAlt = (tel_diam)/sep
		maxObsAlt /= air_mass

		if maxObsAlt>maxAlt:
			maxAlt = maxObsAlt
		if maxObsAlt<minAlt:
			minAlt = maxObsAlt

	return minAlt, maxAlt


if __name__=='__main__':
	nwfs = 3
	gs_pos = numpy.array(([-20,0], [20,0], [0,0]))
	# gs_pos = numpy.array(([0,0], [28.28,28.28]))
	tel_diam = 4.2
	air_mass = 1 
	n_subap = numpy.array([36]*nwfs)
	nx_subap = numpy.array([7]*nwfs)
	pupil_mask = make_pupil_mask('circle', n_subap, nx_subap[0], 1., tel_diam)

	mn, mx = calc_hmax(pupil_mask, n_subap, gs_pos, tel_diam, air_mass)