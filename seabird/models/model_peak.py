'''
Peak detection algorithm, contains both gradient analysis results and shape fitting results
'''
import numpy as np
import logging
from scipy.optimize import curve_fit
from scipy.stats import t,laplace
from ..tools import seabird_preprocessing as spp
import matplotlib.pyplot as plt
import pandas as pd

# Fit a gaussian functions
def gauss_function(x, a, x0, sigma2, y0, k):
	'''
	Define a Gaussian function with background trend
	Args:
		x: x
		a: magnitude
		x0: center
		sigma2: normalize factor/standard deviation ** 2
		y0: background level
		k: the background concentration trend
	Returns:
		the gaussian Y values
	'''
	return a * np.exp(-(x - x0) ** 2 / (2 * sigma2)) + y0 + k * (x - x0)

def fit_gaussian(x, y, x_mean, weight=None):
	"""
	Function to fit the Gaussian
	Args:
		x: x
		y: target y
		x_mean: the center of x
		weight: abandoned, not implemented
	Returens:
		fit_y: the fitted values
		popt: the estimated parameters
	"""

	maxK = abs((y[0]-y[-1])/(x[0]-x[-1]))
	# adding the boundary for the lienar trend, otherwise, 
	# the ascending or descending trend may only be captured by the linear trend
	
	bounds=([0,0,-0.15*maxK], [np.inf,np.inf,0.15*maxK])  
	# bounds = (-np.inf,np.inf)
	if weight is None:
		popt, pcov = curve_fit(f=lambda x,a,sigma2,k: gauss_function(x,a,x_mean,sigma2,max(y)-a,k), xdata=x, ydata=y,bounds = bounds)
	else:
		raise ValueError("WLS not implemented")
		# popt, pcov = curve_fit(lambda x,a,sigma: gauss_function(x,a,x_mean,sigma,max(y)-a), x, y, sigma=weight)
	fit_y = gauss_function(x, popt[0], x_mean, popt[1], max(y) - popt[0], popt[2])
	return fit_y,popt


# fit the t distribution shape
def t_pdf_function(x, a, x0, df):
	return a*t.pdf(x-x0,df)

def fit_t_pdf(x,y,x_mean,weight=None): 
	popt, pcov = curve_fit(lambda x,a,sigma: t_pdf_function(x,a,x_mean,sigma), x, y,method="trf")
	fit_y = t_pdf_function(x, popt[0], x_mean, popt[1])
	return fit_y,popt


# fit laplace function shape
def laplace_function(x,b,x0,df,y0): 
	return laplace.pdf((x-x0)/b)/b+y0

def fit_laplace(x,y,x_mean,weight=None):
	popt, pcov = curve_fit(lambda x,b,sigma: laplace_function(x,b,x_mean,sigma,max(y)-0.5/b), x, y,method="trf")
	fit_y = laplace_function(x, popt[0], x_mean, popt[1], max(y)-0.5/popt[0])
	return fit_y,popt



def fitShape(y,direction,method="gaussian"): 
	"""
	Functions to fit the data with the predefined shape
	Args:
		y: target values
		direction: "left" = fit the left (upper) part of Gaussian
			"right": fit the right (lower) part of the Gaussian
		method: shape to use

	Returns:
		fit_y: fitted values of y
		x_for_fit: x used in the fit
		y_for_fit: target values
		popt: estimated parameters
	"""
	if method == "gaussian":
		fit_func=fit_gaussian
	elif  method == "t":
		fit_func=fit_t_pdf
	elif method == "laplace":
		fit_func = fit_laplace
	else:
		raise "Method not available"

	if direction == "left": # fit the left part of the Gaussian shape
		y_for_fit = y
		x_for_fit = np.arange(len(y_for_fit))
		weight = None
		fit_y,popt = fit_func(x=x_for_fit, y=y_for_fit, x_mean=len(x_for_fit)-1, weight=weight)
			
	else:  # fit the right part of the Gaussian shape
		y_for_fit = y
		x_for_fit = np.arange(len(y_for_fit))
		# weight = range(1,len(y_for_fit)+1,1)
		weight = None
		fit_y,popt = fit_func(x=x_for_fit, y=y_for_fit,x_mean =0,weight=weight)

	return fit_y,x_for_fit, y_for_fit, popt


