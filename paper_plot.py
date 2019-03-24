import seabird
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json,sys
import logging
from sqlalchemy import create_engine
import pickle
import fnmatch
import os

def plotSegment(mySeabird, site = None, year = None, folder = '/Users/wenzhaoxu/Developer/Seabird/output/meta/',legendLoc = 4):
	from seabird.seabird_class import seabird

	# if site is None or year is None:
	# 	for file in os.listdir(folder):
	# 		if fnmatch.fnmatch(file, '*_%d.p' %(fid,)):
	# 			fname = "%s/%s" %(folder,file)
	# 			break
	# else:
	fname = "%s/%s_%d_%d.p" %(folder,mySeabird.site,int(mySeabird.time.year),int(mySeabird.fileId))
	print(fname)

	# mySeabird = pickle.load(open(fname,"rb"))
	mySeabird
	pt = plt.figure(figsize=(4.5,8))
	ax1 = pt.add_subplot(111)
	
	ax1.plot(mySeabird.cleanData.Temperature, -mySeabird.cleanData.Depth, "r",linewidth=1)
	ax1.plot(mySeabird.downCastRawData.Temperature, -mySeabird.downCastRawData.Depth, "r--", alpha=0.5,linewidth=1)
	ax1.set_xlabel("Temperature (C)")
	ax1.set_ylabel("Depth (m)")
	for seg in mySeabird.thermocline.models["segmentation"].segmentList:
		ax1.plot(seg[0],-np.array(mySeabird.cleanData.Depth[seg[1]]),linewidth=5)
	
	plt.savefig("/Users/wenzhaoxu/Developer/Seabird/output/focus/segment_%s_%s.pdf" %(os.path.splitext(os.path.basename(fname))[0],config["Algorithm"]["segment"]["max_error"]),
		bbox_inches='tight', dpi=350)
	plt.close()


def test():
	from seabird.seabird_class import seabird
	config=json.load(open('/Users/wenzhaoxu/Developer/Seabird/SeabirdCode/config.json'))
	mySeabird = seabird(config = config)

	# mySeabird.loadData(dataFile = "/Users/WenzhaoXu/Developer/Seabird/input/history_data/1996/SUMMER96/SU04SU96.CNV")
	# mySeabird.loadData(dataFile="sample.cnv")
	mySeabird.loadData(fileId=961)
	print(mySeabird.site, mySeabird.time)
	# mySeabird.loadData(dataFile= "./sample.cnv")
	# mySeabird.loadData("")
	mySeabird.preprocessing()
	# print mySeabird.cleanData
	mySeabird.identify()
	# mySeabird.plot_all()
	# fname = "/Users/WenzhaoXu/Developer/Seabird/output/plot/"+mySeabird.site+"_"+str(mySeabird.time)+".png"
	fname=None
	print(mySeabird.features)
	mySeabird.plot(filename = fname,meta = True)
	
	print(mySeabird.cleanData.Depth[39])
	plt.show()


def outputData(fid,csvFolder = "/Users/wenzhaoxu/Desktop/"):
	from seabird.seabird_class import seabird
	config=json.load(open('/Users/wenzhaoxu/Developer/Seabird/SeabirdCode/config.json'))
	mySeabird = seabird(config = config)
	mySeabird.loadData(fileId=1268)
	mySeabird.preprocessing()

	cleanData = np.array(mySeabird.cleanData[["Fluorescence","Temperature"]])
	rawData = np.array(mySeabird.downCastRawData[["Fluorescence","Temperature"]])

	np.savetxt("%s/%d_raw.csv" %(csvFolder,fid),rawData)
	np.savetxt("%s/%d_clean.csv" %(csvFolder,fid),cleanData)



