source("plot.R")
source("thermoFlux.R")

gly_LakeSU <- function(SUData, lakeLegend){
	print(lakeLegend)
	SUData$value <- SUData[,lakeLegend]
	SUData$Station <- SUData$site
	reverse <- TRUE
	if(lakeLegend == "DCL_conc"){
		reverse <- FALSE
	}
	plot_gly_on_map(SUData, global=TRUE, trend = TRUE, sprintf("SU_%s", lakeLegend), reverse = reverse)	
}


main_lakeSU <- function(features){
	
	locations <- read.csv("../../input/station_loc.csv")
	
	SUData <- subset(features,lake == "SU")
	SUData$fluoRatio <- SUData$DCL_conc/SUData$epi_mean_Fluorescence
	# tapply(features$TRM_diff,features$lake,summary
	
	print(arrange(SUData,fluoRatio)[,c("site","year","fluoRatio","fileId")])
	print(summary(SUData$fluoRatio))
	print(summary(SUData[,c("year","DCL_depth","TRM_segment","DCL_conc")]))
	
	
	# analyzed by year
	statsGroupByYear <- group_by(SUData,year) %>% summarise(median = median(fluoRatio,na.rm=TRUE)) %>% data.frame()
	print(data.frame(statsGroupByYear))
	
	pdf("./results/ratioTempor.pdf",width = 5, height = 5)
	print(boxplot(fluoRatio~year,data = SUData,ylab = "DCL/Surface Ratio"))
	dev.off()
	
	statsGroupBySite <- group_by(SUData,site) %>% summarise(median = median(fluoRatio,na.rm=TRUE)) %>% data.frame() %>% merge(locations, by.x = "site", by.y = "Station")
	print(data.frame(statsGroupBySite))
	statsGroupBySite$Long = -	statsGroupBySite$Long
	
	pdf("./results/ratioSpatio.pdf")
	print(qmplot(Long,Lat,data = statsGroupBySite, color = median,size = I(5))+scale_color_gradientn(colours = terrain.colors(10)))
	dev.off()
	

	# for(lakeLegend in c("TRM_segment","DCL_depth","DCL_conc","LEP_segment","UHY_segment")){
	# 	gly_LakeSU(SUData, lakeLegend)
	# }

	# plot_gly(SUData,"DCL_conc",reverse = FALSE)
	# plot_gly(SUData,"DCL_depth",reverse = TRUE)
	# plot_gly(SUData,"TRM_segment",reverse = TRUE)
	# plot_gly(SUData,"LEP_segment",reverse = TRUE)
	# plot_gly(SUData,"UHY_segment",reverse = TRUE)
	
	# plot thermoflux
	thermoFlux()


	print(arrange(SUData,DCL_depth)[,c("site","year","DCL_depth","fileId")])
	
	# analyze the correlationship between surface water chemistry and DCL
	for(surfaceWC in paste("epi_mean",c("Specific_Conductivity","Temperature","Fluorescence","Beam_Attenuation","DO"),sep="_")){
		for(aa in c("TRM_segment","DCL_conc","DCL_depth")){
			
			cleanData = SUData[SUData[,surfaceWC]>0,]
			if(aa=="DCL_conc") cleanData[,aa] = log(cleanData[,aa])
			print(aa)
			print(surfaceWC)
			print(cor.test(cleanData[,surfaceWC],cleanData[,aa],use = "complete.obs"))
		}
	}
}

