from models.model_peak3 import peak
import pandas as pd
import numpy as np

class DCL(object):
	def __init__(self,config):
		self.config  = config
		self.allPeaks = None
		self.DCL_idx = None
		self.model = None
		
	def correctConc(self,DCLDepth,rawData):
		# rawData is dataFrame with Depth and Fluorescence
		print DCLDepth
		print rawData
		DCLConc_rawData = rawData.loc[(rawData.Depth< DCLDepth+0.5) & (rawData.Depth > DCLDepth-0.5),"Fluorescence"]
		return np.max(DCLConc_rawData)



	def detect(self,data,rawData,depthThreshold = None,saveModel = True):
		# data is a data frame with "Depth" and "Fluorescence" columns
		# rawData is dataFrame with Depth and Fluorescence. Raw Data are used to correct due to preprocessing
		model = peak(self.config["Algorithm"]["Peak"])
		
		if saveModel:
			self.model = model
		
		model.fit_predict(data.Fluorescence)
		self.allPeaks = model.allPeaks
		
		depthInterval = data.Depth[1]-data.Depth[0]
		
		features = {"DCL_depth":None,
		"peakNums":None,
		"DCL_conc":None,
		"DCL_upperConc":None,
		"DCL_bottomConc":None,
		"DCL_upperDepth_fit":None,
		"DCL_bottomDepth_fit":None,
		"DCL_upperShape":None,
		"DCL_bottomShape":None,
		"DCL_exists":None,
		"DCL_leftShapeFitErr":None,
		"DCL_rightShapeFitErr":None,
		"DCL_upperDepth_gradient":None,
		"DCL_bottomDepth_gradient":None,
		"DCL_concProp_fit":None,
		"DCL_concProp_gradient":None,
		"allConc":None}


		features["allConc"] = np.sum((data.Fluorescence))
		# print "allCOnc",features["allConc"]

		if self.allPeaks is None or self.allPeaks.shape[0]<1:
			features["peakNums"] = 0
			features["DCL_exists"] = 0
			return features
		else:
			features["peakNums"] = self.allPeaks.shape[0]
			peakDepths = np.array(data.Depth[self.allPeaks.peakIndex])
			
			# print "peak Depths",peakDepths

			if depthThreshold is not None and all(peakDepths<depthThreshold):
				# No peaks exists below the depth threshold
				features["DCL_exists"] = 0
				return features

			if depthThreshold is None:
				DCL_idx = np.argmax(np.array(data.Fluorescence[self.allPeaks.peakIndex]))
			else:
				availablePeakIdx = np.array(self.allPeaks.peakIndex*(peakDepths>depthThreshold))
				# print "available",data.Fluorescence[availablePeakIdx]
				DCL_idx = np.argmax(np.array(data.Fluorescence[availablePeakIdx]))
			
			# print data.Fluorescence[self.allPeaks.peakIndex]
			DCL_idx = int(DCL_idx)
			self.DCL_idx = DCL_idx

			# print "DCL_index",DCL_idx
			# print self.allPeaks.peakIndex
			# print "data shape",data.shape
			# print "peakDepths",peakDepths
			# print self.allPeaks.leftIndex_fit
			
			features["DCL_exists"] = 1
			features["DCL_depth"] = peakDepths[DCL_idx]
			# features["DCL_conc"] = data.Fluorescence[self.allPeaks.peakIndex[DCL_idx]]
			features["DCL_conc"] = self.correctConc(peakDepths[DCL_idx], rawData)




			features["DCL_upperConc"] = data.Fluorescence[self.allPeaks.leftIndex_gradient[DCL_idx]]
			features["DCL_bottomConc"] = data.Fluorescence[self.allPeaks.rightIndex_gradient[DCL_idx]]
			features["DCL_upperDepth_fit"]=  data.Depth[self.allPeaks.leftIndex_fit[DCL_idx]]
			features["DCL_bottomDepth_fit"] =  data.Depth[self.allPeaks.rightIndex_fit[DCL_idx]]

			features["DCL_leftShapeFitErr"] = self.allPeaks.leftErr[DCL_idx]
			features["DCL_rightShapeFitErr"] = self.allPeaks.rightErr[DCL_idx]
			
			features["DCL_upperDepth_gradient"] = data.Depth[self.allPeaks.leftIndex_gradient[DCL_idx]]
			features["DCL_bottomDepth_gradient"] = data.Depth[self.allPeaks.rightIndex_gradient[DCL_idx]]

			# adding the DCL concentration
			# print "test10",self.allPeaks.leftIndex_gradient[DCL_idx]
			# print (self.allPeaks.rightIndex_gradient[DCL_idx]+1)
			# print "test2",features["DCL_allConc"]
			features["DCL_concProp_gradient"] = np.sum(data.Fluorescence[self.allPeaks.leftIndex_gradient[DCL_idx]:(self.allPeaks.rightIndex_gradient[DCL_idx]+1)]) / features["allConc"]
			features["DCL_concProp_fit"] = np.sum(data.Fluorescence[self.allPeaks.leftIndex_fit[DCL_idx]:(self.allPeaks.rightIndex_fit[DCL_idx]+1)]) / features["allConc"]

		# print features
		return features







