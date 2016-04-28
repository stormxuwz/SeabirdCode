import seabird
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json,sys
import logging
from sqlalchemy import create_engine

def plotAccumu(x):
	print x,np.cumsum(x)
	p = plt.figure()
	ax1 = p.add_subplot(111)
	ax2 = ax1.twinx()
	ax1.plot(range(len(x)),np.cumsum(x))
	ax2.plot(range(len(x)),x)
	plt.show()

def futureFeatureTest():
	import seabird.tools.seabird_preprocessing as seabirdPrep
	import seabird.futureFeature.timeSeriesSeg as tsModel
	import seabird.futureFeature.peakDetection as peakModel

	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/config.json'))
	sourceFile = "/Users/WenzhaoXu/Developer/Seabird/input/csvFile/ON49_1996_Aug_07.csv"
	# sourceFile=config["testFile"][2]
	data = pd.read_csv(sourceFile)

	tmp,data = seabirdPrep.preprocessing(data,config)

	temperature_error=0.5

	# segModel = slidingWindow(max_error=error)
	segModel = tsModel.bottomUp_efficient(max_error=temperature_error)
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

def seabird_class_test():
	from seabird.tools.misc import findExpertData
	from seabird.seabird_class import seabird
	
	expertDataFile = pd.read_csv("../input/data_expert_lineup.csv")

	config=json.load(open('./config/config.json'))
	# sourceFile = config["testFile"][10]
	# sourceFile = "/Users/WenzhaoXu/Developer/Project_IO/Seabird/csvFile/ER59_1999_Aug_04.csv"
	sourceFile = expertDataFile.iloc[5 ,1]
	print sourceFile
	a = findExpertData(sourceFile)
	# print a
	# print a.values[0]
	mySeabird=seabird(sourceFile,config,expertFile=a)
	mySeabird.preprocessing()
	mySeabird.identify()
	# print mySeabird.cleanData.describe()
	# print mySeabird.rawData.describe()
	# print mySeabird.cleanData["Fluorescence"]
	mySeabird.plot()
	plt.show()
	# mySeabird.plot_all()

def runApp():
	from seabird.seabirdGUI import SeabirdGUI
	import warnings
	from Tkinter import Tk
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		root=Tk()
		root.geometry("1200x650")
		app=SeabirdGUI(master=root)
		root.mainloop()
		root.destroy()



def detectThermocline(fileId,dbEngine = create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')):
	import seabird.tools.seabird_preprocessing as seabirdPrep
	import seabird.futureFeature.timeSeriesSeg as tsModel
	import seabird.futureFeature.peakDetection as peakModel
	from seabird.seabird_class import seabird

	sql = "Select * from seabird_data where fileId = %d Order By 'index' ASC" %(fileId)
	data = pd.read_sql_query(sql,dbEngine).drop('index',axis = 1)
	temperature_error=0.5
	# print data.describe()
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/seabird/config.json'))

	mySeabird = seabird(config = config)
	mySeabird.loadData(fileId = 1000)
	# print mySeabird.time
	mySeabird.preprocessing()
	mySeabird.identify()
	mySeabird.plot()
	plt.show()
# def detectThermocline(engine):
# 	sql = "Select fileId from seabird_meta where duplicate = 0"
# 	fileIdList = pd.read_sql_query(sql,engine)["fileId"]

# 	for i in fileIdList[:1]:
# 		data = retriveData(i, engine)
# 		print data

if __name__ == '__main__':
	# logging.basicConfig(level=logging.INFO)
	# futureFeatureTest()
	# seabird_class_test()
	# runApp()
	# detectThermocline(10)
	# pass
	from seabird.seabird_class import seabird
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/seabird/config.json'))
	mySeabird = seabird(config = config)

	mySeabird.loadData(dataFile = "/Users/WenzhaoXu/Developer/Hypoxia/input/seabird_data/Erie2013DO/DO Survey August/ER73.cnv.cnv")
	mySeabird.plot_all()
