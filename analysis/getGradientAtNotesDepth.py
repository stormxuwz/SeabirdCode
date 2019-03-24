# scripts to get expert gradients from the training data
import pandas as pd
import numpy as np
from seabird.seabird_class import seabird
import traceback
import cPickle as pickle
import sys
import os

def matchSegGradient(depth, segDepth):
	for i in range(len(segDepth)):
		if segDepth[i][1] > depth:
			break
	if segDepth[i][0] >= depth:
		i = i-1	
	return i

def findGradient(depth, pdData):
	# pdData is a pandas framework of columns of depth and temperature
	idx = np.searchsorted(pdData.Depth, depth)[0]
	g = (pdData.Temperature[idx-1] - pdData.Temperature[idx]) / (pdData.Depth[1] - pdData.Depth[0])

	# print "tmp1", pdData.Temperature[idx-1] - pdData.Temperature[idx]
	return g


def getGradientFromSegment(seg, depthInterval = 0.25):
	return (seg[0][0]-seg[0][1])/depthInterval

def getExpertGradientFromSeabirdObj(seabirdObj):
	segmentList = seabirdObj.thermocline.models["segmentation"].segmentList
	segDepth = [  list(seabirdObj.cleanData.Depth[ [seg[1][0],seg[1][-1]] ]) for seg in segmentList]
	segGradient = [getGradientFromSegment(seg) for seg in segmentList]
	res = {}

	# print seabirdObj.expert
	# print segGradient
	# print segDepth
	res["site"] = seabirdObj.site
	res["fileId"] = seabirdObj.fileId
	res["year"] = seabirdObj.time.year

	for legend in ["LEP","UHY","TRM"]:
		targetDepth = seabirdObj.expert[legend]
		if targetDepth is None:
			continue
		idx = matchSegGradient(targetDepth, segDepth)
		# print idx
		res[legend+"_dataGradient"] = findGradient(targetDepth, seabirdObj.cleanData.loc[:,["Depth","Temperature"]])

		if legend == "LEP":
			res["LEP_gradient"] = segGradient[idx] # the gradient of the segment which contains the operators' LEP
			EPI_gradient = [segGradient[i] for i in range(idx)]
			res["EPI_meanGradient"] = np.mean(EPI_gradient) # the mean gradient of all segments in the LEP
		elif legend == "UHY":
			res["UHY_gradient"] = segGradient[idx]
			UHY_gradient = [segGradient[i] for i in range(idx+1, len(segmentList))]
			res["UHY_meanGradient"] = np.mean(UHY_gradient)
		elif legend == "TRM":
			res["TRM_gradient"] = segGradient[idx]
		else:
			raise ValueError("legend is not correct")
	# print res
	return res

if __name__ == '__main__':
	directory = "/Users/wenzhaoxu/Developer/Seabird/output/meta"
	# seabirdObj = pickle.load(open(directory + "/ER09_1996_4.p","rb"))
	# print getExpertGradientFromSeabirdObj(seabirdObj)

	fullRes = []
	for filename in os.listdir(directory):
		if filename.endswith(".p"):
			print filename
			try:
				seabirdObj = pickle.load(open(os.path.join(directory, filename),"rb"))
				fullRes.append(getExpertGradientFromSeabirdObj(seabirdObj))
			except:
				continue
	print fullRes

	df = pd.DataFrame(fullRes)
	df.to_csv("featuresAtExpertDepths.csv")