def zero_crossing(signal, mode):
	'''
	find the index of points that intercept with x axis
	Args:
		mode:
			0: return all indexes
			1: return only from positive to negative
			2: return only from negative to positive
	Returns:
		a list of all crossing points
	'''
	all_index = np.where((signal[1:] * signal[:-1] < 0) == True)[0]
	if mode == 0:
		return all_index + 1  # +1 indicates return 1 in the example of [-1,1]
	elif mode == 1:
		return all_index[signal[all_index] > 0] + 1
	elif mode == 2:
		return all_index[signal[all_index] < 0] + 1
	else:
		raise ValueError("mode can only be 0,1,2")

def fit_error(x, xhat):
	"""
	return the error of x and fitted x (xhat)
	"""
	# using r^2
	return (np.corrcoef(x,xhat)[1,0])**2  
	
class Peak(object):
	def __init__(self,config,method = "gaussian"):
		self.allPeaks = None
		self.shape_fit = []
		self.x = None
		self.method = method

		self.boundaries = None
		self.minPeakMagnitude = config["minPeakMagnitude"] # minimum peak magnitude
		self.peakHeight = config["peakHeight"]
		self.peakSize = config["peakSize"]
		self.peakMinInterval = config["peakMinInterval"]

	def fit_predict(self,x):
		"""
		Function to detect peak in signal x
		Args:
			x: input signal
		Returns:
			None
		"""
		x = np.array(x)
		x_gradient = np.diff(x) # find the gradient of x, len(x_gradient) = len(x)-1, x_gradient[0] = x[1]-x[0]
		rawPeak = zero_crossing(x_gradient, mode=1) 
		
		# the minimum maginitude that a peak should reach
		threshold = (max(x)-min(x))*self.minPeakMagnitude + min(x) 
		# the minimum height that a peak should have
		peakHeightThreshold = (max(x)-min(x)) * self.peakHeight

		
		rawPeak = self.initialFilter(rawPeak, x, threshold, self.peakMinInterval) # remove peaks by threshold

		# add the first and last points as the boundary
		rawPeak.append(len(x)-1)
		rawPeak = [0]+rawPeak

		# print(rawPeak)

		while True:
			# find the heights of all possible peaks in rawPeak
			shape_height = self.findPeakHeight(x,rawPeak)
			
			if len(shape_height) ==0:
				# no peak is detected
				break

			minHeightPeak_index = np.argmin(shape_height) # find the minimum height amoung the peaks

			if shape_height[minHeightPeak_index] < peakHeightThreshold:  # remove shallowest peak
				rawPeak.pop(minHeightPeak_index+1) # +1 because the starting point is the 0th point in rawPeak
			else:
				# all remaining peak is significant
				break

		self.boundaries = self.findBoundaries(x,rawPeak) # find the boundary of the peak in the rawPeak
		self.x = x

		self.allPeaks = self.featureExtraction() # extract the features of the peak
		
	def featureExtraction(self):
		"""
		Extract features from the fitted peaks
		Returns:
			a dataframe, with columns of 
			"peakIndex": the index of the peak point
			"leftIndex_fit": the left (upper) boundary detected by the Gaussian fitting methods
			"rightIndex_fit": the right (lower) boundary detected by the Gaussian fitting methods
			"leftErr":	the fitted error for left (upper) shape
			"rightErr":	 the fitted error for right (lower) shape
			
			"leftShapeFit":"leftShape",
			"rightShapeFit":"rightShape",
			
			"leftSigma": the std of the left Gaussian shape
			"rightSigma": the std of the right Gaussian shape
		"""

		if len(self.boundaries)==0:
			return None
		
		allPeaks = {}
		
		FEATURE_MAP = {
		"peakIndex":"middleNode",
		"leftIndex_fit":"leftBoundary_fit",
		"rightIndex_fit":"rightBoundary_fit",
		"leftErr":"leftShape_err",
		"rightErr":"rightShape_err",
		"leftShapeFit":"leftShape",
		"rightShapeFit":"rightShape",
		"leftSigma":"leftSigma",
		"rightSigma":"rightSigma"}

		for k,v in FEATURE_MAP.items():
			allPeaks[k] = [boundary[v] for boundary in self.boundaries]		

		return pd.DataFrame(allPeaks)

	def find_boundaries(self, x, peaks):
		"""
		Function to find the boundaries of each peak
		Args:
			x: signal
			peaks: the index of peaks
		Returns:
			boundaries: a list of dictionaries. 
			each dictionary contains information of a single peak
		"""
		boundaries = []

		for i in range(1,len(peaks)-1):

			leftNode = peaks[i-1]
			middleNode = peaks[i]
			rightNode = peaks[i+1]

			leftBoundary = np.argmin(x[leftNode:middleNode])+leftNode
			rightBoundary = np.argmin(x[middleNode:rightNode])+middleNode
			
			if i ==1: # for the first peak
				leftBoundary = 0
			
			if i == len(peaks)-2:  # for the last peak
				rightBoundary = len(x)-1

			leftData = x[leftBoundary:(peaks[i]+1)]
			rightData = x[peaks[i]:rightBoundary+1]

			# for left shape
			leftShape = fitShape(leftData, "left",self.method) # fit the half Gaussian to the left shape
			leftShape_err = fit_error(x = leftShape[2], xhat = leftShape[0]) # calculate the fitting error
			
			# for right shape
			rightShape = fitShape(rightData,"right",self.method) # fit the half Gaussian to the right shape
			rightShape_err = fit_error(x = rightShape[2], xhat = rightShape[0])  # calculate the fitting error
			
			# get peak boundary
			leftBoundary_fit = leftBoundary
			leftBoundary_gradient = leftBoundary

			rightBoundary_fit = rightBoundary
			rightBoundary_gradient = rightBoundary

			if i ==1: # get the left boundary of the first peak
				# the boundary of left shape by fitting half Gaussian
				# use two and half sigma as the peak half width
				leftBoundary_fit = max(1,middleNode - int(np.ceil(self.peakSize * np.sqrt(leftShape[3][1]))))  

			if i == len(peaks) -2: # get the right boundary of the last peak
				# the boundary of right shape by fitting half Gaussian
				# use two and half sigma as the peak half width
				rightBoundary_fit = min(len(x)-2, middleNode + int(np.ceil(self.peakSize * np.sqrt(rightShape[3][1])))) 

			boundaries.append({
				"middleNode":middleNode,
				"leftShape_err":leftShape_err,
				"rightShape_err":rightShape_err,
				"leftShape":leftShape[0],
				"rightShape":rightShape[0],
				"leftBoundary_fit":leftBoundary_fit,
				"rightBoundary_fit":rightBoundary_fit,
				"leftSigma": np.sqrt(leftShape[3][1]), # sqrt(sigma2) to get the sigma
				"rightSigma": np.sqrt(rightShape[3][1]) # sqrt(sigma2) to get the sigma
				})

		return boundaries


	def findPeakHeight(self,x,rawPeak):
		"""
		Calcualte the peak heights of all peaks in the rawPeak
		Args:
			x: signal
			rawPeak: the index of peaks, the first and last element is the index of first and last point of x
		Returns:
			shape_height: the height of each peaks 
		"""

		shape_height = []
		shape_fit = []
		boundaries = []

		for i in range(1,len(rawPeak)-1): # start from 1 to the second to the last
			
			leftNode = rawPeak[i-1]
			middleNode = rawPeak[i]
			rightNode =rawPeak[i+1]

			leftBoundary = np.argmin(x[leftNode:middleNode])+leftNode
			rightBoundary = np.argmin(x[middleNode:rightNode+1])+middleNode
			
			if i == 1: # the first peak
				leftBoundary = 0

			if i == len(rawPeak)-2: # the last peak
				rightBoundary = len(x)-1

			leftData = x[leftBoundary:(rawPeak[i]+1)] # including the peak
			rightData = x[rawPeak[i]:rightBoundary+1] # including the peak point

			leftShape_diff = leftData[-1]-min(leftData) # the height of the left shape
			rightShape_diff = rightData[0]-min(rightData) # the height of the right shape

			shape_height.append(min(rightShape_diff,leftShape_diff))  # take the minimum differences as the heights

		return shape_height

	
	def initialFilter(self,rawPeakIndex,x,threshold, minDistance=10):
		"""
		function to remove peaks based on minimum magnitude and merge close peaks
		Args:
			rawPeakIndex: the list stored all the index of peaks
			x: signal
			threshold: minimum magnitude threshold
			minDistance: the minimum distance two peaks should separate
		Returns:
			rawPeakIndex_new: a list containing peaks
		"""

		n = len(x)

		rawPeakIndex = rawPeakIndex[x[rawPeakIndex]>threshold] # keep the index that have significant magnitude
		
		rawPeakIndex_new=[]

		if len(rawPeakIndex)==0:
			return rawPeakIndex_new

		# Combine two peaks if they are too close, choose the larger one
		rawPeakIndex_new = [rawPeakIndex[0]]

		for i, peak_ind in enumerate(rawPeakIndex[1:]):
			if peak_ind-rawPeakIndex_new[-1]>minDistance:
				rawPeakIndex_new.append(peak_ind)
			else:
				if x[peak_ind]>x[rawPeakIndex_new[-1]]: # if the next peak is larger than previous peak
					rawPeakIndex_new[-1] = peak_ind
			
		return rawPeakIndex_new