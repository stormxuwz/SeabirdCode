"""
Thermocline Class
"""
import numpy as np
import traceback
from .models.model_segmentation import BottomUp as SegmentationModel
import logging

class _ThermoclineBase(object):
	"""
	Base class for thermocline.
	"""
	def __init__(self,config):
		"""
		Args:
			config: configuration dictionary
		"""
		self.lep = None
		self.trm = None
		self.uhy = None
		self.config = config
		self.trm_idx = None
		
	def detect(self,data):
		'''
		data is a data frame with Depth and Temperature
		'''
		raise ValueError("not implementated")

class ThermoclineSegmentation(_ThermoclineBase):
	"""
	Class to detect TRM using time series segmentation methods
	"""
	def __init__(self,config):
		"""
		Args:
			config: configuration dictionary
		"""
		super(ThermoclineSegmentation, self).__init__(config)
		self.trm_gradient = None
		self.num_segments = None
		self.num_below_trm = None
		self.model = None
		self.depth_interval = self.config["preprocessing"]["depth_interval"]
		self.positive_gradient_segment = []
		self.double_trm = []
		self.gradient = []

		self.MAX_TEMPERATURE_CHANGE = 2.0 # maximum temprature difference
		
		self.stable_gradient = config["algorithm"]["plr"]["stable_gradient"]
		self.stable_gradient_relaxed = config["algorithm"]["plr"]["stable_gradient_relaxed"]
		self.min_trm_gradient = self.config["algorithm"]["plr"]["min_trm_gradient"]
		self.max_error = self.config["algorithm"]["plr"]["max_error"]

	def get_gradient_from_segment(self,seg):
		"""
		Function to get gradients of each segment, 
		positive means the temperature is decreasing with depth

		Args:
			seg: a list [fitted line, point index]
		Returns:
			the gradient of seg
		"""
		return (seg[0][0] - seg[0][1]) / self.depth_interval

	def detect_double_trm(self, segment_list):
		"""
		Functions to detect double thermocline. The index of segments which represent
		double thermocline will be appended to doubleTRM

		Args:
			segmentList: a list stores all the segments
		Retures:
			None
		"""
		self.double_trm = []

		for i in range(1,len(segment_list)-1):
			seg_gradient = self.get_gradient_from_segment(segment_list[i])
			prev_seg_gradient = self.get_gradient_from_segment(segment_list[i-1])
			next_seg_gradient = self.get_gradient_from_segment(segment_list[i+1])

			if abs(seg_gradient) < self.stable_gradient and \
				prev_seg_gradient > self.min_trm_gradient and \
				next_seg_gradient > self.stable_gradient:
				self.double_trm.append(i)

		if len(self.double_trm)>0:
			logging.info("double thermocline detected")
			logging.info(self.double_trm)

	def detect_positive_gradient(self,segment_list):
		"""
		Functions to detect positive gradient, since positive gradient is abnormal. 
		The index of such segments will be appended to positiveSeg

		Args:
			segmentList: a list stores all the segments
		Retures:
			None
		"""

		self.positive_gradient_segment = []
		for i, seg in enumerate(segment_list):
			gradient = self.get_gradient_from_segment(seg)
			if gradient < -1 * self.stable_gradient:
				self.positive_gradient_segment.append(i)


	def detect(self, data, save_model=False):
		"""
		Function to detect the thermocline
		Args:
			data: a pandas dataframe
			saveModel: whether to save detection model
		Returns:
			None
		"""
		model = SegmentationModel(max_error=self.max_error)
		
		# detect the TRM features
		model.fit_predict(data.Temperature)
		segment_list = model.segment_list # segmentList is a list of [fitted line, point index]

		assert len(data.Depth) > 1
		
		# get the gradient of all segments
		gradient = [self.get_gradient_from_segment(seg) for seg in segment_list]
		max_gradient_index = np.argmax(gradient)
		
		# remove the segment caused by the noise
		if max_gradient_index == 0:
			tmpDepth = np.array(data.Depth[segment_list[max_gradient_index][1]])
			if tmpDepth[-1] - tmpDepth[0] < 2:
				# if the first segment is less than 2 meters and has the maximum gradient
				# then the first segment would be a noise or peak, need to remove
				logging.warning("first segment is affected by noise", tmpDepth)
				model.segment_list.pop(0)
				gradient = [self.get_gradient_from_segment(seg) for seg in segment_list]
				max_gradient_index = np.argmax(gradient)

		self.gradient = gradient

		if gradient[max_gradient_index] > self.min_trm_gradient: 
			# TRM gradient is above the maximum gradient
			# TRM is detected, which is the middle point of the segment with maximum gradient
			self.trm = data.Depth[int(np.mean(segment_list[max_gradient_index][1]))]

			# check whether gradient is stable
			# the gradients of first and last segment use different criteria
			gradient_is_stable = [abs(g) < self.stable_gradient for g in gradient]
			gradient_is_stable[0] = abs(gradient[0]) < self.stable_gradient_relaxed
			gradient_is_stable[-1] = abs(gradient[-1]) < self.stable_gradient_relaxed

			surface_temprature = model.segment_list[0][0][0]
			bottom_temperature = model.segment_list[-1][0][-1]
			
			lep_index = None
			uhy_index = None

			# detect the LEP
			for i in range(max_gradient_index):
				if not (gradient_is_stable[i] and model.segment_list[i][0][-1] - surface_temprature < self.MAX_TEMPERATURE_CHANGE):
					if i > 0:
						lep_index = model.segment_list[i - 1][1][-1]
					break

				if i == max_gradient_index - 1:
					lep_index = model.segment_list[i][1][-1]

			# detect the UHY
			for i in range(len(model.segment_list) - 1, max_gradient_index, -1):
				if not (gradient_is_stable[i] and model.segment_list[i][0][0] - bottom_temperature < self.MAX_TEMPERATURE_CHANGE):
					if i < len(model.segment_list) - 1:
						uhy_index = model.segment_list[i + 1][1][0]
					break

				if i == max_gradient_index + 1:
					uhy_index = model.segment_list[i][1][0]

			if lep_index:
				self.lep = data.Depth[lep_index]

			if uhy_index:
				self.uhy = data.Depth[uhy_index]
		else:
			logging.info("minimum gradient too low")
			logging.info(gradient[max_gradient_index]) 
			logging.info(self.min_trm_gradient)
			logging.info("No TRM deteted")
		
		self.trm_gradient = max(gradient)
		self.num_segments = len(segment_list)
		self.trm_idx = max_gradient_index
		
		self.detect_double_trm(segment_list)
		self.detect_positive_gradient(segment_list)

		if save_model:
			self.model = model


