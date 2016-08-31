from hmmlearn import hmm
import numpy as np
import pandas as pd
from sklearn import preprocessing as pp

class hmmModel(object):
	def __init__(self,nc = 3):
		self.nc = nc

	def fit_predict(self,dataSet):
		# data contains 
		np.random.seed()
		n = dataSet.shape[0]
		# HMM_data = pp.scale(dataSet[["Var","Power"]])
		HMM_data = pp.scale(dataSet[["Var","Gradient"]])
		# print HMM_data
		if self.nc == 3:
			# Initial Transition Matrix
			transmat = np.zeros((3, 3))
			transmat[0, 1] = 3.0/n
			transmat[0, 0] = 1.0 - transmat[0, 1]
			transmat[1, 2] = 3.0/n
			transmat[1, 1] = 1.0 - transmat[1, 2]
			transmat[2, 2] = 1.0

			# Force the first point is in state 0
			startprob = np.array([1, 0, 0])
			
			# The state mean of variable 
			state_means = np.zeros((3, 2))
			state_means[0, 0] = np.percentile(HMM_data[:10, 0],50)
			state_means[2, 0] = np.percentile(HMM_data[-10:, 0],50)
			state_means[1, 0] = (state_means[0, 0] + state_means[1, 0]) / 2.0

		
			# The state mean of power
			state_means[0, 1] = np.percentile(HMM_data[:10, 1],50)
			state_means[2, 1] = np.percentile(HMM_data[-10:, 1],50)
			state_means[1, 1] = np.percentile(HMM_data[:, 1],90) / 2.0

		else:
			raise ValueError("not implemented nc!=3")
	
		
		model = hmm.GaussianHMM(
			n_components=self.nc,
			covariance_type="diag",  # diagnoal matrix
			n_iter=2000,
			params='cmt',
			init_params='c',
			verbose=False)
			# means_prior=state_means,
			# transmat_prior=transmat,
			# startprob_prior=startprob)
		model.transmat_=transmat
		model.means_=state_means
		model.startprob_=startprob

		model.fit(HMM_data)

		hidden_states = model.predict(HMM_data)
		h = np.array(hidden_states)
		diff = h[1:] - h[:-1]
		changePoint = np.argwhere(diff != 0).flatten()

		# feature_index = [dataSet.Power.argmax()] # add thermocline using power
		feature_index = [dataSet.Gradient.argmax()]  # add thermocline using gradient

		for point in changePoint:
			feature_index.append(point)

		return feature_index  # trm index, LEP index, UEP index