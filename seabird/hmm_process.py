'''
This file for the function to do hidden markov model (HMM)
'''
from __future__ import division;
from hmmlearn import hmm
from sklearn import preprocessing as pp
import numpy as np


def HMM_simple_fit(dataSet):
	n = dataSet.shape[0]
	NUM_COMPONENTS = 3
	HMM_data = dataSet[:, [0, 2]]
	# print HMM_data
	model = hmm.GaussianHMM(NUM_COMPONENTS, covariance_type="full", n_iter=2000)
	model.fit([HMM_data])

	hidden_states = model.predict(HMM_data)
	# print model.predict_proba(HMM_data)
	# print HMM_data[:10,]
	h = np.array(hidden_states)
	diff = h[1:] - h[:-1]
	changePoint = list(np.transpose(np.argwhere(diff != 0))[0])

	feature_depth = []
	for point in changePoint:
		feature_depth.append(dataSet[point, 0])

	return HMM_data, feature_depth


def HMM_fit(dataSet, featureCol=[1, 2], nc=3, log=False):  # X=[depth,T]
	np.random.seed()
	'''
	HMM model to identify states from feature(s)
	dataSet: data, each column represents each feature
	featureCol: which feature(s) will be used in HMM model
	nc: number of states to identify
	'''

	n = dataSet.shape[0]
	NUM_COMPONENTS = nc
	HMM_data = pp.scale(dataSet[:, featureCol])
	# HMM_data=np.copy(dataSet[:,featureCol])
	# print HMM_data[:,1].range()

	# import matplotlib.pyplot as plt;
	# plt.figure()
	# plt.plot(dataSet[:,2])
	# plt.show()

	if nc == 3:
		# Initial Transition Matrix
		transmat = np.zeros((3, 3))
		transmat[0, 1] = 3 / n
		transmat[0, 0] = 1 - transmat[0, 1]
		transmat[1, 2] = 3 / n
		transmat[1, 1] = 1 - transmat[1, 2]
		transmat[2, 2] = 1

		# Force the first point is in state 0
		startprob = np.array([1, 0, 0])

	if len(featureCol) == 1:
		HMM_data = np.reshape(HMM_data, (n, 1))
		state_means = np.zeros((3, 1))

		state_means[0, 0] = HMM_data[4, 0]
		state_means[1, 0] = (HMM_data[-4, 0] + HMM_data[4, 0]) / 2
		state_means[2, 0] = HMM_data[-10, 0]

	elif len(featureCol) == 2:  # Identify thermocline from temperature and temperature energy
		# print np.argwhere(HMM_data[:,1]<0)
		# HMM_data[:,1]=np.log(HMM_data[:,1])

		index_energy_max = np.argmax(dataSet[:, 2])
		state_means = np.zeros((3, 2))
		state_means[0, 0] = HMM_data[2, 0]
		state_means[1, 0] = (HMM_data[-4, 0] + HMM_data[4, 0]) / 2
		state_means[2, 0] = HMM_data[-10, 0]

		state_means[0, 1] = HMM_data[4, 1]
		state_means[2, 1] = HMM_data[-10, 1]
		state_means[1, 1] = np.max(HMM_data[:, 1]) / 2
		HMM_data[:, 1] = HMM_data[:, 1] ** 2
	# import matplotlib.pyplot as plt;
	# plt.figure()
	# plt.plot(HMM_data[:,1],-dataSet[:,0])
	# plt.show()

	else:
		pass

	model = hmm.GaussianHMM(
		NUM_COMPONENTS,
		covariance_type="full",
		n_iter=2000,
		# transmat=transmat,
		# startprob=startprob,
		params='cmt', init_params='c')
	model.transmat_=transmat
	model.startprob_=startprob
	model.means_ = state_means
	model.fit(HMM_data)
	if (log):
		print "Data Number", n
		print "Initial Mean", state_means
		print "Initial Transition,", transmat
		print "Parameter:", model.get_params()
		print "Transition Matrix", model.transmat_
		print "Starting Probability", model.startprob_
		print "State Mean", model.means_
		print "covar"
		print np.array(model.covars_)

	hidden_states = model.predict(HMM_data)
	h = np.array(hidden_states)
	diff = h[1:] - h[:-1]
	changePoint = list(np.transpose(np.argwhere(diff != 0))[0])

	feature_depth = []
	for point in changePoint:
		feature_depth.append(dataSet[point, 0])

	data_with_state = np.zeros((n, len(featureCol) + 2))

	data_with_state[:, 0] = dataSet[:, 0]
	data_with_state[:, featureCol] = dataSet[:, featureCol]
	data_with_state[:, -1] = h

	# data_with_power=np.zeros((N-2*w,3))
	# data_with_state=np.vstack((data_with_state.T,h*10)).T

	return data_with_state, feature_depth