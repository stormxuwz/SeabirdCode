from __future__ import division;
from hmmlearn import hmm
from sklearn import preprocessing as pp
import numpy as np
import pandas as pd
from scipy import signal


def window_fft(x):  # Calulate the Power
	hamming_window = np.hamming(len(x))
	n = len(x)
	fftx = np.fft.rfft((x - x.mean()) * hamming_window)
	# fftx=np.fft.rfft(signal.detrend(x)*hamming_window)

	return np.array(abs(fftx))

def extractFeatures(data, w=10):
	'''
	data: a data frame that with depth as first column and the variable as the second column
	w: window for windowed fft
	'''

	N = data.shape[0]
	signalFeature = pd.DataFrame(np.zeros((N - 2 * w, 4)),columns=['Depth','Var','Power','Gradient'])
	variableGradient = np.diff(data.iloc[:,1])

	spectrogram = np.array([window_fft(data.iloc[i-w:i+w,1]) for i in range(w,N-w)])
	
	# x1=data.iloc[43-w:43+w,1]
	# x2=data.iloc[20-w:20+w,1]
	# hw = np.hamming(len(x1))

	# plt.figure()
	# plt.plot(window_fft(x1),"ro")
	# plt.plot(window_fft(x2),"go")


	# plt.figure()
	# plt.plot(x1,"ro")
	# plt.plot(x2,"go")
	# plt.plot(signal.detrend(x1),"r+")
	# plt.plot(signal.detrend(x2),"g+")
	# plt.show()

	# print spectrogram
	signalFeature.Depth=np.array(data.Depth[w:N-w])
	signalFeature.Power=np.sum(spectrogram**2,axis=1)
	signalFeature.Var=np.array(data.iloc[w:N-w,1])
	signalFeature.Gradient=variableGradient[w:N-w]

	return signalFeature

def hmmModel_2(dataSet,nc=2,lag=False):
	np.random.seed()
	n = dataSet.shape[0]
	HMM_data = pp.scale(dataSet[["Var","Power"]])
	
	transmat = np.zeros((2, 2))
	transmat[0, 1] = 1/n
	transmat[0, 0] = 1 - transmat[0, 1]
	transmat[1, 1] = 1
	transmat[1, 0] = 0

	# Force the first point is in state 0
	startprob = np.array([1, 0])
	# The state mean of variable 
	state_means = np.zeros((2, 2))
	state_means[0, 0] = np.percentile(HMM_data[:10, 0],50)
	state_means[1, 0] = HMM_data[-10:,0]
	state_means[0, 1] = HMM_data[4, 1]
	state_means[1, 1] = HMM_data[-4, 1]

	model = hmm.GaussianHMM(
		n_components=nc,
		covariance_type="full",
		n_iter=2000,
		params='cmt',
		init_params='c',verbose=False)
	
	model.transmat_=transmat
	model.means_=state_means
	model.startprob_=startprob
	model.fit(HMM_data)

	hidden_states = model.predict(HMM_data)
	h = np.array(hidden_states)
	diff = h[1:] - h[:-1]
	changePoint = list(np.transpose(np.argwhere(diff != 0))[0])

	# feature_depth = [dataSet.Depth[dataSet.Power.argmax()]] # add thermocline
	feature_depth=[]
	for point in changePoint:
		feature_depth.append(dataSet.Depth[point])

	return feature_depth

