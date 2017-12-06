# CTD thermocline and DCL automated detector

This folder creates a tool to analyze CTD (conductivity, Temperature, and depth) profilers, specifically for SeaBird CTD profilers.

It can:
* Detect lake stratification (the location of thermocline, epilimnion, hypolimnion) using piecewise linear segmentation (HMM with maximum gradient is currently turned off to save compuation time)
* Detect deep chlorophyll layers by fitting two half gaussian curves on peak points

---
To use:
	
	from seabird.seabird_class import seabird
	import json
	import matplotlib.pyplot as plt
	
	config=json.load(open('config.json'))
	mySeabird = seabird(config = config)  # config is in json format
	filename = "sample.cnv"
	mySeabird.loadData(dataFile = filename)  # filename is the cnv file, taking data from database is optional, see the source code
	mySeabird.preprocessing()
	mySeabird.identify()
	features = mySeabird.features  # features are in dictionary format.

	print features
	
To plot:

	mySeabird.plot_all(interestVarList=["Temperature","DO","Specific_Conductivity","Fluorescence","Par"]) # plot the water quality from raw data
	mySeabird.plot() # plot the detected depth
	plt.show()

---
File structure:

 	
	--Seabird:
		--seabirdGUI.py: GUI build based on Tkinter
		--seabird_class.py: seabird class
		-- deepChlLayers.py: DCL class
		-- thermocline.py: thermocline class
		--tools: contain general file parser, database connection
		--models: Piecewise linear segmentation, HMM and threshold methods. 
	