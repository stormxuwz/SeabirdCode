
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
    # <- subset(SU,!(site=="ER08" & year == 1996))
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

