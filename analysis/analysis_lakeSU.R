source("plot.R")

gly_thermoFlux <- function(thermofluxDataSU){
	thermofluxDataSU$value <- (thermofluxDataSU$summerTemperature_meanUHY - thermofluxDataSU$springTemperature_meanUHY)
	plot_gly_on_map(thermofluxDataSU, global = FALSE, trend = TRUE, outputFile = file.path(outputFolder, "SU_thermoFlux_meanUHY"), reverse = FALSE)
}


gly_LakeSU <- function(SUData, lakeLegend){
	# function to plot glyph plot for lake SU
	print(lakeLegend)
	SUData$value <- SUData[,lakeLegend]
	SUData$Station <- SUData$site
	
	reverse <- TRUE
	if(lakeLegend == "DCL_conc"){
		reverse <- FALSE
	}
	plot_gly_on_map(SUData, global=TRUE, trend = TRUE, outputFile = sprintf("%s/SU_%s", outputFolder, lakeLegend), reverse = reverse)
	plot_gly_on_map(SUData, global=FALSE, trend = TRUE, outputFile = sprintf("%s/SU_Local_%s", outputFolder, lakeLegend), reverse = reverse)	
}


compareWithExpert <- function(SUData, algorithmLabel, expertLabel, valueLabel, reverse = FALSE){
	# function to plot glyph plot for lake SU
	SU_locations <- unique(SUData[,c("site","Lat","Long")])
	
	SUData$Algorithm <- SUData[,algorithmLabel]
	SUData$Expert <- SUData[, expertLabel]
	
	
	if(reverse){
		SUData[,c("Algorithm","Expert")] <- -1 * SUData[,c("Algorithm","Expert")]
	}
	
	SUData <- SUData %>% 
		select(site, year, Algorithm, Expert) %>% 
		melt(id.vars = c("site", "year"), variable.name ="Source")
	
	for(i in 1:nrow(SU_locations)){
		station_ <- SU_locations[i,"site"] %>% as.character()
		print(station_)
		subdf <- subset(SUData, site == station_)
		
		pdf(paste0(outputFolder, "/compareWithExpert/", valueLabel,"_",station_,"_", "compareWithExpert.pdf"),width = 3, height = 3)
		print(ggplot(data = subdf, aes(x = year, y = value, color = Source)) + 
						geom_line() + geom_point() + ylab(valueLabel) + xlab("Year") + 
						theme_bw() + theme(legend.position="top") + labs(color = station_))
		dev.off()
	}
}


