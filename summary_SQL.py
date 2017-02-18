from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from seabird.seabird_class import seabird
import traceback
import cPickle as pickle
import sys


class summary(object):
	def __init__(self,engine,config): 
		self.engine = engine
		self.allYears = range(1996,2014)  # [1996, 2013]
		self.allStations = self.getAllStations()
		# print self.allStations
		self.config = config

	def sqlQuery(self,sql):
		return pd.read_sql_query(sql,self.engine)

	def getAllStations(self,depthCode = ['LEP','TRM','UHY','DCL']):
		depthCode = "','".join(depthCode)
		sql = '''Select DISTINCT(stationInfered) as STATION from summer_meta where year(systemUpLoadTime) >= 1996 ORDER BY STATION;'''
		return self.sqlQuery(sql)

	def findEntry(self,station,year, season = "summer"):
		subStation = station[:4]
		sql_meta = '''select systemUploadTime,datcnv_date,fileId,stationInfered, year(systemUpLoadTime) as Year from %s_meta where stationInfered = '%s' And year(systemUpLoadTime) = %d And badProfile = 0''' %(season,subStation,year)
		sql_expertnotes = '''select `index`,SAMPLING_DATE,STATION,YEAR,DepthCode,SMPL_DEPTH as Depth from expertNotes where STATION = '%s' And YEAR = %d AND DepthCode in ('LEP','TRM','UHY','DCL'); ''' %(station,year) #  AND MONTH(SAMPLING_DATE) IN (6,7,8,9,10)
		meta_res = self.sqlQuery(sql_meta)
		expertnotes_res = self.sqlQuery(sql_expertnotes)
		return meta_res,expertnotes_res

	def writeAllAlignments(self):
		tables = []
		for station in self.allStations.STATION:
			for year in self.allYears:
				print station, year
				meta_res,expertnotes_res = self.findEntry(station, year)
				# tables.append(pd.merge(meta_res,expertnotes_res,left_on = 'datcnv_date', right_on = 'SAMPLING_DATE',how = "outer"))
				tables.append(pd.merge(meta_res,expertnotes_res,left_on = 'Year', right_on = 'YEAR',how = "right"))

		allTables = pd.concat(tables)
		return allTables

	def filterDup(self,meta_res, season = "summer"):
		# Find the duplicate profiles
		maxDepth = []
		for fileId_ in meta_res.fileId:
			sql_data = "Select * from %s_data where fileId = %d Order By 'index' ASC" %(season,fileId_)
			sensorData = pd.read_sql_query(sql_data,self.engine).drop('index',axis = 1)
			maxDepth.append(max(sensorData.Depth))

		whichMax = np.argmax(maxDepth)
		return meta_res.fileId[whichMax]


	def calculateThermoFlux(self):
		allResults = []
		maxDepthDict = pickle.load(open("/Users/wenzhaoxu/Developer/Seabird/SeabirdCode/thermoFlux_maxDepth_SU.p","rb"))
		for station in self.allStations.STATION:
			if station.startswith("SU"):
				for year in self.allYears:
					springRes,_ = self.findEntry(station, year,"spring")
					summerRes,_ = self.findEntry(station, year,"summer")

					res = {"year":year,"station":station,"temperatureDifference":None,"maxDepth":None,"minDepth":None,"summerSum":None,"springSum":None}

					if summerRes.shape[0]>0 and springRes.shape[0]>0:
						fileId_summer = self.filterDup(summerRes,"summer")
						fileId_spring = self.filterDup(springRes,"spring")

						# print fileId_summer, fileId_spring

						summerSeabird = seabird(self.config)
						summerSeabird.rawData = pd.read_sql_query("Select * from %s_data where fileId = %d Order By 'index' ASC" %("summer",fileId_summer)
							,self.engine).drop('index',axis = 1)

						springSeabird = seabird(self.config)
						springSeabird.rawData = pd.read_sql_query("Select * from %s_data where fileId = %d Order By 'index' ASC" %("spring",fileId_spring)
							,self.engine).drop('index',axis = 1)

						summerSeabird.preprocessing()
						springSeabird.preprocessing()

						# print springSeabird.cleanData

						# minDepth = max(min(summerSeabird.cleanData.Depth),min(springSeabird.cleanData.Depth))
						minDepth = 3.0
						# maxDepth = min(max(summerSeabird.cleanData.Depth),max(springSeabird.cleanData.Depth))
						maxDepth = maxDepthDict[station]
						# print maxDepth

						summerTemperature = summerSeabird.cleanData.Temperature[(summerSeabird.cleanData.Depth<=maxDepth) & (summerSeabird.cleanData.Depth>=minDepth)]
						springTemperature = springSeabird.cleanData.Temperature[(springSeabird.cleanData.Depth<=maxDepth) & (springSeabird.cleanData.Depth>=minDepth)]


						res["temperatureDifference"] = sum(summerTemperature-springTemperature)
						res["maxDepth"] = maxDepth
						res["minDepth"] = minDepth
						res["summerSum"] = sum(summerTemperature)
						res["springSum"] = sum(springTemperature)
						
						print res

					allResults.append(res)

		return pd.DataFrame(allResults)

	def detect(self):
		# Detect the features
		duplicateExpertNotes = []
		errorFileId = []
		results = []
		for station in self.allStations.STATION:
			for year in self.allYears:
				print station,year
				meta_res,expertnotes_res = self.findEntry(station, year)
				expertNotes = {"LEP":None,"TRM":None,"UHY":None,"DCL":None}

				if len(expertnotes_res) >0:
					for i in range(expertnotes_res.shape[0]):
						if expertNotes[expertnotes_res.DepthCode[i]] is not None:
							duplicateExpertNotes.append(expertnotes_res)
						expertNotes[expertnotes_res.DepthCode[i]] = expertnotes_res.Depth[i]

				if meta_res.shape[0]>0:
					fileId_ = self.filterDup(meta_res)  # choose the depth profile with maximum depth
					print fileId_  

					try:
						mySeabird=seabird(config = self.config)
						mySeabird.loadData(fileId = fileId_)
						mySeabird.setExpert(notes = expertNotes)
						# print expertNotes
						mySeabird.preprocessing()
						mySeabird.identify()
						res = mySeabird.features
						
						res["fileId"] = mySeabird.fileId
						res["site"] = mySeabird.site
						res["time"] = mySeabird.time
						res["year"] = year

						for d in ["LEP","UHY","TRM","DCL"]:
							res["expert_"+d] = expertNotes[d]

						fname = "/Users/wenzhaoxu/Developer/Seabird/output/meta/"+mySeabird.site+"_"+str(year)+"_"+str(fileId_)
						
						pickle.dump(mySeabird,open(fname+".p","wb"))  # pickle the data
						mySeabird.plot(filename = fname+".png") # plot the results
						
					except:
						res = {"site":station,"year":year,"fileId":fileId_}
						errorFileId.append(fileId_)
						traceback.print_exc()
				
				else:
					res = {"site":station,"year":year,"fileId":None}

				results.append(res)

		# print len(results)
		results = pd.DataFrame(results)
		results.to_csv("/Users/wenzhaoxu/Developer/Seabird/output/detectedFeatures.csv")
		pickle.dump(duplicateExpertNotes,open("/Users/wenzhaoxu/Developer/Seabird/output/duplicateExpertNotes.p","wb"))
		pickle.dump(errorFileId,open("/Users/wenzhaoxu/Developer/Seabird/output/errorFileId.p","wb"))

		print duplicateExpertNotes
		print errorFileId


