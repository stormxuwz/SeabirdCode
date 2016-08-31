import numpy as np
import logging
from scipy.optimize import curve_fit
from scipy.stats import t,laplace
from ..tools import seabird_preprocessing as spp
import matplotlib.pyplot as plt
import pandas as pd

'''
Peak detection algorithm, contains both gradient analysis results and shape fitting results

'''

def gauss_function(x, a, x0, sigma,y0):
	'''
	x: x
	a: magnitude
	x0: center
	sigma: normalize factor/standard deviation
	y0: background level
	'''
	return a*np.exp(-(x-x0)**2/(2*sigma**2))+y0

def fitGaussian(x,y,x_mean,weight= None):
	# Fit a gaussian functions
	if weight is None:
		popt, pcov = curve_fit(lambda x,a,sigma: gauss_function(x,a,x_mean,sigma,max(y)-a), x, y,maxfev=2000)
	else:
		popt, pcov = curve_fit(lambda x,a,sigma: gauss_function(x,a,x_mean,sigma,max(y)-a), x, y, sigma=weight,maxfev=2000)
	fit_y = gauss_function(x, popt[0], x_mean, popt[1],max(y)-popt[0])
	return fit_y,popt

def t_pdf_function(x, a, x0, df):
	return a*t.pdf(x-x0,df)

def fit_t_pdf(x,y,x_mean,weight=None):
	popt, pcov = curve_fit(lambda x,a,sigma: t_pdf_function(x,a,x_mean,sigma), x, y,method="trf")
	fit_y = t_pdf_function(x, popt[0], x_mean, popt[1])
	return fit_y,popt

def laplace_function(x,b,x0,df,y0):
	return laplace.pdf((x-x0)/b)/b+y0

def fit_laplace(x,y,x_mean,weight=None):
	popt, pcov = curve_fit(lambda x,b,sigma: laplace_function(x,b,x_mean,sigma,max(y)-0.5/b), x, y,method="trf")
	fit_y = laplace_function(x, popt[0], x_mean, popt[1], max(y)-0.5/popt[0])
	return fit_y,popt

def fitShape(y,direction,method="gaussian"):
	# fit the data with the predefined shape
	if method == "gaussian":
		fit_func=fitGaussian
	elif  method == "t":
		fit_func=fit_t_pdf
	elif method == "laplace":
		fit_func = fit_laplace
	else:
		raise "Method not available"

	if direction == "left":
		y_for_fit = y
		x_for_fit = np.arange(len(y_for_fit))
		weight = None
		fit_y,popt = fit_func(x_for_fit, y_for_fit, len(x_for_fit),weight)
			
	else:
		y_for_fit = y
		x_for_fit = np.arange(len(y_for_fit))
		weight = range(1,len(y_for_fit)+1,1)
		weight = None
		fit_y,popt = fit_func(x_for_fit, y_for_fit,0,weight)

	return fit_y,x_for_fit, y_for_fit, popt

def slopeSum(x,windowSize):
	# get the sum of positive slopes, maybe useful in the future
	gradient_x = np.diff(x)
	windows = np.array([ np.arange(i-windowSize,i) for i in range(windowSize,len(x))])
	y = []
	for seg in windows:
		y.append(np.sum(gradient_x[seg]*(gradient_x[seg]>0)))

	return np.array(y)


def getBoundaryPoints(curve,slopeThres,SNRThres,diffThres, dirc = "up"):
	# function to get boundary points
	# up means the shape, i.e. the half peak is going up and down means the shape is going down
	# boundary points is only for those curve that can't not be fit with Gaussian shape

	maxSlope = 0
	dataRange = max(curve)-min(curve)
	finalJ = 5

	if dirc == "up":
		for j in range(finalJ,len(curve)-finalJ):  # 5 is a parameter that 
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
			return allIndex+1
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
	# print x-l
	# print np.mean(x),np.std(x)
	SNR = np.mean(x)/np.std(x)
	# print max(abs(l-x))
	# SNR = 1/np.std(l-x)
	res = l - x
	dataDiff = abs(l[0]-l[-1])

	# print SNR,slope
	return abs(slope), SNR, dataDiff

