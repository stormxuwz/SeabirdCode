import numpy as np
import pandas as pd
from datetime import datetime
import os
class SeabirdFileParser():
	def __init__(self):
		self.meta = {"longitude":None,
		"latitude":None,
		"UTC":None,
		"station":None,
		"cruise":None,
		"fileOriginName":None,
		"systemUpLoadTime":None,
		"fileName":None,
		"datcnv_date":None,
		"fileId":None,
		"lake":None,
		"stationInfered":None}

		self.variable_name_dictionary={
		"depF":"Depth",
		"depFM":"Depth",
		"t068":"Temperature",
		"t090":"Temperature",
		"t090C":"Temperature",
		"specc":"Specific_Conductivity",
		"bat":"Beam_Attenuation",
		"sbeox0Mg/L":"DO",
		"oxMg/L":"DO",
		"xmiss":"Beam_Transmission",
		"flSP":"Fluorescence",
		"flS":"Fluorescence",
		"ph":"pH",
		"c0mS/cm":"Conductivity",
		"c0uS/cm":"Conductivity",
		"par":"Par",
		"spar":"SPar",
		"prDE":"Pressure"}
		
		self.variables = [
		"Depth",
		"Temperature",
		"Specific_Conductivity",
		"Beam_Attenuation",
		"DO","Beam_Transmission",
		"Fluorescence","pH",
		"Conductivity",
		"Par",
		"SPar",
		"Pressure"]

		self.bad_file = False
		self.cruise = None
		self.data_columns = []
		self.sensordata = None

	def read_file(self,filename, fileId=None, columns=None):
		self.meta["fileId"] = fileId
		
		if columns is None:
			columns = self.variable_name_dictionary

		if filename.lower().endswith(".cnv"):
			sensordata = self.read_cnv(filename)

			self.sensordata = sensordata.rename(columns=columns)
		
			# fill NA to missing features
			for var in self.variables:
				if var not in self.sensordata.columns.values:
					self.sensordata[var] = np.nan

			# self.sensordata = self.sensordata[self.variableFinal]
			# self.sensordata["fileId"] = self.meta["fileId"]

			self.meta["lake"] = os.path.basename(self.meta["fileName"])[:2].upper()
			self.meta["stationInfered"] = os.path.basename(self.meta["fileName"])[:4].upper()

		elif filename.lower().endswith(".csv"):
			self.sensordata = self.read_csv(filename, columns=columns)
			
		if self.bad_file:
			return None

		self.sensordata = self.sensordata[self.variables]

	def read_csv(self,filename,columns = None):
		return pd.read_csv(filename).rename(columns = columns)

	def read_cnv(self,filename):
		sensordata = []
		is_data_line = False

		self.meta["fileName"] = filename
		with open(filename,"r", errors='ignore') as file:
			lines = file.readlines()
			if(lines == []):
				raise ValueError("file is empty")

			for line in lines:
				if is_data_line is False:
					if line[0] == "*" and line[1]!="*":
						if line.startswith("*END*"):
							is_data_line = True
							continue
						content = line[1:].split("=")
						
						if len(content) < 2: # No configuration data
							content2 = line[1:].split(":")
							if len(content2) < 2:
								continue
							else:
								self.get_meta_data(content2)
						else:
							self.get_meta_data(content)
					
					if line[:2] == "**":
						content = line[2:].split(":")
						if len(content)<2:
							continue
						else:
							self.get_meta_data(content)

					if line[:1] == "#":
						content = line[1:].split("=")
						if len(content) < 2:
							continue
						else:
							self.extract_data_column(content)
				else:
					try:
						content = line.split()
						if len(content) != len(self.data_columns):
							continue
						sensordata.append([float(t) for t in content])
					except:
						continue
		
		if len(sensordata) < 1:
			raise ValueError("no data")
		else:	
			sensordata = pd.DataFrame(data=np.array(sensordata), columns=self.data_columns)
		
		if "c0mS/cm" in sensordata.columns.values:
			sensordata["c0mS/cm"] = sensordata["c0mS/cm"] * 1000 # change to uS/cm
		
		return sensordata
		

	def get_meta_data(self,content):
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

	def extract_data_column(self,content):
		key = content[0].strip()
		value = content[1].strip()

		if key.startswith("name"):
			key = key.split(" ")
			value = value.split(":")
			self.data_columns.append(value[0])

		if key == "datcnv_date":
			self.meta["datcnv_date"] = datetime.strptime(value.split(",")[0],"%b %d %Y %H:%M:%S")

	def send_to_db(self,engine,tableName):
		meta = pd.DataFrame.from_dict([self.meta],orient='columns')
		self.sensordata.to_sql(tableName["data"],engine,flavor="mysql",if_exists="append",index = True,chunksize=2000)
		meta.to_sql(tableName["meta"],engine,flavor="mysql",if_exists="append",index = False)

