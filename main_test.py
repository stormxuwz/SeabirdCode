from __future__ import print_function
from seabird.seabird_class import seabird
from seabird.models.stratificationIndex import *
from seabird.models.model_peak import peak
from scipy import signal
import pickle
import os

if __name__ == '__main__':
	import json
	config=json.load(open('config.json'))

	mySeabird = seabird(config=config)	
	mySeabird.loadData(dataFile="sample.cnv")

	print(mySeabird.site, mySeabird.time)
	mySeabird.preprocessing()
	mySeabird.identify()

	print (mySeabird.features)
	print (mySeabird.features["DCL_leftShapeFitErr"], mySeabird.features["DCL_rightShapeFitErr"])
	print (mySeabird.features["DCL_leftSigma"], mySeabird.features["DCL_rightSigma"])
	depth = mySeabird.cleanData.Depth
	print (depth)
	Fluorescence = mySeabird.cleanData.Fluorescence

	plt.figure()
	plt.plot(Fluorescence)
	mySeabird.plot()
	plt.show()