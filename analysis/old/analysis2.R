library(ggplot2)
setwd("~/Developer/Project_IO/Seabird/")
data_expert <- read.csv("depthFeature_expert.csv")
data_noexpert <- read.csv("depthFeature_noExpert.csv")

waterChemistry_expert <- read.csv("waterChemistry_expert.csv")
waterChemistry_noexpert <- read.csv("waterChemistry_noexpert.csv")

allwaterData <- rbind(waterChemistry_expert,waterChemistry_noexpert)

allData <- rbind(data_expert,data_noexpert)
allData <- cbind(allData,allwaterData)

location <- read.csv("station_loc.csv")


getLake <- function(site){
	return(substr(site,1,2))
}

allData$Lake <- substr(allData$Site,1,2)
allData$Year <- as.numeric(substr(allData$Site,6,9))
allData$Station <- substr(allData$Site,1,4)
allData <- subset(allData,Station %in% location$Station)

# allData <- subset(allData,DCL_index>-1)

# Define the function to plot

plot_surfaceChl_DCLChl <- function(data,save=TRUE){
	qplot(Surface_Chl,Algo_DCL_Conc,data=data,color=Station)+geom_abline()
}

plot_surfaceChl_DCLChl(subset(allData,Lake=="SU"))

SU_data <- subset(allData,Lake=="SU")

SU_data <- subset(SU_data,num_peaks==1 & DCL_index>-1)
SU_data$ratio <- SU_data$Algo_DCL_Conc/SU_data$Mean_Chl
SU_data$diff <- SU_data$Algo_DCL_Conc-SU_data$Mean_Chl


by_station <- group_by(SU_data, Station)
by_year <- group_by(SU_data, Year)

summ_station <- summarise(by_station,ratioMedian = median(ratio),ratioMedian=mean(ratio))
summ_year <- summarise(by_year,ratioMedian = median(ratio),ratioMedian=mean(ratio))


corList <- c()
RMSE <- c()
trainIndexList <- list()
feature <- c("Mean_Temp","Mean_BAT","Mean_Chl","Mean_DO","Var_Temp","Var_DO","Var_BAT","Var_Chl")
for(i in 1:1000){
	trainIndex <- sample(nrow(SU_data),nrow(SU_data)*0.7)
	
	xTrain <- SU_data[trainIndex,feature]
	yTrain <- SU_data[trainIndex,"diff"]

	xTest <- SU_data[-trainIndex,feature]
	yTest <- SU_data[-trainIndex,"diff"]

	svmModel <- svm(xTrain,yTrain,kernel="radial")
	yPred <- predict(svmModel,xTest)

	SU_data$pred <- 0
	SU_data[-trainIndex,"pred"] <- yPred

	corList <- c(corList,cor(yTest,yPred))
	RMSE <- c(RMSE,rmse(yPred,yTest))
	trainIndexList[[i]] <- trainIndex
}

summary(corList)
summary(RMSE)
trainIndex <- trainIndexList[[which.max(corList)]]

trainIndex <- trainIndexList[[which.min(corList)]]

cor(SU_data[,c(feature,"ratio","Algo_DCL_depth","diff")])

qplot(ratio,Algo_DCL_depth,data=SU_data,color=Year)





# library(randomForest)
# rf_model_depth<-randomForest(trainData[,""],trainData[,"Algo_DCL_depth"])

# Take Samples of the 


# Create SU_data
SU_data <- subset(allData,Lake=="SU" & Site!="SUP1_1996" & Year!=2011 & Algo_DCL_depth>0 &num_peaks==1)
SU_data$ratio <- SU_data$Algo_DCL_Conc/SU_data$Mean_Chl
SU_data$diff <- SU_data$Algo_DCL_Conc-SU_data$Mean_Chl

feature <- c("Mean_Temp","Mean_BAT","Mean_Chl","Mean_DO","Var_Temp","Var_DO","Var_BAT","Var_Chl")
uniqueStation <- unique(SU_data$Station)
for(col in feature){
	SU_data[SU_data[,col]<0,col] <- NA
}

# Remove bad features
SU_data <- na.omit(SU_data)
rownames(SU_data) <- SU_data$Site
eachStationData <- list()
for(station in uniqueStation){
	eachStationData[[station]] <- subset(SU_data,Station==station)
}

for(i in 1:length(eachStationData)){
	MeanValue <- colMeans(eachStationData[[i]][,c(feature,"Algo_DCL_depth","Algo_DCL_Conc","diff")])
	for(j in 1:nrow(eachStationData[[i]])){
		eachStationData[[i]][j,c(feature,"Algo_DCL_depth","Algo_DCL_Conc","diff")]=(eachStationData[[i]][j,c(feature,"Algo_DCL_depth","Algo_DCL_Conc","diff")]-MeanValue)/MeanValue
	}
}


newData <- eachStationData[[1]]
for(i in 2:length(eachStationData)){
	newData <- rbind(newData,eachStationData[[i]])
}




featureUsed <- c("Mean_Temp","Mean_Chl","Mean_DO")
trainData<-subset(newData,Year<2012)
testData<-subset(newData,Year>2011)
xTrain<-trainData[,featureUsed]
yTrain<-trainData[,"diff"]
xTest<-testData[,featureUsed]
yTest<-testData[,"diff"]

library(randomForest)
library(e1071)
lm_model <- lm(diff~.,data=newData[,c(featureUsed,"diff")])
summary(lm_model)

rf_model<-randomForest(xTrain[,featureUsed],yTrain,ntree=1000)
svm_model<-svm(xTrain[,featureUsed],yTrain,kernel="radial")

xTrain$predict <- rf_model$predicted
xTrain$y <- yTrain

testData$rf_predict<-predict(rf_model,xTest)
testData$svm_predict<-predict(svm_model,xTest)

ggplot(data=testData)+geom_line(aes(x=1:nrow(testData),y=diff,label=Site))+geom_text(aes(x=1:nrow(testData),y=diff,label=Site))+geom_line(aes(1:nrow(testData),rf_predict),color="red")+geom_line(aes(1:nrow(testData),svm_predict),color="blue")



# create each 
for(i in 1:length(eachStationData)){
	print(names(eachStationData)[i])
	lm_model <- lm(Algo_DCL_depth~Mean_Temp+Mean_BAT+Mean_Chl,data=eachStationData[[1]])
	print(summary(lm_model))
}

plot(newData[,c(featureUsed,"ratio","Algo_DCL_depth","Algo_DCL_Conc")])