import seabird
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json,sys
import logging
from sqlalchemy import create_engine

def test():
	from seabird.seabird_class import seabird
	config=json.load(open('/Users/WenzhaoXu/Developer/Seabird/SeabirdCode/config.json'))
	mySeabird = seabird(config = config)

	# mySeabird.loadData(dataFile = "/Users/WenzhaoXu/Developer/Seabird/input/history_data/1996/SUMMER96/SU04SU96.CNV")
	# mySeabird.loadData(dataFile="sample.cnv")
	mySeabird.loadData(fileId=733)
	# mySeabird.loadData("")
	mySeabird.preprocessing()
	# print mySeabird.cleanData
	mySeabird.identify()
	# mySeabird.plot_all()
	# fname = "/Users/WenzhaoXu/Developer/Seabird/output/plot/"+mySeabird.site+"_"+str(mySeabird.time)+".png"
	fname=None
	mySeabird.plot(filename = fname,meta = True)
	print mySeabird.cleanData.Depth[39]
	plt.show()

	print mySeabird.features

def runApp():
	from seabird.seabirdGUI import SeabirdGUI
	import warnings
	from Tkinter import Tk
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		root=Tk()
		root.geometry("1200x650")
		app=SeabirdGUI(master=root)
		root.mainloop()
		root.destroy()


if __name__ == '__main__':
	test()
