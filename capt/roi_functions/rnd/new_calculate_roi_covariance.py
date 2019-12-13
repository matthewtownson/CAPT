import time
import numpy
import itertools
from scipy.misc import comb
from astropy.io import fits
from aotools.functions import circle
from matplotlib import pyplot; pyplot.ion()
from capt.misc_functions.cross_cov import cross_cov
from capt.roi_functions.gamma_vector import gamma_vector
from capt.misc_functions.make_pupil_mask import make_pupil_mask
from capt.roi_functions.roi_referenceArrays import roi_referenceArrays
from capt.misc_functions.mapping_matrix import get_mappingMatrix, covMap_superFast, arrayRef



def calculate_roi_covariance(shwfs_centroids, allMapPos, covMapDim, n_subap, mm, sa_mm, sb_mm, selector, roi_axis, mapping_type):
	"""Takes SHWFS centroids and directly calculates the covariance map ROI (does not require going via covariance matrix).

	Parameters:
		shwfs_centroids (ndarray): SHWFS centroid measurements.
		allMapPos (ndarray): covariance map ROI coordinates within covariance map (for each GS combination).
		covMapDim (int): covariance map length in x or y (should be equal).
		n_subap (ndarray): number of sub-apertures within each SHWFS.
		mm (ndarray): Mapping Matrix.
		sa_mm (ndarray): Mapping Matrix sub-aperture numbering of SHWFS 1.
		sb_mm (ndarray): Mapping Matrix sub-aperture numbering of SHWFS 2.
		selector (ndarray): array of all covariance map combinations.
		roi_axis (str): in which axis to express ROI ('x', 'y', 'x+y' or 'x and y')
		mapping_type (str): how to calculate overall sub-aperture separation covariance ('mean' or 'median')

	Returns:
		roi_covariance (ndarray): covariance map ROI.
		time_taken (float): time taken to complete calculation."""


	timeStart = time.time()

	#subtracts mean at each sub-aperture axis (first step in calculating cross-covariance).
	shwfs_centroids = (shwfs_centroids - shwfs_centroids.mean(0)).T

	if roi_axis=='x' or roi_axis=='y' or roi_axis=='x+y':
		roi_covariance = numpy.zeros((allMapPos.shape[0]*allMapPos.shape[1], allMapPos.shape[2]))
	if roi_axis=='x and y':
		roi_covariance = numpy.zeros((allMapPos.shape[0]*allMapPos.shape[1], allMapPos.shape[2]*2))



	wfs1_n_subap = n_subap[0]
	wfs2_n_subap = n_subap[0]

	mm_subapPos = allMapPos[:, :, :, 1] + allMapPos[:, :, :, 0] * covMapDim

	for i in range(allMapPos.shape[0]):

		roi_ones = numpy.ones(allMapPos[i,:,:,0].shape)
		roi_ones[numpy.where(allMapPos[i,:,:,0]==2*covMapDim)] = 0

		num_roi_baselines = int(roi_ones.sum())
		arange_baselines = numpy.arange(num_roi_baselines)+1
		roi_ones_arange = roi_ones.copy()
		roi_ones_arange[roi_ones==1] = arange_baselines

		av = numpy.ones(roi_ones.shape)

		#integer shift for each GS combination 
		subap1_comb_shift = selector[i][0]*2*wfs1_n_subap
		subap2_comb_shift = selector[i][1]*2*wfs1_n_subap

		if roi_axis!='y':
			x1_map_centroids = numpy.zeros((roi_ones.shape[0], roi_ones.shape[1], wfs1_n_subap, shwfs_centroids.shape[1]))
			x2_map_centroids = numpy.zeros((roi_ones.shape[0], roi_ones.shape[1], wfs1_n_subap, shwfs_centroids.shape[1]))
			# roi_cov_xx = numpy.zeros(roi_ones.shape[0])

		if roi_axis!='x':
			y1_map_centroids = numpy.zeros((roi_ones.shape[0], roi_ones.shape[1], wfs1_n_subap, shwfs_centroids.shape[1]))
			y2_map_centroids = numpy.zeros((roi_ones.shape[0], roi_ones.shape[1], wfs1_n_subap, shwfs_centroids.shape[1]))
			# roi_cov_yy = numpy.zeros(roi_ones.shape)


		for j in range(1, num_roi_baselines+1):
			print(j)
			roi_loc = numpy.where(roi_ones_arange==j)
			roi_baseline = mm_subapPos[i, roi_loc[0], roi_loc[1]]
			
			subaps1 = sa_mm[:, roi_baseline][numpy.where(mm[:, roi_baseline]==1)] + subap1_comb_shift
			subaps2 = sb_mm[:, roi_baseline][numpy.where(mm[:, roi_baseline]==1)] + subap2_comb_shift
			num_subaps = subaps1.shape[0]
			av[roi_loc[0], roi_loc[1]] = num_subaps


			if roi_axis!='y':
				x1_map_centroids[roi_loc[0], roi_loc[1], :num_subaps] = shwfs_centroids[subaps1]
				x2_map_centroids[roi_loc[0], roi_loc[1], :num_subaps] = shwfs_centroids[subaps2]
				# cova = numpy.mean((shwfs_centroids[subaps1] * (shwfs_centroids[subaps2])).sum(1)/(shwfs_centroids.shape[1]-1))
				# roi_cov_xx[roi_loc[0], roi_loc[1]] = cova

			if roi_axis!='x':
				y1_map_centroids[roi_loc[0], roi_loc[1], :num_subaps] = shwfs_centroids[subaps1+wfs1_n_subap]
				y2_map_centroids[roi_loc[0], roi_loc[1], :num_subaps] = shwfs_centroids[subaps2+wfs2_n_subap]

			# 	cova = numpy.mean((shwfs_centroids[subaps1+wfs1_n_subap] * (shwfs_centroids[subaps2+wfs2_n_subap])).sum(1)/(shwfs_centroids.shape[1]-1))
			# 	roi_cov_yy[roi_loc[0], roi_loc[1]] = cova
		
		if roi_axis!='y':
			roi_cov_xx = ((x1_map_centroids*x2_map_centroids).sum(3)/(shwfs_centroids.shape[1]-1)).sum(2)/av
		if roi_axis!='x':
			roi_cov_yy = ((y1_map_centroids*y2_map_centroids).sum(3)/(shwfs_centroids.shape[1]-1)).sum(2)/av

		# cring
		if roi_axis=='x':
			roi_covariance[i*allMapPos.shape[1]:(i+1)*allMapPos.shape[1]] = roi_cov_xx
		if roi_axis=='y':
			roi_covariance[i*allMapPos.shape[1]:(i+1)*allMapPos.shape[1]] = roi_cov_yy
		if roi_axis=='x+y':
			roi_covariance[i*allMapPos.shape[1]:(i+1)*allMapPos.shape[1]] = (roi_cov_xx+roi_cov_yy)/2.
		if roi_axis=='x and y':
			roi_covariance[i*allMapPos.shape[1]:(i+1)*allMapPos.shape[1]] = numpy.hstack((roi_cov_xx, roi_cov_yy))

	timeStop = time.time()
	time_taken = timeStop - timeStart

	return roi_covariance, time_taken






