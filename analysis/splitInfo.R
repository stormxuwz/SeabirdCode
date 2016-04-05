# read lake csv info

infoTable <- read.csv("~/Developer/Project_IO/Seabird/LayerInformation/All_Lakes_through2012.csv")

strToNum <- function(v){
	v <- as.character(v)
	return(as.numeric(v))
}

lakes <- levels(infoTable$LAKE)
Year <- unique(infoTable$YEAR)
Month  <- levels(infoTable$MONTH)
depthLoc <- levels(infoTable$DepthCode)


featureName <- c("YEAR","STATION","SAMPLING_DATE","SMPL_DEPTH..m",
	"Alkalinity..mg.l","Cl...mg.l","NH3.N..ug.l","NOx..mg.l","TDP..ug.l","SiO2..mg.l","TKN..ug.l","TP..ug.l","Trubidity..NTU","Chlorophyll.a..ug.l","Water.Temperature..C","SB.Irradiance..uE.sec.m2","SB.Beam.Transmission...")
dataHasDCL <- subset(infoTable,DepthCode=="DCL")

otherWaterChemistry <- matrix(,ncol=length(featureName),nrow=0)

for(i in 1:dim(dataHasDCL)[1]){
	item <- dataHasDCL[i,]
	year <- item$YEAR
	station <- item$STATION
	time <- item$SAMPLING_DATE
	relevantData <- subset(infoTable[,featureName],YEAR==year & STATION==station & SAMPLING_DATE==time)
	relevantData["DCL_depth"]=item["SMPL_DEPTH..m"]
	relevantData["DCL_value"]=item["Chlorophyll.a..ug.l"]
	minIndex <- which.min(relevantData$SMPL_DEPTH..m) # find the surface water chemistry as the predictors
	otherWaterChemistry <- rbind(otherWaterChemistry,relevantData[minIndex,])
}

# Make as a data frame
otherWaterChemistry <- as.data.frame(otherWaterChemistry)
otherWaterChemistry$Station <- as.character(otherWaterChemistry$Station)
names(otherWaterChemistry) <- c("Year","Station","Time","Depth","ALK_mg_L","Cl_mg_L","NH3_ug_L","NOx_mg_L","TDP_ug_L","SiO2_mg_L","TKN_ug_L","TP_ug_L","Turbidity","Chl","Temp","Irrad","Transmission","DCL_depth","DCL_Conc")

otherWaterChemistry$Lake <- as.factor(substr(otherWaterChemistry$Station,1,2))

for(lake in lakes){
	data=subset(infoTable,LAKE==lake)
	data_10m=subset(data,DepthCode=="10M")
}

usefulWaterChemistry <- otherWaterChemistry[,c("Year","Lake","Station","TP_ug_L","Turbidity","Chl","Transmission","DCL_depth","DCL_Conc","NOx_mg_L","Cl_mg_L","ALK_mg_L")]

for(colName in c("ALK_mg_L","Cl_mg_L","NH3_ug_L","NOx_mg_L","TDP_ug_L","TP_ug_L","Turbidity","Chl","Temp","Irrad","Transmission","DCL_depth","DCL_Conc","NOx_mg_L","Cl_mg_L","ALK_mg_L")){
	otherWaterChemistry[,colName]=strToNum(otherWaterChemistry[,colName])
}

SUdata <- na.omit(subset(usefulWaterChemistry,Lake=="SU"))

rfModel <- randomForest(DCL_Conc/Chl~TP_ug_L+Turbidity+Chl+Transmission,data=SUdata)

lmModel <- lm(DCL_Conc~TP_ug_L+I(TP_ug_L^2)+Turbidity+I(Turbidity^2),data=SUdata)
summary(lmModel)
a <- predict(lmModel,SUdata)

qplot(a,SUdata$DCL_Conc)+coord_fixed()+geom_abline()

