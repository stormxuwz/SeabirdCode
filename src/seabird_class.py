from tools.seabird_cnvFileParser import read_seabird_file
from tools.seabird_bottleFileParser import read_bottle_file
from tools.seabird_preprocessing import preprocessing as seabird_pp
from thermocline_class import thermocline
from DCL_class import DCL,DCL_future
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging

class seabird:
	def __init__(self, fileName, config, variable=None, expertFile=None):
		self.data_file = fileName
		self.expertFile = expertFile

		self.config=config
		self.interstVar = variable
		self.thermocline = thermocline(config)
		self.DCL = DCL(config)
		self.DCL_future = DCL_future(config)

		self.time = "NA"
		self.site = "NA"
		self.ID = "NA"
		
		self.downCastRawData= None
		self.rawData = None
		self.bottleData = None
		self.cleanData = None
		self.bottleFile = None # maybe useful
		self.feature = None
		# Read files
		self.read_data()
		logging.info("initialized")

	def updateConfig(self,new_config):
		self.config=new_config
		self.thermocline.config=new_config
		self.DCL.config=new_config

	def updateData(self):
		self.downCastRawData, self.cleanData = seabird_pp(self.rawData, self.config)

	def extractWaterChemistry(self,location="LEP",interestVarList=None):
		if interestVarList is None:
			interestVarList=["Temperature", "DO", "Beam_Attenuation","Specific_Conductivity","Fluorescence", "Par"]

		subdata = None
		if location == "EPI":
			depth_criteria = self.thermocline.threshold_epi
			subData=self.cleanData[self.cleanData.Depth<depth_criteria]

		elif location=="HYP":
			depth_criteria = self.thermocline.hmm_hyp
			subData=self.cleanData[self.cleanData.Depth>depth_criteria]

		elif location=="MET":
			subData=self.cleanData[self.cleanData.Depth>self.thermocline.hmm_hyp and self.cleanData.Depth<self.thermocline.threshold_epi]

		varMean = np.mean(subdata, axis=0)  # variable mean above depth criteria
		varVariance = np.var(subdata, axis=0)  # variable mean

		return np.concatenate((varMean, varVariance))

	def completePar(self):
		if "Par" not in self.rawData.columns.values:
			self.rawData["Par"]=-99

	def transTransimissionToBAT(self):
		if "Beam_Attenuation" not in self.rawData.columns.values and "Beam_Transmission" in self.rawData.columns.values:
			self.rawData["BAT"]=-np.log(self.rawData["Beam_Transmission"]/100)*4
		else:
			self.rawData["BAT"]=-99

	def transCondToSpecCond(self):
		if "Specific_Conductivity" not in self.rawData.columns.values:
			self.rawData["Specific_Conductivity"]=self.rawData.Conductivity/(1+0.02*(self.rawData.Temperature-25))

	def read_data(self):
		import os
		if self.data_file.endswith('.csv'):  # Read CSV data
			self.rawData = pd.read_csv(self.data_file)

			sampleInfo = os.path.basename(self.data_file)
			sampleInfo = sampleInfo[0:-4]
			sampleInfo = sampleInfo.split("_")
			self.site = sampleInfo[0]
			self.time = sampleInfo[1]
			self.ID = self.site + "_" + self.time

		else:  # Read cnv data
			self.rawData, self.time, self.site, varList = read_seabird_file(self.data_file);
			self.rawData=pd.DataFrame(self.rawData,columns=varList)
			self.ID = self.site + "_" + self.time

		if self.bottleFile is not None:  # read bottle File
			self.bottleData = read_bottle_file(self.bottleFile)

		if self.expertFile is not None and self.expertFile is not np.nan:  # read expert File
			# print self.expertFile
			expertData = pd.read_csv(self.expertFile,header=None)
			self.thermocline.setExpert([expertData.iloc[0,0], expertData.iloc[0,1], expertData.iloc[0,2]])
			self.DCL_future.setExpert(expertData.iloc[0,3])

	def preprocessing(self):
		self.completePar()
		self.transTransimissionToBAT()
		self.transCondToSpecCond()
		self.downCastRawData, self.cleanData=seabird_pp(self.rawData, self.config)
		
	def DCLBelowThm(self):
		return self.thermocline.tsSeg_epi<self.DCL_future.peakDepth
	
	
	def identify(self,data=None):
		if data is None:
			data=self.cleanData

		self.thermocline.identify(self.cleanData)
		logging.info("THM finished")
		# if max(self.cleanData.Fluorescence)>0.1:
		if max(self.cleanData.Depth) >10:
			# self.DCL.identify(self.cleanData)
			self.DCL_future.identify(self.cleanData)
			logging.info("peakDepth")
			logging.info(self.DCL_future.peakDepth)

		if self.DCL_future.peakNum==0:
			print "no peak detected"
			DCL_peak_index = 0
			DCLexist = 0
		else:
			if any(self.DCLBelowThm()) is True:
				DCL_peak_index = np.argmax(self.DCL_future.magnitude * (self.DCL_future.peakDepth > self.thermocline.tsSeg_epi))
				DCLexist = 1
			else:
				print "no peak below thermocline exists"
				DCL_peak_index = 0
				DCLexist = 0

		logging.info("DCL finished")
		self.feature = {	
		"THM_expert":self.thermocline.expert_thm,
		"LEP_expert":self.thermocline.expert_epi,
		"UHY_expert":self.thermocline.expert_hyp,

		"THM_HMM":self.thermocline.hmm_thm,
		"LEP_HMM":self.thermocline.hmm_epi,
		"UHY_HMM":self.thermocline.hmm_hyp,

		"THM_segment":self.thermocline.tsSeg_thm,
		"LEP_segment":self.thermocline.tsSeg_epi,
		"UHY_segment":self.thermocline.tsSeg_hyp,
		"num_segment":self.thermocline.tsSegNum,
		"THM_gradient":self.thermocline.tsSegGradient,

		"THM_threshold":self.thermocline.threshold_thm,
		"LEP_threshold":self.thermocline.threshold_epi,
		"UHY_threshold":self.thermocline.threshold_hyp,

		"DCL_expert":self.DCL_future.expert_peakDepth,
		"DCL_peakNum":self.DCL_future.peakNum,
		"DCL_exist":DCLexist,
		"DCL_depth":self.DCL_future.peakDepth[DCL_peak_index],
		"DCL_magnitude":self.DCL_future.magnitude[DCL_peak_index],
		"DCL_magnitude_upperBoundary":self.DCL_future.boundaryMagnitude[DCL_peak_index][0],
		"DCL_magnitude_bottomBoundary":self.DCL_future.boundaryMagnitude[DCL_peak_index][1],
		"DCL_depth_upperBoundary":self.DCL_future.boundaryDepth[DCL_peak_index][0],
		"DCL_depth_bottomBoundary":self.DCL_future.boundaryDepth[DCL_peak_index][1],
		"DCL_fitness":self.DCL_future.fitness
		}

	
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
			# print xlimRange
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
		host.set_title(self.site + "_" + self.time)
		host.set_xlim((max(host.get_xlim()[0], 0), host.get_xlim()[1]))
		host.set_ylim((host.get_ylim()[0], min(host.get_ylim()[1], 0),))
		if fileTitle is None:
			plt.show()
		else:
			plt.draw()
			plt.savefig(fileTitle)