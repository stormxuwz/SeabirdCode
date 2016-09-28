## this is the script to compare the HMM models and segmentation methods
require(plotly)

addingFeatures <- function(features){
	features$TRM_diff <- features$TRM_segment-features$TRM_threshold
	features$LEP_diff <- features$LEP_segment-features$LEP_threshold
	features$UHY_diff <- features$UHY_segment-features$UHY_threshold
	
	return(features)
}


statistics <- function(features){
	summary(features[,c("TRM_diff","LEP_diff","UHY_diff")])
	
}