def plotHistoryProfile(site, years = range(1996,2014), var = "TRM", targetYear = 2000):
	# site is site
	# year is a list
	folder = '/Users/wenzhaoxu/Developer/Seabird/output/meta/'

	depths = []
	values = []
	pt = plt.figure(figsize = (3.5, 4.5))

	for year in years:
		# if year == targetYear:
			# continue
		fname = None
		for file in os.listdir(folder):
			if fnmatch.fnmatch(file, '%s_%d_*.p' %(site,year)):
				fname = "%s/%s" %(folder,file)
				print(fname)
				break
		if fname is None:
			continue
		mySeabird = pickle.load(open(fname,"rb"), encoding="latin1")
		features = mySeabird.features
		depths.append(max(mySeabird.cleanData.Depth))

		if var in ["TRM","UHY","LEP"]:
			plt.plot(mySeabird.downCastRawData.Temperature, -mySeabird.downCastRawData.Depth, ls = "--", alpha=1, color = '0.75', label='_nolegend_')
			values.append(max(mySeabird.downCastRawData.Temperature))
		elif var == "DCL":
			plt.plot(mySeabird.downCastRawData.Fluorescence, -mySeabird.downCastRawData.Depth, ls = "--", alpha=1, color = '0.75',  label='_nolegend_')
			values.append(max(mySeabird.downCastRawData.Fluorescence))

	if targetYear:
		for file in os.listdir(folder):
			if fnmatch.fnmatch(file, '%s_%d_*.p' %(site,targetYear)):
				fname = "%s/%s" %(folder,file)
				break
		mySeabird = pickle.load(open(fname,"rb"), encoding="latin1")
		features = mySeabird.features


		if var in ["TRM","UHY","LEP"]:
			depth_algorithm = mySeabird.features[var+"_segment"]
			plt.plot(mySeabird.downCastRawData.Temperature, -mySeabird.downCastRawData.Depth, ls = "--", alpha=1, color = '0.75', label = "Historical Profile")
			plt.plot(mySeabird.downCastRawData.Temperature, -mySeabird.downCastRawData.Depth, "r", alpha=1, label = "%d Profile" % targetYear)
			plt.axhline(y = -1*depth_algorithm if depth_algorithm is not None else -999,color = 'b',label = "%d %s" %(targetYear, var))
		elif var == "DCL":
			depth_algorithm = mySeabird.features["DCL_depth"]
			plt.plot(mySeabird.downCastRawData.Fluorescence, -mySeabird.downCastRawData.Depth, ls = "--", alpha=1, color = '0.75', label = "Historical Profile")
			plt.plot(mySeabird.downCastRawData.Fluorescence, -mySeabird.downCastRawData.Depth, "r", alpha=1, label = "%d Profile" % targetYear)
			plt.axhline(y = -1*depth_algorithm if depth_algorithm is not None else -999,color = 'b',label = "%d %s" %(targetYear, var))

	plt.ylim((-max(depths) - 5, 0))
	plt.xlim((0, max(values)*1.1))
	plt.ylabel("Depth (m)")

	if var in ["TRM", "UHY", "LEP"]:
		plt.xlabel("Temperature (C)")
	elif var == "DCL":
		plt.xlabel("Fluorescence (ug/L)")

	# plt.show()
	plt.legend(loc = 4)
	plt.savefig("/Users/wenzhaoxu/Developer/Seabird/finalResults/focus/History_%s_%d_%s.png" %(site, targetYear, var), bbox_inches='tight', dpi = 350)
	plt.close()



