'''
This file contains a function to parse Seabird cnv files
'''
import numpy as np

def check_StationName(Name):
	# print Name
	if len(Name)<5:
		accurateName=Name
	else:
		if(Name[4]=="M" or Name[4]=="B"):
			accurateName=Name[0:5]
		else:
			accurateName=Name[0:4]

	return accurateName  


def read_seabird_file(filename):
	sensordata=[]
	columnNum=0
	with open(filename,"r") as file:
		lines=file.readlines();
		if(lines==[]):
			return None,None,None,None
		variable_name_dictionary={"depF:":"Depth","depFM:":"Depth","t068:":"Temperature","t090:":"Temperature","t090C:":"Temperature","specc:":"Specific_Conductivity","bat:":"Beam_Attenuation","sbeox0Mg/L:":"DO","oxMg/L:":"DO","xmiss:":"Beam_Transmission","flSP:":"Fluorescence","flS:":"Fluorescence","ph:":"pH","c0mS/cm:":"Conductivity","c0uS/cm:":"Conductivity","par:":"Par","spar:":"SPar","prDE":"Pressure"}

		column_index=[];
		varNameList=[];

		for line_index,line in enumerate(lines):
			# This loop finds the meta information
			content=line.split()
			if len(content)==1 and content[0]!="*END*":
				continue;
			
			if len(content)<1:
				continue;

			if content[0]=="*":
				if content[1]=="System":
					if content[3]=="Time":
						data_time=content[7]+"_"+content[5]+"_"+content[6]+"-"+content[8]

				if content[1]=="Station" or content[1]=="Station:":
					if len(content)==2:
						stationName=filename.split("/")[-1][:4]

					else:
						stationName=content[2].upper()
						stationName=check_StationName(stationName)


			elif content[0]=="**":
				if content[1]=="Station:" or content[1]=="Station":
					if len(content)==2:
						stationName=filename.split("/")[-1][:4]

					else:
						stationName=content[2].upper()
						stationName=check_StationName(stationName)

			elif content[0]=="#":
				if content[1]=="name":
					columnNum=columnNum+1;
					if(content[4] in variable_name_dictionary):
						varname=variable_name_dictionary[content[4]];
						column_index.append(int(content[2]))
						varNameList.append(varname)
					else:
						# print content[4]+"is not in the dictionary"
						pass;

			elif content[0]=="*END*":
				endline_index=line_index
				break

		for line in lines[endline_index+1:]:
			# This loop Read all data information
			try:
				if(len(line.split())!=columnNum):
					continue;
				else:
					data=[float(t) for t in line.split()];
					sensordata.append(data);
			except: # dealing with contaminated data
				continue

	sensordata=np.array(sensordata)

	if(sensordata.shape[0]==0):
		sensordata=None
	else:
		sensordata=np.array(sensordata)[:,column_index]

	return sensordata,data_time,stationName,varNameList






if __name__ == '__main__':
	# filename="/Users/XuWenzhao/Developer/DataSource/Seabird/Summer12 SBE/Michigan/MI48b.cnv.cnv"
	import os,sys
	duplicate=1
	import pandas as pd

	def cnv2csv(filename):
		station_fileName=filename.split("/")[-1][:4].upper() # Station_fileName is the station information extracted from file name
		data,time,site,varList=read_seabird_file(filename)
		 # station is the station information extracted from file meta data part
		if(data is None):
			return
		
		nrow_data=data.shape[0]
		index_column=np.array(range(nrow_data))+1
		index_column=np.reshape(index_column,(nrow_data,1))
		data=np.append(data,index_column,1)
		varList.append(time+";"+filename)

		## Save to csv file ##
		import csv
		filename=station_fileName+"_"+time.split("-")[0]
		full_filename="/Users/XuWenzhao/Developer/Project_IO/Seabird/csvFile2/"+filename
		
		
		if(os.path.isfile(full_filename+".csv")):
			duplicate=1
			while(os.path.isfile(full_filename+"-"+str(duplicate)+".csv")):
				duplicate=duplicate+1

			full_filename=full_filename+"-"+str(duplicate)

		print full_filename;
		
		with open(full_filename+".csv","wb") as outcsv:
			writer=csv.writer(outcsv)
			writer.writerow(varList)
			[writer.writerow(line) for line in data]

	def reGenerateCSV():
		directory="/Users/XuWenzhao/Developer/Project_IO/Seabird/csvFile/"
		for root,dirs,files in os.walk(directory):
			for filename in files:
				if filename.endswith(".csv"):
					data=pd.read_csv(os.path.join(root,filename))
					item=list(data.columns.values)[-1]
					originalName=item.split(";")[1]
					print originalName
					cnv2csv(originalName)

	# cnv to csv
	# directory="/Users/XuWenzhao/Developer/Project_IO/Seabird/history_data/"
	# directory="/Users/XuWenzhao/Developer/Project_IO/Seabird/history_data/2012/Summer12 SBE/Erie"
	# for root, dirs, files in os.walk(directory):
	# 	for filename in files:
	# 		if filename.endswith('.cnv') or filename.endswith('.CNV'):
	# 			if filename.endswith(".cnvbin.cnv") or filename.endswith("cnvbin.cnv") :
	# 				print "pass", filename
	# 				pass
	# 			else:
	# 				fullpath = os.path.join(root, filename)
	# 				# if "SUMMER" in str(fullpath).upper() and "DUP" not in str(fullpath).upper() and "CAST" not in str(fullpath).upper() and "TEMP" not in str(fullpath).upper() and "ROS" not in str(fullpath).upper():
	# 				if any(lake in str(fullpath).upper() for lake in ["MI","ER","SU","ON","HU"]):
	# 					print fullpath

	# 					# Finds the five Great Lakes data in Summer.
	# 					cnv2csv(fullpath)
							

	# cnv2csv("/Users/XuWenzhao/Developer/Project_IO/Seabird/history_data/1999/Summer99/Susea/su121b9921.cnv")
	reGenerateCSV()






	