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
	waterChemistry <- read.csv("../../output/waterFeature.csv")
	
	features <- read.csv("../../output/detectedFeatures.csv") %>%
		preprocessing(locations = locations, waterChemistry = waterChemistry, startYear = 1996)
	
	print("Doing algorithm validation")
	main_expertValidation(features)  # expert comparision
	print("****************")
	main_seg_comparison(features)	# HMM comparison
	print("****************")
	print("Doing DCL algorithm")
	print("****************")
	main_analysis_DCL(features)		# DCL shape 
	print("****************")
	print("Doing TRM analysis")
	main_analysis_TRM(features)		# TRM shape
	print("****************")
	print("Analyzing Lake SU")
	main_lakeSU(features)			# lake SU case
}




sink(sprintf("./results/%s_results.txt",Sys.Date()))
main()
sink()
sink()


