"""
Seabird Class
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from .tools.seabird_preprocessing import preprocessing as seabird_pp
from .tools.seabird_parser import seabird_file_parser
from .thermocline import thermocline
from .deepChlLayers import DCL

class seabird:
	def __init__(self, config):
		"""
		Args: 
			config: dictionary, configuration
		"""
		self.data_file = None
		self.config=config

		# create THM and DCL model
		self.thermocline = thermocline(config)
		self.DCL = DCL(config)

		# site information
		self.time = None
		self.site = None
		self.ID = None
		self.fileId = None  # file id

		self.downCastRawData= None
		self.rawData = None
		self.cleanData = None
		
		self.features = None
		self.expert = {"TRM":None,"LEP":None,"UHY":None,"DCL":None}   # expert notes
		
		self.saveModel = False
		self.waterChemistry = {}

		# self.bottleData = None
		# self.bottleFile = None # maybe useful

	def loadData(self,dataFile = None, fileId = None, dbEngine = None, columns = None):
		"""
		Load data into the Seabird Class
		Args:
			dataFile: seabird raw file, cnv or csv file
			fileId: Id in the database, should not used in application
			dbEngine: database engine
		Returns:

		"""
		if fileId is None:
			# read from the seabird raw data.
			parser = seabird_file_parser()
			parser.readFile(dataFile, columns = columns)
			sensorData = parser.sensordata
			self.time = parser.meta["systemUpLoadTime"]
			self.site = parser.meta["stationInfered"]

		else:
			from sqlalchemy import create_engine
			if dbEngine is None:
				dbEngine = create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')
			
			sql_data = "Select * from summer_data where fileId = %d Order By 'index' ASC" %(fileId)
			sensorData = pd.read_sql_query(sql_data,dbEngine).drop('index',axis = 1)
			sql_meta = "Select * from summer_meta where fileId = %d" %(fileId)
			meta = pd.read_sql_query(sql_meta,dbEngine)
			self.time = meta["systemUpLoadTime"][0]
			self.site = meta["stationInfered"][0]
			self.fileId = fileId
		
		self.rawData = sensorData
	

	def setExpert(self,notes):
		"""
		Load operator judgements:
		Args:
			notes: a dictionary stored the depth values of keys of TRM, LEP, UHY and DCL
		Returns:

		"""
		self.expert["TRM"] = notes["TRM"]
		self.expert["LEP"] = notes["LEP"]
		self.expert["UHY"] = notes["UHY"]
		self.expert["DCL"] = notes["DCL"]

	def updateConfig(self,new_config):
		"""
		Function to update configuration, useful when users want to change configurations
		interactively
		Args:
			new_config: the new configuration dictionary
		"""
		self.config=new_config
		self.thermocline = thermocline(new_config)
		self.DCL = DCL(new_config)
		self.features = None

	def preprocessing(self):
		"""
		Function to do preprocess the data, including separating and smoothing
		"""
		self.downCastRawData, self.cleanData = seabird_pp(self.rawData, self.config["Preprocessing"])
		

	def identify(self,saveModel = True):
		"""
		Function to identify features of DCL and TRM
		"""
		self.saveModel = saveModel

		# detect TRM features

		TRM_features = self.thermocline.detect(data = self.cleanData[["Depth","Temperature"]],\
		                                       saveModel = saveModel)

		if TRM_features["LEP_segment"] is None:
			peakMinDepth = 0
			peakUpperDepthBoundary = 0
		else:
			peakMinDepth = TRM_features["LEP_segment"]
			peakUpperDepthBoundary =TRM_features["LEP_segment"]
		# detect DCL features
		DCL_features = self.DCL.detect(data = self.cleanData[["Depth","Fluorescence"]],\
									   rawData = self.downCastRawData[["Depth","Fluorescence"]],\
		                               peakMinDepth = peakMinDepth,\
		                               peakUpperDepthBoundary = peakUpperDepthBoundary,\
		                               saveModel = saveModel)

		self.features = TRM_features.copy()
		self.features.update(DCL_features)  # add DCL features

	def plot(self, legend=True, pt=None, filename=None,meta=True):
		"""
		Function to plot the results
		Args:
			Legend: whether to plot DCL and TRM features
			pt: the plot canvas
			filename: the file name plot to be saved. None means don't save
			meta: whether to plot meta information such as the curve and segments fitted
		Returns:
			None
		"""
		if pt is None:
			pt = plt.figure(figsize=(6, 7), dpi=80)

		# plot the depth profile
		ax1 = pt.add_subplot(111)  # ax1 is the temperature axis
		ax2 = ax1.twiny()	# ax2 is the fluorescence axis

		# plot the raw Temperature data
		ax1.plot(self.cleanData.Temperature, -self.cleanData.Depth, "r")
		ax1.plot(self.downCastRawData.Temperature, -self.downCastRawData.Depth, "r--", alpha=0.5)
		ax1.set_xlabel("Temperature (C)")
		ax1.set_ylabel("Depth (m)")
		ax1.set_ylim((-max(self.cleanData.Depth) - 5, 0))
		
		if legend == False:  # Don't plot thermocline and DCL identification
			pass;

		else:
			colors = ["r","b","y","g"]

			# plot the depth of TRM data
			for i,depth in enumerate([self.features["TRM_segment"],self.features["LEP_segment"],self.features["UHY_segment"]]):
				ax1.axhline(y = -1*depth if depth is not None else -999,color = colors[i])

			if meta:
				# plot HMM results for comparison
				for i,depth in enumerate([self.features["TRM_HMM"],self.features["LEP_HMM"],self.features["UHY_HMM"]]):
					ax1.axhline(y = -1*depth if depth is not None else -999,color = colors[i],ls = ":")

			# plot expert judgement
			for i,depth in enumerate([self.expert["TRM"],self.expert["LEP"],self.expert["UHY"],self.expert["DCL"]]):
				ax1.axhline(y = -1*depth if depth is not None else -999,color = colors[i],ls="--")


			if self.saveModel and meta:
				# plot all the fitted segments
				for seg in self.thermocline.models["segmentation"].segmentList:
					ax1.plot(seg[0],-np.array(self.cleanData.Depth[seg[1]]))

			xlimRange = (
				np.percentile(self.downCastRawData["Fluorescence"][self.downCastRawData.Depth > 2],5) * 0.95,
				np.percentile(self.downCastRawData["Fluorescence"][self.downCastRawData.Depth > 2],99) * 1.3)

			# plot fluorescence 
			if max(xlimRange)>0.01:
				ax2.set_xlim(xlimRange)
				ax2.set_xlabel("Fluorescence (ug/L)")
				ax2.plot(self.cleanData.Fluorescence, -self.cleanData.Depth, "g")
				ax2.plot(self.downCastRawData.Fluorescence, -self.downCastRawData.Depth, "g--", alpha=0.5)
				
				if self.saveModel and meta:
					meta_allPeaks = self.DCL.model.allPeaks

					if meta_allPeaks is not None:
						for i in range(len(meta_allPeaks["peakIndex"])):
							# plot the fitted shape
							leftShapeFit = meta_allPeaks["leftShapeFit"][i]
							rightShapeFit = meta_allPeaks["rightShapeFit"][i]

							peakIndex = meta_allPeaks["peakIndex"][i]

							leftShapeIndex = range(peakIndex-len(leftShapeFit)+1,peakIndex+1)
							rightShapeIndex = range(peakIndex,peakIndex+len(rightShapeFit))
							print(leftShapeIndex)
							print(rightShapeIndex)
							ax2.plot(leftShapeFit,-self.cleanData.Depth.iloc[leftShapeIndex])
							ax2.plot(rightShapeFit,-self.cleanData.Depth.iloc[rightShapeIndex])

				# if detected DCL, plo the depth of the DCL peak
				if self.features["DCL_depth"] is not None:
					ax2.axhline(y=-self.features["DCL_depth"],color="g")
					ax2.axhline(y=-self.features["DCL_upperDepth_fit"],color = "g")
					ax2.axhline(y=-self.features["DCL_bottomDepth_fit"],color = "g")
					# ax2.axhline(y=-self.features["DCL_upperDepth_gradient"],color = "m")
					# ax2.axhline(y=-self.features["DCL_bottomDepth_gradient"],color = "m")

		if filename is None:
			pass
		else:
			plt.savefig(filename)
			plt.close()


	def plot_all(self, interestVarList=None, fileTitle=None):
		# Function to plot all water chemistry
		from mpl_toolkits.axes_grid1 import host_subplot
		import mpl_toolkits.axisartist as AA

		# create a map from water feature to plot line color 
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
				 np.percentile(self.downCastRawData[var][(self.downCastRawData.Depth > 3)], 95) * 1.05 * 2))

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