source("global.R")
require(MASS)

linearAnalysis <- function(feature,yVariable,xVariable){
  fl <- as.formula(paste(yVariable,"~",paste(xVariable,collapse="+")))
  lmModel <- lm(fl,data=subset(feature, epi_mean_DO>0 & DCL_depth>0))
}




GWPCA <- function(feature){

}


MDS_sub <- function(dataSet,featureName,targetFeatureName,outlier = FALSE){
	# feature is the 
	targetFeature <- dataSet[,targetFeatureName]
	feature <- dataSet[,featureName]
	label <- paste(dataSet$year,dataSet$site)
	print(summary(feature))
	d <- dist(scale(feature))
	fit <- isoMDS(d,k=2)
	x <- fit$points[,1]
	y <- fit$points[,2]


	p <- qplot(x,y,color = targetFeature)+scale_color_gradientn(colors=topo.colors(5),name = targetFeatureName)+geom_text(aes(x,y,label = label))+theme_bw()+ggtitle(dataSet$site)
	
	if(!outlier){
		p <- p+xlim(c(-4,4))+ylim(c(-4,4))
	}
	p
}

MDS <- function(feature,distanceFeature ,targetFeature = "DCL_depth",site_ = "all",outlier = TRUE){
	if(site_ == "all"){
		# MDS on all sites
		dataSet <- feature
	}else{
		dataSet <- subset(feature,site == site_)
	}

	dataSet <- dataSet[,c(distanceFeature,targetFeature,"year","site")]
	# dataSet <- dataSet[,c("epi_mean_Temperature","hyp_mean_Temperature","epi_mean_Fluorescence","hyp_mean_Fluorescence",detectedVariables,"year","site")]
	dataSet <- na.omit(dataSet)
	# MDS_sub(dataSet,c("epi_mean_Temperature","hyp_mean_Temperature","epi_mean_Fluorescence","hyp_mean_Fluorescence"),targetFeature)
	MDS_sub(dataSet,distanceFeature,targetFeature,outlier)
}