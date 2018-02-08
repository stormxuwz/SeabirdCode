from seabird_parser import seabird_file_parser
import os
from sqlalchemy import create_engine
import cPickle as pickle
from collections import defaultdict

SU = defaultdict(int)

SQLEngine=create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')

path = "/Users/wenzhaoxu/Developer/Seabird/input/springData/"
fileId = 0
for year in range(1996,2015):
	inputFolder = "%s/%d/SU/" %(path,year)
	
	for filename in os.listdir(inputFolder):
		if filename.lower().endswith(".cnv") and "bin" not in filename.lower():
			parser = seabird_file_parser()
			parser.readFile(inputFolder+filename,fileId=fileId)
			parser.sendtoDatabase(SQLEngine, tableName = {"meta":"spring_meta","data":"spring_data"})
			
			SU[(year, parser.meta["stationInfered"])]+=1
			
			print year,parser.meta["stationInfered"]

			fileId+=1


for k,v in SU.items():
	if v>1:
		print k,v

pickle.dump(SU, open("/Users/wenzhaoxu/Developer/Seabird/output/stations_SU.p","wb"))

