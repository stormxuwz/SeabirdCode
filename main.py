import seabird
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json,sys
import logging
from sqlalchemy import create_engine
import cPickle as pickle
import fnmatch
import os

def test():
	from seabird.seabird_class import seabird
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/config.json'))
	mySeabird = seabird(config = config)

	# mySeabird.loadData(dataFile = "/Users/WenzhaoXu/Developer/Seabird/input/history_data/1996/SUMMER96/SU04SU96.CNV")
	# mySeabird.loadData(dataFile="sample.cnv")
	mySeabird.loadData(fileId=1268)
	# mySeabird.loadData(dataFile= "./sample.cnv")
	# mySeabird.loadData("")
	mySeabird.preprocessing()
	# print mySeabird.cleanData
	mySeabird.identify()
	# mySeabird.plot_all()
	# fname = "/Users/WenzhaoXu/Developer/Seabird/output/plot/"+mySeabird.site+"_"+str(mySeabird.time)+".png"
	fname=None
	print mySeabird.features
	mySeabird.plot(filename = fname,meta = True)
	
	print mySeabird.cleanData.Depth[39]
	plt.show()


def outputData(fid,csvFolder = "/Users/WenzhaoXu/Desktop/"):
	from seabird.seabird_class import seabird
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/config.json'))
	mySeabird = seabird(config = config)
	mySeabird.loadData(fileId=1268)
	mySeabird.preprocessing()

	cleanData = np.array(mySeabird.cleanData[["Fluorescence","Temperature"]])
	rawData = np.array(mySeabird.downCastRawData[["Fluorescence","Temperature"]])

	np.savetxt("%s/%d_raw.csv" %(csvFolder,fid),rawData)
	np.savetxt("%s/%d_clean.csv" %(csvFolder,fid),cleanData)


def plotProfile(fid,var="DCL",site = None,year = None,folder = '/Users/WenzhaoXu/Developer/Seabird/output/meta/',legendLoc = 4):
	from seabird.seabird_class import seabird

	if site is None or year is None:
		for file in os.listdir(folder):
			if fnmatch.fnmatch(file, '*_%d.p' %(fid,)):
				fname = "%s/%s" %(folder,file)
				break
	else:
		fname = "%s/%s_%d_%d.p" %(folder,site,int(year),int(fid))
	print fname
	mySeabird = pickle.load(open(fname,"rb"))
	features = mySeabird.features

	pt = plt.figure(figsize=(6,8))
	ax1 = pt.add_subplot(111)
	ax2 = ax1.twiny()

	# ax1.plot(mySeabird.cleanData.Temperature, -mySeabird.cleanData.Depth, "r",label = "Preprocessed Temperature")
	ax1.plot(mySeabird.downCastRawData.Temperature, -mySeabird.downCastRawData.Depth, "r--", alpha=0.5,label = "Raw Temperature")
	
	xlimRange = (0,np.percentile(mySeabird.downCastRawData["Fluorescence"][mySeabird.downCastRawData.Depth > 2],99) * 1.3)

	ax2.set_xlim(xlimRange)

	ax2.set_xlabel("Fluorescence (ug/L)")
	# ax2.plot(mySeabird.cleanData.Fluorescence, -mySeabird.cleanData.Depth, "g",label = "Preprocessed Fluorescence")
	ax2.plot(mySeabird.downCastRawData.Fluorescence, -mySeabird.downCastRawData.Depth, "g--", alpha=0.5,label = "Raw Fluorescence")
	
	ax1.set_xlabel("Temperature (C)")
	ax1.set_ylabel("Depth (m)")
	
	ax1.set_ylim((-max(mySeabird.cleanData.Depth) - 5, 0))

	if var == "DCL":
		depth_algorithm = mySeabird.features["DCL_depth"]
		ax2.axhline(y = -1*depth_algorithm if depth_algorithm is not None else -999,color = 'b',label = "Algorithm Outputs")

		depth_expert = mySeabird.expert["DCL"]
		ax2.axhline(y = -1*depth_expert if depth_expert is not None else -999,color = 'b',ls="--",label = "Expert Notes")

	elif var in ["TRM","LEP","UHY"]:
		depth_algorithm = mySeabird.features["TRM"+"_segment"]
		ax2.axhline(y = -1*depth_algorithm if depth_algorithm is not None else -999,color = 'b',label = "Algorithm Outputs")

		depth_expert = mySeabird.expert[var]
		ax2.axhline(y = -1*depth_expert if depth_expert is not None else -999,color = 'b',ls="--", label = "Expert Notes")
	else:
		pass
	lines, labels = ax1.get_legend_handles_labels()
	lines2, labels2 = ax2.get_legend_handles_labels()
	ax1.legend(lines + lines2, labels + labels2, loc=legendLoc,prop={'size':11})
	plt.savefig("/Users/WenzhaoXu/Developer/Seabird/output/focus/%s_%s.pdf" %(os.path.splitext(os.path.basename(fname))[0],var))
	plt.close()

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


if __name__ == '__main__':
	# test()
	# plotProfile(1767,var = "None",legendLoc = 4)
	outputData(1767)