class Thermocline(object):
	"""
	Class to detect thermocline
	"""
	def __init__(self,config):
		self.config = config
		self.features = {}
		self.models = {}
		
	def detect(self, data, methods=["segmentation"], save_model=True):
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
				features[d + "_" + m] = None
		features["TRM_gradient_segment"] = None
		features["TRM_num_segment"] = None

		if "segmentation" in methods:
			try:
				model = ThermoclineSegmentation(self.config)
				model.detect(data, save_model=save_model)

				# the gradient of TRM
				features["TRM_gradient_segment"] = model.trm_gradient

				# the depth of TRM, LEP and UHY
				features["TRM_segment"] = model.trm
				features["LEP_segment"] = model.lep
				features["UHY_segment"] = model.uhy
				
				# the number of segments
				features["TRM_num_segment"] = model.num_segments

				# which segment is the TRM
				features["TRM_idx"] = model.trm_idx

				# how many double TRM sequences
				features["doubleTRM"] = len(model.double_trm)

				# how many positive gradient segments
				features["positiveGradient"] = len(model.positive_gradient_segment)

				# the gradient of the some key segments
				features["firstSegmentGradient"] = model.gradient[0]
				features["lastSegmentGradient"] = model.gradient[-1]
				features["lastButTwoSegmentGradient"] = model.gradient[-2]

				if save_model:
					self.models["segmentation"] = model.model

			except Exception as err:
				print("segmentation Fail")
				print(traceback.format_exc())
				
		return features


