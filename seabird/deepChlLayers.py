from models.model_peak import peak
import pandas as pd
import numpy as np

class DCL(object):
	def __init__(self,config):
		self.config  = config
		self.allPeaks = None
		self.DCL_idx = None
		self.model = None
		
	def detect(self,data,depthThreshold = None,saveModel = True):
		# data is a data frame with "Depth" and "Fluorescence" columns
		model = peak(self.config["Algorithm"]["Peak"])
		
		if saveModel:
			self.model = model
		
		model.fit_predict(data.Fluorescence)
		self.allPeaks = model.allPeaks
		
		depthInterval = data.Depth[1]-data.Depth[0]
		
		features = {"DCL_depth":None,"peakNums":None,"DCL_conc":None,"DCL_upperConc":None,"DCL_bottomConc":None,"DCL_upperDepth":None,"DCL_bottomDepth":None,"DCL_upperShape":None,"DCL_bottomShape":None,"DCL_exists":None}

		if self.allPeaks.shape[0]<1:
			features["peakNums"] = 0
			features["DCL_exists"] = 0
			return features
		else:
			features["peakNums"] = self.allPeaks.shape[0]
			peakDepths = np.array(data.Depth[self.allPeaks.peakIndex])
			
			if depthThreshold is not None and all(peakDepths<depthThreshold):
				features["DCL_exists"] = 0
				return features

			if depthThreshold is None:
				DCL_idx = np.argmax(peakDepths)
			else:
				availablePeaks = peakDepths*(peakDepths>depthThreshold)
				DCL_idx = np.argmax(availablePeaks)
			
			self.DCL_idx = DCL_idx
			# print self.allPeaks,DCL_idx
			features["DCL_depth"] = peakDepths
			features["DCL_conc"] = data.Fluorescence[self.allPeaks.peakIndex[DCL_idx]]
			features["DCL_upperConc"] = data.Fluorescence[self.allPeaks.leftIndex[DCL_idx]]
			features["DCL_bottomConc"] = data.Fluorescence[self.allPeaks.rightIndex[DCL_idx]]
			features["DCL_upperDepth"]=  data.Depth[self.allPeaks.leftIndex[DCL_idx]]
			features["DCL_bottomDepth"] =  data.Depth[self.allPeaks.rightIndex[DCL_idx]]
			features["DCL_upperShape"] = self.allPeaks.leftStd[DCL_idx]*depthInterval
			features["DCL_bottomShape"] = self.allPeaks.rightStd[DCL_idx]*depthInterval

		return features







