from tools.seabird_cnvFileParser import read_seabird_file
from tools.seabird_bottleFileParser import read_bottle_file
from tools.seabird_preprocessing import preprocessing as seabird_pp
from thermocline import thermocline
from deepChlLayers import DCL
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from tools.seabird_parser import seabird_file_parser
from sqlalchemy import create_engine


class seabird:
	def __init__(self, config):
		self.data_file = None
		self.config=config

		self.thermocline = thermocline(config)
		self.DCL = DCL(config)

		self.time = None
		self.site = None
		self.ID = None
		
		self.downCastRawData= None
		self.rawData = None
		self.bottleData = None
		self.cleanData = None
		self.bottleFile = None # maybe useful
		self.features = None
		self.expert = {"TRM":None,"LEP":None,"UHY":None,"DCL":None}

	def loadData(self,dataFile = None,fileId = None, dbEngine = None):
		
		if fileId is None:
			parser = seabird_file_parser()
			parser.readFile(dataFile)
			sensorData = parser.sensordata
			self.time = parser.meta["systemUpLoadTime"]
			self.site = parser.meta["stationInfered"]

		else:
			if dbEngine is None:
				 dbEngine = create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')
			
			sql_data = "Select * from summer_data where fileId = %d Order By 'index' ASC" %(fileId)
			sensorData = pd.read_sql_query(sql_data,dbEngine).drop('index',axis = 1)
			sql_meta = "Select * from summer_meta where fileId = %d" %(fileId)
			meta = pd.read_sql_query(sql_meta,dbEngine)
			self.time = meta["systemUpLoadTime"][0]
		
		self.rawData = sensorData
		self.preprocessing()
	
	def setExpert(self,notes):
		self.expert["TRM"] = notes["TRM"]
		self.expert["LEP"] = notes["LEP"]
		self.expert["UHY"] = notes["UHY"]
		self.expert["DCL"] = notes["DCL"]

	def updateConfig(self,new_config):
		self.config=new_config
		self.thermocline = thermocline(new_config)
		self.DCL = DCL(new_config)
		self.features = None

	def updateData(self):
		self.downCastRawData, self.cleanData = seabird_pp(self.rawData, self.config)

	def preprocessing(self):
		self.downCastRawData, self.cleanData=seabird_pp(self.rawData, self.config)
		
	def DCLBelowThm(self):
		return self.thermocline.tsSeg_epi<self.DCL_future.peakDepth
	
	def identify(self):
		TRM_features = self.thermocline.detect(self.cleanData[["Depth","Temperature"]])
		DCL_features = self.DCL.detect(self.cleanData[["Depth","Fluorescence"]])

		self.features = TRM_features.copy()
		self.features.update(DCL_features)


	def plot(self, legend=True, pt=None, OtherFeatures=None, bottle=None, filename=None):
		if pt is None:
			pt = plt.figure(figsize=(6, 7), dpi=80)

		# plot the depth profile
		ax1 = pt.add_subplot(111)
		ax2 = ax1.twiny()

		ax1.plot(self.cleanData.Temperature, -self.cleanData.Depth, "r")
		ax1.plot(self.downCastRawData.Temperature, -self.downCastRawData.Depth, "r--", alpha=0.5)

		ax1.set_xlabel("Temperature (C)")
		ax1.set_ylabel("Depth (m)")
		
		
		ax1.set_ylim((-max(self.cleanData.Depth) - 5, 0))
		logging.info("Start to plot")
		
		if legend == False:  # Don't plot thermocline and DCL identification
			pass;

		else:
			ax1.axhline(y=-self.thermocline.tsSeg_thm, color="r",label="tsSeg_thm")
			ax1.axhline(y=-self.thermocline.expert_thm, color="r", ls="--")
			ax1.axhline(y=-self.thermocline.threshold_thm, color="r", ls=":",marker=  r'$\circlearrowleft$',label = "oldTHM")

			ax1.axhline(y=-self.thermocline.tsSeg_epi, color="b",label="tsSeg_epi")
			ax1.axhline(y=-self.thermocline.expert_epi, color="b", ls="--")
			ax1.axhline(y=-self.thermocline.threshold_epi, color="b", ls=":",marker=  r'$\circlearrowleft$',label = "oldEPI")

			ax1.axhline(y=-self.thermocline.tsSeg_hyp, color="y",label = "tsSeg_hyp")
			ax1.axhline(y=-self.thermocline.expert_hyp, color="y", ls="--")
			ax1.axhline(y=-self.thermocline.hmm_hyp, color="y", ls=":",marker=  r'$\circlearrowleft$',label = "oldHYP")

			for seg in self.thermocline.tsSegModel.segmentList:
				ax1.plot(seg[0],-np.array(self.cleanData.Depth[seg[1]]))

			xlimRange = (
				np.percentile(self.downCastRawData["Fluorescence"][self.downCastRawData.Depth > 3],5) * 0.95,
				np.percentile(self.downCastRawData["Fluorescence"][self.downCastRawData.Depth > 3],95) * 1.3)
			
			if max(xlimRange)>0.01:
				ax2.set_xlim(xlimRange)
				ax2.axhline(y=-self.DCL_future.expert_peakDepth, color="g", ls="--")
				ax2.set_xlabel("Fluorescence (ug/L)")
				ax2.plot(self.cleanData.Fluorescence, -self.cleanData.Depth, "g")
				ax2.plot(self.downCastRawData.Fluorescence, -self.downCastRawData.Depth, "g--", alpha=0.5)
				
				if self.DCL_future.myPeak is not None:
					for i, shape_res in enumerate(self.DCL_future.myPeak.shape_fit):
						ax2.plot(shape_res["left_data"],-self.cleanData.Depth[shape_res["left_index"]])
						ax2.plot(shape_res["right_data"],-self.cleanData.Depth[shape_res["right_index"]])
				for peakDepth in self.DCL_future.peakDepth:
					ax2.axhline(y=-peakDepth, color="g")

				for i in range(len(self.DCL_future.boundaryDepth)):
					ax2.plot(self.DCL_future.boundaryMagnitude, -1*np.array(self.DCL_future.boundaryDepth), "ro")

		logging.info(self.feature)

		if filename is None:
			pass
		else:
			plt.savefig(filename)
			plt.close()


	def plot_all(self, interestVarList=None, fileTitle=None):
		# Function to plot all water chemistry
		from mpl_toolkits.axes_grid1 import host_subplot
		import mpl_toolkits.axisartist as AA

		col = dict(zip(["Temperature", "DO", "Specific_Conductivity", "Fluorescence", "Beam_Attenuation", "Par"],
		               ["r", "b", "y", "g", "m", "k"]))

		if interestVarList is None:
			# interestVarList = self.cleanData.columns.values
			interestVarList=["Temperature", "DO", "Specific_Conductivity", "Fluorescence", "Beam_Attenuation", "Par"]

		plt.figure(figsize=[8, 10])
		host = host_subplot(111, axes_class=AA.Axes)
		plt.subplots_adjust(top=0.75, bottom=0.2)

		num_axis = len(interestVarList) - 1
		offset = 23

		parList = []

		for i in range(num_axis):
			par = host.twiny()
			new_fixed_axis = par.get_grid_helper().new_fixed_axis
			par.axis["top"] = new_fixed_axis(loc="top", axes=par, offset=(0, offset))
			par.axis["top"].toggle(all=True)
			parList.append(par)
			offset += 35

		p0, = host.plot(self.downCastRawData.Temperature, -self.downCastRawData.Depth, col["Temperature"] + "+-", label="Temperature")

		for index, var in enumerate(interestVarList[1:]):
			par = parList[index]
			p, = par.plot(self.downCastRawData[var], -self.downCastRawData.Depth, col[var] + "+-",
			              label=var)
			par.set_xlabel(var)
			par.set_xlim(
				(np.percentile(self.downCastRawData[var][(self.downCastRawData.Depth > 3)], 5) * 0.95
				 ,
				 np.percentile(self.downCastRawData[var][(self.downCastRawData.Depth > 3)], 95) * 1.05))

			par.axis["top"].label.set_color(p.get_color())

		host.legend(bbox_to_anchor=(0., -0.27, 1., 0), loc=8, borderaxespad=0.6, ncol=2, mode="expand")
		host.axis["bottom"].label.set_color(p0.get_color())

		host.set_xlabel("Temperature")
		host.set_ylabel("Depth (m)")
		# host.set_title(self.site + "_" + self.time)
		host.set_xlim((max(host.get_xlim()[0], 0), host.get_xlim()[1]))
		host.set_ylim((host.get_ylim()[0], min(host.get_ylim()[1], 0),))
		if fileTitle is None:
			plt.show()
		else:
			plt.draw()
			plt.savefig(fileTitle)