def hmmModel(dataSet, nc=3, log=False):
	np.random.seed()
	
	n = dataSet.shape[0]
	HMM_data = pp.scale(dataSet[["Var","Power"]])
	
	# Initialize
	if nc == 3:
		# Initial Transition Matrix
		transmat = np.zeros((3, 3))
		transmat[0, 1] = 3/n
		transmat[0, 0] = 1 - transmat[0, 1]
		transmat[1, 2] = 3/n
		transmat[1, 1] = 1 - transmat[1, 2]
		transmat[2, 2] = 1

		# Force the first point is in state 0
		startprob = np.array([1, 0, 0])
		
		# The state mean of variable 
		state_means = np.zeros((3, 2))
		state_means[0, 0] = np.percentile(HMM_data[:10, 0],50)
		state_means[2, 0] = np.percentile(HMM_data[-10:, 0],50)
		state_means[1, 0] = (state_means[0, 0] + state_means[1, 0]) / 2

		
		# The state mean of power
		state_means[0, 1] = np.percentile(HMM_data[:10, 1],50)
		state_means[2, 1] = np.percentile(HMM_data[-10:, 1],50)
		state_means[1, 1] = np.percentile(HMM_data[:, 1],90) / 2

	else:
		raise
	
	model = hmm.GaussianHMM(
		n_components=nc,
		covariance_type="diag",
		n_iter=2000,
		params='cmt',
		init_params='c',
		verbose=False)
		# means_prior=state_means,
		# transmat_prior=transmat,
		# startprob_prior=startprob)
	
	model.transmat_=transmat
	model.means_=state_means
	model.startprob_=startprob

	# print model.transmat_
	# print model.decode(HMM_data)
	# print HMM_data
	model.fit(HMM_data)
	# print model.decode(HMM_data)
	# print model.score(HMM_data)

	hidden_states = model.predict(HMM_data)
	h = np.array(hidden_states)
	diff = h[1:] - h[:-1]
	changePoint = list(np.transpose(np.argwhere(diff != 0))[0])

	feature_depth = [dataSet.Depth[dataSet.Power.argmax()]] # add thermocline

	for point in changePoint:
		feature_depth.append(dataSet.Depth[point])

	return feature_depth

def thresholdModel(signal_data, threshold=None, log=False):
	
	'''
	Function to calculate the legend depth based on energy profile
	signal_data has three columns:
	0: depth
	1: feature
	2: feature's derived feature (energy, RTRM, etc)
	'''

	N = signal_data.shape[0]
	power=np.array(signal_data.Power)
	# Identify thermocline
	therm_idx=power.argmax()
	therm_depth = signal_data.Depth[therm_idx]

	if threshold is None:
		count, division = np.histogram(power, bins=30)
		# critical = np.percentile(power,80);
		critical = division[1]
		critical_hyp = division[8]
		critical_epi = division[3]
	else:
		print "Using Threshold"
		critical = np.max(power) * threshold
		critical_hyp = threshold * 1.1
		critical_epi = threshold

	stable = np.argwhere(power < critical)[:, 0]
	shallow = [s for s in stable if s < therm_idx]
	deep = [s for s in stable if s > therm_idx]

	newshallow = []
	newdeep = []

	for i in deep[:-2]:
		if max(power[i:]) < critical_hyp:
			newdeep.append(i)

	for i in shallow[1:]:
		if max(power[:i]) < critical_epi:
			newshallow.append(i)

	newshallow.append(0)
	newdeep.append(N - 1)

	if (log):
		print "shallow index", shallow
		print "deep index", deep
		print "thermocline index", therm_idx

	hypo_depth = signal_data.Depth[min(newdeep)]
	epi_depth = signal_data.Depth[max(newshallow)]

	return [therm_depth, epi_depth, hypo_depth]


def findStratification(data,config):
	signalFeature = extractFeatures(data[["Depth","Temperature"]],w=config["Algorithm"]["Spectrum"]["windowSize"])
	
	hmm_depth=hmmModel(signalFeature)
	threshold_depth=thresholdModel(signalFeature,config["Algorithm"]["Spectrum"]["threshold"])

	return hmm_depth,threshold_depth



if __name__ == '__main__':
	import pandas as pd
	import json
	from seabird_preprocessing import preprocessing as seabird_pp
	import matplotlib.pyplot as plt

	config=json.load(open('./config/config.json'))
	data=pd.read_csv(config["testFile"][3])
	rawData,data=seabird_pp(data, config)
	signalFeature = extractFeatures(data[["Depth","Temperature"]],w=config["Algorithm"]["Spectrum"]["windowSize"])

	hmmResults = hmmModel(signalFeature)

	print hmmResults
	fig=plt.figure()
	ax1 = fig.add_subplot(111)
	ax2 = ax1.twiny()
	ax1.plot(signalFeature.Var,-signalFeature.Depth,"ro")
	ax2.plot(signalFeature.Power,-signalFeature.Depth,"go")
	ax1.axhline(y=-hmmResults[1])
	plt.show()

	
	# plt.plot()
	# signalFeature[["Power"]].plot()

	# signalFeature[["Var"]].plot()
	# print data
	# print signalFeature
	# model2 = hmmModel_2(signalFeature)
	# model1=hmmModel(signalFeature)
	# print model1
	# signalFeature.plot(x="Var",y="Depth")
	# plt.axhline(y=model2[0])
	# plt.axhline(y=model1[1],c="r")
	# plt.axhline(y=model1[2],c="g")



