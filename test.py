import seabird
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json,sys
import logging

def plotAccumu(x):
	print x,np.cumsum(x)
	p = plt.figure()
	ax1 = p.add_subplot(111)
	ax2 = ax1.twinx()
	ax1.plot(range(len(x)),np.cumsum(x))
	ax2.plot(range(len(x)),x)
	plt.show()

def futureFeatureTest(sourceFile):
	import seabird.tools.seabird_preprocessing as seabirdPrep
	import seabird.futureFeature.timeSeriesSeg as tsModel
	import seabird.futureFeature.peakDetection as peakModel

	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/config/config.json'))
	data = pd.read_csv(sourceFile)

	tmp,data = seabirdPrep.preprocessing(data,config)

	temperature_error=0.5


	# segModel = slidingWindow(max_error=error)
	segModel = tsModel.bottomUp(max_error=temperature_error)
	segModel.fit_predict(np.array(data.Temperature))

	#print len(segModel.segmentList)
	segModel.plot()
	print "Finish the thermocline detection"

	peakModel = peakModel.peak(max_error=(max(data.Fluorescence)-min(data.Fluorescence))*0.2,method = "laplace")
	peakModel.detect(np.array(data.Fluorescence))

	print peakModel.shape_fit

	pt = plt.figure()
	ax1 = pt.add_subplot(111)
	ax2 = ax1.twiny()
	ax1.plot(data.Temperature,-np.arange(len(data.Depth)),"ro--")
	ax2.plot(data.Fluorescence,-np.arange(len(data.Depth)),"go--")

	for seg in segModel.segmentList:
		ax1.plot(seg[0],-np.array(seg[1]))

	for i, shape_res in enumerate(peakModel.shape_fit):
		ax2.plot(shape_res["left_data"],-shape_res["left_index"],)
		ax2.plot(shape_res["right_data"],-shape_res["right_index"])
		ax2.axhline(-peakModel.peak[i][1])
		ax2.axhline(-peakModel.peak[i][2])

	plt.xlabel("Temperature (C)")
	plt.ylabel("Depth (m)")
	plt.show()

	plt.close()

def seabird_class_test(sourceFile):
	from seabird.tools.misc import findExpertData
	from seabird.seabird_class import seabird
	config=json.load(open('./config/config.json'))
	
	mySeabird=seabird(sourceFile,config,expertFile=findExpertData(sourceFile))
	# mySeabird.plot_all()
	mySeabird.identify()
	# print mySeabird.feature

	mySeabird.plot()
	plt.show()

def testSlopeSum(sourceFile):
	from seabird.tools.misc import findExpertData
	from seabird.seabird_class import seabird
	import seabird.futureFeature.peakDetection as peakModel

	config=json.load(open('./config/config.json'))
	mySeabird=seabird(sourceFile,config,expertFile=findExpertData(sourceFile))
	mySeabird.preprocessing()

	x = mySeabird.cleanData.Fluorescence
	y = peakModel.slopeSum(x, 20)
	
	print y
	pt = plt.figure()
	ax1 = pt.add_subplot(111)
	ax2 = ax1.twinx()
	ax1.plot(x,"ro--")
	ax2.plot(np.arange(len(y))+20+1,y,"go--")
	plt.show()


def runApp():
	from seabird.seabirdGUI import SeabirdGUI
	import warnings
	from Tkinter import Tk
	with warnings.catch_warnings():
		# warnings.simplefilter("ignore")
		root=Tk()
		root.geometry("1200x650")
		app=SeabirdGUI(master=root)
		root.mainloop()
		root.destroy()

if __name__ == '__main__':
	# sourceFile = config["testFile"][10]
	# logging.basicConfig(level=logging.INFO)
	expertDataFile = pd.read_csv("./data/data_expert_lineup.csv")
	sourceFile = expertDataFile.iloc[1340 ,1]
	# sourceFile = "/Users/WenzhaoXu/Developer/Project_IO/Seabird/csvFile/MI31_2007_Aug_03.csv"
	# futureFeatureTest(sourceFile)
	# seabird_class_test(sourceFile)
	testSlopeSum(sourceFile)
	# runApp()
