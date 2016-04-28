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
		sql_expertnotes = '''select SAMPLING_DATE,STATION,YEAR from expertNotes where STATION = '%s' And YEAR = %d AND DepthCode in ('LEP','TRM','UHY','DCL') group by SAMPLING_DATE, STATION, YEAR; ''' %(station,year)

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
		tables = []
		for station in self.allStations.STATION:
			for year in self.allYears:
				meta_res,expertnotes_res = self.findEntry(station, year)
				
				mySeabird=seabird(fileName=self.counterpart.dataFile[i],config=config, expertFile=self.counterpart.expertFile[i])

				mySeabird = seabird(config = config)




if __name__ == '__main__':
	engine = create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/seabird/config.json'))
	GLSummary = summary(engine)
	# print GLSummary.allStations.STATION
	# allTables = GLSummary.writeAllAlignments()
	# allTables.to_csv("/Users/WenzhaoXu/Desktop/test.csv")
