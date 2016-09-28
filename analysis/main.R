rm(list=ls())

library(dplyr)
library(reshape2)
library(ggplot2)
source("./plot.R")
source("./preprocessing.R")
source("./expertValidation.R")
source("./lakeSU.R")
source("./analysis_DCL.R")
source("./analysis_TRM.R")
source("./global.R") # some global varialbes

otherData <- function(){
	waterChemistry <- 
	expertNotes <- read.csv("../../input/All_Lakes_through2012.csv")
}


main<- function(){
	# read the data and combine data
	locations <- read.csv("../../input/station_loc.csv")
	waterChemistry <- read.csv("../../output/waterFeature.csv")
	
	features <- read.csv("../../output/detectedFeatures.csv") %>%
		preprocessing(locations = locations, waterChemistry = waterChemistry)
	
	# main_expertValidation(features)
	# main_analysis_DCL(features)
	main_analysis_TRM(features)
}





main()



