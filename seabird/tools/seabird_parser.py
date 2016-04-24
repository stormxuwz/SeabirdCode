import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from pytz import timezone
import os

class expert_file_parser():
	def __init__(self):
		self.data = None

	def readFile(self,filename):
		def timeConverter(timeString_):
			print timeString_
			timeString =timeString_.split()
			t = datetime.strptime(timeString[0]+" "+timeString[1],"%Y/%m/%d %H:%M")
			if timeString[2] in ["EDT","EST"]:
				t = timezone("US/Eastern").localize(t)
			elif timeString[2] in ["CDT","CST"]:
				t = timezone("US/Central").localize(t)
			elif timeString[2] == "GMT":
				t = timezone('GMT').localize(t)
			else:
				raise NameError('unknown tz')
			# print t
			t = t.astimezone(timezone("UTC"))
			return t.strftime ("%Y-%m-%d %H:%M:%S")

		self.data = pd.read_csv(filename)
		for i in range(11,69):
			colname = self.data.columns.values[i]
			self.data[colname]= pd.to_numeric(self.data[colname],errors = "coerce")

		self.data["SAMPLING_DATE"] = [timeConverter(t) for t in self.data["SAMPLING_DATE"]]


	def saveToCSV(self,filename):
		self.data.to_csv(filename,index=False)

	def sendtoDatabase(self,dbEngine,tableName):
		self.data.to_sql(tableName,dbEngine,flavor="mysql",if_exists="replace",index = True,chunksize=2000)


class seabird_file_parser():
	def __init__(self):
		self.meta = {"longitude":None,"latitude":None,"UTC":None,"station":None,"cruise":None,"fileOriginName":None,"systemUpLoadTime":None,"fileName":None,"datcnv_date":None,"fileId":None,"lake":None,"stationInfered":None}

		self.variable_name_dictionary={"depF":"Depth","depFM":"Depth","t068":"Temperature","t090":"Temperature","t090C":"Temperature","specc":"Specific_Conductivity","bat":"Beam_Attenuation","sbeox0Mg/L":"DO","oxMg/L":"DO","xmiss":"Beam_Transmission","flSP":"Fluorescence","flS":"Fluorescence","ph":"pH","c0mS/cm":"Conductivity","c0uS/cm":"Conductivity","par":"Par","spar":"SPar","prDE":"Pressure"}
		
		self.variableFinal = ["Depth","Temperature","Specific_Conductivity","Beam_Attenuation","DO","Beam_Transmission","Fluorescence","pH","Conductivity","Par","SPar","Pressure"]
		self.badFile = False
		self.cruise = None
		self.dataColumn = []
		self.sensordata = None

	def readFile(self,filename,fileId = None):
		self.meta["fileId"] = fileId

		if filename.lower().endswith(".cnv"):
			sensordata = self.readCnvFile(filename)
		elif filename.lower().endswith(".csv"):
			sensordata = self.readCSVFile(filename)
		
		if self.badFile:
			return None

		self.sensordata = sensordata.rename(columns = self.variable_name_dictionary)

		for var in self.variableFinal:
			if var not in self.sensordata.columns.values:
				self.sensordata[var] = np.nan

		self.sensordata = self.sensordata[self.variableFinal]
		self.sensordata["fileId"] = self.meta["fileId"]

		self.meta["lake"] = os.path.basename(self.meta["fileName"])[:2].upper()
		self.meta["stationInfered"] = os.path.basename(self.meta["fileName"])[:4].upper()
			
	def readCSVFile(self,filename):
		return pd.read_csv(filename).rename(columns = self.variable_name_dictionary)

	def readCnvFile(self,filename):
		sensordata = []
		dataStarts = False
		self.meta["fileName"] = filename
		with open(filename,"r") as file:
			lines = file.readlines();
			if(lines == []):
				self.badFile = True
				return None

			for line_index, line in enumerate(lines):
				if not dataStarts:
					
					if line[0] == "*" and line[1]!="*":
						if line.startswith("*END*"):
							dataStarts = True
							continue
						content = line[1:].split("=")
						
						if len(content)<2: # No configuration data
							content2 = line[1:].split(":")
							if len(content2)<2:
								continue
							else:
								self.extractMeta(content2)
						else:
							self.extractMeta(content)

					
					if line[:2] == "**":
						content = line[2:].split(":")
						if len(content)<2:
							continue
						else:
							self.extractMeta(content)

					if line[:1] == "#":
						content = line[1:].split("=")
						if len(content)<2:
							continue
						else:
							self.extractDataColumn(content)
				else:
					try:
						content = line.split()
						if len(content)!=len(self.dataColumn):
							continue
						sensordata.append([float(t) for t in content])
					except:
						continue
		
		# print sensordata,self.dataColumn
		if len(sensordata)<1:
			self.badFile = True
			return None
		else:	
			sensordata = pd.DataFrame(data=np.array(sensordata),columns=self.dataColumn)
		
		if "c0mS/cm" in sensordata.columns.values:
			sensordata["c0mS/cm"] = sensordata["c0mS/cm"] * 1000
		
		return sensordata
		

	def extractMeta(self,content):
		key = content[0].strip()
		value = content[1].strip()

		if key in ["NMEA Longitude","Longitude"]:
			self.meta["longitude"] = value

		if key in ["NMEA Latitude","Latitude"]:
			self.meta["latitude"] = value
		
		if key == "NMEA UTC (Time)":
			if value == "none":
				self.meta["UTC"] = None
			else:
				try:
					self.meta["UTC"] = datetime.strptime(value,"%b %d %Y %H:%M:%S")
				except:
					self.meta["UTC"] = datetime.strptime(value,"%H:%M:%S")
		
		if key == "Station":
			self.meta["station"] = value

		if key == "Cruise":
			self.meta["cruise"] = value

		if key == "System UTC":
			self.meta["UTC"] = datetime.strptime(value,"%b %d %Y %H:%M:%S")

		if key == "FileName":
			self.meta["fileOriginName"] = value

		if key  == "System UpLoad Time":
			try:
				self.meta["systemUpLoadTime"] = datetime.strptime(value,"%b %d %Y %H:%M:%S")
			except:
				self.meta["systemUpLoadTime"] = datetime.strptime(value,"%m/%d/%y %I:%M:%S %p")

	def extractDataColumn(self,content):
		key = content[0].strip()
		value = content[1].strip()

		if key.startswith("name"):
			key = key.split(" ")
			value = value.split(":")
			self.dataColumn.append(value[0])

		if key == "datcnv_date":
			self.meta["datcnv_date"] = datetime.strptime(value.split(",")[0],"%b %d %Y %H:%M:%S")

	def sendtoDatabase(self,engine,tableName):
		meta = pd.DataFrame.from_dict([self.meta],orient='columns')
		self.sensordata.to_sql(tableName["data"],engine,flavor="mysql",if_exists="append",index = True,chunksize=2000)
		meta.to_sql(tableName["meta"],engine,flavor="mysql",if_exists="append",index = False)

	def saveToCSV(self,fileToSave):
		pass


