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
def gauss_function(x, a, x0, sigma2,y0,k):
	'''
	x: x
	a: magnitude
	x0: center
	sigma: normalize factor/standard deviation
	y0: background level
	'''
	return a*np.exp(-(x-x0)**2/(2*sigma2))+y0+k*(x-x0)

def fitGaussian(x,y,x_mean,weight= None):
	# parameter a,sigma,k

	maxK = abs(0.5*(y[0]-y[-1])/(x[0]-x[-1]))
	bounds=([0,0,-0.5*maxK], [np.inf,np.inf,0.5*maxK])
	# bounds = (-np.inf,np.inf)
	if weight is None:
		popt, pcov = curve_fit(f=lambda x,a,sigma,k: gauss_function(x,a,x_mean,sigma,max(y)-a,k), xdata=x, ydata=y,bounds = bounds)
	else:
		raise ValueError("WLS not implemented")
		# popt, pcov = curve_fit(lambda x,a,sigma: gauss_function(x,a,x_mean,sigma,max(y)-a), x, y, sigma=weight)
	fit_y = gauss_function(x, popt[0], x_mean, popt[1],max(y)-popt[0],popt[2])
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



# fit the data with the predefined shape
def fitShape(y,direction,method="gaussian"): 
	"""
	return:
		fit_y: fitted values of y
		x_for_fit: x for fit
		y_for_fit: y labels
		popt: coefficients of the model
	"""
	if method == "gaussian":
		fit_func=fitGaussian
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


def getStableGradientPoints(curve,slopeThres,SNRThres,diffThres, dirc = "up"):
	# function to get boundary points based on slope and Signal noise ratio, 
	# could be used to detect peaks that can't fit by a Gaussian shape
	"""
		Input: curve: 
		slopeThres: the maximum gradient available
		SNRThres: the minimum SNR
		diffThres: 
		dirc: "up" means the shape, i.e. the half peak is going up; "down" means the shape is going down
	"""
	
	maxSlope = 0
	dataRange = max(curve)-min(curve)
	finalJ = 5

	if dirc == "up":
		for j in range(finalJ,len(curve)-finalJ):  # 3 is a parameter that 
			if len(curve[0:-j])<3:
				next

			slope,SNR,dataDiff = slope_SNR(curve[0:-j])
			slope_tmp,SNR_tmp,dataDiff_tmp = slope_SNR(curve[(j-3):(j+3)])
			# print slope_tmp
			maxSlope = max(maxSlope,slope_tmp)
			if slope < slopeThres*maxSlope and SNR > SNRThres and dataDiff < dataRange *diffThres:
				# leftBoundary = middleNode - j
				print "left",slope,SNR
				finalJ = j
				break
	else:
		for j in range(finalJ,len(curve)-finalJ):
			if len(curve[j:])<3:
				next
			slope,SNR,dataDiff = slope_SNR(curve[j:])
			slope_tmp,SNR_tmp,dataDiff_tmp = slope_SNR(curve[(j-3):(j+3)])
			
			maxSlope = max(maxSlope,slope_tmp)
			
			# print "cond1",slope < slopeThres*maxSlope
			# print "cond2",SNR > SNRThres
			# print "cond3",dataDiff < dataRange *diffThres

			if slope < slopeThres*maxSlope and SNR > SNRThres and dataDiff < dataRange *diffThres:
				# rightBoundary = middleNode+j
				finalJ = j
				print "right",slope,maxSlope,SNR
				break
	
	return finalJ

def zeroCrossing(signal, mode):
	'''
	find the index of points that intercept with x axis
	mode:
		0: return all indexes
		1: return only from positive to negative
		2: return only from negative to positive
	'''
	allIndex = np.where((signal[1:] * signal[:-1] < 0) == True)[0]
	if mode == 0:
		return allIndex+1  # +1 indicates return 1 in the example of [-1,1]
	elif mode == 1:
		return allIndex[signal[allIndex] > 0]+1
	elif mode == 2:
		return allIndex[signal[allIndex] < 0]+1
	else:
		raise ValueError("mode can only be 0,1,2")


