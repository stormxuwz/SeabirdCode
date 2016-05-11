rm(list=ls())
library(reshape2)
library(dplyr)
library(ggplot2)
library(plotly)
require(gridExtra)

source("data.R")
source("EDA.R")
# source("labDataExplore.R")
source("plot.R")
source("ML.R")
source("global.R")

main <- function(){
  feature <- readFeature()
  
  # waterChemistryVariables
  # [1] "epi_mean_Temperature"           "epi_mean_Specific_Conductivity" "epi_mean_Fluorescence"         
  # [4] "hyp_mean_Temperature"           "hyp_mean_Specific_Conductivity" "hyp_mean_Fluorescence" 
  
  MDS(feature,distanceFeature = waterChemistryVariables,targetFeature = "DCL_depth",site = "SU04",outlier = TRUE)
  
  # plot all the summary of differences between expert and algorithm
  # THM_res <- summary_diff_stat(feature,"THM")
  # LEP_res <- summary_diff_stat(feature,"LEP")
  # UHY_res <- summary_diff_stat(feature,"UHY")
  # DCL_res <- summary_diff_stat(feature,"DCL")

  # LakeSU_analysis(feature)

}

# plot(subset(totalSU,epi_mean_Beam_Attenuation>0 & epi_mean_DO>0 & DCL_depth >0)[,c(mean_varList,"DCL_depth")])

# df <- subset(totalSU,DCL_depth>0)
# # lmModel <- lm(DCL_depth~epi_mean_Temperature+epi_mean_Fluorescence,data=df)

# df$site <- as.factor(df$site)
# ggplot(df)+geom_boxplot(aes(x=as.factor(year),y=DCL_depth))+geom_text(aes(x=factor(year),y=DCL_depth,label = site))

getdf <- function(feature,site_,var="DCL_depth"){
  df <- subset(feature,site %in% site_)
  df <- df[df[,var]>0,]
  return(df)
}


