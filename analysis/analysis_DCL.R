require(reshape2)

gaussianFit <- function(features,threshold=0.9){
	# print the ratio of each lake that the peak is satisfy a Gaussian shape
	goodFitData <- subset(features, DCL_leftShapeFitErr > threshold & 
			DCL_rightShapeFitErr > threshold )
	return(goodFitData)
}


shapeAnalysis_DCL <- function(features){
	# those features should be fit by Gaussian shape well
	features$DCL_upperSize <- features$DCL_depth-features$DCL_upperDepth_fit
	features$DCL_bottomSize <- features$DCL_bottomDepth_fit-features$DCL_depth
	features$DCL_size <- features$DCL_upperSize+features$DCL_bottomSize
	features$DCL_sizeRatio <- (features$DCL_leftSigma-features$DCL_rightSigma)/((features$DCL_leftSigma+features$DCL_rightSigma)*0.5)
	print(summary(features[,c("DCL_upperSize","DCL_bottomSize","DCL_sizeRatio","DCL_size")]))
	
	print("peak size")
	print(head(arrange(features,desc(DCL_size))[,c("year","site","DCL_size","DCL_upperSize","DCL_bottomSize","DCL_depth","DCL_upperDepth_fit","DCL_bottomDepth_fit","fileId")],10))
	
	return(features)
}

getGoodFitRatio <- function(features,threshold = seq(0,1,0.1)){
	ratio <- data.frame(thres = threshold)
	for(lake_ in allLakes){
		subData <- subset(features,lake == lake_) 
		r <- c()
		for(t in threshold){
			goodFitData <- gaussianFit(subData,threshold = t)
			r <- c(r,nrow(goodFitData)/nrow(subData))
		}
		ratio[,lake_] = r
	}
	return(ratio)
}

main_analysis_DCL <- function(features){
	# analyze each lake
	# filte the data set to detected DCL and peakNums = 1
	DCLfeatures <- subset(features, !is.na(DCL_depth) & peakNums == 1)

	for(lake_ in allLakes){
		print("*******")
		print(lake_)
		print("*******")

		subData <- subset(DCLfeatures,lake == lake_)
		goodFitData <- gaussianFit(subData,threshold = 0.9)
		
		print(paste("good fit ratio",nrow(goodFitData)/nrow(subData)))
		shapeAnalysis_DCL(goodFitData)
	}
	
	# analyze as a whole
	print("all data")
	allFitRatios <- getGoodFitRatio(DCLfeatures) %>% 
		melt(id.vars = c("thres"),value.name = "Ratio",variable.name = "Lake")
	
	pdf(file.path(outputFolder, "DCL_Fit_ratio.pdf"),height = 3, width = 5)
	print(qplot(thres, Ratio, data=allFitRatios, color = Lake)+xlab("Threshold")+geom_line()+theme_bw())
	dev.off()
	
	allGoodFit <- gaussianFit(DCLfeatures,threshold = 0.9) %>% shapeAnalysis_DCL()
	
	# plot the size boxplot
	pdf(file.path(outputFolder, "peakSizeRatio.pdf"),width = 3.25, height = 2)
	print(ggplot(data = allGoodFit) + geom_boxplot(aes(lake, DCL_sizeRatio)) + theme_bw() + 
		xlab("")+ ylab("Gamma"))
	dev.off()


	pdf(file.path(outputFolder, "peakThinness.pdf"),width = 3.25, height = 2)
	print(ggplot(data = allGoodFit) + geom_boxplot(aes(lake, (DCL_leftSigma+DCL_rightSigma)/2)) + theme_bw() + 
		xlab("")+ ylab("Mean Gamma"))
	dev.off()
	
	print("sizeRatio descrease")
	print(head(arrange(allGoodFit,desc(DCL_sizeRatio))[,c("year","site","DCL_sizeRatio","DCL_upperSize","DCL_bottomSize","DCL_depth","DCL_upperDepth_fit","DCL_bottomDepth_fit","fileId")],20))
	print("sizeRatio increase")
	print(head(arrange(allGoodFit,DCL_sizeRatio)[,c("year","site","DCL_sizeRatio","DCL_upperSize","DCL_bottomSize","DCL_depth","DCL_upperDepth_fit","DCL_bottomDepth_fit","fileId")],20))
	
	print("sizeRatio middle")
	print(head(subset(allGoodFit,DCL_sizeRatio<0.05 & DCL_sizeRatio>-0.05)[,c("year","site","DCL_sizeRatio","DCL_upperSize","DCL_bottomSize","DCL_depth","DCL_upperDepth_fit","DCL_bottomDepth_fit","fileId")],20))
	
	labeledBoxplot_ggplot(allGoodFit, "DCL_sizeRatio", outlier = TRUE)
}