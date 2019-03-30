rm(list=ls())

library(dplyr)
library(reshape2)
library(ggplot2)
library(gridExtra)
source("./plot.R")
source("./expertValidation.R")
source("./analysis_lakeSU.R")
source("./analysis_DCL.R")
source("./analysis_TRM.R")
source("./global.R") # some global varialbes

outputFolder <- "./paperResults/"
dataFolder <- "./data/"

detectedFeatures <- read.csv(file.path(dataFolder, "detectedFeatures.csv"))
featuresAtExpertDepths <- read.csv(file.path(dataFolder,"featuresAtExpertDepths.csv"))
thermofluxDataSU <- read.csv(file.path(dataFolder,"thermoFlux_SU.csv"))

# expert comparision, will filter data using only [1998, 2012], operators' notes in 1996 and 1997 seems not reliable. 
print("Doing algorithm validation")
main_expertValidation(subset(detectedFeatures, year < 2013 & year > 1997)) 
print("****************")

print("****************")
print("Doing DCL algorithm")
print("****************")

main_analysis_DCL(detectedFeatures)		# DCL shape 
print("****************")

# Not run
# the following will print some analysis for stratification patterns features including
# doutble thermocline and positive gradient 
# main_analysis_TRM(features)

print("****************")
print("analyze Lake SU")

SUData <- subset(detectedFeatures,lake == "SU")

# generate mean UHY and LEP
SUData %>% group_by(site) %>% summarise(
	mean_UHY = mean(UHY_segment, na.rm = TRUE),
	mean_LEP = mean(LEP_segment, na.rm = TRUE),
	max_UHY = max(UHY_segment, na.rm = TRUE)) %>% data.frame()


for(lakeLegend in c("TRM_segment","DCL_depth","DCL_conc","LEP_segment","UHY_segment")){
	gly_LakeSU(SUData, lakeLegend)
}

gly_thermoFlux(thermofluxDataSU)

compareWithExpert(subset(SUData, year < 2013 & year > 1997) , "TRM_segment", "expert_TRM", "Thermocline Depth (m)", TRUE)
compareWithExpert(subset(SUData, year < 2013 & year > 1997) , "DCL_depth", "expert_DCL", "DCL Depth (m)", TRUE)




