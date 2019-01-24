"""
Thermocline Class
"""
import numpy as np
import traceback
import sys
# from models.model_HMM import hmmModel
from .models.model_segmentation import splitAndMerge as segModel # or choose between splitAndMerge or bottomUp
from .tools.signalProcessing import extractSignalFeatures

class thermocline_base(object):
	"""
	Base class for thermocline.
	"""
	def __init__(self,config):
		"""
		Args:
			config: configuration dictionary
		"""
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
	"""
	Class to detect TRM using time series segmentation methods
	"""
	def __init__(self,config):
		"""
		Args:
			config: configuration dictionary
		"""
		super(thermocline_segmentation, self).__init__(config)
		self.TRM_gradient = None
		self.num_segments = None
		self.num_belowTRM = None
		self.model = None
		self.depthInterval = self.config["Preprocessing"]["depthInterval"]
		self.positiveSeg = []
		self.doubleTRM = []
		self.gradient = []

		self.maxTempertureChange = 2.0
		
		self.stableGradient = config["Algorithm"]["PLR"]["stable_gradient"]
		self.stableGradient_relaxed = config["Algorithm"]["PLR"]["stable_gradient2"]
		self.minimumGradient_TRM = self.config["Algorithm"]["PLR"]["minTRM_gradient"]
		self.max_error = self.config["Algorithm"]["PLR"]["max_error"]

	def getGradientFromSegment(self,seg):
		"""
		Function to get gradients of each segment, 
		positive means the temperature is decreasing with depth

		Args:
			seg: a list [fitted line, point index]
		Returns:
			the gradient of seg
		"""
		return (seg[0][0]-seg[0][1])/self.depthInterval

	def detectDoubleTRM(self,segmentList):
		"""
		Functions to detect double thermocline. The index of segments which represent
		double thermocline will be appended to doubleTRM

		Args:
			segmentList: a list stores all the segments
		Retures:
			None
		"""
		for i in range(1,len(segmentList)-1):
			segGradient = self.getGradientFromSegment(segmentList[i])
			previousSegGradient = self.getGradientFromSegment(segmentList[i-1])
			nextSegGradient = self.getGradientFromSegment(segmentList[i+1])

			if abs(segGradient) < self.stableGradient and \
				previousSegGradient > self.minimumGradient_TRM and \
				nextSegGradient > self.stableGradient:

				self.doubleTRM.append(i)

		if len(self.doubleTRM)>0:
			print("detected double thermocline")
			print(self.doubleTRM)

	def detectPositiveGradient(self,segmentList):
		"""
		Functions to detect positive gradient, since positive gradient is abnormal. 
		The index of such segments will be appended to positiveSeg

		Args:
			segmentList: a list stores all the segments
		Retures:
			None
		"""

		self.positiveSeg = []
		for i, seg in enumerate(segmentList):
			gradient = self.getGradientFromSegment(seg)
			if gradient < -1 * self.stableGradient:
				self.positiveSeg.append(i)


	def detect(self,data,saveModel = False):
		"""
		Function to detect the thermocline
		Args:
			data: a pandas dataframe
			saveModel: whether to save detection model
		Returns:
			None
		"""
		model = segModel(max_error = self.max_error)
		
		# detect the TRM features
		model.fit_predict(data.Temperature)

		segmentList = model.segmentList # segmentList is a list of [fitted line, point index]

		assert len(data.Depth) > 1
		depthInterval = data.Depth[1] - data.Depth[0]
		
		# get the gradient of all segments
		gradient = [self.getGradientFromSegment(seg) for seg in model.segmentList]
		print(gradient)
		maxGradient_index = np.argmax(gradient)
		
		# remove the segment caused by the noise
		if maxGradient_index == 0:
			tmpDepth = np.array(data.Depth[segmentList[maxGradient_index][1]])
			if tmpDepth[-1] - tmpDepth[0] < 2:
				# if the first segment is less than 2 meters and has the maximum gradient
				# then the first segment would be a noise or peak, need to remove
				print("**** first segment is affected by noise")
				print(tmpDepth)
				model.segmentList.pop(0)
				gradient = [self.getGradientFromSegment(seg) for seg in model.segmentList]
				maxGradient_index = np.argmax(gradient)

		self.gradient = gradient

		if gradient[maxGradient_index] > self.minimumGradient_TRM: 
			# TRM gradient is above the maximum gradient
			# Detect TRM, which is the middle point of the segment with maximum gradient
			self.TRM = data.Depth[int(np.mean(segmentList[maxGradient_index][1]))]

			gradientIsStable = [abs(g) < self.stableGradient for g in gradient]
			gradientIsStable[0] = abs(gradient[0]) < self.stableGradient_relaxed
			gradientIsStable[-1] = abs(gradient[-1]) < self.stableGradient_relaxed

			surfaceTemperature = model.segmentList[0][0][0]
			bottomTemperature = model.segmentList[-1][0][-1]
			
			LEP_index = None
			UHY_index = None

			# detect the LEP
			for i in range(maxGradient_index):
				if not (gradientIsStable[i] and model.segmentList[i][0][-1] - surfaceTemperature < self.maxTempertureChange):
					if i > 0:
						LEP_index = model.segmentList[i - 1][1][-1]
					break

				if i == maxGradient_index - 1:
					LEP_index = model.segmentList[i][1][-1]

			# detect the UHY
			for i in range(len(model.segmentList) - 1, maxGradient_index, -1):
				print(model.segmentList[i][0][0] - bottomTemperature)
				if not (gradientIsStable[i] and model.segmentList[i][0][0] - bottomTemperature < self.maxTempertureChange):
					if i < len(model.segmentList) - 1:
						UHY_index = model.segmentList[i + 1][1][0]
					break

				if i == maxGradient_index + 1:
					UHY_index = model.segmentList[i][1][0]

			if LEP_index:
				self.LEP = data.Depth[LEP_index]

			if UHY_index:
				self.UHY = data.Depth[UHY_index]
		else:
			print("minimum Gradient")
			print(gradient[maxGradient_index]) 
			print(self.minimumGradient_TRM)
			print("No TRM deteted")
		
		self.TRM_gradient = max(gradient)
		self.num_segments = len(segmentList)
		self.TRM_idx = maxGradient_index
		
		self.detectDoubleTRM(segmentList)
		self.detectPositiveGradient(segmentList)

		if saveModel:
			self.model = model