def createDataBase(rootDir,dbEngine,tableName):
	fileId = 0
	for dirName, subdirList, fileList in os.walk(rootDir):
		for fname in fileList:
			if fname.lower().endswith(".cnv") and "bin" not in fname.lower():
				filepath = os.path.join(dirName,fname)
				fileId +=1
				print(filepath)
				parser = seabird_file_parser()
				parser.readFile(filepath,fileId)
				
				if parser.badFile is False:
					parser.sendtoDatabase(dbEngine,tableName)


def createDataBase_main():
	SQLEngine=create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')

	# Create database for DO in Lake Erie
	# createDataBase(rootDir = , dbEngine = SQLEngine, tableName = {"meta":"ERDO_meta","data":"ERDO_data"})

	# Create database for summer Seabird Data
	createDataBase(rootDir ="/Users/WenzhaoXu/Developer/Seabird/input/history_data/", dbEngine = SQLEngine, tableName = {"meta":"summer_meta","data":"summer_data"})


	# expertFile = expert_file_parser()
	# expertFile.readFile("/Users/WenzhaoXu/Developer/Seabird/input/All_Lakes_through2012.csv")
	# expertFile.sendtoDatabase(SQLEngine, "expertNotes")
	# expertFile.saveToCSV("/Users/WenzhaoXu/Desktop/expert.csv")

def test(filename):
	SQLEngine=create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')
	parser = seabird_file_parser()
	parser.readFile(filename)
	# print parser.meta
	# print parser.sensordata
	# parser.sendtoDatabase(SQLEngine,tableName = {"meta":"summer_meta","data":"summer_data"})

if __name__ == '__main__':
	createDataBase_main()
	# testFilename = "/Users/WenzhaoXu/Developer/Seabird/input/history_data/2005/summer05/Mich052/MI41cnv.cnv"
	# test(testFilename)



