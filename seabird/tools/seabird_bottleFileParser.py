"""
function to read bottle files
"""
import numpy as np

def read_bottle_file(filename):
	bottle_data=[]
	with open(filename,"r") as input_file:
		lines=input_file.readlines()
		for line in lines:
			line_splitted= line.split()
			if line_splitted[0] in [str(i) for i in range(1,13)]:
				single_bottle=[float(i) for i in line_splitted[4:21]]
				single_bottle.insert(0,float(line_splitted[0]))
				bottle_data.append(single_bottle)

	return np.array(bottle_data)

if __name__ == '__main__':
	filename="/Users/XuWenzhao/Developer/DataSource/Rosette Data/SeaBird/2014/Spring Survey/Michigan/MI11.cnvbtl.btl"
	print read_bottle_file(filename)