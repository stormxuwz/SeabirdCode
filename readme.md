# CTD thermocline and DCL automated detector

This folder creates a tool to analyze CTD (conductivity, Temperature, and depth) profilers, specifically for SeaBird CTD profilers.

It can 
* Detect lake stratification (the location of thermocline, epilimnion, hypolimnion) using linear segmentation, HMM or spectrogram methods. 
* Detect deep chlorophyll layers by fitting two half gaussian curves on peak points

---
To use:
	
	import seabird
	
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/seabird/config.json'))
	mySeabird = seabird(config = config)  # config is in json format
	filename = "sample.cnv"
	mySeabird.loadData(dataFile = filename)  # filename is the cnv file, taking data from database is optional, see the source code
	mySeabird.preprocessing()
	mySeabird.identify()
	features = mySeabird.features  # features are in dictionary format.
	
To plot:

	mySeabird.plot_all(interestVarList=["Temperature","DO","Specific_Conductivity","Fluorescence","Par"]) # plot the water quality from raw data
	mySeabird.plot() # plot the detected depth

---
File structure:

	--Seabird:
		--seabirdGUI.py: GUI build based on Tkinter
		--seabird_class.py: seabird class
		-- deepChlLayers: DCL class
		-- thermocline: thermocline class
	--tools: contain general file parser, database connection
	--models: linear segmentation, HMM and threshold methods
	