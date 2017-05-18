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
source("./seg_comparison.R")

otherData <- function(){
	waterChemistry <- 
	expertNotes <- read.csv("../../input/All_Lakes_through2012.csv")
}


main<- function(){
	# read the data and combine data
	locations <- read.csv("../../input/station_loc.csv")
	waterChemistry <- read.csv("../../output_0515/waterFeature.csv")
	
	features <- read.csv("../../output_0515/detectedFeatures.csv") %>%
		preprocessing(locations = locations, waterChemistry = waterChemistry)
	
	print("Doing algorithm validation")
	main_expertValidation(features)
	print("****************")
	main_seg_comparison(features)
	print("****************")
	print("Doing DCL algorithm")
	print("****************")
	main_analysis_DCL(features)
	print("****************")
	print("Doing TRM analysis")
	main_analysis_TRM(features)
	print("****************")
	print("Analyzing Lake SU")
	main_lakeSU(features)
}




sink(sprintf("./results/%s_results.txt",Sys.Date()))
main()
sink()
sink()
sink()
sink()
