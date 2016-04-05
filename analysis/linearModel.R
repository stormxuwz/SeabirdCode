library(e1071)
library(ggplot2)

setwd("~/Developer/Project_IO/Seabird")
rawData=readRDS("rawDataSet.rds")

dataSet <- rawData
dataSet <- subset(dataSet,Algo_DCL_depth>0)
dataSet <- subset(dataSet,Mean_DO>0)
dataSet <- subset(dataSet,Mean_BAT>0)

dataSet$Lake="XX"

for (lakeName in c("ER","MI","HU","SU","ON")){
	dataSet[grepl(lakeName,dataSet[,1]),"Lake"]=lakeName
}

lakeData=list()

for (lakeName in c("ER","MI","HU","SU","ON")){
	lakeData[[lakeName]]=subset(dataSet,Lake==lakeName)
}

model=list()


for(data in lakeData){
	# data = lakeData[[lakeName]]
	data$ratio=data$Algo_DCL_Conc/data$Mean_Chl
	training_ind=sample(dim(data)[1],dim(data)[1]*0.8)
	model<- svm(Algo_DCL_depth~Mean_Temp+Mean_DO+Mean_BAT+Mean_SC+Mean_Chl+Var_Temp+Var_DO+Var_BAT+Var_SC+Var_Chl,data=data[training_ind,])
	print(summary(model))
	pred=predict(model,data[-training_ind,])
	quartz()
	qplot(data[-training_ind,"Algo_DCL_depth"],pred)
	# plot(pred~data[-training_ind,"Algo_DCL_depth"])
}
