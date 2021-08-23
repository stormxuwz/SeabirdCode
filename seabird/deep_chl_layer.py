"""
Class of DCL
"""

from .models.model_peak import Peak
import numpy as np

class DCL(object):
	def __init__(self,config):
		"""
		Class initialization
		Args:
			config: dictionary, the configuration
		"""
		self.config  = config
		self.all_peaks = None
		self.dcl_index = None
		self.model = None
		
	def adjust_concentration(self, dcl_depth, rawdata):
		"""
		Function to correct the fluorescence concentration by searching 
		the maximum fluorescence in the raw data within 1 meter around the 
		detected depth.
		Args:
			DCLDepth: the detected DCL depth
			rawData: a pandas dataframe, with Depth and Fluorescence as columns
		Returns:
			corrected chlorophyll concentration
		"""
		values = rawdata.loc[(rawdata.Depth < dcl_depth + 0.5) & (rawdata.Depth > dcl_depth - 0.5), "Fluorescence"]
		return np.max(values)

	def detect(self, data, rawdata, chl_peak_min_depth=None, chl_peak_upper_depth_boundary=None, save_model=True):
		"""
		function to detect DCL
		Args:
			data: preprocessed data
			rawData: rawData
			peakMinDepth: the minimum depth DCM exists. 
				Could be the depth of LEP. None means 
			peakUpperDepthBoundary: the upper boundary of the DCL shape, i.e. the starting 
				depth to calculate the total chlorophyll concentration in DCL
			saveModel: whether to save the peak model, which contains all the detected peak information, such
				as the fitted values, the depth of other peaks, etc. 
		Returns:
			features: a dictionary containing detected DCL information
		"""
		
		# define all the related DCL features
		features = {
		"DCL_depth":None, # the DCM depth
		"peakNums":None, # the total number of peaks detected
		"DCL_conc":None, # the concentration at DCM
		"DCL_exists":None,  # whether DCL exists

		# "DCL_upperConc":None, # the concentration at the upper boundary of the DCL peak
		# "DCL_bottomConc":None, # the concentration at the lower boundary of the DCL peak
		
		"DCL_upperDepth_fit":None, # the depth of the upper boundary of the DCL peak by fitting Gaussian models
		"DCL_bottomDepth_fit":None, # the depth of the lower boundary of the DCL peak by fitting Gaussian models
		
		"DCL_leftShapeFitErr":None,  # the fitting error of the upper shape
		"DCL_rightShapeFitErr":None,  # the fitting error of the lower shape

		"DCL_concProp_fit":None,	# the concentration ratio in DCL

		"allConc":None, # the sum of all fluorescence concentration
		
		"DCL_leftSigma":None,  # the std of the Gaussian shape fitted for upper shape
		"DCL_rightSigma":None,  # the std of the Gaussian shape fitted for lower shape
		"allConc_upper": None # the sum of concentrations above a depth threshold
		}

		# initialize peak model
		model = Peak(self.config["algorithm"]["peak"]) 
		
		if save_model: # save model
			self.model = model
		
		model.fit_predict(data.Fluorescence) # Detect the peak
		
		self.all_peaks = model.all_peaks # a np.array storing
				
		features["allConc"] = np.sum((data.Fluorescence))

		chl_peak_upper_depth_boundary_index = np.searchsorted(data.Depth, chl_peak_upper_depth_boundary) + 1 # find the boundary index
		features["allConc_upper"] = np.sum(data.Fluorescence[:chl_peak_upper_depth_boundary_index])

		if self.all_peaks is None or self.all_peaks.shape[0] < 1:
			# no peak exists
			features["peakNums"] = 0
			features["DCL_exists"] = 0
			return features
		
		else:
			features["peakNums"] = self.all_peaks.shape[0] 
			chl_peak_depths = np.array(data.Depth[self.all_peaks.peakIndex]) # the peak depth
			
			if chl_peak_min_depth is not None and all(chl_peak_depths < chl_peak_min_depth):
				# No peaks exists below the depth threshold
				features["DCL_exists"] = 0
				return features

			# choose which peak represents DCM
			if chl_peak_min_depth is None:
				dcl_idx = np.argmax(np.array(data.Fluorescence[self.all_peaks.peakIndex]))
			else:
				available_peak_index = np.array(self.all_peaks.peakIndex * (chl_peak_depths > chl_peak_min_depth))
				dcl_idx = np.argmax(np.array(data.Fluorescence[available_peak_index])) # choose the maximum concentration as the peak
			

			dcl_idx = int(dcl_idx)
			self.dcl_idx = dcl_idx

			features["DCL_exists"] = 1
			features["DCL_depth"] = chl_peak_depths[dcl_idx]
			
			# features["DCL_conc"] = data.Fluorescence[self.allPeaks.peakIndex[DCL_idx]]
			features["DCL_conc"] = self.adjust_concentration(chl_peak_depths[dcl_idx], rawdata) # correct the peak concentration

			features["DCL_leftShapeFitErr"] = self.all_peaks.leftErr[dcl_idx]
			features["DCL_rightShapeFitErr"] = self.all_peaks.rightErr[dcl_idx]

			features["DCL_leftSigma"] = self.all_peaks.leftSigma[dcl_idx]
			features["DCL_rightSigma"] = self.all_peaks.rightSigma[dcl_idx]

			# apply the DCL upper boundary for Gaussian fitting method boundary
			chl_peak_upper_depth = data.Depth[self.all_peaks.leftIndex_fit[dcl_idx]]
			features["DCL_Org_UpperDepth_fit"] = chl_peak_upper_depth

			if chl_peak_upper_depth > chl_peak_upper_depth_boundary:
				# if the peak upper is deeper than chl_peak_upper_depth_boundary
				features["DCL_upperDepth_fit"] = chl_peak_upper_depth
				features["DCL_upperConc_fit"] = data.Fluorescence[self.all_peaks.leftIndex_fit[dcl_idx]]
				features["DCL_concProp_fit"] = np.sum(data.Fluorescence[self.all_peaks.leftIndex_fit[dcl_idx]:(self.all_peaks.rightIndex_fit[dcl_idx] + 1)]) / features["allConc"]
			else:
				# if the peak upper boundary is shallower than peakUpperDepthBoundary, using the upperboundary as the upper DCL boundary
				features["DCL_upperDepth_fit"] = chl_peak_upper_depth_boundary
				features["DCL_upperConc_fit"] = data.Fluorescence[chl_peak_upper_depth_boundary_index]
				features["DCL_concProp_fit"] = np.sum(data.Fluorescence[chl_peak_upper_depth_boundary_index:(self.all_peaks.rightIndex_fit[dcl_idx] + 1)]) / features["allConc"]
			
			# find the DCL lower boundary
			features["DCL_bottomConc_fit"] = data.Fluorescence[self.all_peaks.rightIndex_fit[dcl_idx]]
			features["DCL_bottomDepth_fit"] =  data.Depth[self.all_peaks.rightIndex_fit[dcl_idx]]

		return features







