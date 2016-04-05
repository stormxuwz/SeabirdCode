from __future__ import division
import numpy as np
import matplotlib.pyplot as plt

def scaleTo01(y,ymin=None):
	if ymin is None:
		ymin=np.min(y)
	return (y-ymin)/(np.max(y)-ymin)

class Spectrogram:
	def __init__(self, signal, frameSize, stepInterval):
		self.signal = signal
		self.frameSize = frameSize
		self.frames = None
		self.spectrogram = None
		self.stepInterval = stepInterval
		self.nfft = -1
		self.signal = signal
		self.signalPower = None
		self.specVariance = None

	def createFrames(self):
		signalLength = len(self.signal)

		frames = [self.signal[i:i + self.frameSize] for i in
		          np.arange(0, signalLength - self.frameSize, self.stepInterval)]
		frames=np.array(frames)
		return frames-np.mean(frames, axis=1).reshape((len(frames),1))

	def createSpectrogram(self):
		frames = self.createFrames()
		print frames.shape
		self.nfft = frames.shape[1]
		window = np.hamming(self.nfft)
		frames = frames * window
		print frames.shape
		self.spectrogram = np.abs(np.fft.rfft(frames, axis=1))


	def transformSpectrogram(self, returnType):
		if returnType == "log":
			return np.log(self.spectrogram)
		if returnType == "other":
			return self.spectrogram ** 2 / self.nfft

	def showSpectrogram(self):
		plt.figure()
		plt.subplot(121)
		# extent = [0, 1300, 0, 8000]
		plt.imshow(self.spectrogram, aspect='auto')
		cb = plt.colorbar()
		cb.set_label('Signal Power')

		plt.subplot(122)
		plt.plot(scaleTo01(self.signal),-np.arange(len(self.signal)) ,"+-",label="Signal")
		plt.plot(scaleTo01(self.signalPower), -np.arange(np.round(self.frameSize/2),np.round(self.frameSize/2)+len(self.signalPower)),"+--",label="Signal Power")
		plt.plot(scaleTo01(self.signalPower[1:]-self.signalPower[:-1]), -np.arange(np.round(self.frameSize/2),np.round(self.frameSize/2)+len(self.signalPower)-1),"+-",label="Signal Power Gradient")
		plt.plot(scaleTo01(self.signal[1:]-self.signal[:-1]), -np.arange(self.signal.shape[0]-1),"+-",label="Gradient")
		# plt.plot(scaleTo01(self.specVariance), -np.arange(self.specVariance.shape[0]),"+--",label="Variance")
		plt.legend(loc=4)
		plt.show()

	def findFeatures(self):
		self.signalPower = np.mean(self.spectrogram, axis=1)
		self.specVariance = np.var(self.spectrogram, axis=1)

	def explore(self):
		self.createSpectrogram()
		self.findFeatures()
		self.showSpectrogram()

if __name__ == "__main__":
	from seabird_class import *

	# seabird_sample=seabird(fileName='/Users/WenzhaoXu/Developer/Project_IO/Seabird/csvFile/HU32_2011_Aug_07.csv',expertFile='/Users/WenzhaoXu/Developer/Project_IO/Seabird/LayerInformation/site_year/HU32_2011.csv')
	# seabird_sample=seabird(fileName='/Users/WenzhaoXu/Developer/Project_IO/Seabird/csvFile/ON64_2004_Aug_09.csv',expertFile='/Users/WenzhaoXu/Developer/Project_IO/Seabird/LayerInformation/site_year/ER78M_2005.csv')
	seabird_sample=seabird(fileName='/Users/WenzhaoXu/Developer/Project_IO/Seabird/csvFile/HU95_2010_Aug_07.csv',expertFile='/Users/WenzhaoXu/Developer/Project_IO/Seabird/LayerInformation/site_year/ER78M_2010.csv')

	seabird_sample.read_data()
	myVarList = ["Temperature", "DO", "Beam_Attenuation", "Specific_Conductivity", "Fluorescence"]
	seabird_sample.smoothing([1, 0, 0, 0, 0], myVarList)

	signal_real = seabird_sample.cleanData[:,1]
	signal_linear = np.arange(len(signal_real))

	signal=signal_real
	mySpectrogram = Spectrogram(signal_real, frameSize=10, stepInterval=1)
	mySpectrogram.explore()



