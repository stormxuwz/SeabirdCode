rm(list=ls())
library(reshape2)
library(dplyr)
library(ggplot2)
library(plotly)
require(gridExtra)

readFeature <- function(){
	feature <- read.csv("testFeature.csv")
	validStation <- read.csv("station_loc.csv")

	validStation$Station <- as.character(validStation$Station)
  validStation$bathymetry <- retriveBathyMetriy(validStation,"./superior_lld/superior_lld.asc")
	
  feature$lake <- addLake(feature$site)
	# feature <- subset(feature,site %in% validStation$Station)
  feature <- merge(feature,validStation,by.x = "site", by.y = "Station")
	return(feature)
}

addLake <- function(site){
  return(strtrim(site,2))
}


retriveBathyMetriy <- function(spData,sourceMapFile){
  require(raster)
  spData$Long <- -spData$Long
  coordinates(spData)=~Long+Lat
  # spData must be a sp data class
  bathymetry_raster = raster(sourceMapFile)
  bathymetry <- extract(bathymetry_raster,spData)
  return(bathymetry)
}

algorithmDiff <- function(feature,lake_="ER",var = "THM"){
  expertVar <- paste(var,"expert",sep="_")
  algorithmVar <- paste(var,"segment",sep="_")
  if(var =="DCL"){
 	algorithmVar <- "DCL_depth"
  }
  feature$diff <- abs(feature[,expertVar]-feature[,algorithmVar])
  feature$ratio <- round((feature[,expertVar]-feature[,algorithmVar])/feature[,expertVar]*100,2)
  subdata <- subset(feature,lake==lake_) %>% arrange(diff)
  return(subdata[,c("diff","site","year","ratio","lake",expertVar,algorithmVar)])
}

algorithmDiff_threshold <- function(feature,lake_="ER",var = "THM"){
  expertVar <- paste(var,"expert",sep="_")
  algorithmVar <- paste(var,"threshold",sep="_")
  if(var =="DCL"){
    algorithmVar <- "DCL_depth"
  }
  feature$diff <- abs(feature[,expertVar]-feature[,algorithmVar])
  feature$ratio <- round((feature[,expertVar]-feature[,algorithmVar])/feature[,expertVar]*100,2)
  subdata <- subset(feature,lake==lake_) %>% arrange(diff)
  return(subdata[,c("diff","site","year","ratio","lake",expertVar,algorithmVar)])
}

algorithmDiff_hmm <- function(feature,lake_="ER",var = "THM"){
  expertVar <- paste(var,"expert",sep="_")
  algorithmVar <- paste(var,"HMM",sep="_")
  if(var =="DCL"){
    algorithmVar <- "DCL_depth"
  }
  feature$diff <- abs(feature[,expertVar]-feature[,algorithmVar])
  feature$ratio <- round((feature[,expertVar]-feature[,algorithmVar])/feature[,expertVar]*100,2)
  subdata <- subset(feature,lake==lake_) %>% arrange(diff)
  return(subdata[,c("diff","site","year","ratio","lake",expertVar,algorithmVar)])
}

filterOutValidFeature <- function(feature,legend){
  varName <- paste(legend,"expert",sep="_")
  return(feature[feature[,varName]>0 & feature$hasError<1,])
}

is_outlier <- function(x) {
 	 	return(x < quantile(x, 0.25) - 1.5 * IQR(x) | x > quantile(x, 0.75) + 1.5 * IQR(x))
}

myboxplot <- function(data){
	data %>% group_by(lake) %>% ggplot(., aes(x = factor(lake), y = diff)) + geom_boxplot() + geom_text(aes(label = ifelse(is_outlier(diff),paste(site,year),NA), na.rm = TRUE, hjust = -0.3))
}

summary_diff_stat <- function(feature,var = "THM"){
	# Differences between algorithm and expert 
	subFeature <- filterOutValidFeature(feature,var)
	comparison <- data.frame()
	comparison_notDetected <- data.frame()
	outlier <- c()
	for(lake in c("ER","ON","MI","SU","HU")){
		sub_comparison <- algorithmDiff(subFeature,lake,var)
		comparison <- rbind(comparison,sub_comparison[sub_comparison[,7]>0,])
		comparison_notDetected <- rbind(comparison_notDetected,sub_comparison[sub_comparison[,7]<0,])
		outlier <- c(outlier,is_outlier(sub_comparison[sub_comparison[,7]>0,"diff"]))
	}
	comparison$lake <- as.factor(comparison$lake)
	bp <- ggplot(data=subset(comparison,diff<100))+geom_boxplot(aes(lake,diff),outlier.size = 0.5)+xlab(NULL)+ylab("Depth Differences (m)")+theme_bw()+theme(text = element_text(size = 16))
	
	comparison_outlier <- comparison[outlier,]
	pdf(paste(var,"_diff.pdf",sep=""),width = 5, height =3)
	print(bp)
	dev.off()
	
	return(list(outlier=comparison_outlier,notDetected=comparison_notDetected))
}


