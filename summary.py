import numpy as np
import os
import pandas as pd
import sys
from seabird.seabird_class import seabird
import traceback
import cPickle as pickle

class seabirdSummary:
	def __init__(self, sensorDir=None, expertDir=None):
		self.sensorDir = sensorDir
		self.expertDir = expertDir
		self.counterpart = []
		self.config=config

	def find_expert_opinion(self):
		for root_sensor, dir_sensor, files_sensor in os.walk(self.sensorDir):
			for fileName in files_sensor:
				# print fileName
				if fileName.endswith('.csv'):
					print fileName
					sensorFileName_fullpath = os.path.join(root_sensor, fileName)
					sampleInfo = fileName[0:-4]
					sampleInfo = sampleInfo.split("_")
					station = sampleInfo[0]
					year = sampleInfo[1]

					targetFile1 = station.upper() + "_" + year + ".csv"
					targetFile2 = station.upper() + "M" + "_" + year + ".csv"
					targetFile3 = station.upper() + "B" + "_" + year + ".csv"

					targetFileList = [];
					for root_expert, dirs_expert, files_expert in os.walk(self.expertDir):
						if targetFile1 in files_expert:
							targetFile = targetFile1

						elif targetFile2 in files_expert:
							targetFile = targetFile2

						elif targetFile3 in files_expert:
							targetFile = targetFile3
						else:
							print fileName + "expert file not existed";
							targetFile = None

						if targetFile is not None:
							expertFileName_fullpath = os.path.join(root_expert, targetFile)
							targetFileList.append(expertFileName_fullpath);

					if len(targetFileList) ==1 :
						self.counterpart.append([sensorFileName_fullpath, targetFileList[0]])
					elif len(targetFileList) >1:
						raise "error"
					else:
						self.counterpart.append([sensorFileName_fullpath, None])

	def write_counterpart_list(self):
		filename = "./config/data_expert_lineup.csv"
		self.counterpart = pd.DataFrame(self.counterpart,columns=["dataFile","expertFile"])
		self.counterpart.to_csv(filename)

	def load_counterpart_list(self, fname):
		self.counterpart = pd.read_csv(fname)

	def extractSeabirdFeature(self,config):
		wrongFile=[]
		seabirdResults = pd.DataFrame()
		for i in range(self.counterpart.shape[0]):
		# for i in range(10):
			print i,self.counterpart.dataFile[i]
			mySeabird=seabird(fileName=self.counterpart.dataFile[i],config=config, expertFile=self.counterpart.expertFile[i])
			try:
				mySeabird.preprocessing()
				mySeabird.plot_all(interestVarList=["Temperature","DO","Specific_Conductivity","Fluorescence","Par"],
					fileTitle="../Project_IO/Seabird/allPlot2/" + str(i) + "_" + mySeabird.ID + "_all.jpg",)
				# if i == 5:
					# raise ValueError
				if max(mySeabird.cleanData.Depth) < 1000:
					mySeabird.identify()
					# print mySeabird.feature
				seabird_feature = pd.DataFrame(mySeabird.feature,index=[0])
				seabird_feature["fileRowId"] = i
				seabird_feature["hasError"] = 0
				seabird_feature["year"] = mySeabird.time
				seabird_feature["site"] = mySeabird.site
				seabird_feature["fileName"] = self.counterpart.dataFile[i]
				mySeabird.plot(filename="../Project_IO/Seabird/allPlot2/" + str(i) + "_" + mySeabird.ID + ".jpg")
				pickle.dump(mySeabird,open("../Project_IO/Seabird/pickle/"+i+"_"+mySeabird.site+"_"+mySeabird.time+".p","wb"))
				seabirdResults = seabirdResults.append(seabird_feature,ignore_index=True)

			except:
				print "Unexpected error:", sys.exc_info()[0]
				seabird_feature = pd.DataFrame(None,index=[0])
				seabird_feature["hasError"] = 1
				seabird_feature["fileRowId"] = i
				seabird_feature["year"] = mySeabird.time
				seabird_feature["site"] = mySeabird.site
				seabird_feature["fileName"] = self.counterpart.dataFile[i]
				seabirdResults = seabirdResults.append(seabird_feature,ignore_index=False)
				wrongFile.append(self.counterpart.dataFile[i])

		wrongFile = pd.Series(wrongFile)
		# print wrongFile

		seabirdResults.to_csv("../output/testFeature.csv")
		wrongFile.to_csv("../output/testFeature.csv",index=True)
		# print seabird_feature

def extractWaterChemistryData(featureFile):

	feature = pd.read_csv(featureFile)

	varList = ["DO","Temperature","Specific_Conductivity","Fluorescence","Beam_Attenuation"]
	epilimnionFeature = np.zeros((feature.shape[0],2*len(varList)))
	hypolimnionFeature = np.zeros((feature.shape[0],2*len(varList)))
	# for i in range(374,375):
	for i in range(feature.shape[0]):
		print i
		site = feature.site[i]
		year = feature.year[i]
		LEP = feature.LEP_segment[i]
		UHY = feature.UHY_segment[i]
		try:
			mySeabird = pickle.load(open("../output/pickle/%s_%d.p" %(site,year),"rb"))
			data = mySeabird.cleanData
			# print data.columns.values
			for var in varList:
				if var not in data.columns.values:
					print var
					# print data.columns.values
					data[var]=-99
			epilimnion = data[data.Depth<LEP][varList]
			hypolimnion = data[data.Depth>UHY][varList]
			
			epilimnionFeature[i,:len(varList)] = epilimnion.mean()
			epilimnionFeature[i,len(varList):] = epilimnion.var()

			hypolimnionFeature[i,:len(varList)] = hypolimnion.mean()
			hypolimnionFeature[i,len(varList):] = hypolimnion.var()
		except:
			print "Unexpected error:", sys.exc_info()[0]
			traceback.print_exc()
			pass

	epilimnionFeature = pd.DataFrame(epilimnionFeature,columns=["epi_mean_"+name for name in varList] + ["epi_var_"+name for name in varList])
	hypolimnionFeature = pd.DataFrame(hypolimnionFeature,columns =["hyp_mean_"+name for name in varList] + ["hyp_var_"+name for name in varList])
	# print epilimnionFeature
	waterChemistryFeature = pd.concat([epilimnionFeature,hypolimnionFeature],axis=1)
	waterChemistryFeature.to_csv("../output/waterFeature.csv")
	

if __name__ == '__main__':
	# import json

	# config=json.load(open('./config/config.json'))
	# summary = seabirdSummary(sensorDir="/Users/WenzhaoXu/Developer/Project_IO/Seabird/csvFile/",expertDir="/Users/WenzhaoXu/Developer/Project_IO/Seabird/LayerInformation/site_year/")
	# summary.find_expert_opinion()
	# summary.write_counterpart_list()
	# summary.load_counterpart_list("./config/data_expert_lineup.csv")
	summary.extractSeabirdFeature(config)
	# extractWaterChemistryData("/Users/WenzhaoXu/Desktop/SU.csv")
	# extractWaterChemistryData("../output/testFeature.csv")
