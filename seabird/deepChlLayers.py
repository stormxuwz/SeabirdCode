from models.model_peak import peak
import pandas as pd
import numpy as np

class DCL(object):
	def __init__(self,config):
		self.config  = config
		self.allPeaks = None
		self.DCL_idx = None
		self.model = None
		
	def correctConc(self,DCLDepth,rawData):
		# rawData is dataFrame with ["Depth","Fluorescence"]
		# DCLDepth: the detected DCL
		# return: corrected DCL concentration

		DCLConc_rawData = rawData.loc[(rawData.Depth< DCLDepth+0.5) & (rawData.Depth > DCLDepth-0.5),"Fluorescence"]
		return np.max(DCLConc_rawData)

	def detect(self,data,rawData,peakMinDepth=None,peakUpperDepthBoundary=None,saveModel=True):
		# rawData is dataFrame with Depth and Fluorescence. 

		model = peak(self.config["Algorithm"]["Peak"]) # initialize peak model
		
		if saveModel: # save model
			self.model = model
		
		model.fit_predict(data.Fluorescence) # Detect the peak
		self.allPeaks = model.allPeaks
		
		depthInterval = data.Depth[1]-data.Depth[0]
		
		features = {"DCL_depth":None,
		"peakNums":None, # the total number of peaks detected
		"DCL_conc":None,
		"DCL_upperConc":None,
		"DCL_bottomConc":None,
		"DCL_upperDepth_fit":None,
		"DCL_bottomDepth_fit":None,
		"DCL_upperShape":None,
		"DCL_bottomShape":None,
		"DCL_exists":None,  # whether DCL exists
		"DCL_leftShapeFitErr":None,  
		"DCL_rightShapeFitErr":None,
		"DCL_upperDepth_gradient":None,
		"DCL_bottomDepth_gradient":None,
		"DCL_concProp_fit":None,
		"DCL_concProp_gradient":None,
		"allConc":None,
		"DCL_leftSigma":None,
		"DCL_rightSigma":None}

		features["allConc"] = np.sum((data.Fluorescence))

		if self.allPeaks is None or self.allPeaks.shape[0]<1: # if any peak exists
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

			# apply the DCL upper boundary for gradient boundary
			sizeUpperDepth_gradient = data.Depth[self.allPeaks.leftIndex_gradient[DCL_idx]]
			if sizeUpperDepth_gradient>peakUpperDepthBoundary:
				features["DCL_upperDepth_gradient"] = sizeUpperDepth_gradient
				features["DCL_upperConc_gradient"] = data.Fluorescence[self.allPeaks.leftIndex_gradient[DCL_idx]]
				features["DCL_concProp_gradient"] = np.sum(data.Fluorescence[self.allPeaks.leftIndex_gradient[DCL_idx]:(self.allPeaks.rightIndex_gradient[DCL_idx]+1)]) / features["allConc"]
			else:
				newIdx = np.searchsorted(data.Depth,peakUpperDepthBoundary)[0]+1
				features["DCL_upperDepth_gradient"] = data.Depth[newIdx]
				features["DCL_upperConc_gradient"] = data.Fluorescence[newIdx]


				features["DCL_concProp_gradient"] = np.sum(data.Fluorescence[newIdx:self.allPeaks.rightIndex_gradient[DCL_idx]+1])/features["allConc"]

			# apply the DCL upper boundary for Gaussian fitting method boundary
			sizeUpperDepth_fit = data.Depth[self.allPeaks.leftIndex_fit[DCL_idx]]
			
			if sizeUpperDepth_fit > peakUpperDepthBoundary:
				features["DCL_upperDepth_fit"] = sizeUpperDepth_fit
				# _fit means the gaussian shape fitting method
				features["DCL_upperConc_fit"] = data.Fluorescence[self.allPeaks.leftIndex_fit[DCL_idx]]
				features["DCL_concProp_fit"] = np.sum(data.Fluorescence[self.allPeaks.leftIndex_fit[DCL_idx]:(self.allPeaks.rightIndex_fit[DCL_idx]+1)]) / features["allConc"]
			else:
				newIdx = np.searchsorted(data.Depth,peakUpperDepthBoundary)[0]+1
				# print "DCL upper level should be below LEP"
				features["DCL_upperDepth_fit"] = peakUpperDepthBoundary
				features["DCL_upperConc_fit"] = data.Fluorescence[newIdx]
				features["DCL_concProp_fit"] = np.sum(data.Fluorescence[newIdx:(self.allPeaks.rightIndex_fit[DCL_idx]+1)]) / features["allConc"]
			
			# find the DCL lower boundary
			features["DCL_bottomConc_fit"] = data.Fluorescence[self.allPeaks.rightIndex_fit[DCL_idx]]
			features["DCL_bottomConc_gradient"] = data.Fluorescence[self.allPeaks.rightIndex_gradient[DCL_idx]]
			features["DCL_bottomDepth_fit"] =  data.Depth[self.allPeaks.rightIndex_fit[DCL_idx]]
			features["DCL_bottomDepth_gradient"] = data.Depth[self.allPeaks.rightIndex_gradient[DCL_idx]]

		return features







