import numpy as np
import logging

class timeSeriesSegmentation(object):
	def __init__(self,max_error):
		self.segmentList=None
		self.x=None
		self.max_error=max_error

	def fit_predict(self,x):
		raise ValueError("not implementated")

	def calculate_error(self,x,y):
		return np.max(np.abs(x-y))

	def plot(self):
		import matplotlib.pyplot as plt
		plt.figure()
		plt.plot(self.x,"ro")
		for seg in self.segmentList:
			plt.plot(seg[1],seg[0],"+-")
		plt.show()

	def createLine(self,x,method="regression"):
		x = np.array(x)
		n=len(x)

		if method=="simple":
			line = np.linspace(x[0],x[-1],n)

		elif method == "regression":
			line = np.poly1d(np.polyfit(range(n),x,1))(range(n))
		
		elif method == "poly":
			line=np.poly1d(np.polyfit(range(n),x,2))(range(n))

		return line


class slidingWindow(timeSeriesSegmentation):
	"""
	segment signal using sliding window approach (not used)
	"""
	def fit_predict(self,x):
		n=len(x)
		leftNode=0
		segmentList=[]
		print n
		
		while leftNode<n-1:
			print leftNode
			newSeg = False
			for rightNode in range(leftNode+3,n):
				testSeg=x[leftNode:rightNode]

				testLine = self.createLine(testSeg,"regression")
				segError = self.calculate_error(testSeg, testLine)

				if segError>self.max_error:
					segmentList.append([testLine,range(leftNode,rightNode)])
					leftNode=rightNode
					newSeg = True
					break

			if newSeg is False:
				segmentList.append([testLine,range(leftNode,rightNode)])
				leftNode = n-1
		
		self.segmentList=segmentList
		self.x=x

class bottomUp(timeSeriesSegmentation):
	"""
	segment signal using sliding bottom up approach (not used)
	"""

	def fit_predict(self,x):
		"""
		Function to fit linear segments based on x
		Args:
			x: input signal
		Returns:
			None
		"""
		n=len(x)
		segmentIndexList = [[i,i+1] for i in range(0,n,2)]
		errorList = [self.mergeCost(x[segmentIndexList[i]], x[segmentIndexList[i+1]]) for i in range(len(segmentIndexList)-1)]

		while True:
			minIndex = np.argmin(errorList)
			self.mergeRight(segmentIndexList,minIndex)
			
			if len(segmentIndexList) == 3:
				break
			if minIndex > 0:
				errorList[minIndex-1] = self.mergeCost(x[segmentIndexList[minIndex-1]],x[segmentIndexList[minIndex]])

			if minIndex < len(errorList)-1:
				errorList[minIndex+1] = self.mergeCost(x[segmentIndexList[minIndex]], x[segmentIndexList[minIndex+1]])

			errorList.pop(minIndex)
			
			if len(errorList)!=len(segmentIndexList)-1:
				raise ValueError("error length not right")

			if min(errorList)>self.max_error:
				break

		self.x = x
		self.segmentList=[[self.createLine(x[segIndex],"regression"),segIndex] for segIndex in segmentIndexList]
		
		# self.finalAdjust()
		

	def finalAdjust(self):
		nSeg = len(self.segmentList)
		
		newSegment = []
		i = 0
		
		while i < nSeg - 1:
			newSeg1, newSeg2 = self.splitAdjust(self.segmentList[i],self.segmentList[i+1])
			# print seg1, seg2
			self.segmentList[i] = newSeg1
			self.segmentList[i+1] = newSeg2
			i += 1
			# print newSeg1, newSeg2


	def splitAdjust(self, seg1, seg2):
		# function to find the best split point given seg1 and seg2
		# Args:
		#	seg1: [fitted value, idx]
		# 	seg2: [fitted value, idx]
		# print seg1[1], seg2[1]

		segIdx = seg1[1] + seg2[1]
		segX = self.x[segIdx]
		
		n = len(segIdx)


		minErr = self.max_error*100
		minErrIdx = 1

		for i in range(1, n - 2):
			s1 = segX[:i]
			s2 = segX[i:]
			# print s1, s2
			if len(s1) > 2:
				e1 = self.calculate_error(self.createLine(s1), s1)
			else:
				e1 = 0

			if len(s2) > 2:
				e2 = self.calculate_error(self.createLine(s2), s2)
			else:
				e2 = 0

			if e1 + e2 < minErr:
				minErr = e1 + e2
				minErrIdx = i
	
		# print "***", minErrIdx, s1, s2

		return [self.createLine(segX[:minErrIdx]), segIdx[:minErrIdx] ], [self.createLine(segX[minErrIdx:]), segIdx[minErrIdx:] ]

		


	def mergeCost(self, leftSeg,rightSeg):
		"""
		function to calculate the error when merging the right segment
		Args:
			leftSeg: left segment
			rightSeg: the segment to merge
		Returns:
			error when merging the right segment
		"""
		allSeg=np.concatenate((leftSeg,rightSeg))
		line = self.createLine(allSeg)
		return self.calculate_error(line, allSeg)

	def mergeRight(self,segList,index):
		"""
		function to merge the segment of "index" with its right segment
		Args:
			segList: a list of segment
			index: the segment to merge with its right segment
		"""
		segList[index]=(segList[index]+segList[index+1]) # merge 
		segList.pop(index+1) # pop the right segment