def plotProfile(fid,var="DCL",site = None,year = None,folder = '/Users/wenzhaoxu/Developer/Seabird/output/meta/',legendLoc = 4):
	from seabird.seabird_class import seabird

	if site is None or year is None:
		for file in os.listdir(folder):
			if fnmatch.fnmatch(file, '*_%d.p' %(fid,)):
				fname = "%s/%s" %(folder,file)
				break
	else:
		fname = "%s/%s_%d_%d.p" %(folder,site,int(year),int(fid))
	print(fname)
	mySeabird = pickle.load(open(fname,"rb"), encoding="latin1")
	features = mySeabird.features

	pt = plt.figure(figsize=(3,4))
	ax1 = pt.add_subplot(111)
	ax2 = ax1.twiny()

	# ax1.plot(mySeabird.cleanData.Temperature, -mySeabird.cleanData.Depth, "r",label = "Preprocessed Temperature")
	ax1.plot(mySeabird.downCastRawData.Temperature, -mySeabird.downCastRawData.Depth, "r--", alpha=0.5,label = "Raw Temperature")
	# ax1.set_xlim(max(0,min(mySeabird.downCastRawData.Temperature)),max(mySeabird.downCastRawData.Temperature))
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
		ax2.axhline(y = -1*depth_algorithm if depth_algorithm is not None else -999,color = 'b',label = "Algorithm")

		depth_expert = mySeabird.expert["DCL"]
		ax2.axhline(y = -1*depth_expert if depth_expert is not None else -999,color = 'b',ls="--",label = "Operator")

	elif var in ["TRM","LEP","UHY"]:
		depth_algorithm = mySeabird.features[var+"_segment"]
		ax2.axhline(y = -1*depth_algorithm if depth_algorithm is not None else -999,color = 'b',label = "Algorithm")

		depth_expert = mySeabird.expert[var]
		ax2.axhline(y = -1*depth_expert if depth_expert is not None else -999,color = 'b',ls="--", label = "Operator")
	

	elif var in ["TRM_compare","LEP_compare","UHY_compare"]:
		# plot the comparision between PLR and HMM models
		depth_algorithm = mySeabird.features[var.split("_")[0]+"_segment"]
		ax2.axhline(y = -1*depth_algorithm if depth_algorithm is not None else -999,color = 'b',label = "PLR")

		
		depth_expert = mySeabird.features[var.split("_")[0]+"_HMM"]
		ax2.axhline(y = -1*depth_expert if depth_expert is not None else -999,color = 'b',ls="--", label = "MG-HMM")

	elif var in ["Stratification_compare"]:
		# compare the stratification
		depth = mySeabird.features["LEP"+"_segment"]
		ax2.axhline(y = -1*depth if depth is not None else -999,color = 'b',label = "PLR_LEP")

		depth = mySeabird.features["UHY"+"_segment"]
		ax2.axhline(y = -1*depth if depth is not None else -999,color = 'm',label = "PLR_UHY")

		depth = mySeabird.features["LEP"+"_HMM"]
		ax2.axhline(y = -1*depth if depth is not None else -999,color = 'b',ls="--",label = "HMM_LEP")

		depth = mySeabird.features["UHY"+"_HMM"]
		ax2.axhline(y = -1*depth if depth is not None else -999,color = 'm',ls="--",label = "HMM_LEP")
	else:
		pass

	lines, labels = ax1.get_legend_handles_labels()
	lines2, labels2 = ax2.get_legend_handles_labels()
	if legendLoc >-1:
		ax1.legend(lines + lines2, labels + labels2, loc=legendLoc, prop={'size':10})
	plt.savefig("/Users/wenzhaoxu/Developer/Seabird/finalResults/focus/%s_%s.png" %(os.path.splitext(os.path.basename(fname))[0],var),
		bbox_inches='tight', dpi = 350)
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
	# plotProfile(1000,var = "DCL", legendLoc=4) # ER78 2005, smoothing so that not able to detect DCL
	# plotProfile(989,var = "DCL",legendLoc = 4) # ER36 2005 for DCL peak missing
		# # plotProfile(1655,var = "Stratification_compare",legendLoc = 4) # for not good stratification
	# # plotProfile(1380,var = "Stratification_compare",legendLoc = 4) # for not good stratification 1380
	# plotProfile(466,var = "None",legendLoc = 4) # MI30 2000 for double thermocline

	# # plotProfile(776,var = "None",legendLoc = 4) # HU37 2006 for double thermocline
	# # plotProfile(1426,var = "None",legendLoc = 4) # HU37 2006 for double thermocline
	# # plotProfile(1637,var = "None",legendLoc = 4) # HU37 2006 for double thermocline	




	# plotProfile(1544,var = "TRM_compare",legendLoc = 4) # SU15 2009 for TRM difference
	# plotProfile(363,var = "Stratification_compare",legendLoc = 4) # MI47 1999 for not good stratification 363
	# plotProfile(675,var = "Stratification_compare",legendLoc = 4) # 675 HU53 2002 for UHY difference

	plotProfile(1763,var = "DCL",legendLoc = -1) # SU09 2011 for DCL mislabled
	plotProfile(1444,var = "LEP",legendLoc = -1) # ER15_2009_1444 for LEP algorithm limitations
	plotProfile(734,var = "TRM",legendLoc = -1) # SU09 2002 for TRM definition
	plotProfile(1696,var = "DCL",legendLoc = -1) # HU32 2011 for DCL definition
	plotProfile(1037,var = "DCL",legendLoc = -1) # # MI40_2005_1037 for lage DCL peak
	plotProfile(383,var = "UHY",legendLoc = -1) # ON55_1999 for large transition zone

	# plotProfile(1856,var = "None",legendLoc = 4) # ON33 2012 for positive temperature gradient
	# plotProfile(1154,var = "None",legendLoc = 4) # MI42_2006_1154 for double thermocline
	
	plotProfile(1433,var = "None",legendLoc = 4)# 2008 SU17 for DCL asymesstry shape 1.459844
	plotProfile(438,var = "None",legendLoc = 4)# HU12 2000 for DCL symmetric shape b, 0.003450122
	plotProfile(1426,var = "None",legendLoc = 4)# SU11 2008 for DCL asymmetric shape c, -1.835088
	# # outputData(1767)

	plotHistoryProfile("SU15",var = "TRM", targetYear=2009)
	plotHistoryProfile("SU21",var = "TRM", targetYear=2010)

	plotHistoryProfile("SU07",var = "DCL", targetYear=2011)
	plotHistoryProfile("SU05",var = "DCL", targetYear=2004)