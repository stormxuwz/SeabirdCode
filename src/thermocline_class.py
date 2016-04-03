from seabird_thermocline import extractFeatures,thresholdModel
from seabird_thermocline import hmmModel as hmmModel
from futureFeature.timeSeriesSeg import bottomUp
import numpy as np
import logging

def thermoclineModel(signal_data,config):
	depthInterval = signal_data.Depth[1]-signal_data.Depth[0]

	model = bottomUp(max_error=config["Algorithm"]["segment"]["max_error"])
	model.fit_predict(signal_data.Temperature)

	gradient = [(seg[0][0]-seg[0][1])/depthInterval for seg in model.segmentList]
	maxGradient_index = np.argmax(gradient)

	logging.info("gradient list")
	logging.info(gradient)

	logging.info("seg length")
	logging.info([len(seg[0]) for seg in model.segmentList])
	# check if the next segment is in stable region
	epilimnion_seg = model.segmentList[0]
	LEP_index = epilimnion_seg[1][-1]

	if maxGradient_index == 0: # if the maximum gradient is the first segment
		LEP_index = epilimnion_seg[1][0]
	elif maxGradient_index == 1: # if the maximum gradient is the second segment
		pass
	elif abs(gradient[1]) < config["Algorithm"]["segment"]["stable_gradient"]:
		LEP_index = model.segmentList[1][1][-1]
	# elif abs(gradient[0]) > config["Algorithm"]["segment"]["stable_gradient"]:
		# LEP_index=None

	# if abs(gradient[0]) > config["Algorithm"]["segment"]["stable_gradient"]:
		# LEP_index=None


	hypolimnion_seg = model.segmentList[-1]
	UHY_index = hypolimnion_seg[1][0]

	if maxGradient_index == len(gradient)-1: # if the THM is the last segment
		UHY_index = hypolimnion_seg[1][-1]

	elif maxGradient_index == len(gradient)-2: # if THM is the last but one segment
		pass

	elif abs(gradient[-2])< config["Algorithm"]["segment"]["stable_gradient"]:
	# if abs(gradient[-2])< max(gradient)*0.05:
		UHY_index = model.segmentList[-2][1][0]
	
	elif abs(gradient[-1]) > max(gradient)*0.2:
		UHY_index=None

	


	thermocline_seg = model.segmentList[maxGradient_index]
	THM_index = int(np.mean(thermocline_seg[1]))
	
	legendDepthIndex = [THM_index,LEP_index,UHY_index]

	return {"segNum":len(model.segmentList),"legendDepth":[signal_data.Depth[i] if i is not None else -99 for i in legendDepthIndex],"tsModel":model,"THMGradient":max(gradient)}

class thermocline(object):
	def __init__(self,config):
		self.threshold_thm=None
		self.threshold_epi=None
		self.threshold_hyp=None
		
		self.hmm_thm=None
		self.hmm_epi=None
		self.hmm_hyp=None

		self.expert_thm=-99
		self.expert_epi=-99
		self.expert_hyp=-99

		self.tsSeg_thm = None
		self.tsSeg_epi = None
		self.tsSeg_hyp = None

		self.config=config

	def identify(self, data):
		signalFeature = extractFeatures(data[["Depth","Temperature"]],w=self.config["Algorithm"]["Spectrum"]["windowSize"])
		
		self.threshold_thm,self.threshold_epi,self.threshold_hyp=thresholdModel(signalFeature,self.config["Algorithm"]["Spectrum"]["threshold"])
		self.hmm_thm,self.hmm_epi,self.hmm_hyp=hmmModel(signalFeature)
		
		tsSegModelResults = thermoclineModel(data,self.config)
		self.tsSeg_thm,self.tsSeg_epi,self.tsSeg_hyp=tsSegModelResults["legendDepth"]

		self.tsSegNum = tsSegModelResults["segNum"]
		self.tsSegModel = tsSegModelResults["tsModel"]
		self.tsSegGradient = tsSegModelResults["THMGradient"]
	 	
	def setExpert(self,data):
		self.expert_thm,self.expert_epi,self.expert_hyp=data