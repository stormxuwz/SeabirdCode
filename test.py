from seabird.seabird_class import seabird
from seabird.models.stratificationIndex import *


if __name__ == '__main__':
	import json
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/config.json'))
	mySeabird = seabird(config = config)
	mySeabird.loadData(fileId = 600)
	mySeabird.preprocessing()
	mySeabird.identify()

	depth = mySeabird.cleanData.Depth
	temperature = mySeabird.cleanData.Temperature

	BV_idx,BV_depth = BVfrequency(temperature,depth)
	RTRM_idx,RTRM_depth = RTRM(temperature,depth)

	plt.figure()
	ax1 = plt.subplot(131)
	ax1.plot(temperature,-np.array(depth))
	ax1.axhline(-mySeabird.features["TRM_segment"],color = "r")
	ax1.axhline(-mySeabird.features["LEP_segment"],color = "g")
	ax1.axhline(-mySeabird.features["UHY_segment"],color = "y")
	
	ax2 = plt.subplot(132, sharey=ax1)
	ax2.plot(BV_idx,-np.array(BV_depth))
	ax2.axhline(-mySeabird.features["TRM_segment"],color = "r")
	ax2.axhline(-mySeabird.features["LEP_segment"],color = "g")
	ax2.axhline(-mySeabird.features["UHY_segment"],color = "y")
	
	ax3 = plt.subplot(133, sharey=ax1)
	ax3.plot(RTRM_idx,-np.array(RTRM_depth))
	ax3.axhline(-mySeabird.features["TRM_segment"],color = "r")
	ax3.axhline(-mySeabird.features["LEP_segment"],color = "g")
	ax3.axhline(-mySeabird.features["UHY_segment"],color = "y")
	plt.show()
	# print mySeabird.thermocline.detect(data = mySeabird.cleanData[["Depth","Temperature"]],methods = ["segmentation"])
	# print mySeabird.thermocline.detect(data = mySeabird.cleanData[["Depth","Temperature"]],methods = ["HMM"])
	# print mySeabird.thermocline.detect(data = mySeabird.cleanData[["Depth","Temperature"]],methods = ["threshold"])
	# print mySeabird.DCL.detect(data = mySeabird.cleanData[["Depth","Fluorescence"]])
	# mySeabird.identify()
	
	# print mySeabird.features