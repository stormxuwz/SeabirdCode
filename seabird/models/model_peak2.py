import numpy as np
import logging
from scipy.optimize import curve_fit
from scipy.stats import t,laplace
from ..tools import seabird_preprocessing as spp
import matplotlib.pyplot as plt
import pandas as pd

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

def correctBoundaryPoint(shape,dirc = "left"):
	fit_y = shape[0]
	x_for_fit = shape[1]
	y_for_fit = shape[2]
	popt = shape[3]
	
	print "shape",shape

	zCIndex = zeroCrossing(fit_y - y_for_fit,0)
	
	print "ZCindex",zCIndex

	if dirc == "left":
		x_boundary = x_for_fit[-1] - popt[1]
		closeInd = np.argmin(zCIndex - x_boundary)
		new_width = x_for_fit[-1] - zCIndex[closeInd]
	else:
		x_boundary = x_for_fit[0] + popt[1]
		closeInd = np.argmin(zCIndex - x_boundary)
		new_width = x_for_fit[0] + zCIndex[closeInd]
	
	return new_width
	
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
	# detect the slope of
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

	return abs(slope), SNR, dataDiff

class peak(object):
	def __init__(self,config,method = "gaussian"):
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
			shape_fit,shape_height,boundaries = self.single_detect(x,rawPeak)
			logging.debug(peakHeightThreshold)
			logging.debug(shape_height)

			if len(shape_height) ==0:
				break
			minHeightPeak_index = np.argmin(shape_height)
			if shape_height[minHeightPeak_index]<peakHeightThreshold:  # remove shalloest peak
				rawPeak.pop(minHeightPeak_index+1) # +1 because the starting point as the 1st point in rawPeak
			else:
				break

		self.boundaries = boundaries
		self.x = x
		self.allPeaks = self.featureExtraction()
		
	def featureExtraction(self):
		# if self.shape_fit is None:
			# raise   "Fit shape first"
		if len(self.boundaries)==0:
			return None
		
		allPeaks = {"peakIndex":[],"leftIndex":[],"rightIndex":[],"leftStd":[],"rightStd":[]}

		for boundary in self.boundaries:
			allPeaks["peakIndex"].append(boundary[1])
			allPeaks["leftIndex"].append(boundary[0])
			allPeaks["rightIndex"].append(boundary[2])
			allPeaks["leftStd"].append(None)
			allPeaks["rightStd"].append(None)
			
		return pd.DataFrame(allPeaks)

	def single_detect(self,x,rawPeak):
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

			# print rightBoundary
			# leftShape = fitShape(leftData, "left",self.method)
			shape_fit = None

			leftShape_diff = leftData[-1]-min(leftData)
			rightShape_diff = rightData[0]-min(rightData)
			
			# recheck left boundary

			if i ==1:
				maxSlope = 0
				leftDataRange = max(leftData)-min(leftData)
				for j in range(5,len(leftData)-5):  # 5 is a parameter 
					if len(leftData[0:-j])<3:
						next

					slope,SNR,dataDiff = slope_SNR(leftData[0:-j])
					slope_tmp,SNR_tmp,tmp = slope_SNR(leftData[(j-3):(j+3)])
					# print slope_tmp
					maxSlope = max(maxSlope,slope_tmp)
					# maxSlope = max(maxSlope,slope)
					if slope < self.config["slope"]*maxSlope and SNR > self.config["SNR"] and dataDiff < leftDataRange *0.1:
						leftBoundary = middleNode - j
						# print "left",leftBoundary
						print "left",slope,SNR
						break
			
			# recheck right boundary
			if i == len(rawPeak) -2:
				maxSlope = 0
				rightDataRange = max(rightData)-min(rightData)

				for j in range(5,len(rightData)-5):
					if len(rightData[j:])<3:
						next
					slope,SNR,dataDiff = slope_SNR(rightData[j:])
					slope_tmp,SNR_tmp,tmp = slope_SNR(rightData[(j-3):(j+3)])
					# print slope_tmp
					maxSlope = max(maxSlope,slope_tmp)
					# maxSlope = max(maxSlope,slope)
					#print "cond1",slope < self.config["slope"]*maxSlope
					#print "cond2",SNR > self.config["SNR"]
					#print "cond3",dataDiff < rightDataRange*0.1
					if slope < self.config["slope"]*maxSlope and SNR > self.config["SNR"] and dataDiff < rightDataRange*0.2: # 0.01 is a parameter, 0.02 is a parameter
						rightBoundary = middleNode+j
						#print rightData[j:]
						print "right",slope,maxSlope,SNR
						break
			# print leftBoundary,rightBoundary

			boundaries.append([leftBoundary,rawPeak[i],rightBoundary])

			# check right data					

			# shape_fit.append({"left_index":rawPeak[i]-len(leftShape[1])+leftShape[1]+1,"left_data":leftShape[0],
			#                   "right_index":rightShape[1]+rawPeak[i],"right_data":rightShape[0],
			#                   "left_std":leftShape[3][1],"right_std":rightShape[3][1],
			#                   "left_corr":leftShape_corr,"right_corr":rightShape_corr})

			shape_height.append(min(rightShape_diff,leftShape_diff))  # take the minimum differences as the heights
			# print "left,right corr",leftShape_corr,rightShape_corr
			# print "shape_height",shape_height
		# print "boundaryies", boundaries
		return shape_fit,shape_height,boundaries

	
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