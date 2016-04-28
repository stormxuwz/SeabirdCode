from seabird.seabird_class import seabird



if __name__ == '__main__':
	import json
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/seabird/config.json'))
	mySeabird = seabird(config = config)
	mySeabird.loadData(fileId = 511)


	# print mySeabird.thermocline.detect(data = mySeabird.cleanData[["Depth","Temperature"]],methods = ["segmentation"])
	# print mySeabird.thermocline.detect(data = mySeabird.cleanData[["Depth","Temperature"]],methods = ["HMM"])
	# print mySeabird.thermocline.detect(data = mySeabird.cleanData[["Depth","Temperature"]],methods = ["threshold"])
	# print mySeabird.DCL.detect(data = mySeabird.cleanData[["Depth","Fluorescence"]])
	mySeabird.identify()
	print mySeabird.features