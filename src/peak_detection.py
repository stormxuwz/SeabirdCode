from __future__ import division
import numpy as np
import matplotlib.pyplot as plt;
from tools.spectrogram import *
from tools.seabird_preprocessing import window_smooth as ws
import logging

class peak:
	def __init__(self, config):
		self.rawPeak = None
		self.peak = []
		self.data = None
		self.derivative = None
		self.config = config
		self.maxValue = None
		self.minValue = None
		self.maxGradient = None  # positive gradient
		self.minGradient = None  # negative gradient

	def detect(self, data, debug=False):
		self.data = np.array(data)
		self.gradient = self._getGradient(self.data, smoothed=True)

		self.rawPeak = self._zeroCrossing(self.gradient, mode=1)
		self._adjustIndex()

		self.maxValue = np.max(self.data)
		self.minValue = np.min(self.data)
		self.maxGradient = np.max(self.gradient)
		self.minGradient = np.min(self.gradient)

		nodes = [0]

		if debug:
			plt.figure()
			plt.plot(data, "o--")
			# plt.plot(self.rawPeak,data[self.rawPeak], "ro",markersize=10)
			plt.show()

		if debug:
			plt.figure()
			plt.plot(data, "o--")
			plt.plot(self.rawPeak,data[self.rawPeak], "ro",markersize=10)
			plt.show()


		# Initial Filter of raw peaks
		for i in self.rawPeak:
			if self._checkPeak(i):
				nodes.append(i)
		nodes.append(len(self.data) - 1)

		if debug:
			plt.figure()
			plt.plot(data, "o--")
			plt.plot(nodes,data[nodes], "ro",markersize=10)
			plt.show()

		if len(nodes) < 3:
			print "No Peak Found"
			return []

		allPeakNotSig=True

		while(allPeakNotSig):
			allPeakNotSig=False
			self.peak=[]
			allPeakHeights=[]

			for i_node, node in enumerate(nodes[1:-1]):
				leftBoundary, rightBoundary, peakHeight = self._findPeakBoundary(nodes[i_node], node, nodes[i_node + 2])
				allPeakHeights.append(peakHeight)
				self.peak.append([node,leftBoundary,rightBoundary])

			allPeakHeights=np.array(allPeakHeights)

			if len(allPeakHeights)==0:
				break
			minPeakIndex=allPeakHeights.argmin()
			minPeak=allPeakHeights[minPeakIndex]

			if minPeak<(np.max(self.data)-np.min(self.data))*self.config["peakHeight"]:
				logging.info("small peak")
				nodes.pop(minPeakIndex+1)
				allPeakNotSig=True

		logging.info("Final Peak")
		logging.info(self.peak)

		if debug:
			plt.figure()
			plt.plot(data, "o--")
			for peak in self.peak:
				plt.plot(peak, data[peak], "ro",markersize=10)
			plt.show()

		return self.peak

	def _adjustIndex(self, width=2):
		for i, rawIndex in enumerate(self.rawPeak):
			leftBoundary = max(0, rawIndex - width)
			rightBoundary = min(len(self.data), rawIndex+width)
			self.rawPeak[i] = np.argmax(self.data[leftBoundary:rightBoundary]) + leftBoundary

	def _findPeakBoundary(self, prev_node, node, post_node):
		# This is to find the boundary of one peak

		leftData = self.data[prev_node:node]
		rightData = self.data[node:post_node]
		leftGradient = self.gradient[prev_node:node]
		rightGradient = self.gradient[node:post_node]

		leftBoundary = 1
		rightBoundary = len(self.data) - 2

		leftDataBoundary=(np.max(leftData) - np.min(leftData)) * self.config["minBoundaryValue"] + np.min(leftData)
		rightDataBoundary=(np.max(rightData) - np.min(rightData)) * self.config["minBoundaryValue"] + np.min(rightData)

		leftStableIndex, = np.where(
			abs(leftGradient) < min(0.02 * 1000, (max(abs(leftGradient))-min(abs(leftGradient))) * self.config["maxBoundaryGradient"]+min(abs(leftGradient))))
			# abs(leftGradient)<min(0.02*1000,np.percentile(abs(leftGradient),30)))
		rightStableIndex, = np.where(
			abs(rightGradient) < min(0.02 * 1000, (max(abs(rightGradient))-min(abs(leftGradient))) * self.config["maxBoundaryGradient"]+min(abs(rightGradient))))
			# abs(rightGradient)<min(0.02*1000,np.percentile(abs(rightGradient),50)))

		leftSmallIndex, = np.where(leftData <leftDataBoundary)
			# leftData<np.percentile(leftData,20))
		rightSmallIndex, = np.where(rightData <rightDataBoundary)
			# rightData<np.percentile(rightData,20))

		if len(leftStableIndex)>0: # the left parts are continuous decreasing/increasing
			leftSearchRange = np.intersect1d(leftStableIndex, leftSmallIndex, True)
			if len(leftSearchRange)==0:
				leftSearchRange=leftSmallIndex
		else:
			leftSearchRange=[1]

		if len(rightStableIndex)>0:
			rightSearchRange = np.intersect1d(rightStableIndex, rightSmallIndex, True)
			if len(rightSearchRange)==0:
				rightSearchRange=rightSmallIndex
		else:
			rightSearchRange=[len(rightData)-2]

		if prev_node==0: # this is the first peak
			cumsum=np.cumsum(leftData[leftSearchRange]*(leftData[leftSearchRange]>leftDataBoundary*(1+self.config["tailTol"])))
			tmpIndex,=np.where(cumsum==0)
			leftSearchRange=leftSearchRange[tmpIndex]

		if post_node==len(self.data)-1: # this is the last peak
			# cumsum=np.cumsum(rightData[rightSearchRange]*(rightData[rightSearchRange]<rightDataBoundary))
			# rightSearchRange,
			for ind_i,i in enumerate(rightSearchRange):
				if (rightData[i:]<rightDataBoundary*self.config["tailTol"]).all():
					rightSearchRange=rightSearchRange[ind_i:]
					break

		if len(leftSearchRange) > 0:
			leftBoundary = leftSearchRange[-1] + prev_node
		if len(rightSearchRange) > 0:
			rightBoundary = rightSearchRange[0] + node

		peakHeightLeft=self.data[node]-self.data[leftBoundary]
		peakHeightRight=self.data[node]-self.data[rightBoundary]

		return leftBoundary, rightBoundary, min(peakHeightLeft,peakHeightRight)


	def _checkPeak(self, peakIndex):

		peakNeighbor = [max(0, peakIndex - 10), min(peakIndex + 10, len(self.data))]

		peakValue = self.data[peakIndex]
		largestGradientLeft = np.max(abs(self.gradient[peakNeighbor[0]:peakIndex]))
		largestGradientRight = np.max(abs(self.gradient[peakIndex:peakNeighbor[1]]))

		maxGradient = np.max(abs(self.gradient))

		# peak value should be large enough
		if peakValue < (self.maxValue - self.minValue) * self.config["minPeakMagnitude"] + self.minValue:
		# if peakValue < np.percentile(self.data, 70):
			return False

		# eliminate peak boundary with small gradient
		# if largestGradientLeft < maxGradient * self.config["minBoundaryGradient"] or \
		# 				largestGradientRight < maxGradient * self.config["minBoundaryGradient"]:
		if largestGradientLeft<np.percentile(abs(self.gradient),30) or largestGradientRight<np.percentile(abs(self.gradient),30):
			return False

		return True

	def changeConfig(self, _config={}):
		config={}
		for item in _config:
			config[item] = _config[item]

		return config

	def _zeroCrossing(self, signal, mode):
		'''
		find the index of points that intercept with x axis
		mode:
			0: return all indexes
			1: return only from positive to negative
			2: return only from negative to positive
		'''
		allIndex = np.where((signal[1:] * signal[:-1] < 0) == True)[0]

		if mode == 0:
			return allIndex
		elif mode == 1:
			return allIndex[signal[allIndex] > 0]
		elif mode == 2:
			return allIndex[signal[allIndex] < 0]
		else:
			raise ValueError("mode can only be 0,1,2")

	def _getGradient(self, signal, smoothed=True):
		'''
			backward gradient calculation
		'''
		gradient = np.diff(signal)
		if smoothed is True:
			gradient = ws(gradient)
		# print np.transpose(gradient)
		return np.transpose(gradient)

	def plot(self):
		pass