class peak(object):
	def __init__(self,config,method = "gaussian"):
		print "Using Peak3 models"
		self.allPeaks = None
		self.shape_fit = []
		self.x=None
		self.method = method
		self.config = config
		self.boundaries = None

	def fit_predict(self,x):
		x = np.array(x)
		x_gradient = np.diff(x)
		rawPeak = zeroCrossing(x_gradient, mode=1)
		threshold = (max(x)-min(x))*self.config["minPeakMagnitude"]+min(x) # a tuning parameter

		rawPeak = self.initialFilter(rawPeak, x, threshold)
		
		rawPeak.append(len(x)-1)
		rawPeak = [0]+rawPeak

		peakHeightThreshold = (max(x)-min(x))*self.config["peakHeight"]  # a tuning parameter
		
		logging.info(x)
		logging.info("rawPeak")
		logging.info(rawPeak)
		logging.info("peakHeightThreshold = "+str(peakHeightThreshold))

		while True:
			shape_height = self.singlePeakAnalysis(x,rawPeak)
			
			logging.debug(peakHeightThreshold)
			logging.debug(shape_height)

			if len(shape_height) ==0:
				break

			minHeightPeak_index = np.argmin(shape_height)
			if shape_height[minHeightPeak_index]<peakHeightThreshold:  # remove shalloest peak
				rawPeak.pop(minHeightPeak_index+1) # +1 because the starting point as the 1st point in rawPeak
			else:
				break

		# print "rawPeaks",rawPeak
		self.boundaries = self.findBoundaries(x,rawPeak)
		# print "boundaries", self.boundaries
		self.x = x
		self.allPeaks = self.featureExtraction()
		
	def featureExtraction(self):
		# if self.shape_fit is None:
			# raise   "Fit shape first"
		if len(self.boundaries)==0:
			return None
		
		allPeaks = {
		"peakIndex":[],
		"leftIndex_gradient":[],
		"rightIndex_gradient":[],
		"leftIndex_fit":[],
		"rightIndex_fit":[],
		"leftErr":[],
		"rightErr":[],
		"leftShapeFit":[],
		"rightShapeFit":[]}

		for boundary in self.boundaries:
			allPeaks["peakIndex"].append(boundary["middleNode"])
			
			allPeaks["leftIndex_gradient"].append(boundary["leftBoundary_gradient"])
			allPeaks["rightIndex_gradient"].append(boundary["rightBoundary_gradient"])
			
			allPeaks["leftIndex_fit"].append(boundary["leftBoundary_fit"])
			allPeaks["rightIndex_fit"].append(boundary["rightBoundary_fit"])

			allPeaks["leftErr"].append(boundary["leftShape_err"])
			allPeaks["rightErr"].append(boundary["rightShape_err"])
			allPeaks["leftShapeFit"].append(boundary["leftShape"])
			allPeaks["rightShapeFit"].append(boundary["rightShape"])

		return pd.DataFrame(allPeaks)

	def findBoundaries(self,x,peaks):
		# find the boundaries for peaks
		boundaries = []

		for i in range(1,len(peaks)-1):
			# Logger Info
			logging.info(i)
			logging.info("peaks i = %d" %(peaks[i]))

			leftNode = peaks[i-1]
			middleNode = peaks[i]
			rightNode =peaks[i+1]

			leftBoundary = np.argmin(x[leftNode:middleNode])+leftNode
			rightBoundary = np.argmin(x[middleNode:rightNode])+middleNode
			
			if i ==1:
				leftBoundary = 0
			if i == len(peaks)-2:
				rightBoundary = len(x)-1

			leftData = x[leftBoundary:(peaks[i]+1)]
			rightData = x[peaks[i]:rightBoundary+1]

			# for left shape
			leftShape = fitShape(leftData, "left",self.method)
			leftShape_err = np.mean(abs(leftShape[0]-leftShape[2]))/(max(x)-min(x)) # approximation level
			# leftShape_diff = leftShape[2][-1]-min(leftShape[2]) # using fitted shape
			
			# for right shape
			rightShape = fitShape(rightData,"right",self.method)
			rightShape_err = np.mean(abs(rightShape[0]-rightShape[2]))/(max(x)-min(x))
			# rightShape_diff = rightShape[2][0]-min(rightShape[2])
			
			# get peak boundary
			leftBoundary_fit = leftBoundary
			leftBoundary_gradient = leftBoundary

			rightBoundary_fit = rightBoundary
			rightBoundary_gradient = rightBoundary

			if i ==1: # get the left boundary of the first peak
				# if leftShape_err > self.config["peakFitTol"]: # If the Gaussian shape doesn't fit well
					# print "left shape not fit"
				leftBoundary_gradient = middleNode - getBoundaryPoints(leftData, self.config["slope"], self.config["SNR"], self.config["stableDiff"])
				# else:
				leftBoundary_fit = max(1,middleNode - int(np.ceil(3*leftShape[3][1])))  # use three sigma as the peak half width

			if i == len(peaks) -2: # get the right boundary of the last peak
				# if rightShape_err > self.config["peakFitTol"]: # If the Gaussian shape doesn't fit well
					# print "right shape not fit"
				rightBoundary_gradient = middleNode + getBoundaryPoints(rightData, self.config["slope"], self.config["SNR"], self.config["stableDiff"],"down")
				# else:
				rightBoundary_fit = min(len(x)-2,middleNode + int(np.ceil(3*rightShape[3][1])))  #  use three sigma as the peak half width

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
		# print boundaries
		return boundaries
	
	def singlePeakAnalysis(self,x,rawPeak):
		shape_height = []
		shape_fit = []

		boundaries = []

		for i in range(1,len(rawPeak)-1):
			# Logger Info
			logging.info(i)
			logging.info("rawPeak i = %d" %(rawPeak[i]))

			leftNode = rawPeak[i-1]
			middleNode = rawPeak[i]
			rightNode =rawPeak[i+1]

			leftBoundary = np.argmin(x[leftNode:middleNode])+leftNode
			rightBoundary = np.argmin(x[middleNode:rightNode])+middleNode
			
			if i ==1:
				leftBoundary = 0
			if i == len(rawPeak)-2:
				rightBoundary = len(x)-1

			leftData = x[leftBoundary:(rawPeak[i]+1)]
			rightData = x[rawPeak[i]:rightBoundary+1]

			leftShape_diff = leftData[-1]-min(leftData)
			rightShape_diff = rightData[0]-min(rightData)

			shape_height.append(min(rightShape_diff,leftShape_diff))  # take the minimum differences as the heights

		return shape_height

	
	def initialFilter(self,rawPeakIndex,x,threshold):
		n = len(x)
		rawPeakIndex = rawPeakIndex[x[rawPeakIndex]>threshold]
		rawPeakIndex_new=[]
		if len(rawPeakIndex)==0:
			return rawPeakIndex_new

		if rawPeakIndex[0] > 10:
			rawPeakIndex_new.append(rawPeakIndex[0])

		for i in range(1,len(rawPeakIndex)):
			if len(rawPeakIndex_new)==0:
				rawPeakIndex_new.append(rawPeakIndex[i])
				continue

			if n-rawPeakIndex[i]<10:
				continue
			if rawPeakIndex[i]-rawPeakIndex_new[-1]>10:
				rawPeakIndex_new.append(rawPeakIndex[i])
			else:
				if x[rawPeakIndex[i]]>x[rawPeakIndex_new[-1]]:
					rawPeakIndex_new.pop()
					rawPeakIndex_new.append(rawPeakIndex[i])
			
		return rawPeakIndex_new