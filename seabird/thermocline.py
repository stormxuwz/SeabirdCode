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
	# Class to detect TRM using time series segmentation methods
	def __init__(self,config):
		super(thermocline_segmentation, self).__init__(config)
		self.TRM_gradient = None
		self.num_segments = None
		self.num_belowTRM = None
		self.model = None
		self.depthInterval = self.config["Preprocessing"]["Interval"]
		self.positiveSeg = []
		self.doubleTRM = []

	def getGradientFromSegment(self,seg):
		return (seg[0][0]-seg[0][1])/self.depthInterval

	def detectDoubleTRM(self,segmentList):
		# detect double thermocline from the segmentList
		for i in range(1,len(segmentList)-1):
			segGradient = self.getGradientFromSegment(segmentList[i])
			previousSegGradient = self.getGradientFromSegment(segmentList[i-1])
			nextSegGradient = self.getGradientFromSegment(segmentList[i+1])

			if abs(segGradient) < self.config["Algorithm"]["segment"]["stable_gradient"] and \
				previousSegGradient > self.config["Algorithm"]["segment"]["minTRM_gradient"] and \
				nextSegGradient > self.config["Algorithm"]["segment"]["minTRM_gradient"]:


				self.doubleTRM.append(i)

		if len(self.doubleTRM)>0:
			print "detected double thermocline", self.doubleTRM

	def detectPositiveGradient(self,segmentList):
		# detect positive gradient, since positive gradient is abnormal
		self.positiveSeg = []
		for i, seg in enumerate(segmentList):
			gradient = self.getGradientFromSegment(seg)
			if gradient < -1*self.config["Algorithm"]["segment"]["stable_gradient"]:
				self.positiveSeg.append(i)

	def detect(self,data,saveModel = False):
		model = bottomUp(max_error = self.config["Algorithm"]["segment"]["max_error"])
		model.fit_predict(data.Temperature)
		segmentList = model.segmentList

		depthInterval = data.Depth[1]-data.Depth[0]
		
		# segmentList is a list of [fitted line,point index]
		gradient = [self.getGradientFromSegment(seg) for seg in model.segmentList]

		maxGradient_index = np.argmax(gradient)


		if gradient[maxGradient_index]>self.config["Algorithm"]["segment"]["minTRM_gradient"]: 
			# TRM gradient is above the maximum gradient

			# Detect TRM
			self.TRM = data.Depth[int(np.mean(segmentList[maxGradient_index][1]))]

			# Detect LEP
			epilimnion_seg = model.segmentList[0]
			LEP_index = epilimnion_seg[1][-1]
			
			if maxGradient_index == 0: # if maximum gradient is the first segment, change to no thermocline is detected
				# LEP_index = epilimnion_seg[1][0]
				LEP_index = None
			elif abs(gradient[1]) < self.config["Algorithm"]["segment"]["stable_gradient"]: # if the first seg is anomaly and second seg is stable
				LEP_index = model.segmentList[1][1][-1]
		
			# Detect the HYP
			hypolimnion_seg = model.segmentList[-1]
			UHY_index = hypolimnion_seg[1][0]

			if maxGradient_index == len(gradient)-1: # if the TRM is the last segment
				# UHY_index = hypolimnion_seg[1][-1]
				UHY_index = None # No UHY in this profile

			elif abs(gradient[-2])< self.config["Algorithm"]["segment"]["stable_gradient"]: # if the last second one is stable
				UHY_index = model.segmentList[-2][1][0] # pick the last second as the HYP
			
			elif abs(gradient[-1]) > max(gradient)*0.2: # if last one still has large gradient
				UHY_index=None # No UHY in this profile

			if LEP_index is not None:
				self.LEP = data.Depth[LEP_index]

			if UHY_index is not None:
				self.UHY = data.Depth[UHY_index]
		else:
			print "No TRM deteted"
		
		self.TRM_gradient = max(gradient)
		self.num_segments = len(segmentList)
		self.TRM_idx = maxGradient_index
		
		self.detectDoubleTRM(segmentList)
		self.detectPositiveGradient(segmentList)

		if saveModel:
			self.model = model

class thermocline_HMM(thermocline_base):
	def detect(self,data):
		signal_data = extractSignalFeatures(data, "Temperature")
		model = hmmModel(nc = 3)
		res = model.fit_predict(signal_data)
		self.TRM = signal_data.Depth[res[0]]
		self.LEP = signal_data.Depth[res[1]]
		self.UHY = signal_data.Depth[res[2]]


class thermocline_threshold(thermocline_base):
	def detect(self,data):
		signal_data = extractSignalFeatures(data, "Temperature")
		model = thresholdModel(threshold = None)
		res = model.fit_predict(signal_data.Power)
		self.TRM = signal_data.Depth[res[0]]
		self.LEP = signal_data.Depth[res[1]]
		self.UHY = signal_data.Depth[res[2]]

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

				features["TRM_gradient_segment"] = model.TRM_gradient
				features["TRM_segment"] = model.TRM
				features["LEP_segment"] = model.LEP
				features["UHY_segment"] = model.UHY
				features["TRM_num_segment"] = model.num_segments
				features["TRM_idx"] = model.TRM_idx
				features["doubleTRM"] = len(model.doubleTRM)
				features["positiveGradient"] = len(model.positiveSeg)

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


