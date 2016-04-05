import pandas as pd

def findExpertData(sourceFile):
	import os
	expertDataFile = pd.read_csv("./data/data_expert_lineup.csv")
	
	hasExpert = expertDataFile.dataFile.str.contains(sourceFile, na=False)

	if len(expertDataFile.expertFile[hasExpert])==0:
		return None
	return expertDataFile.expertFile[hasExpert].values[0]