LakeSU_analysis <- function(feature){
  SU <- subset(feature,lake=="SU")
    <- subset(SU,!(site=="ER08" & year == 1996))
  waterFeature <- read.csv("waterFeature.csv")

  totalSU <- cbind(validSU,waterFeature)
  totalSU <- subset(totalSU,hasError<1)
  
  write.csv(totalSU,"SU_data.csv")
  totalSU <- read.csv("SU_data.csv")

  varList <-c("DO","Temperature","Specific_Conductivity","Fluorescence","Beam_Attenuation")
  mean_varList <- paste("epi_mean_",varList,sep="")
  var_varList <- paste("epi_var_",varList,sep="")


  ggplot(subset(totalSU,DCL_depth>0))+geom_boxplot(aes(x=as.factor(year),y=DCL_depth))+geom_text(aes(x=factor(year),y=DCL_depth,label = year))
}


main <- function(){
  feature <- readFeature()

  # plot all the summary of differences between expert and algorithm
  THM_res <- summary_diff_stat(feature,"THM")
  LEP_res <- summary_diff_stat(feature,"LEP")
  UHY_res <- summary_diff_stat(feature,"UHY")
  DCL_res <- summary_diff_stat(feature,"DCL")

  LakeSU_analysis(feature)

}

linearAnalysis <- function(feature,yVariable,xVariable){
  fl <- as.formula(paste(yVariable,"~",paste(xVariable,collapse="+")))
  lmModel <- lm(fl,data=subset(feature, epi_mean_DO>0 & DCL_depth>0))
}


GWPCA <- function(feature){

}

plot(subset(totalSU,epi_mean_Beam_Attenuation>0 & epi_mean_DO>0 & DCL_depth >0)[,c(mean_varList,"DCL_depth")])

df <- subset(totalSU,DCL_depth>0)
# lmModel <- lm(DCL_depth~epi_mean_Temperature+epi_mean_Fluorescence,data=df)

df$site <- as.factor(df$site)
ggplot(df)+geom_boxplot(aes(x=as.factor(year),y=DCL_depth))+geom_text(aes(x=factor(year),y=DCL_depth,label = site))

getdf <- function(feature,site_,var="DCL_depth"){
  df <- subset(feature,site %in% site_)
  df <- df[df[,var]>0,]
  return(df)
}


bbox <- make_bbox(Long, Lat, cleanSU, f = 0.3)

plotSPData <- function(data,varName){
  map <- ggmap(get_map(bbox,source="stamen"))
  data$var <- data[,varName]
  data <- subset(data,var>0)

  years <- unique(data$year)
  colorLimits <- range(data$var)

  for(targetyear in years){
    p1 <- map+geom_point(aes(x=Long,y=Lat,color=var,label=substr(site,3,4)),data=subset(data,year==targetyear),size=5)+scale_color_gradientn(colours = terrain.colors(10),limits=colorLimits)+geom_text(aes(x=Long,y=Lat,label=substr(site,3,4)),data=subset(data,year==targetyear),color="black")+ggtitle(paste(targetyear,"_",varName,sep=""))
    p2 <- map+geom_point(aes(x=Long,y=Lat,color=var,label=substr(site,3,4)),data=subset(data,year==targetyear),size=5)+scale_color_gradientn(colours = terrain.colors(10))+geom_text(aes(x=Long,y=Lat,label=substr(site,3,4)),data=subset(data,year==targetyear),color="black")+ggtitle(paste(targetyear,"_",varName,sep=""))

    plotName <- paste("./plotResults/",targetyear,"_",varName,"_SU.png",sep="")
    print(plotName)
    png(plotName,width=1000,height=250)

    grid.arrange(p1,p2,ncol=2)
    dev.off()
  }
}


plotSPData(totalSU,"DCL_depth")
plotSPData(totalSU,"hyp_mean_Temperature")
plotSPData(totalSU,"DCL_depth")
plotSPData(totalSU,"DCL_depth")
# df <- getdf(totalSU,c("SU06","SU07","SU08"))
# df <- subset(df,DCL_exist>0)
# ggplot(df)+geom_boxplot(aes(x=as.factor(year),y=DCL_depth))+geom_text(aes(x=factor(year),y=DCL_depth,label = site))



# main()
