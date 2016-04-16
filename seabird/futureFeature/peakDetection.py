import numpy as np
import logging
from scipy.optimize import curve_fit
from scipy.stats import t,laplace
from ..tools import seabird_preprocessing as spp
import matplotlib.pyplot as plt

def gauss_function(x, a, x0, sigma,y0):
	return a*np.exp(-(x-x0)**2/(2*sigma**2))+y0

def fitGaussian(x,y,x_mean,weight= None):
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

def calculate_error(x,y):
	return np.percentile(np.abs(x-y),90)


def fitShape(y,direction,method="gaussian"):
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

		# weight = range(len(y_for_fit),0,-1)
		weight = None
		fit_y,popt = fit_func(x_for_fit, y_for_fit, len(x_for_fit),weight)
			
	else:
		y_for_fit = y
		x_for_fit = np.arange(len(y_for_fit))
		weight = range(1,len(y_for_fit)+1,1)
		weight = None
		fit_y,popt = fit_func(x_for_fit, y_for_fit,0,weight)

	return fit_y,x_for_fit, y_for_fit, popt,

def slopeSum(x,windowSize):
	gradient_x = np.diff(x)
	windows = np.array([ np.arange(i-windowSize,i) for i in range(windowSize,len(x))])
	y = []
	for seg in windows:
		y.append(np.sum(gradient_x[seg]*(gradient_x[seg]>0)))

	return np.array(y)

class peak(object):
	def __init__(self,config,method = "gaussian"):
		self.peak = []
		self.shape_fit = []
		self.x=None
		self.method = method
		self.config = config

	def detect(self,x):
		x_gradient = np.diff(x)
		rawPeak = self._zeroCrossing(x_gradient, mode=1)
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
			shape_fit,shape_height = self.single_detect(x,rawPeak)
			logging.debug(peakHeightThreshold)
			logging.debug(shape_height)

			if len(shape_height) ==0:
				break
			minHeightPeak_index = np.argmin(shape_height)
			if shape_height[minHeightPeak_index]<peakHeightThreshold:  # remove shalloest peak
				rawPeak.pop(minHeightPeak_index+1) # +1 because the starting point as the 1st point in rawPeak
			else:
				break

		self.shape_fit = shape_fit
		self.x = x
		self.featureExtraction()

		return self.peak
		
	def featureExtraction(self):
		if self.shape_fit is None:
			raise   "Fit shape first"
		if len(self.shape_fit)==0:
			return
		
		for shape in self.shape_fit:
			peakIndex = shape["right_index"][0]

			leftIndex = max(0, shape["left_index"][0],int(peakIndex - 3* (shape["left_std"])))
			rightIndex = min(len(self.x)-1,shape["right_index"][-1],int(peakIndex + 3* (shape["right_std"])))

			self.peak.append([peakIndex,leftIndex, rightIndex])


	def single_detect(self,x,rawPeak):
		shape_height = []
		shape_fit = []

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

			# print rightBoundary
			leftShape = fitShape(leftData, "left",self.method)
			leftShape_diff = leftShape[2][-1]-min(leftShape[2])
			leftShape_corr = np.mean(abs(leftShape[0]-leftShape[2]))/(max(x)-min(x))

			if leftShape_corr>self.config["peakFitTol"]:  
				# the shape is not fit very well
				# back to recurison methods
				logging.info("Fitting data gradually -left")
				for k in range(3,len(leftData)):
					sub_leftData = leftData[-k:]
					sub_leftShape = fitShape(sub_leftData, "left",self.method)
					sub_leftShape_diff = sub_leftShape[2][-1]-min(sub_leftShape[2])
					sub_leftShape_corr = np.mean(abs(sub_leftShape[0]-sub_leftShape[2]))/(max(x)-min(x))
					
					if sub_leftShape_corr > self.config["peakFitTol"]:
						leftData = leftData[-k+1:]
						leftShape = fitShape(leftData, "left",self.method)
						leftShape_diff = leftShape[2][-1]-min(leftShape[2])
						leftShape_corr = np.mean(abs(leftShape[0]-leftShape[2]))/(max(x)-min(x))
						break
					# pre_sub_leftData = sub_leftData.copy()
					# pre_sub_leftShape = sub_leftShape.copy()
					# pre_sub_leftShape_diff = sub_leftShape_diff
					# pre_sub_leftShape_corr = sub_leftShape_corr


			rightShape = fitShape(rightData,"right",self.method)
			rightShape_diff = rightShape[2][0]-min(rightShape[2])
			rightShape_corr = np.mean(abs(rightShape[0]-rightShape[2]))/(max(x)-min(x))

			if rightShape_corr>0.08:
				# the shape is not fit very well
				# back to recurison methods
				logging.info("Fitting data gradually - right")
				for k in range(3,len(rightData)):
					sub_rightData = rightData[:k]
					sub_rightShape = fitShape(sub_rightData, "right",self.method)
					sub_rightShape_diff = sub_rightShape[2][0]-min(sub_rightShape[2])
					sub_rightShape_corr = np.mean(abs(sub_rightShape[0]-sub_rightShape[2]))/(max(x)-min(x))
					if sub_rightShape_corr > 0.08:
						rightData = rightData[:k-1]
						rightShape = fitShape(rightData, "right",self.method)
						rightShape_diff = rightShape[2][0]-min(rightShape[2])
						rightShape_corr = np.mean(abs(rightShape[0]-rightShape[2]))/(max(x)-min(x))
						break

			

			shape_fit.append({"left_index":rawPeak[i]-len(leftShape[1])+leftShape[1]+1,"left_data":leftShape[0],
			                  "right_index":rightShape[1]+rawPeak[i],"right_data":rightShape[0],
			                  "left_std":leftShape[3][1],"right_std":rightShape[3][1],
			                  "left_corr":leftShape_corr,"right_corr":rightShape_corr})

			shape_height.append(min(rightShape_diff,leftShape_diff))
			# print "left,right corr",leftShape_corr,rightShape_corr
			# print "shape_height",shape_height

		return shape_fit,shape_height

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
			return allIndex+1
		elif mode == 1:
			return allIndex[signal[allIndex] > 0]+1
		elif mode == 2:
			return allIndex[signal[allIndex] < 0]+1
		else:
			raise ValueError("mode can only be 0,1,2")

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