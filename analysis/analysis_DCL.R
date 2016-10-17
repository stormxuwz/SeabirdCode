require(reshape2)

gaussianFit <- function(features,threshold=0.8){
	# print the ratio of each lake that the peak is satisfy a Gaussian shape
	goodFitData <- subset(features, DCL_leftShapeFitErr > threshold & DCL_rightShapeFitErr > threshold & peakNums ==1)
	return(goodFitData)
}


shapeAnalysis_DCL <- function(features){
	# those features should be fit by Gaussian shape well
	
	features$DCL_upperSize <- features$DCL_depth-features$DCL_upperDepth_fit
	features$DCL_bottomSize <- features$DCL_bottomDepth_fit-features$DCL_depth
	
	features$DCL_size <- features$DCL_bottomDepth_fit+features$DCL_depth
	# features$DCL_sizeRatio <- features$DCL_upperSize/features$DCL_bottomSize
	features$DCL_sizeRatio <- (features$DCL_upperSize - features$DCL_bottomSize)/(features$DCL_upperSize + features$DCL_bottomSize)
	# features$DCL_upperConc <- features$DCL_upperDepth_fit
	# features$DCL_bottomConc <- features$DCL_bottomDepth_fit
	#features <- subset(features,DCL_sizeRatio<Inf & DCL_sizeRatio>0)
	print(summary(features[,c("DCL_upperSize","DCL_bottomSize","DCL_sizeRatio","DCL_size")]))
	
	print("peak size")
	print(head(arrange(features,desc(DCL_size))[,c("year","site","DCL_size","DCL_upperSize","DCL_bottomSize","DCL_depth","DCL_upperDepth_fit","DCL_bottomDepth_fit","fileId")],10))
	
	
	return(features)
}

getGoodFitRatio <- function(features,lake,threshold = seq(-0.5,1,0.1)){
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
	# qplot(lake,fluoRatio,data = features)+geom_boxplot()+geom_text(aes(lake,fluoRatio,label = paste(site,year)),data =features)
	# analyze each lake
	for(lake_ in allLakes){
		print("*******")
		print(lake_)
		print("*******")

		subData <- subset(features,lake == lake_)
		goodFitData <- gaussianFit(subData,threshold = 0.8)
		
		print(paste("good fit ratio",nrow(goodFitData)/nrow(subData)))
		shapeAnalysis_DCL(goodFitData)
	}
	
	# analyze as a whole
	print("all data")
	allFitRatios <- getGoodFitRatio(features) %>% 
		melt(id.vars = c("thres"),value.name = "Ratio",variable.name = "Lake")
	
	pdf("../../output/DCL_Fit_ratio.pdf",height = 5, width = 8)
	print(qplot(thres, Ratio, data=allFitRatios, color = Lake)+xlab("Threshold")+geom_line())
	dev.off()
	
	
	allGoodFit <- gaussianFit(features) %>% shapeAnalysis_DCL()
	print("sizeRatio descrease")
	print(head(arrange(allGoodFit,desc(DCL_sizeRatio))[,c("year","site","DCL_sizeRatio","DCL_upperSize","DCL_bottomSize","DCL_depth","DCL_upperDepth_fit","DCL_bottomDepth_fit","fileId")],10))
	print("sizeRatio increase")
	print(head(arrange(allGoodFit,DCL_sizeRatio)[,c("year","site","DCL_sizeRatio","DCL_upperSize","DCL_bottomSize","DCL_depth","DCL_upperDepth_fit","DCL_bottomDepth_fit","fileId")],10))
	
	print("sizeRatio middle")
	print(head(subset(allGoodFit,DCL_sizeRatio<0.05 & DCL_sizeRatio>-0.05)[,c("year","site","DCL_sizeRatio","DCL_upperSize","DCL_bottomSize","DCL_depth","DCL_upperDepth_fit","DCL_bottomDepth_fit","fileId")],10))
	
	#print("peak size")
	#print(head(arrange(allGoodFit,desc(DCL_size))[,c("year","site","DCL_size","DCL_upperSize","DCL_bottomSize","DCL_depth","DCL_upperDepth_fit","DCL_bottomDepth_fit","fileId")],10))
	
	
	labeledBoxplot_ggplot(allGoodFit, "DCL_sizeRatio", outlier = TRUE)
}