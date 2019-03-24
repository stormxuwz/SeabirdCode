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

outputFolder <- "../../output/"

otherData <- function(){
	waterChemistry <- 
	expertNotes <- read.csv("../../input/All_Lakes_through2012.csv")
}


main<- function(){
	# read the data and combine data
	locations <- read.csv("../../input/station_loc.csv")
	waterChemistry <- read.csv("../../output/waterFeature.csv")
	
	# starting from 1996 for SU lake 
	features <- read.csv(paste0(outputFolder,"/detectedFeatures.csv")) %>%
		preprocessing(locations = locations, waterChemistry = waterChemistry, startYear = 1996)
	
	
	print("Doing algorithm validation")
	main_expertValidation(subset(features, year < 2013 & year > 1997))  # expert comparision, will filter data using only [1998, 2012]
	print("****************")
	#main_seg_comparison(features)	# HMM comparison
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


df = read.csv("/Users/wenzhaoxu/Desktop/Research Desktop Backup/tmp.csv") %>% filter(year > 1997)
df2 = merge(df, locations, by.x = "site", by.y = "Station")[,c("LEP_dataGradient", "UHY_dataGradient")]
names(df2) = c("LEP","UHY")

pdf("~/Desktop/Figure 4.pdf", width = 5, height = 4)
print(boxplot(df2, outline = FALSE,  whisklty = 0, staplelty = 0, ylim = c(0, 0.4), ylab = "°C/meter"))
dev.off()


 #sink(sprintf("./results/%s_results.txt",Sys.Date()))
main()
#sink()
#sink()


