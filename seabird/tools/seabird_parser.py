import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import os

class seabird_file_parser():
	def __init__(self,fileId = None):
		self.meta = {"longitude":None,"latitude":None,"UTC":None,"station":None,"cruise":None,"fileOriginName":None,"systemUpLoadTime":None,"fileName":None,"datcnv_date":None,"fileId":fileId}

		self.variable_name_dictionary={"depF":"Depth","depFM":"Depth","t068":"Temperature","t090":"Temperature","t090C":"Temperature","specc":"Specific_Conductivity","bat":"Beam_Attenuation","sbeox0Mg/L":"DO","oxMg/L":"DO","xmiss":"Beam_Transmission","flSP":"Fluorescence","flS":"Fluorescence","ph":"pH","c0mS/cm":"Conductivity","c0uS/cm":"Conductivity","par":"Par","spar":"SPar","prDE":"Pressure"}
		
		self.variableFinal = ["Depth","Temperature","Specific_Conductivity","Beam_Attenuation","DO","Beam_Transmission","Fluorescence","pH","Conductivity","Par","SPar","Pressure"]
		self.badFile = False
		self.cruise = None
		self.dataColumn = []
		self.sensordata = None

	def readFile(self,filename):
		if filename.lower().endswith(".cnv"):
			sensordata = self.readCnvFile(filename)
		elif filename.lower().endswith(".csv"):
			sensordata = self.readCSVFile(filename)
		
		self.sensordata = sensordata.rename(columns = self.variable_name_dictionary)

		for var in self.variableFinal:
			if var not in self.sensordata.columns.values:
				self.sensordata[var] = np.nan

		self.sensordata = self.sensordata[self.variableFinal]
		self.sensordata["fileId"] = self.meta["fileId"]
			
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
						sensordata.append([float(t) for t in line.split()])
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

	def sendtoDatabase(self,engine):
		meta = pd.DataFrame.from_dict([self.meta],orient='columns')
		self.sensordata.to_sql("seabird_data",engine,flavor="mysql",if_exists="append",index = True)
		meta.to_sql("seabird_meta",engine,flavor="mysql",if_exists="append",index = False)

	def saveToCSV(self,fileToSave):
		pass

def main():
	fileId = 0
	rootDir = "/Users/WenzhaoXu/Developer/Hypoxia/input/seabird_data/"
	for dirName, subdirList, fileList in os.walk(rootDir):
		for fname in fileList:
			if fname.lower().endswith(".cnv") and "bin" not in fname.lower():
				filepath = os.path.join(dirName,fname)
				fileId +=1
				print(filepath)
				parser = seabird_file_parser(fileId)
				parser.readFile(filepath)
				
				if parser.badFile is False:
					SQLEngine=create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')
					parser.sendtoDatabase(SQLEngine)



if __name__ == '__main__':
	# main()
	SQLEngine=create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')
	# print retriveData(1, SQLEngine)
	detectThermocline(SQLEngine)


