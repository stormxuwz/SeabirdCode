# scripts to analysis the TRM results

shapeAnalysis_TRM <- function(features){
	print(summary(features[,c("TRM_num_segment","TRM2UHY_segNum")]))
	print(arrange(features,desc(doubleTRM))[,c("site","year","doubleTRM","fileId")] %>% subset(doubleTRM>0))
	print(arrange(features,desc(positiveGradient))[,c("site","year","positiveGradient","fileId")] %>% subset(positiveGradient>0))
}


main_analysis_TRM <- function(features){
	# features
	for(lake_ in allLakes){
		print("*******")
		print(lake_)
		print("*******")
		subData <- subset(features,lake == lake_)
		shapeAnalysis_TRM(subData)
	}
	
	print("All data")
	shapeAnalysis_TRM(features)
}