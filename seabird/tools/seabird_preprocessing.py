'''
	This file contains all the data noise removal functions
'''
import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline
import pywt
import logging

def window_smooth(x, window_len=11, window='hanning'):
	"""
	Function to smooth signal based moving window
	Args:
		x: signal
		window_len: window size
		window: window shape
	Returns
		y: smoothed data
	"""
	window_len = min(int(len(x)/5),window_len)
	if window_len % 2 ==0:
		window_len+=1
	if x.ndim != 1:
		raise ValueError, "smooth only accepts 1 dimension arrays."
	if x.size < window_len:
		raise ValueError, "Input vector needs to be bigger than window size."
	if window_len < 3:
		return x
	if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
		raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"

	s = np.r_[x[window_len - 1:0:-1], x, x[-1:-window_len:-1]]
	if window == 'flat':  # moving average
		w = np.ones(window_len, 'd')
	else:
		w = eval('np.' + window + '(window_len)')

	y = np.convolve(w / w.sum(), s, mode='valid')
	n = len(y)
	y = y[divmod(window_len - 1, 2)[0]:n - divmod(window_len - 1, 2)[0]]

	return y


def spline_smooth(x, smoothing_para=1):
	"""
	Function to smooth data by spline smooth
	Args:
		x: signal
	Returns
		y: smoothed data
	"""
	ind=range(1,len(x)+1)
	y = UnivariateSpline(ind, x, k=3, s=smoothing_para)
	return y(ind)


def testFilter(x, smoothing_para=1):
	'''
	Not implemented yet
	'''
	from scipy.signal import wiener, filtfilt, butter, gaussian, freqz
	pass


def dwt_smooth(x, smoothing_para={'wavelet':'bior3.1','level':0}):
	"""
	Function to smooth data by spline smooth
	Args:
		x: signal
		smoothing_para: dictionary with key of "wavelet" and "level"
	Returns:
		y: smoothed data
	"""
	wavelet=smoothing_para["wavelet"]
	level = smoothing_para["level"]
	num = len(x)
	
	maxlevel = pywt.dwt_max_level(data_len=num, filter_len=pywt.Wavelet(wavelet).dec_len)

	if level > 0:
		level = int(level)
	elif level < 0:
		level=maxlevel;
	else:  # level==0, choose the max level-4
		level = max(1, maxlevel - 4)

	# multilevel decomposition, return CA_n, CD_n, CD_n-1
	coeffs = pywt.wavedec(x, wavelet, 'cpd', level=level) 

	coeffs_size = []
	coeff_conj = []

	for coeff in coeffs:
		for j in coeff:
			coeff_conj.append(j)
		coeffs_size.append(len(coeff))

	coeff_zeros = []
	reconstruct_new = []

	for size in coeffs_size:
		coeff_zeros.append(np.zeros(size))
	for i in range(level + 1):
		new_coeff = coeff_zeros[:]
		new_coeff[i] = coeffs[i]
		reconstruct_new.append(pywt.waverec(new_coeff, wavelet)) # reconstruct the signal using CA_n + (CD_n +CD_n-1,...)

	y = reconstruct_new[0]  # set the output as the approximate signal
	
	return y


def init_filter(data, depth_threshold=1):
	"""
	function to remove the surface data (depth < threshold)
	Args:
		data: a pandas dataframe storing the sensor data
		depth_threshold: the depth threshold
	Returns:
		data: cleaned pandas dataframe
	"""
	data = data.copy()
	data = data[data.Depth > depth_threshold-0.5]
	data = data[data.Temperature>0]
	data = data[data.Depth<1000]
	logging.debug("finished init_filter")
	return data


def separate(sensordata):
	"""
	function to separate upcast and downcast
	Args:
		data: a pandas dataframe storing the sensor data
	Returns:
		downcast: downcast data
		upcast: upcast data
	"""
	maxDepth_ind = np.argmax(sensordata.Depth)
	downcast = sensordata.iloc[:maxDepth_ind, :]
	upcast = sensordata.iloc[maxDepth_ind:, :]
	return downcast, upcast


def resample(sensordata, interval=0.25):
	"""
	Function to resample data based on averaging or linear interpolation
	Args:
		data: a pandas dataframe storing the sensor data
		interval: averaging interval
	Returns:
		downcast: downcast data
	"""
	depth = np.array(sensordata.Depth)

	featureNum = sensordata.shape[1] - 1
	new_depth = np.arange(np.ceil(depth.min()), depth.max(), interval)
	new_sensordata = np.zeros((len(new_depth), sensordata.shape[1]-1))
	new_sensordata[:, 0] = new_depth

	dataAgged = True
	meanRange = []

	if min(np.abs(np.diff(depth)))<= 2*interval:
		dataAgged = False
		meanRange = [(depth >= d-interval) * (depth<=d+interval) >0 for d in new_depth]

	for i in range(1, sensordata.shape[1]-1):
		if sum(~sensordata.iloc[:,i].isnull())<1: # no data 
			new_sensordata[:, i] = np.nan
		else:
			if dataAgged:
				new_sensordata[:, i] = np.interp(new_depth, depth, sensordata.iloc[:, i])
			else:
				oldFeatures = np.array(sensordata.iloc[:, i])
				new_sensordata[:, i] = [np.mean(oldFeatures[meanRange[j]]) for j in range(len(new_depth))]
				
	return pd.DataFrame(new_sensordata,columns=sensordata.columns.values[:-1])


def transTransimissionToBAT(transmission):
	"""
	function to change transsmission to BAT
	"""
	return -np.log(transmission/100)*4
	
def transCondToSpecCond(conductitivty,temperature):
	"""
	function to conductivity to specific conductivity
	"""
	return conductitivty/(1+0.02*(self.temperature-25))


def filter(data,config):
	"""
	function to smooth each column of data
	Args:
		data: input data
		config: configuration dictionary
	Returns:
		data, the smoothed data
	"""

	for var in data.columns.values[1:]:

		if var in config["SmoothingMethod"]:
			smoothCfg=config["SmoothingMethod"][var]
		else:
			smoothCfg = config["SmoothingMethod"]["Other"]

		method=smoothCfg[0]
		# print var, method
		if method == "spline":
			data[var] = spline_smooth(data[var],smoothCfg[1])
		
		elif method == "dwt":
			smoothing_para={'wavelet':smoothCfg[1],'level':smoothCfg[2]}
			print smoothing_para
			data[var] = dwt_smooth(data[var],smoothing_para)

		elif method == "window":
			data[var] = window_smooth(data[var],smoothCfg[1])
		
	return data


def preprocessing(data,config):
	"""
	function to preprocess the raw input data by separating, resampling and smoothing
	Args:
		data: input data
		config: configuration dictionary
	Returns:
		downcast: the raw downcast
		filtered_data: the cleaned downcast
	"""
	downcast, upcast = separate(data)
	pre_data = init_filter(downcast,config["Preprocessing"]["badDepthThreshold"])
	if pre_data.shape[0]<1:
		return None,None
	pre_data_resample = resample(sensordata=pre_data, interval=config["Preprocessing"]["Interval"])

	if pre_data_resample.shape[0] % 2 > 0:
		pre_data_resample = pre_data_resample.iloc[:-1, :]

	filtered_data = filter(pre_data_resample, config)
	# filtered_data = pre_data_resample

	return downcast, filtered_data
	