if __name__=='__main__':
    n_wfs = 3
    gs_pos = numpy.array(([0,-40], [0, 0], [30,0]))
    # gs_pos = numpy.array(([0,-40], [0, 0]))
    tel_diam = 4.2
    roi_belowGround = 2
    roi_envelope = 4
    nx_subap = numpy.array([7]*n_wfs)
    n_subap = numpy.array([36]*n_wfs)

    pupil_mask = make_pupil_mask('circle', n_subap, nx_subap[0], 
            1., tel_diam)

    onesMat, wfsMat_1, wfsMat_2, allMapPos, selector, xy_separations = roi_referenceArrays(
                pupil_mask, gs_pos, tel_diam, roi_belowGround, roi_envelope)
    
    shwfs_centroids = fits.getdata('../../../../windProfiling/wind_paper/canary/data/test_fits/canary_noNoise_it10k_nl3_h0a10a20km_r00p1_L025_ws10a15a20_wd260a80a350_infScrn_wss448_gsPos0cn40a0c0a30c0.fits')#[:, :72*2]
    # shwfs_centroids = numpy.ones((10000, 36*2*3))
    covMapDim = 13
    roi_axis = 'x and y'
    mapping_type = 'mean'

    nr, nt = calculate_roi_covariance(shwfs_centroids, allMapPos, covMapDim, n_subap, onesMat, wfsMat_1, wfsMat_2, selector, roi_axis, mapping_type)
    print('Time taken: {}'.format(nt))