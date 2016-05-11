import numpy as np
import traceback
import sys
from models.model_HMM import hmmModel
from models.model_segmentation import bottomUp
from models.model_threshold import thresholdModel
from tools.signalProcessing import extractSignalFeatures

class thermocline_base(object):
	def __init__(self,config):
		self.LEP = None
		self.TRM = None
		self.UHY = None
		self.config = config
		
	def detect(self,data):
		'''
		data is a data frame with Depth and Temperature
		'''
		raise ValueError("not implementated")

class thermocline_segmentation(thermocline_base):
	def __init__(self,config):
		super(thermocline_segmentation, self).__init__(config)
		self.TRM_gradient = None
		self.num_segments = None
		self.model = None
	
	def detect(self,data,saveModel = False):
		model = bottomUp(max_error = self.config["Algorithm"]["segment"]["max_error"])
		model.fit_predict(data.Temperature)
		segmentList = model.segmentList

		depthInterval = data.Depth[1]-data.Depth[0]
		# segmentList is a list of [fitted line,point index]
		gradient = [(seg[0][0]-seg[0][1])/depthInterval for seg in model.segmentList]
		
		maxGradient_index = np.argmax(gradient)

		epilimnion_seg = model.segmentList[0]
		LEP_index = epilimnion_seg[1][-1]
		
		# Detect the epiliminion
		if maxGradient_index == 0: # if the maximum gradient is the first segment
			LEP_index = epilimnion_seg[1][0]
		elif maxGradient_index == 1: # if the maximum gradient is the second segment
			pass
		elif abs(gradient[1]) < self.config["Algorithm"]["segment"]["stable_gradient"]:
			LEP_index = model.segmentList[1][1][-1]

		# Detect the Hypolimnion
		hypolimnion_seg = model.segmentList[-1]
		UHY_index = hypolimnion_seg[1][0]

		if maxGradient_index == len(gradient)-1: # if the TRM is the last segment
			UHY_index = hypolimnion_seg[1][-1]

		elif maxGradient_index == len(gradient)-2: # if TRM is the last but one segment
			pass

		elif abs(gradient[-2])< self.config["Algorithm"]["segment"]["stable_gradient"]:
			UHY_index = model.segmentList[-2][1][0]
		
		elif abs(gradient[-1]) > max(gradient)*0.2:
			UHY_index=None # No 

		self.LEP = data.Depth[LEP_index]
		self.TRM = data.Depth[int(np.mean(segmentList[maxGradient_index][1]))]
		self.UHY = data.Depth[UHY_index]
		self.TRM_gradient = max(gradient)
		self.num_segments = len(segmentList)
		
		if saveModel:
			self.model = model

class thermocline_HMM(thermocline_base):
	def detect(self,data):
		signal_data = extractSignalFeatures(data, "Temperature")
		model = hmmModel(nc = 3)
		res = model.fit_predict(signal_data)
		self.TRM = data.Depth[res[0]]
		self.LEP = data.Depth[res[1]]
		self.UHY = data.Depth[res[2]]

class thermocline_threshold(thermocline_base):
	def detect(self,data):
		signal_data = extractSignalFeatures(data, "Temperature")
		model = thresholdModel(threshold = None)
		res = model.fit_predict(signal_data.Power)
		self.TRM = data.Depth[res[0]]
		self.LEP = data.Depth[res[1]]
		self.UHY = data.Depth[res[2]]

class thermocline(object):
	def __init__(self,config):
		self.config = config
		self.features = {}
		self.models = {}
		
	def detect(self,data,methods = ["segmentation","HMM","threshold"],saveModel = True):
		features = {}
		# initialize Features
		for d in ["TRM","LEP","UHY"]:
			for m in ["segment","HMM","threshold"]:
				features[d+"_"+m] = None
		features["TRM_gradient_segment"] = None
		features["TRM_num_segment"] = None

		if "segmentation" in methods:
			try:
				model = thermocline_segmentation(self.config)
				model.detect(data,saveModel = saveModel)
				features["TRM_segment"] = model.TRM
				features["LEP_segment"] = model.LEP
				features["UHY_segment"] = model.UHY
				features["TRM_gradient_segment"] = model.TRM_gradient
				features["TRM_num_segment"] = model.num_segments
				if saveModel:
					self.models["segmentation"] = model.model
			except Exception,err:
				print "segmentation Fail"
				print(traceback.format_exc())

			


		if "HMM" in methods:
			try:
				model = thermocline_HMM(self.config)
				model.detect(data)
				features["TRM_HMM"] = model.TRM
				features["LEP_HMM"] = model.LEP
				features["UHY_HMM"] = model.UHY
			except Exception,err:
				print "HMM Fail"
				print(traceback.format_exc())

		if "threshold" in methods:
			try:
				model = thermocline_threshold(self.config)
				model.detect(data)
				features["TRM_threshold"] = model.TRM
				features["LEP_threshold"] = model.LEP
				features["UHY_threshold"] = model.UHY
			except Exception,err:
				print "threshold Fail"
				print(traceback.format_exc())

		return features


