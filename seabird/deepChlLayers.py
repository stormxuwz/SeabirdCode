"""
Class of DCL
"""

from models.model_peak import peak
import pandas as pd
import numpy as np

class DCL(object):
	def __init__(self,config):
		"""
		Class initialization
		Args:
			config: dictionary, the configuration
		"""
		self.config  = config
		self.allPeaks = None
		self.DCL_idx = None
		self.model = None
		
	def correctConc(self,DCLDepth,rawData):
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
		DCLConc_rawData = rawData.loc[(rawData.Depth< DCLDepth+0.5) & (rawData.Depth > DCLDepth-0.5),"Fluorescence"]
		return np.max(DCLConc_rawData)

	def detect(self,data,rawData,peakMinDepth=None,peakUpperDepthBoundary=None,saveModel=True):
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
		"DCL_aboveConc": None # the sum of concentrations above a depth threshold
		}

		# initialize peak model
		model = peak(self.config["Algorithm"]["Peak"]) 
		
		if saveModel: # save model
			self.model = model
		
		model.fit_predict(data.Fluorescence) # Detect the peak
		
		self.allPeaks = model.allPeaks # a np.array storing
		
		depthInterval = data.Depth[1]-data.Depth[0]
		
		features["allConc"] = np.sum((data.Fluorescence))
		peakUpperDepthBoundary_idx = np.searchsorted(data.Depth,peakUpperDepthBoundary)[0]+1 # find the boundary index
		features["allConc_upper"] = np.sum(data.Fluorescence[:peakUpperDepthBoundary_idx])

		if self.allPeaks is None or self.allPeaks.shape[0]<1:
			# no peak exists
			features["peakNums"] = 0
			features["DCL_exists"] = 0
			return features
		
		else:
			features["peakNums"] = self.allPeaks.shape[0] 
			peakDepths = np.array(data.Depth[self.allPeaks.peakIndex]) # the peak depth
			
			if peakMinDepth is not None and all(peakDepths<peakMinDepth):
				# No peaks exists below the depth threshold
				features["DCL_exists"] = 0
				return features

			# choose which peak represents DCM
			if peakMinDepth is None:
				DCL_idx = np.argmax(np.array(data.Fluorescence[self.allPeaks.peakIndex]))
			else:
				availablePeakIdx = np.array(self.allPeaks.peakIndex*(peakDepths>peakMinDepth))
				DCL_idx = np.argmax(np.array(data.Fluorescence[availablePeakIdx])) # choose the maximum concentration as the peak
			

			DCL_idx = int(DCL_idx)
			self.DCL_idx = DCL_idx

			features["DCL_exists"] = 1
			features["DCL_depth"] = peakDepths[DCL_idx]
			
			# features["DCL_conc"] = data.Fluorescence[self.allPeaks.peakIndex[DCL_idx]]
			features["DCL_conc"] = self.correctConc(peakDepths[DCL_idx], rawData) # correct the peak concentration

			features["DCL_leftShapeFitErr"] = self.allPeaks.leftErr[DCL_idx]
			features["DCL_rightShapeFitErr"] = self.allPeaks.rightErr[DCL_idx]

			features["DCL_leftSigma"] = self.allPeaks.leftSigma[DCL_idx]
			features["DCL_rightSigma"] = self.allPeaks.rightSigma[DCL_idx]

			# apply the DCL upper boundary for Gaussian fitting method boundary
			sizeUpperDepth_fit = data.Depth[self.allPeaks.leftIndex_fit[DCL_idx]]
			features["DCL_Org_UpperDepth_fit"] = sizeUpperDepth_fit

			if sizeUpperDepth_fit > peakUpperDepthBoundary:
				# if the peak upper is deeper than peakUpperDepthBoundary
				features["DCL_upperDepth_fit"] = sizeUpperDepth_fit
				features["DCL_upperConc_fit"] = data.Fluorescence[self.allPeaks.leftIndex_fit[DCL_idx]]
				features["DCL_concProp_fit"] = np.sum(data.Fluorescence[self.allPeaks.leftIndex_fit[DCL_idx]:(self.allPeaks.rightIndex_fit[DCL_idx]+1)]) / features["allConc"]
			else:
				# if the peak upper boundary is shallower than peakUpperDepthBoundary, using the upperboundary as the upper DCL boundary
				features["DCL_upperDepth_fit"] = peakUpperDepthBoundary
				features["DCL_upperConc_fit"] = data.Fluorescence[peakUpperDepthBoundary_idx]
				features["DCL_concProp_fit"] = np.sum(data.Fluorescence[peakUpperDepthBoundary_idx:(self.allPeaks.rightIndex_fit[DCL_idx]+1)]) / features["allConc"]
			
			# find the DCL lower boundary
			features["DCL_bottomConc_fit"] = data.Fluorescence[self.allPeaks.rightIndex_fit[DCL_idx]]
			features["DCL_bottomDepth_fit"] =  data.Depth[self.allPeaks.rightIndex_fit[DCL_idx]]

		
		print "DCL Features", features
		return features







