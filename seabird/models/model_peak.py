'''
Peak detection algorithm, contains both gradient analysis results and shape fitting results
'''
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import t,laplace
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
	return fit_y, popt


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


def fit_shape(y,direction,method="gaussian"): 
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
		self.all_peaks = None
		self.shape_fit = []
		self.x = None
		self.method = method

		self.boundaries = None
		self.peak_minimum_magnitude = config["minPeakMagnitude"] # minimum peak magnitude
		self.peak_height = config["peakHeight"]
		self.peak_size = config["peakSize"]
		self.peak_minimum_interval = config["peakMinInterval"]

	def fit_predict(self, x):
		"""
		Function to detect peak in signal x
		Args:
			x: input signal
		Returns:
			None
		"""
		x = np.array(x)
		x_gradient = np.diff(x) # find the gradient of x, len(x_gradient) = len(x)-1, x_gradient[0] = x[1]-x[0]
		raw_peaks = zero_crossing(x_gradient, mode=1) 
		
		# the minimum maginitude that a peak should reach
		threshold = (max(x) - min(x)) * self.peak_minimum_magnitude + min(x) 
		# the minimum height that a peak should have
		peak_height_threshold = (max(x) - min(x)) * self.peak_height
		raw_peaks = self.initial_filter(raw_peaks, x, threshold, self.peak_minimum_interval) # remove peaks by threshold

		# add the first and last points as the boundary
		raw_peaks = [0] + raw_peaks + [len(x)-1]

		while True:
			# find the heights of all possible peaks in rawPeak
			shape_height = self.find_peak_heights(x, raw_peaks)
			
			if len(shape_height) == 0:
				# no peak is detected
				break

			minimum_peak_height_index = np.argmin(shape_height) # find the minimum height amoung the peaks

			if shape_height[minimum_peak_height_index] < peak_height_threshold:  # remove shallowest peak
				raw_peaks.pop(minimum_peak_height_index + 1) # +1 because the starting point is the 0th point in rawPeak
			else:
				# all remaining peak is significant
				break

		self.boundaries = self.find_boundaries(x, raw_peaks) # find the boundary of the peak in the rawPeak
		self.x = x
		self.all_peaks = self.feature_extraction() # extract the features of the peak
		
	def feature_extraction(self):
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
		
		result = {}
		
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
			result[k] = [boundary[v] for boundary in self.boundaries]		

		return pd.DataFrame(result)

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

		for i in range(1, len(peaks) - 1):

			prev_point = peaks[i - 1]
			curr_point = peaks[i]
			next_point = peaks[i + 1]

			left_boundary_index = np.argmin(x[prev_point : curr_point]) + prev_point
			right_boundary_index = np.argmin(x[curr_point : next_point + 1]) + curr_point
			
			if i == 1: # for the first peak
				left_boundary_index = 0
			
			if i == len(peaks)-2:  # for the last peak
				right_boundary_index = len(x)-1

			left_data = x[left_boundary_index:(peaks[i] + 1)]
			right_data = x[peaks[i]:right_boundary_index + 1]

			# for left shape
			left_shape = fit_shape(left_data, "left", self.method) # fit the half Gaussian to the left shape
			left_shape_error = fit_error(x=left_shape[2], xhat=left_shape[0]) # calculate the fitting error
			
			# for right shape
			right_shape = fit_shape(right_data,"right", self.method) # fit the half Gaussian to the right shape
			right_shape_error = fit_error(x=right_shape[2], xhat=right_shape[0])  # calculate the fitting error

			# change the boundary 
			if i == 1: # get the left boundary of the first peak
				# the boundary of left shape by fitting half Gaussian
				# use two and half sigma as the peak half width
				left_boundary_index = max(1, curr_point - int(np.ceil(self.peak_size * np.sqrt(left_shape[3][1]))))  

			if i == len(peaks) -2: # get the right boundary of the last peak
				# the boundary of right shape by fitting half Gaussian
				# use two and half sigma as the peak half width
				right_boundary_index = min(len(x)-2, curr_point + int(np.ceil(self.peak_size * np.sqrt(right_shape[3][1])))) 

			boundaries.append({
				"middleNode":curr_point,
				"leftShape_err":left_shape_error,
				"rightShape_err":right_shape_error,
				"leftShape":left_shape[0],
				"rightShape":right_shape[0],
				"leftBoundary_fit":left_boundary_index,
				"rightBoundary_fit":right_boundary_index,
				"leftSigma": np.sqrt(left_shape[3][1]), # sqrt(sigma2) to get the sigma
				"rightSigma": np.sqrt(right_shape[3][1]) # sqrt(sigma2) to get the sigma
				})

		return boundaries


	def find_peak_heights(self, x, raw_peaks):
		"""
		Calcualte the peak heights of all peaks in the rawPeak
		Args:
			x: signal
			rawPeak: the index of peaks, the first and last element is the index of first and last point of x
		Returns:
			shape_height: the height of each peaks 
		"""

		shape_height = []

		for i in range(1, len(raw_peaks) - 1): # start from 1 to the second to the last
			prev_point = raw_peaks[i - 1]
			curr_point = raw_peaks[i]
			next_point = raw_peaks[i + 1]

			left_boundary_index = np.argmin(x[prev_point : curr_point]) + prev_point
			right_boundary_index = np.argmin(x[curr_point : next_point + 1]) + curr_point
			
			if i == 1: # the first peak
				left_boundary_index = 0

			if i == len(raw_peaks) - 2: # the last peak
				right_boundary_index = len(x) - 1

			left_data = x[left_boundary_index : (curr_point + 1)] # including the peak
			right_data = x[curr_point : right_boundary_index + 1] # including the peak point

			left_peak_height = x[curr_point] - min(left_data) # the height of the left shape
			right_peak_height = x[curr_point] - min(right_data) # the height of the right shape

			shape_height.append(min(left_peak_height, right_peak_height))  # take the minimum differences as the heights

		return shape_height

	
	def initial_filter(self, raw_peaks, x, threshold, minimum_point_distance=10):
		"""
		function to remove peaks based on minimum magnitude and merge close peaks
		Args:
			raw_peaks: the list stored all the index of peaks
			x: signal
			threshold: minimum magnitude threshold
			minimum_point_distance: the minimum distance two peaks should separate
		Returns:
			raw_peaks_new: a list containing peaks
		"""

		n = len(x)
		raw_peaks = raw_peaks[x[raw_peaks] > threshold] # keep the index that have significant magnitude
		raw_peaks_new = []

		if len(raw_peaks) == 0:
			return raw_peaks_new

		# Combine two peaks if they are too close, choose the larger one
		raw_peaks_new = [raw_peaks[0]]

		for i, peak_ind in enumerate(raw_peaks[1:]):
			if peak_ind - raw_peaks_new[-1] > minimum_point_distance:
				raw_peaks_new.append(peak_ind)
			else:
				if x[peak_ind] > x[raw_peaks_new[-1]]: # if the next peak is larger than previous peak
					raw_peaks_new[-1] = peak_ind
			
		return raw_peaks_new