def slope_SNR(x):
	# get the slope and SNR of the signal x
	n = len(x)
	l = np.poly1d(np.polyfit(range(n),x,1))(range(n))
	slope = l[1]-l[0]

	SNR = np.mean(x)/np.std(x)
	# SNR = 1/np.std(l-x)
	res = l - x
	dataDiff = abs(l[0]-l[-1])

	# print SNR,slope
	return abs(slope), SNR, dataDiff


def fit_error(x,xhat):
	# # # using R^2, Coefficient of determination
	# x_mean = np.mean(x)
	# SStot = sum((x - x_mean)**2)
	# SSres = sum((x-xhat)**2)
	# print "R^2",1-SSres/SStot
	return (np.corrcoef(x,xhat)[1,0])**2  # using r^2, not R^2 
	# print "abs(dx)/x (0.95,max)",np.percentile(abs(x-xhat)/x, 0.95),max(abs(x-xhat)/x)
	# return 1-SSres/SStot
	# return (np.corrcoef(x,xhat)[1,0]) # return pearson coefficient
	# print x,xhat
	# print np.percentile(abs(x-xhat)/x, 0.5),np.percentile(abs(x-xhat)/x, 0.9),np.percentile(abs(x-xhat)/x, 0.99)
	# return np.percentile(abs(x-xhat)/x, 0.95)
	# print "RMSE_median normalized",np.mean((x-xhat)**2)/np.mean(x)
	# return max(abs(x-xhat)/x)
	# return np.mean((x-xhat)**2)/np.mean(x) # return the normalized RMSE as the performance measurement