def extractWaterChemistryData(featureFile):
	# Extract Water chemistry data
	feature = pd.read_csv(featureFile)

	varList = ["DO","Temperature","Specific_Conductivity","Fluorescence","Beam_Attenuation"]
	epilimnionFeature = np.zeros((feature.shape[0],2*len(varList)))-1
	hypolimnionFeature = np.zeros((feature.shape[0],2*len(varList)))-1

	metaArray = []

	for i in range(feature.shape[0]):
		site = feature.site[i]
		year = feature.year[i]
		fid = feature.fileId[i]
		metaArray.append([fid,site,year])
		print fid

		if fid  is None:
			continue

		LEP = feature.LEP_segment[i]
		UHY = feature.UHY_segment[i]
		
		try:
			mySeabird = pickle.load(open("/Users/wenzhaoxu/Developer/Seabird/output/meta/%s_%d_%d.p" %(site,int(year),int(fid)),"rb"))
			data = mySeabird.cleanData
			# print data.columns.values
			for var in varList:
				if var not in data.columns.values:
					print var
					# print data.columns.values
					data[var]=np.nan

			if LEP is not None:
				epilimnion = data[data.Depth<LEP][varList]
				epilimnionFeature[i,:len(varList)] = epilimnion.mean()
				epilimnionFeature[i,len(varList):] = epilimnion.var()
			if UHY is not None:
				hypolimnion = data[data.Depth>UHY][varList]
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

	metaArray = pd.DataFrame(metaArray,columns = ["fid","site","year"]) # create meta array
	waterChemistryFeature = pd.concat([metaArray,waterChemistryFeature],axis = 1) # create final water chemistry

	waterChemistryFeature.to_csv("../output/waterFeature.csv")

if __name__ == '__main__':
	import json

	engine = create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')
	config = json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/config.json'))
	GLSummary = summary(engine,config)

	res = GLSummary.calculateThermoFlux()
	res.to_csv("thermoFlux_SU.csv")
	pickle.dump(res, open("thermoFlux_SU.p","wb"))
	# GLSummary.detect()
	# extractWaterChemistryData("/Users/WenzhaoXu/Developer/Seabird/output/detectedFeatures.csv")
	
	# print GLSummary.allStations.STATION
	# allTables = GLSummary.writeAllAlignments()
	# allTables.to_csv("/Users/WenzhaoXu/Desktop/test2.csv")
