# scripts to analysis the TRM results

shapeAnalysis_TRM <- function(features){
	print(summary(features[,c("TRM_num_segment","TRM2UHY_segNum")]))
	print(head(arrange(features,desc(doubleTRM))[,c("site","year","doubleTRM")],25)) # print the site of double thermocline
	print(head(arrange(features,desc(positiveGradient))[,c("site","year","positiveGradient")],25))
}


main_analysis_TRM <- function(features){
	# features
	print(head(arrange(features,desc(doubleTRM))[,c("site","year","doubleTRM")],25)) # print the site of double thermocline
	
	for(lake_ in allLakes){
		print(lake_)
		subData <- subset(features,lake == lake_)
		shapeAnalysis_TRM(subData)
	}
	
	print("all data")
	labeledBoxplot_ggplot(features, "TRM_num_segment", label = FALSE, outlier = TRUE)
	labeledBoxplot_ggplot(features, "TRM2UHY_segNum", outlier = TRUE)
	
}