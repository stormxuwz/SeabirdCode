from futureFeature.peakDetection import peak as futurePeak
from peak_detection import peak
import numpy as np

class DCL:
	def __init__(self,config):
		self.peakNum = 0
		self.peakDepth = np.array([-99])
		self.magnitude = np.array([-99])

		self.config=config

		self.expert_peakDepth=-99
		self.boundaryMagnitude=np.array([[-99,-99]])
		self.boundaryDepth=np.array([[-99,-99]])

	def identify(self, data):
		myPeak = peak(self.config["Algorithm"]["Peak"])
		fluorescenceData=np.array(data.Fluorescence)
		depthData=np.array(data.Depth)
		
		peakIndex = myPeak.detect(fluorescenceData,debug=False)
		self.peakNum = len(peakIndex)
		
		if self.peakNum > 0:
			self.peakDepth = np.array([depthData[onePeak[0]] for onePeak in peakIndex])
			self.magnitude = np.array([fluorescenceData[onePeak[0]] for onePeak in peakIndex])
			self.boundaryMagnitude = np.array([fluorescenceData[onePeak[1:]] for onePeak in peakIndex])
			self.boundaryDepth = np.array([depthData[onePeak[1:]] for onePeak in peakIndex])

	def setExpert(self,data):
		self.expert_peakDepth=data

class DCL_future:
	def __init__(self,config):
		self.peakNum = 0
		self.peakDepth = np.array([-99])
		self.magnitude = np.array([-99])

		self.config=config
		self.myPeak = None
		self.expert_peakDepth=-99
		self.boundaryMagnitude=np.array([[-99,-99]])
		self.boundaryDepth=np.array([[-99,-99]])
		self.fitness = None

	def identify(self, data):
		self.myPeak = futurePeak(self.config["Algorithm"]["Peak"])
		fluorescenceData=np.array(data.Fluorescence)
		depthData=np.array(data.Depth)
		
		peakIndex = self.myPeak.detect(fluorescenceData)
		self.peakNum = len(peakIndex)
		# print "peakIndex",peakIndex
		if self.peakNum > 0:
			self.peakDepth = np.array([depthData[onePeak[0]] for onePeak in peakIndex])
			self.magnitude = np.array([fluorescenceData[onePeak[0]] for onePeak in peakIndex])
			self.boundaryMagnitude = np.array([fluorescenceData[onePeak[1:]] for onePeak in peakIndex])
			self.boundaryDepth = np.array([depthData[onePeak[1:]] for onePeak in peakIndex])
			corrList = []
			for shape in self.myPeak.shape_fit:
				corrList = corrList + [shape["left_corr"],shape["right_corr"]]

			self.fitness = np.mean(corrList)

	def setExpert(self,data):
		self.expert_peakDepth=data