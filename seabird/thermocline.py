import numpy as np
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
		self.TRM_segment = thermocline_segmentation(config)
		self.TRM_HMM = thermocline_HMM(config)
		self.TRM_threshold = thermocline_threshold(config)
		self.features = {}
		
	def detect(self,data,methods = ["segmentation","HMM","threshold"]):
		features = {}
		if "segmentation" in methods:
			self.TRM_segment.detect(data)
			features["TRM_segment"] = self.TRM_segment.TRM
			features["LEP_segment"] = self.TRM_segment.LEP
			features["UHY_segment"] = self.TRM_segment.UHY
			features["TRM_gradient_segment"] = self.TRM_segment.TRM_gradient
			features["TRM_num_segment"] = self.TRM_segment.num_segments

		if "HMM" in methods:
			self.TRM_HMM.detect(data)
			features["TRM_HMM"] = self.TRM_HMM.TRM
			features["LEP_HMM"] = self.TRM_HMM.LEP
			features["UHY_HMM"] = self.TRM_HMM.UHY

		if "threshold" in methods:
			self.TRM_threshold.detect(data)
			features["TRM_threshold"] = self.TRM_threshold.TRM
			features["LEP_threshold"] = self.TRM_threshold.LEP
			features["UHY_threshold"] = self.TRM_threshold.UHY

		return features


