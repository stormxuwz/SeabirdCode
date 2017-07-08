## this is the script to compare the HMM models and segmentation methods
require(plotly)

addingFeatures_diff_HMM_seg <- function(features){
	features$TRM_diff_HMM_seg <- features$TRM_segment-features$TRM_HMM
	features$LEP_diff_HMM_seg <- features$LEP_segment-features$LEP_HMM
	features$UHY_diff_HMM_seg <- features$UHY_segment-features$UHY_HMM
	
	return(features)
}



HMM_scatter <- function(features, lake_, legend, note = FALSE){

	d <- features[,c("year","site",paste0(legend,"_segment"),paste0(legend,"_HMM"),"lake")] %>% na.omit()

	if(lake_!="all"){
		d <- subset(d, lake == lake_)
	}
	
	names(d) <- c("year","site","PLR","MGHMM","lake")
	plotRange <- range(d[,c("PLR","MGHMM")])

	p <- ggplot(d) + geom_point(aes(PLR, MGHMM, color = lake), alpha = 0.2) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("PLR (m)") + ylab("MG-HMM(m)") + 
		xlim(plotRange) + ylim(plotRange) + 
		ggtitle(sprintf("%s (RMSE:%.2f, Err:%.2f)", legend, rmse(d$PLR, d$MGHMM), mean(d$PLR-d$MGHMM)))
		
	if(note){
		p = p + geom_text(aes(PLR,MGHMM, label = paste(year,site)))
		pdf(sprintf("../../output/%s_%s_algorithmScatterPlot_%s_PLRHMM.pdf",legend,lake_, note),height = 10, width = 10)
		print(p)
		dev.off()
	}else{
		pdf(sprintf("../../output/%s_%s_algorithmScatterPlot_%s_PLRHMM.pdf",legend,lake_, note),height = 3.5, width = 3.5)
		print(p)
		dev.off()
	}
}

main_seg_comparison <- function(features){
	features <- addingFeatures_diff_HMM_seg(features)
	print(summary(features[,c("TRM_diff_HMM_seg","LEP_diff_HMM_seg","UHY_diff_HMM_seg")]))
	print(arrange(features,desc(abs(TRM_diff_HMM_seg)))[,c("fileId","site","year","TRM_diff_HMM_seg")] %>% head(16))
	print(arrange(features,desc(abs(LEP_diff_HMM_seg)))[,c("fileId","site","year","LEP_diff_HMM_seg")] %>% head(100))
	print(arrange(features,desc(abs(UHY_diff_HMM_seg)))[,c("fileId","site","year","UHY_diff_HMM_seg")] %>% head(100))



	for(lake_ in c(allLakes)){
		for(l in c("LEP","TRM","UHY")){
			HMM_scatter(features, lake_, l, TRUE)
		}
	}

	for(l in c("LEP","TRM","UHY")){
		HMM_scatter(features, "all", l, FALSE)
	}
	

}





