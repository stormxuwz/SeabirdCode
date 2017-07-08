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
	plot_gly_on_map(SUData, global=TRUE, trend = TRUE, outputFile = sprintf("../../output/SU_%s", lakeLegend), reverse = reverse)
	plot_gly_on_map(SUData, global=FALSE, trend = TRUE, outputFile = sprintf("../../output/SU_Local_%s", lakeLegend), reverse = reverse)	
}


fluoRatio <- function(SUData){
	SUData$fluoRatio <- SUData$DCL_conc/SUData$epi_mean_Fluorescence
	# tapply(features$TRM_diff,features$lake,summary	
	print(arrange(SUData,fluoRatio)[,c("site","year","fluoRatio","fileId")])
	print(summary(SUData$fluoRatio))

	# analyzed by year
	statsGroupByYear <- group_by(SUData,year) %>% summarise(median = median(fluoRatio,na.rm=TRUE)) %>% data.frame()
	print(data.frame(statsGroupByYear))
	
	pdf("./results/ratioTempor.pdf",width = 5, height = 5)
	print(boxplot(fluoRatio~year,data = SUData,ylab = "DCL/Surface Ratio"))
	dev.off()
	
	statsGroupBySite <- group_by(SUData,site) %>% summarise(median = median(fluoRatio,na.rm=TRUE)) %>% data.frame() %>% merge(locations, by.x = "site", by.y = "Station")
	print(data.frame(statsGroupBySite))
	statsGroupBySite$Long = -statsGroupBySite$Long
	
	pdf("./results/ratioSpatio.pdf")
	print(qmplot(Long,Lat,data = statsGroupBySite, color = median,size = I(5))+scale_color_gradientn(colours = terrain.colors(10)))
	dev.off()
}


main_lakeSU <- function(features){
	
	locations <- read.csv("../../input/station_loc.csv")
	SUData <- subset(features,lake == "SU")
	# SUData <- subset(SUData, fileId!=1544)
	SUData$metalimnion <- (SUData$UHY_segment +  SUData$LEP_segment)/2
	print(summary(SUData[,c("year","DCL_depth","TRM_segment","DCL_conc")]))

	# fluoRatio(SUData) # plot fluorescence ratio
	thermoFlux() # plot thermoflux

	for(lakeLegend in c("TRM_segment","DCL_depth","DCL_conc","LEP_segment","UHY_segment","metalimnion")){
		gly_LakeSU(SUData, lakeLegend)
	}
	
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

