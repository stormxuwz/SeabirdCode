from __future__ import print_function
from seabird.seabird import Seabird
import matplotlib.pyplot as plt

if __name__ == '__main__':
	import json
	config=json.load(open('config.json'))

	seabird_obj = Seabird(config=config)	
	seabird_obj.load_data(data_file="sample.cnv")

	print(seabird_obj.site, seabird_obj.time)
	seabird_obj.preprocess()
	seabird_obj.identify()

	print(seabird_obj.features)
	print(seabird_obj.features["DCL_leftShapeFitErr"], seabird_obj.features["DCL_rightShapeFitErr"])
	print(seabird_obj.features["DCL_leftSigma"], seabird_obj.features["DCL_rightSigma"])
	depth = seabird_obj.cleandata.Depth
	print(depth)
	fluorescence = seabird_obj.cleandata.Fluorescence

	plt.figure()
	plt.plot(fluorescence)
	seabird_obj.plot()
	plt.show()