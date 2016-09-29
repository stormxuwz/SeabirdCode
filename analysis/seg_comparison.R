## this is the script to compare the HMM models and segmentation methods
require(plotly)

addingFeatures_diff_HMM_seg <- function(features){
	features$TRM_diff_HMM_seg <- features$TRM_segment-features$TRM_threshold
	features$LEP_diff_HMM_seg <- features$LEP_segment-features$LEP_HMM
	features$UHY_diff_HMM_seg <- features$UHY_segment-features$UHY_HMM
	
	return(features)
}


main_seg_comparison <- function(features){
	features <- addingFeatures_diff_HMM_seg(features)
	print(summary(features[,c("TRM_diff_HMM_seg","LEP_diff_HMM_seg","UHY_diff_HMM_seg")]))
	print(arrange(features,desc(abs(TRM_diff_HMM_seg)))[,c("site","year","TRM_diff_HMM_seg")] %>% head(30))
	print(arrange(features,desc(abs(LEP_diff_HMM_seg)))[,c("site","year","LEP_diff_HMM_seg")] %>% head(30))
	print(arrange(features,desc(abs(UHY_diff_HMM_seg)))[,c("site","year","UHY_diff_HMM_seg")] %>% head(30))
}





