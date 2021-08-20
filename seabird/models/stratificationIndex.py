import numpy as np 
import matplotlib.pyplot as plt

def get_rtrm(temperature,depth):
	temperature = np.asarray(temperature)
	density = get_density(temperature)
	return -np.diff(density)/(get_density(5) - get_density(4)), [np.mean(depth[i:i+2]) for i in range(len(depth)-1)]

def get_density(T):
	T = np.asarray(T)
	return (999.83952+ T*(16.945176+T*(-7.9870401*10**(-3)+T*(-46.170461*10**(-6)+T*(105.56302*10**(-9)-280.54253*10**(-12)*T)))))/(1.0+16.87985*10**(-3)*T)


def get_BV_frequency(temperature,depth):
	temperature = np.asarray(temperature)
	density = get_density(temperature)
	return np.sqrt(-9.8/density[0:-1]*(np.diff(temperature)/np.diff(depth))), [np.mean(depth[i:i+2]) for i in range(len(depth)-1)]

if __name__ == '__main__':

	depth =  [20,19,18,17,16,15,14,13]
	temperature = [3,4,5,6,10,20,22,23]
	BV_idx,BV_depth = get_BV_frequency(temperature,depth)
	RTRM_idx,RTRM_depth = get_rtrm(temperature,depth)
	# print BV_depth,RTRM_depth
	
	plt.figure()
	ax1 = plt.subplot(131)
	ax1.plot(temperature,-np.array(depth))
	
	ax2 = plt.subplot(132, sharey=ax1)
	ax2.plot(BV_idx,-np.array(BV_depth))

	ax3 = plt.subplot(133, sharey=ax1)
	ax3.plot(RTRM_idx,-np.array(RTRM_depth))
	plt.show()
	
