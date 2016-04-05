from sqlalchemy import create_engine
import sqlalchemy
import numpy as np
import pandas as pd
from datetime import datetime
import glob,os

def extractTimeInfo(metaString):
	metaString=metaString.split(";")
	timeInfo=datetime.strptime(metaString[0],"%Y_%b_%d-%H:%M:%S")
	originFile=metaString[1]
	return timeInfo,originFile

def addingInfo(data,station,year,index):
	maxDepth_index=np.argmax(data["Depth"])
	data=data.iloc[:maxDepth_index+1,:-1]
	data["station"]=station
	data["year"]=year
	data["stationIndex"]=index
	if "Beam_Transmission" not in data:
		data["Beam_Transmission"]=np.nan
	# data.reset_index(drop=True)
	return data

class seabird2SQL(object):

	def __init__(self,csvFolder):
		self.csvFolder=csvFolder
		self.SQLEngine=create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')

	def readCSV(self,fname,index):
		data=pd.read_csv(fname)
		fname=os.path.basename(fname)
		fname_tmp = fname.split("_")
		station=fname_tmp[0]
		year=int(fname_tmp[1])

		time,originalFile=extractTimeInfo(list(data)[-1])
		meta=pd.DataFrame({"stationIndex":[index],"station":[station],"time":[time],"originalFile":[originalFile]},index=[index])
		data=addingInfo(data,station,year,index)
		return data,meta


	def push2SQL(self,data,meta):
		data.to_sql("seabird",self.SQLEngine,flavor="mysql",if_exists="append")
		meta.to_sql("seabird_meta",self.SQLEngine,flavor="mysql",if_exists="append",dtype={"time":sqlalchemy.types.DateTime})

	def test(self,fname):
		data,meta=self.readCSV(self.csvFolder+fname,0)
		self.push2SQL(data,meta)

	def pushAll(self):
		df = pd.DataFrame()
		allMeta=pd.DataFrame()
		for findex,fname in enumerate(glob.glob(self.csvFolder+"*.csv")):
			print(fname)
			data,meta=self.readCSV(fname,findex)
			# df=df.append(data)
			# allMeta=allMeta.append(meta)
			# df=df.reset_index(drop=True)
			self.push2SQL(data,meta)
			
		# self.push2SQL(df,allMeta)

			

if __name__ == '__main__':
	job=seabird2SQL("/Volumes/Mac Backup/Developer/Project_IO/Seabird/csvFile/")
	# print job.test("ER09_1999_Aug_06.csv")
	job.pushAll()


