import numpy as np
import pandas as pd

def window_fft(x):  # Calulate the Power
	hamming_window = np.hamming(len(x))
	n = len(x)
	fftx = np.fft.rfft((x - x.mean()) * hamming_window)
	# fftx=np.fft.rfft(signal.detrend(x)*hamming_window)

	return np.array(abs(fftx))

def extractSignalFeatures(data, var, w=10):
	'''
	data: a data frame that with depth as first column and the variable as the second column
	w: window for windowed fft
	'''
	# when data only has a few points, w might be too large
	N = data.shape[0]
	signalFeature = pd.DataFrame(np.zeros((N - 2 * w, 4)),columns=['Depth','Var','Power','Gradient'])
	variableGradient = np.diff(data[var])

	spectrogram = np.array([window_fft(data.iloc[i-w:i+w,1]) for i in range(w,N-w)])
	
	signalFeature.Depth=np.array(data.Depth[w:N-w])
	signalFeature.Power=np.sum(spectrogram**2,axis=1)
	signalFeature.Var=np.array(data[var][w:N-w])
	signalFeature.Gradient=variableGradient[w:N-w]

	return signalFeature