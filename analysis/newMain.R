rm(list=ls())

library(dplyr)
library(reshape2)
library(ggplot2)
source("./plot.R")


#### Function to preprocess the feature matrix
preprocessing <- function(features){
	# make consistent of the site name
	ind_MI18M <- which(features$site == "MI18M")
	ind_ER15M <- which(features$site == "ER15M")
	
	features[ind_MI18M,"site"] = "MI18"
	features[ind_ER15M,"site"] = "ER15"
	
	features$lake <- substr(features$site,1,2)
	
	return(features)
}



# functions to summary statistics
# probably remove data before 1998 would be a good choice
feature_stat <- function(df,varName = "TRM"){
	predVar <- paste(varName,"segment",sep = "_")
	expertVar <- paste("expert",varName, sep = "_")

	diffVar <- paste(varName,"diff",sep ="_")

	expertExist <- !is.na(df[,expertVar])
	predExist <- !is.na(df[,predVar])

	df$only_pred <- predExist == TRUE & expertExist !=TRUE  # you only have expert
	df$only_expert <- predExist == FALSE & expertExist == TRUE # you only have predication
	df$pred_expert <- predExist == TRUE & expertExist == TRUE
	
	res <- group_by(df,lake) %>% summarise(totalN = n(),only_pred = sum(only_pred),only_expert = sum(only_expert),allExist = sum(pred_expert))
	print(res)

	pdf(sprintf("../../output/%s_diff_meta.pdf",varName),height = 50, width = 30)
	print(qplot(lake,df[,diffVar],data = df)+geom_boxplot()+geom_text(aes(lake,df[,diffVar],label = paste(site,year)),data =df))
	dev.off()
	
	pdf(sprintf("../../output/%s_diff.pdf",varName),height = 4, width = 7)
	print(
		qplot(lake,abs(df[,diffVar]),data = df)+geom_boxplot(size = 1)+theme_bw()+xlab("Lake")+ylab("Absolute Depth Differences (m)")
	)
	dev.off()
}


clusteringAlgorithm <- function(){}



# read the data
features <- read.csv("../../output/detectedFeatures.csv") %>% preprocessing()
locations <- read.csv("../../input/station_loc.csv")

waterChemistry <- read.csv("../../output/waterFeature.csv")

locations$Long <- -locations$Long

expertNotes <- read.csv("../../input/All_Lakes_through2012.csv")

features <- merge(features,locations,by.x = "site",by.y = "Station")


# calculate the differences between algorithm and expert notes
features$TRM_diff <- features$TRM_segment-features$expert_TRM
features$LEP_diff <- features$LEP_segment-features$expert_LEP
features$UHY_diff <- features$UHY_segment-features$expert_UHY
features$DCL_diff <- features$DCL_depth-features$expert_DCL
features$UHY_num <- features$TRM_num_segment-(features$TRM_idx+1)
features$DCL_segment <- features$DCL_depth

features$DCL_size <- features$DCL_bottomDepth-features$DCL_upperDepth


# filter out the strange year and site
features <-
	subset(features,year>1997 & lake %in% c("ER","HU","SU","ON","MI")) %>%
	arrange(site,year)

# merge with water chemistry 
features <- merge(features,waterChemistry,by.x = c("fileId","site","year"),by.y = c("fid","site","year")) %>%
	arrange(site,year)


features$fluoRatio <- features$DCL_conc/features$epi_mean_Fluorescence
qplot(lake,fluoRatio,data = features)+geom_boxplot()+geom_text(aes(lake,fluoRatio,label = paste(site,year)),data =features)


SUData <- subset(features,lake == "SU")


plot_gly(SUData,"DCL_conc",reverse = FALSE)
plot_gly(SUData,"DCL_depth",reverse = TRUE)
plot_gly(SUData,"TRM_segment",reverse = TRUE)
plot_gly(SUData,"LEP_segment",reverse = TRUE)
plot_gly(SUData,"UHY_segment",reverse = TRUE)
plot_gly(SUData,"TRM_num_segment",reverse = FALSE)
plot_gly(SUData,"UHY_num",reverse = FALSE)
plot_gly(SUData,"TRM_gradient_segment",reverse = TRUE)

plot_gly(SUData,"fluoRatio", reverse = TRUE)
plot_gly(SUData,"DCL_size", reverse = TRUE)

#tapply(features$fluoRatio,features$lake,summary)

# plot the boxplot of the differences between algorithm and expert notes

feature_stat(features,varName = "DCL")
feature_stat(features,varName = "TRM")
feature_stat(features,varName = "UHY")
feature_stat(features,varName = "LEP")





# # construct all possible data combination
# yearRange <- unique(features$year)
# siteRange <- unique(locations$Station)
# fullRange <- expand.grid(year = yearRange,site = siteRange)

# cleanFeatures <- merge(fullRange,features,by.x = c("year","site"),by.y = c("year","site"),all.x =TRUE)
# cleanFeatures <- merge(cleanFeatures,locations,by.x = c("site"), by.y = "Station") %>% arrange(site,year)


# # plot differences
# for(var in c("TRM","LEP","DLC","UHY")){
# 	tmp <- algorithmDiff(cleanFeatures)
# 	png(paste("../../output/",var,".png",sep=""),width = 1000,height = 3000)
# 	print(ggplot(aes(lake,diff),data=tmp)+geom_boxplot()+geom_text(aes(lake,diff,label = paste(site,year))))
# 	dev.off()
# }


### adding differences between 
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




