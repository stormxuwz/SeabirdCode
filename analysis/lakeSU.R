source("plot.R")

main_lakeSU <- function(features){
	
	SUData <- subset(features,lake == "SU")
	
	# tapply(features$TRM_diff,features$lake,summary
	
	plot_gly(SUData,"DCL_conc",reverse = FALSE)
	plot_gly(SUData,"DCL_depth",reverse = TRUE)
	plot_gly(SUData,"TRM_segment",reverse = TRUE)
	plot_gly(SUData,"LEP_segment",reverse = TRUE)
	plot_gly(SUData,"UHY_segment",reverse = TRUE)
	plot_gly(SUData,"TRM_num_segment",reverse = FALSE)
	# plot_gly(SUData,"UHY_num",reverse = FALSE)
	plot_gly(SUData,"TRM_gradient_segment",reverse = FALSE)
	
	#plot_gly(SUData,"fluoRatio", reverse = FALSE)
	#plot_gly(SUData,"DCL_size", reverse = TRUE)
}

