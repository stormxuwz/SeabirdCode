rm(list=ls())

library(dplyr)
library(reshape2)
library(ggplot2)

preprocessing <- function(features){
	# make consistent of the site name
	ind_MI18M <- which(features$site == "MI18M")
	ind_ER15M <- which(features$site == "ER15M")
	
	features[ind_MI18M,"site"] = "MI18"
	features[ind_ER15M,"site"] = "ER15"
	
	features$lake <- substr(features$site,1,2)
	
	return(features)
}


algorithmDiff <- function(feature,lake_=NULL,var = "TRM"){
	expertVar <- paste("expert",var,sep="_")
	algorithmVar <- paste(var,"segment",sep="_")
	if(var =="DCL"){
		algorithmVar <- "DCL_depth"
	}
	feature$diff <- feature[,expertVar]-feature[,algorithmVar]
	feature$ratio <- round((feature[,expertVar]-feature[,algorithmVar])/feature[,expertVar]*100,2)
	
	if(is.null(lake_))
		subdata <- arrange(feature,diff,site,year)
	else
		subdata <- subset(feature,lake==lake_) %>% arrange(diff,site,year)
	
	return(subdata[,c("diff","site","year","ratio","lake",expertVar,algorithmVar)])
}

# read the data
features <- read.csv("../../output/detectedFeatures.csv") %>% preprocessing()
locations <- read.csv("../../input/station_loc.csv")
expertNotes <- read.csv("../../input/All_Lakes_through2012.csv")

# construct all possible data combination
yearRange <- unique(features$year)
siteRange <- unique(locations$Station)
fullRange <- expand.grid(year = yearRange,site = siteRange)

cleanFeatures <- merge(fullRange,features,by.x = c("year","site"),by.y = c("year","site"),all.x =TRUE)
cleanFeatures <- merge(cleanFeatures,locations,by.x = c("site"), by.y = "Station") %>% arrange(site,year)


# plot differences
for(var in c("TRM","LEP","DLC","UHY")){
	tmp <- algorithmDiff(cleanFeatures)
	png(paste("../../output/",var,".png",sep=""),width = 1000,height = 3000)
	print(ggplot(aes(lake,diff),data=tmp)+geom_boxplot()+geom_text(aes(lake,diff,label = paste(site,year))))
	dev.off()
}