class peak(object):
	def __init__(self,config,method = "gaussian"):
		self.allPeaks = None
		self.shape_fit = []
		self.x = None
		self.method = method
		self.config = config
		self.boundaries = None

	def fit_predict(self,x):
		x = np.array(x)
		x_gradient = np.diff(x) # find the gradient of x, len(x_gradient) = len(x)-1, x_gradient[0] = x[1]-x[0]
		rawPeak = zeroCrossing(x_gradient, mode=1) 
		
		threshold = (max(x)-min(x))*self.config["minPeakMagnitude"]+min(x) # the minimum maginitude that a peak should reach

		rawPeak = self.initialFilter(rawPeak, x, threshold)

		rawPeak.append(len(x)-1)
		rawPeak = [0]+rawPeak

		peakHeightThreshold = (max(x)-min(x))*self.config["peakHeight"]  # a tuning parameter
		
		while True:
			shape_height = self.findPeakHeight(x,rawPeak) # the heights of all possible peaks in rawPeak
			
			if len(shape_height) ==0:
				break

			minHeightPeak_index = np.argmin(shape_height) # find the minimum height amoung the peaks

			if shape_height[minHeightPeak_index]<peakHeightThreshold:  # remove shallowest peak
				rawPeak.pop(minHeightPeak_index+1) # +1 because the starting point as the 1st point in rawPeak
			else:
				break

		self.boundaries = self.findBoundaries(x,rawPeak) # find the boundary of the peak in the rawPeak
		self.x = x
		self.allPeaks = self.featureExtraction() # extract the features of the peak
		
	def featureExtraction(self):

		if len(self.boundaries)==0:
			return None
		
		allPeaks = {}
		
		featureMapDic = {"peakIndex":"middleNode",
		"leftIndex_gradient":"leftBoundary_gradient",
		"rightIndex_gradient":"rightBoundary_gradient",
		"leftIndex_fit":"leftBoundary_fit",
		"rightIndex_fit":"rightBoundary_fit",
		"leftErr":"leftShape_err",
		"rightErr":"rightShape_err",
		"leftShapeFit":"leftShape",
		"rightShapeFit":"rightShape"}

		for k,v in featureMapDic.iteritems():
			allPeaks[k] = [boundary[v] for boundary in self.boundaries]		

		return pd.DataFrame(allPeaks)

	def findBoundaries(self,x,peaks):
		"""
		Function to find the boundaries of each peak
		x: curve magnitude
		peaks: the index of peaks
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

				# the boundary of left shape by analying the gradient
				leftBoundary_gradient = middleNode - getStableGradientPoints(leftData, self.config["slope"], self.config["SNR"], self.config["stableDiff"])
				
				# the boundary of left shape by fitting half Gaussian
				leftBoundary_fit = max(1,middleNode - int(np.ceil(2.5*np.sqrt(leftShape[3][1]))))  # use two and half sigma as the peak half width

			if i == len(peaks) -2: # get the right boundary of the last peak
				
				# the boundary of right shape by analying the gradient
				rightBoundary_gradient = middleNode + getStableGradientPoints(rightData, self.config["slope"], self.config["SNR"], self.config["stableDiff"],"down")
				
				# the boundary of right shape by fitting half Gaussian
				rightBoundary_fit = min(len(x)-2, middleNode + int(np.ceil(2.5*np.sqrt(rightShape[3][1]))))  #  use two and half sigma as the peak half width

			boundaries.append({
				"middleNode":middleNode,
				"leftBoundary_gradient":leftBoundary_gradient,
				"rightBoundary_gradient":rightBoundary_gradient,
				"leftShape_err":leftShape_err,
				"rightShape_err":rightShape_err,
				"leftShape":leftShape[0],
				"rightShape":rightShape[0],
				"leftBoundary_fit":leftBoundary_fit,
				"rightBoundary_fit":rightBoundary_fit
				})

		return boundaries


	def findPeakHeight(self,x,rawPeak):
		"""
		Calcualte the peak heights of all peaks in the rawPeak
		x: curve magnitude
		rawPeak: the index of peaks, the first and last element is the index of first and last point of x
		"""

		shape_height = []
		shape_fit = []
		boundaries = []

		for i in range(1,len(rawPeak)-1):
			
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
		n = len(x)

		rawPeakIndex = rawPeakIndex[x[rawPeakIndex]>threshold] # keep the index that have significant magnitude
		
		rawPeakIndex_new=[]

		if len(rawPeakIndex)==0:
			return rawPeakIndex_new

		# if rawPeakIndex[0] > 10:
			# rawPeakIndex_new.append(rawPeakIndex[0])

		# Combine two peaks if they are too close, choose the larger one
		rawPeakIndex_new = [rawPeakIndex[0]]

		for i, peak_ind in enumerate(rawPeakIndex[1:]):
			if peak_ind-rawPeakIndex_new[-1]>minDistance:
				rawPeakIndex_new.append(peak_ind)
			else:
				if x[peak_ind]>x[rawPeakIndex_new[-1]]: # if the next peak is larger than previous peak
					rawPeakIndex_new[-1] = peak_ind

		# for i in range(1,len(rawPeakIndex)):

		# 	if len(rawPeakIndex_new)==0:
		# 		rawPeakIndex_new.append(rawPeakIndex[i])
		# 		continue

		# 	# if n-rawPeakIndex[i]<10:
		# 		# continue

		# 	if rawPeakIndex[i]-rawPeakIndex_new[-1]>10:
		# 		rawPeakIndex_new.append(rawPeakIndex[i])
		# 	else:
		# 		if x[rawPeakIndex[i]]>x[rawPeakIndex_new[-1]]:
		# 			rawPeakIndex_new.pop()
		# 			rawPeakIndex_new.append(rawPeakIndex[i])
			
		return rawPeakIndex_new






def slopeSum(x,windowSize):
	# get the sum of positive slopes, maybe useful in the future
	gradient_x = np.diff(x)
	windows = np.array([ np.arange(i-windowSize,i) for i in range(windowSize,len(x))])
	y = []
	for seg in windows:
		y.append(np.sum(gradient_x[seg]*(gradient_x[seg]>0)))

	return np.array(y)