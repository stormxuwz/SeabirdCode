from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from seabird.seabird_class import seabird
import traceback
import cPickle as pickle

class summary(object):
	def __init__(self,engine,config):
		self.engine = engine
		self.allYears = range(1996,2014)
		self.allStations = self.getAllStations()
		print self.allStations
		self.config = config

	def sqlQuery(self,sql):
		return pd.read_sql_query(sql,self.engine)

	def getAllStations(self,depthCode = ['LEP','TRM','UHY','DCL']):
		depthCode = "','".join(depthCode)
		sql = '''Select DISTINCT(stationInfered) as STATION from summer_meta where year(systemUpLoadTime) >= 1996 ORDER BY STATION;'''
		return self.sqlQuery(sql)

	def findEntry(self,station,year):
		subStation = station[:4]
		sql_meta = '''select systemUploadTime,datcnv_date,fileId,stationInfered, year(systemUpLoadTime) as Year from summer_meta where stationInfered = '%s' And year(systemUpLoadTime) = %d''' %(subStation,year)
		sql_expertnotes = '''select `index`,SAMPLING_DATE,STATION,YEAR,DepthCode,SMPL_DEPTH as Depth from expertNotes where STATION = '%s' And YEAR = %d AND DepthCode in ('LEP','TRM','UHY','DCL') AND MONTH(SAMPLING_DATE) IN (6,7,8,9,10); ''' %(station,year)
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

	def filterDup(self,meta_res):
		maxDepth = []
		for fileId_ in meta_res.fileId:
			sql_data = "Select * from summer_data where fileId = %d Order By 'index' ASC" %(fileId_)
			sensorData = pd.read_sql_query(sql_data,self.engine).drop('index',axis = 1)
			maxDepth.append(max(sensorData.Depth))

		whichMax = np.argmax(maxDepth)
		return meta_res.fileId[whichMax]

	def detect(self):
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
					# for fileId_ in meta_res.fileId:
						# print fileId_
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

						fname = "/Users/WenzhaoXu/Developer/Seabird/output/meta/"+mySeabird.site+"_"+str(mySeabird.time)+"_"+str(fileId_)
						
						pickle.dump(mySeabird,open(fname+".p","wb"))  # pickle the data
						mySeabird.plot(filename = fname+".png") # plot the results
						
					except:
						res = {"site":station,"year":year}
						errorFileId.append(fileId_)
				
				else:
					res = {"site":station,"year":year}

				results.append(res)

		# print len(results)
		results = pd.DataFrame(results)
		results.to_csv("/Users/WenzhaoXu/Developer/Seabird/output/detectedFeatures.csv")
		pickle.dump(duplicateExpertNotes,open("/Users/WenzhaoXu/Developer/Seabird/output/duplicateExpertNotes.p","wb"))
		pickle.dump(errorFileId,open("/Users/WenzhaoXu/Developer/Seabird/output/errorFileId.p","wb"))

		print duplicateExpertNotes
		print errorFileId

if __name__ == '__main__':
	import json
	engine = create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')
	config = json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/config.json'))
	GLSummary = summary(engine,config)

	GLSummary.detect()
	# print GLSummary.allStations.STATION
	# allTables = GLSummary.writeAllAlignments()
	# allTables.to_csv("/Users/WenzhaoXu/Desktop/test2.csv")
