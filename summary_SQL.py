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
		self.config = config

	def sqlQuery(self,sql):
		return pd.read_sql_query(sql,self.engine)

	def getAllStations(self,depthCode = ['LEP','TRM','UHY','DCL']):
		depthCode = "','".join(depthCode)
		sql = '''Select DISTINCT(STATION) from expertNotes where DepthCode in ('%s') and YEAR >= 1996;''' %(depthCode)
		return self.sqlQuery(sql)

	
	def findEntry(self,station,year):
		subStation = station[:4]
		sql_meta = '''select systemUploadTime,datcnv_date,fileId,stationInfered, year(systemUpLoadTime) as Year from summer_meta where stationInfered = '%s' And year(systemUpLoadTime) = %d''' %(subStation,year)
		sql_expertnotes = '''select 'index',SAMPLING_DATE,STATION,YEAR,DepthCode,SMPL_DEPTH as Depth from expertNotes where STATION = '%s' And YEAR = %d AND DepthCode in ('LEP','TRM','UHY','DCL') AND MONTH(SAMPLING_DATE) IN (6,7,8,9,10); ''' %(station,year)
		meta_res = self.sqlQuery(sql_meta)
		expertnotes_res = self.sqlQuery(sql_expertnotes)
		return meta_res,expertnotes_res

	def writeAllAlignments(self):
		tables = []
		for station in self.allStations.STATION:
			for year in self.allYears:
				meta_res,expertnotes_res = self.findEntry(station, year)
				tables.append(pd.merge(meta_res,expertnotes_res,left_on = 'datcnv_date', right_on = 'SAMPLING_DATE',how = "outer"))
		allTables = pd.concat(tables)
		return allTables

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


				for fileId_ in meta_res.fileId:
					try:
						mySeabird=seabird(config = self.config)
						mySeabird.loadData(fileId = fileId_)
						mySeabird.setExpert(notes = expertNotes)
						mySeabird.preprocessing()
						mySeabird.identify()
						res = mySeabird.features
						res["fileId"] = mySeabird.fileId
						res["site"] = mySeabird.site
						res["year"] = mySeabird.time
						for d in ["LEP","UHY","TRM"]:
							res["expert_"+d] = expertNotes[d]

						fname = "/Users/WenzhaoXu/Developer/Seabird/output/plot/"+mySeabird.site+"_"+str(mySeabird.time)+".png"
						mySeabird.plot(filename = fname)
						results.append(res)
					except:
						errorFileId.append(fileId_)

		print len(results)
		results = pd.DataFrame(results)
		results.to_csv("/Users/WenzhaoXu/Developer/Seabird/output/newDetected.csv")
		pickle.dump(duplicateExpertNotes,open("/Users/WenzhaoXu/Developer/Seabird/output/duplicateExpertNotes.p","wb"))
		pickle.dump(errorFileId,open("/Users/WenzhaoXu/Developer/Seabird/output/errorFileId.p","wb"))

		print duplicateExpertNotes
		print errorFileId

if __name__ == '__main__':
	import json
	engine = create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/seabird/config.json'))
	GLSummary = summary(engine,config)
	GLSummary.detect()
	# print GLSummary.allStations.STATION
	# allTables = GLSummary.writeAllAlignments()
	# allTables.to_csv("/Users/WenzhaoXu/Desktop/test.csv")
