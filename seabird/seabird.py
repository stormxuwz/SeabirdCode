"""
Seabird Class
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from .tools.seabird_preprocessing import preprocess as seabird_pp
from .tools.seabird_parser import SeabirdFileParser
from .thermocline import Thermocline
from .deep_chl_layer import DCL

class Seabird:
	def __init__(self, config):
		"""
		Args: 
			config: dictionary, configuration
		"""
		self.data_file = None
		self.config = config

		# create THM and DCL model
		self.thermocline = Thermocline(config)
		self.dcl = DCL(config)

		# site information
		self.time = None
		self.site = None
		self.id = None
		self.file_id = None  # file id

		self.downcast_rawdata= None
		self.rawdata = None
		self.cleandata = None
		
		self.features = None
		self.expert = {"TRM":None,"LEP":None,"UHY":None,"DCL":None}   # expert notes
		
		self.save_model = False
		self.water_chemistry = {}

		# self.bottleData = None
		# self.bottleFile = None # maybe useful

	def load_data(self, data_file=None, file_id=None, db_engine=None, columns=None):
		"""
		Load data into the Seabird Class
		Args:
			dataFile: seabird raw file, cnv or csv file
			fileId: Id in the database, should not used in application
			dbEngine: database engine
		Returns:

		"""
		if file_id is None:
			# read from the seabird raw data.
			parser = SeabirdFileParser()
			parser.read_file(data_file, columns=columns)
			sensor_data = parser.sensordata
			self.time = parser.meta["systemUpLoadTime"]
			self.site = parser.meta["stationInfered"]

		else:
			from sqlalchemy import create_engine
			if db_engine is None:
				dbEngine = create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')
			
			sql_data = "Select * from summer_data where fileId = %d Order By 'index' ASC" %(file_id)
			sensor_data = pd.read_sql_query(sql_data,dbEngine).drop('index',axis = 1)
			sql_meta = "Select * from summer_meta where fileId = %d" %(file_id)
			meta = pd.read_sql_query(sql_meta,dbEngine)
			self.time = meta["systemUpLoadTime"][0]
			self.site = meta["stationInfered"][0]
			self.file_id = file_id
		
		self.rawdata = sensor_data
	
	def set_expert(self, notes):
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

	def update_config(self,new_config):
		"""
		Function to update configuration, useful when users want to change configurations
		interactively
		Args:
			new_config: the new configuration dictionary
		"""
		self.config = new_config
		self.thermocline = Thermocline(new_config)
		self.DCL = DCL(new_config)
		self.features = None

	def preprocess(self):
		"""
		Function to do preprocess the data, including separating and smoothing
		"""
		self.downcast_rawdata, self.cleandata = seabird_pp(self.rawdata, self.config["preprocessing"])
		

	def identify(self, save_model=True):
		"""
		Function to identify features of DCL and TRM
		"""
		self.saveModel = save_model

		# detect TRM features

		trm_features = self.thermocline.detect(data=self.cleandata[["Depth","Temperature"]],\
		                                       save_model=save_model)
		
		if trm_features["LEP_segment"] is None:
			# if no LEP is detected, no dcl is detected
			chl_peak_min_depth = 0
			chl_peak_upper_depth_boundary = 0
		else:
			chl_peak_min_depth = trm_features["LEP_segment"]
			chl_peak_upper_depth_boundary =trm_features["LEP_segment"]
		
		# detect DCL features
		dcl_features = self.dcl.detect(data=self.cleandata[["Depth","Fluorescence"]],\
									   rawdata=self.downcast_rawdata[["Depth","Fluorescence"]],\
		                               chl_peak_min_depth=chl_peak_min_depth,\
		                               chl_peak_upper_depth_boundary=chl_peak_upper_depth_boundary,\
		                               save_model=save_model)

		self.features = trm_features.copy()
		self.features.update(dcl_features)  # add DCL features

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
		ax1.plot(self.cleandata.Temperature, -self.cleandata.Depth, "r")
		ax1.plot(self.downcast_rawdata.Temperature, -self.downcast_rawdata.Depth, "r--", alpha=0.5)
		ax1.set_xlabel("Temperature (C)")
		ax1.set_ylabel("Depth (m)")
		ax1.set_ylim((-max(self.cleandata.Depth) - 5, 0))
		
		if legend == False:  # Don't plot thermocline and DCL identification
			pass

		else:
			colors = ["r","b","y","g"]

			# plot the depth of TRM data
			for i,depth in enumerate([self.features["TRM_segment"],self.features["LEP_segment"],self.features["UHY_segment"]]):
				ax1.axhline(y = -1*depth if depth is not None else -999,color = colors[i])

			if meta:
				# plot HMM results for comparison
				for i,depth in enumerate([self.features["TRM_HMM"],self.features["LEP_HMM"], self.features["UHY_HMM"]]):
					ax1.axhline(y = -1 * depth if depth is not None else -999,color = colors[i],ls = ":")

			# plot expert judgement
			for i,depth in enumerate([self.expert["TRM"], self.expert["LEP"],self.expert["UHY"], self.expert["DCL"]]):
				ax1.axhline(y = -1 * depth if depth is not None else -999,color = colors[i],ls="--")


			if self.save_model and meta:
				# plot all the fitted segments
				for seg in self.thermocline.models["segmentation"].segmentList:
					ax1.plot(seg[0],-np.array(self.cleandata.Depth[seg[1]]))

			xlimRange = (
				np.percentile(self.downcast_rawdata["Fluorescence"][self.downcast_rawdata.Depth > 2],5) * 0.95,
				np.percentile(self.downcast_rawdata["Fluorescence"][self.downcast_rawdata.Depth > 2],99) * 1.3)

			# plot fluorescence 
			if max(xlimRange)>0.01:
				ax2.set_xlim(xlimRange)
				ax2.set_xlabel("Fluorescence (ug/L)")
				ax2.plot(self.cleandata.Fluorescence, -self.cleandata.Depth, "g")
				ax2.plot(self.downcast_rawdata.Fluorescence, -self.downcast_rawdata.Depth, "g--", alpha=0.5)
				
				if self.save_model and meta:
					chl_peaks = self.dcl.model.all_peaks

					if chl_peaks is not None:
						for i in range(len(chl_peaks["peakIndex"])):
							# plot the fitted shape
							leftShapeFit = chl_peaks["leftShapeFit"][i]
							rightShapeFit = chl_peaks["rightShapeFit"][i]

							peakIndex = chl_peaks["peakIndex"][i]

							leftShapeIndex = range(peakIndex-len(leftShapeFit)+1,peakIndex+1)
							rightShapeIndex = range(peakIndex,peakIndex+len(rightShapeFit))
							print(leftShapeIndex)
							print(rightShapeIndex)
							ax2.plot(leftShapeFit,-self.cleandata.Depth.iloc[leftShapeIndex])
							ax2.plot(rightShapeFit,-self.cleandata.Depth.iloc[rightShapeIndex])

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
			# interestVarList = self.cleandata.columns.values
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

		p0, = host.plot(self.downcast_rawdata.Temperature, -self.downcast_rawdata.Depth, col["Temperature"] + "+-", label="Temperature")

		for index, var in enumerate(interestVarList[1:]):
			par = parList[index]
			p, = par.plot(self.downcast_rawdata[var], -self.downcast_rawdata.Depth, col[var] + "+-",
			              label=var)
			par.set_xlabel(var)
			par.set_xlim(
				(np.percentile(self.downcast_rawdata[var][(self.downcast_rawdata.Depth > 3)], 5) * 0.95 
				 ,
				 np.percentile(self.downcast_rawdata[var][(self.downcast_rawdata.Depth > 3)], 95) * 1.05 * 2))

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