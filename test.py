from seabird.seabird_class import seabird
from seabird.models.stratificationIndex import *
# from seabird.futureFeature.peakDetection3 import peak
from seabird.models.model_peak2 import peak
from scipy import signal
import cPickle as pickle


if __name__ == '__main__':
	import json
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/config.json'))
	mySeabird = seabird(config = config)
	mySeabird.loadData(fileId = 1191)
	print mySeabird.site
	mySeabird.preprocessing()
	
	mySeabird.identify()
	print mySeabird.features
	depth = mySeabird.cleanData.Depth
	Fluorescence = mySeabird.cleanData.Fluorescence


	# a = pickle.load(open("/Users/WenzhaoXu/Developer/Seabird/output/meta/ER09_1996-08-05 00:16:11_4.p","rb"))
	# print a.config

	# myPeak = peak(config["Algorithm"]["Peak"])
	# myPeak.fit_predict(Fluorescence)
	# peakFeatures = myPeak.featureExtraction()

	# width = np.array(range(5,80,5))
	# peakind = signal.find_peaks_cwt(Fluorescence,width,min_length = 3,max_distances = width/2)

	# print peakind

	# plt.figure()
	# cwtmatr = signal.cwt(Fluorescence, signal.ricker, width)
	# print cwtmatr
	# plt.imshow(cwtmatr, extent=[-1, 1, 31, 1], cmap='PRGn', aspect='auto',
           # vmax=abs(cwtmatr).max(), vmin=-abs(cwtmatr).max())
	# plt.show()
	plt.figure()
	plt.plot(Fluorescence)


	plt.figure()
	plt.plot(Fluorescence,-depth)
	plt.axhline(-mySeabird.features["DCL_depth"])
	plt.axhline(-mySeabird.features["DCL_upperDepth_gradient"])
	plt.axhline(-mySeabird.features["DCL_bottomDepth_gradient"])

	plt.axhline(-mySeabird.features["DCL_upperDepth_fit"],c = "g")
	plt.axhline(-mySeabird.features["DCL_bottomDepth_fit"],c = "g")


	# plt.figure()
	mySeabird.plot()
	
	plt.show()
	# myPeak = peak(config)
	# myPeak.detect(temperature)

	# BV_idx,BV_depth = BVfrequency(temperature,depth)
	# RTRM_idx,RTRM_depth = RTRM(temperature,depth)

	# plt.figure()
	# ax1 = plt.subplot(131)
	# ax1.plot(temperature,-np.array(depth))
	# ax1.axhline(-mySeabird.features["TRM_segment"],color = "r")
	# ax1.axhline(-mySeabird.features["LEP_segment"],color = "g")
	# ax1.axhline(-mySeabird.features["UHY_segment"],color = "y")
	
	# ax2 = plt.subplot(132, sharey=ax1)
	# ax2.plot(BV_idx,-np.array(BV_depth))
	# ax2.axhline(-mySeabird.features["TRM_segment"],color = "r")
	# ax2.axhline(-mySeabird.features["LEP_segment"],color = "g")
	# ax2.axhline(-mySeabird.features["UHY_segment"],color = "y")
	
	# ax3 = plt.subplot(133, sharey=ax1)
	# ax3.plot(RTRM_idx,-np.array(RTRM_depth))
	# ax3.axhline(-mySeabird.features["TRM_segment"],color = "r")
	# ax3.axhline(-mySeabird.features["LEP_segment"],color = "g")
	# ax3.axhline(-mySeabird.features["UHY_segment"],color = "y")
	# plt.show()
	# print mySeabird.thermocline.detect(data = mySeabird.cleanData[["Depth","Temperature"]],methods = ["segmentation"])
	# print mySeabird.thermocline.detect(data = mySeabird.cleanData[["Depth","Temperature"]],methods = ["HMM"])
	# print mySeabird.thermocline.detect(data = mySeabird.cleanData[["Depth","Temperature"]],methods = ["threshold"])
	# print mySeabird.DCL.detect(data = mySeabird.cleanData[["Depth","Fluorescence"]])
	# mySeabird.identify()
	
	# print mySeabird.features