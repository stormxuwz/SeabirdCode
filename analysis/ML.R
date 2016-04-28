source("global.R")
require(MASS)

linearAnalysis <- function(feature,yVariable,xVariable){
  fl <- as.formula(paste(yVariable,"~",paste(xVariable,collapse="+")))
  lmModel <- lm(fl,data=subset(feature, epi_mean_DO>0 & DCL_depth>0))
}




GWPCA <- function(feature){

}


MDS_sub <- function(dataSet,featureName,targetFeatureName){
	# feature is the 
	targetFeature <- dataSet[,targetFeatureName]
	feature <- dataSet[,featureName]
	label <- paste(dataSet$year,dataSet$site)
	print(summary(feature))
	d <- dist(scale(feature))
	fit <- isoMDS(d,k=2)
	x <- fit$points[,1]
	y <- fit$points[,2]

	qplot(x,y,color = targetFeature)+scale_color_gradientn(colors=topo.colors(5),name = targetFeatureName)+geom_text(aes(x,y,label = label))+theme_bw()+xlim(c(-4,4))+ylim(c(-4,4))
}

MDS <- function(feature,site_ = "all",targetFeature = "DCL_depth"){
	if(site_ == "all"){
		# MDS on all sites
		dataSet <- feature
	}else{
		dataSet <- subset(feature,site == site_)
	}

	dataSet <- dataSet[,c(waterChemistryVariables,detectedVariables,"year","site")]
	# dataSet <- dataSet[,c("epi_mean_Temperature","hyp_mean_Temperature","epi_mean_Fluorescence","hyp_mean_Fluorescence",detectedVariables,"year","site")]
	dataSet <- na.omit(dataSet)
	# MDS_sub(dataSet,c("epi_mean_Temperature","hyp_mean_Temperature","epi_mean_Fluorescence","hyp_mean_Fluorescence"),targetFeature)
	MDS_sub(dataSet,waterChemistryVariables,targetFeature)
}