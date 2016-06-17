'''
	This file contains all the data noise removal functions
'''
import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline
import pywt
import logging

def window_smooth(x, window_len=11, window='hanning'):
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

	wavelet=smoothing_para["wavelet"]
	level = smoothing_para["level"]
	num = len(x)
	
	maxlevel = pywt.dwt_max_level(data_len=num, filter_len=pywt.Wavelet(wavelet).dec_len)

	if level > 0:
		level = int(level)
	elif level < 0:
		level=maxlevel;
	else:  # level==0
		level = max(1, maxlevel - 3)

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
		reconstruct_new.append(pywt.waverec(new_coeff, wavelet))

	y = reconstruct_new[0]  # approximate
	
	return y


def init_filter(data, depth_threshold=1):  # Remove the data on the surface
	data = data[data.Depth > depth_threshold]
	# data = data[data.Depth < 1000]
	data = data[data.Temperature>0]
	data = data[data.Depth<1000]
	logging.debug("finished init_filter")
	return data


def separate(sensordata):
	maxDepth_ind = np.argmax(sensordata.Depth)
	downcast = sensordata.iloc[:maxDepth_ind, :]
	upcast = sensordata.iloc[maxDepth_ind:, :]
	return downcast, upcast


def resample(sensordata, interval=0.25):
	depth = sensordata.Depth

	featureNum = sensordata.shape[1] - 1
	new_depth = np.arange(np.ceil(depth.min()), depth.max(), interval)
	new_sensordata = np.zeros((len(new_depth), sensordata.shape[1]-1))
	new_sensordata[:, 0] = new_depth

	for i in range(1, sensordata.shape[1]-1):
		if sum(~sensordata.iloc[:,i].isnull())<1:
			new_sensordata[:, i] = np.nan
		else:
			new_sensordata[:, i] = np.interp(new_depth, depth, sensordata.iloc[:, i])

	return pd.DataFrame(new_sensordata,columns=sensordata.columns.values[:-1])


def transTransimissionToBAT(transmission):
	return -np.log(transmission/100)*4
	
def transCondToSpecCond(conductitivty,temperature):
	return conductitivty/(1+0.02*(self.temperature-25))


def filter(data,config):
	for var in data.columns.values[1:]:

		if var in config["SmoothingMethod"]:
			smoothCfg=config["SmoothingMethod"][var]
		else:
			smoothCfg = config["SmoothingMethod"]["Other"]

		method=smoothCfg[0]
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
	downcast, upcast = separate(data)
	pre_data = init_filter(downcast)
	if pre_data.shape[0]<1:
		return None,None
	pre_data_resample = resample(sensordata=pre_data, interval=config["Preprocessing"]["Interval"])

	if pre_data_resample.shape[0] % 2 > 0:
		pre_data_resample = pre_data_resample.iloc[:-1, :]

	filtered_data = filter(pre_data_resample, config)

	return downcast, filtered_data
	