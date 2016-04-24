import numpy as np

class thresholdModel(object):
	'''
	This is a generic model to find the tails of one peak shape curve
	'''
	def __init__(self,threshold = None):
		self.threshold = threshold

	def fit_predict(self,x):
		# x is the energy
		n = len(x)
		max_idx=x.argmax()

		if self.threshold is None:
			count, division = np.histogram(x, bins=30)
			# critical = np.percentile(power,80);
			critical = division[1]
			critical_lower = division[8]
			critical_upper = division[3]
		else:
			print "Using Threshold"
			critical = np.max(x) * threshold
			critical_lower = threshold * 1.1
			critical_upper = threshold

		stable = np.argwhere(x < critical)[:, 0]
		shallow = [s for s in stable if s < max_idx]
		deep = [s for s in stable if s > max_idx]

		newshallow = []
		newdeep = []

		for i in deep[:-2]:
			if max(x[i:]) < critical_lower:
				newdeep.append(i)

		for i in shallow[1:]:
			if max(x[:i]) < critical_upper:
				newshallow.append(i)
		
		newshallow.append(0)
		newdeep.append(n- 1)


		
		bottomTail_idx = min(newdeep)
		upperTail_idx = max(newshallow)

		return [max_idx,upperTail_idx,bottomTail_idx]