class thermocline_HMM(thermocline_base):
	"""
	HMM model
	"""
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
	"""
	Function to detect
	"""
	def __init__(self,config):
		self.config = config
		self.features = {}
		self.models = {}
		
	def detect(self,data,methods = ["segmentation"], saveModel = True):
		"""
		Function to detect features of thermocline
		Args:
			data: preprocessed data, a pandas dataframe
			methods: a list indicating which algorithms to use
			saveModel: whether to save model
		Returns:
			features: a dictionary stored the TRM features
		"""
		features = {}
		# initialize Features
		for d in ["TRM","LEP","UHY"]:
			for m in ["segment","HMM","threshold"]:
				features[d+"_"+m] = None
		features["TRM_gradient_segment"] = None
		features["TRM_num_segment"] = None

		# try each model one by one.

		if "segmentation" in methods:
			try:
				model = thermocline_segmentation(self.config)
				model.detect(data,saveModel = saveModel)

				# the gradient of TRM
				features["TRM_gradient_segment"] = model.TRM_gradient

				# the depth of TRM, LEP and UHY
				features["TRM_segment"] = model.TRM
				features["LEP_segment"] = model.LEP
				features["UHY_segment"] = model.UHY
				
				# the number of segments
				features["TRM_num_segment"] = model.num_segments

				# which segment is the TRM
				features["TRM_idx"] = model.TRM_idx

				# how many double TRM sequences
				features["doubleTRM"] = len(model.doubleTRM)

				# how many positive gradient segments
				features["positiveGradient"] = len(model.positiveSeg)

				# the gradient of the some key segments
				features["firstSegmentGradient"] = model.gradient[0]
				features["lastSegmentGradient"] = model.gradient[-1]
				features["lastButTwoSegmentGradient"] = model.gradient[-2]

				if saveModel:
					self.models["segmentation"] = model.model

			except Exception as err:
				print("segmentation Fail")
				print(traceback.format_exc())

		if "HMM" in methods:
			try:
				model = thermocline_HMM(self.config)
				model.detect(data)
				# the depth of TRM, LEP and UHY
				features["TRM_HMM"] = model.TRM
				features["LEP_HMM"] = model.LEP
				features["UHY_HMM"] = model.UHY
			except Exception as err:
				print("HMM Fail")
				print(traceback.format_exc())

		if "threshold" in methods:
			try:
				model = thermocline_threshold(self.config)
				model.detect(data)

				# the depth of TRM, LEP and UHY
				features["TRM_threshold"] = model.TRM
				features["LEP_threshold"] = model.LEP
				features["UHY_threshold"] = model.UHY
			except Exception as err:
				print("threshold Fail")
				print(traceback.format_exc())

		return features


