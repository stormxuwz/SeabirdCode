require(RMySQL)
require(reshape2)

dbConfig <- list(dbname = "Seabird", username="root", password="XuWenzhaO", host="127.0.0.1")

sqlQuery <- function (sql) {
	if(nchar(sql)<1){
		stop("wrong sql")  	
  	}
  	conn <- dbConnect(MySQL(), dbname = dbConfig$dbname, username=dbConfig$username, password=dbConfig$password, host=dbConfig$host, port=3306)

  	result <- dbGetQuery(conn,sql)
  	dbDisconnect(conn)
  	return(result)
}

stationAllYearPlot <- function(site){

	allYear = 1996:2013
	site = "SU01"
	fileId_sql <- "SELECT fileId,year(systemUpLoadTime) as year,fileName from summer_meta where stationInfered = 'SU01'"
	fileIdDF <- sqlQuery(fileId_sql)
	

	maxDepth_sql <- sprintf("Select max(Depth) from summer_data where fileId in (%s)", paste(fileIdDF$fileId,collapse=","))
	temperature_range_sql <- sprintf("Select min(Temperature),max(Temperature) from summer_data where fileId in (%s)", paste(fileIdDF$fileId,collapse=","))
	fluorescence_range_sql <- sprintf("Select min(Fluorescence),max(Fluorescence) from summer_data where fileId in (%s)", paste(fileIdDF$fileId,collapse=","))

	maxDepth <- sqlQuery(maxDepth_sql)[1,1]
	temperatureRange <- as.numeric(sqlQuery(temperature_Range_sql)[,1:2])
	fluorescenceRange <- as.numeric(sqlQuery(fluorescence_range_sql)[,1:2])

	plotList_temperature <- list()
	plotList_fluorescence <- list()
	
	for(i in 1:nrow(fileIdDF)){
		id <- fileIdDF$fileId[i]
		name <- paste(fileIdDF$year[i],basename(fileIdDF$fileName[i]))
		sql <- sprintf("Select * from summer_data where fileId = %s order by 'index'",  id)
		data <- sqlQuery(sql)
		# data <- melt(data,id.vars = ("index","Depth","id","fileId")))
		p_temperature <- qplot(Temperature,-Depth,data=data,color=I("red"))+ylim(c(-maxDepth,0))+xlim(temperatureRange)+ggtitle(name)
		plotList_temperature[[as.character(id)]] <- p_temperature

		p_fluorescence <- qplot(Fluorescence,-Depth,data=data,color=I("red"))+ylim(c(-maxDepth,0))+xlim(fluorescenceRange)+ggtitle(name)
		plotList_fluorescence[[as.character(id)]] <- p_fluorescence
	}
	
	args.list <- c(plotList_temperature,list(nrow=2,ncol=16))
	png(sprintf("~/Desktop/Temperature.png"),width = 2000,height = 500)
	print(do.call(grid.arrange, args.list))
	dev.off()

	args.list <- c(plotList_fluorescence,list(nrow=2,ncol=16))
	png(sprintf("~/Desktop/Fluorescence.png"),width = 2000,height = 500)
	print(do.call(grid.arrange, args.list))
	dev.off()
	
	pm <- ggmatrix(plotList,nrow=2,ncol=16)
}


readFeature <- function(){
  feature <- read.csv("../../output/testFeature.csv")
  validStation <- read.csv("../../input/station_loc.csv")
  waterChemistryData <- read.csv("../../output/waterFeature.csv")[,-1]
  feature <- cbind(feature,waterChemistryData)
  yearRange <- unique(feature$year)
  siteRange <- unique(feature$site)
  fullRange <- expand.grid(year = yearRange,site = siteRange)
  
  feature <- merge(fullRange,feature, by = c("year","site"),all.x=T,all.y=F)
  
  for(var in c(waterChemistryVariables,detectedVariables)){
  	feature[,var] <- ifelse(feature[,var]<0.001,NA,feature[,var])
  }

  # feature[,waterChemistryVariables] <- ifelse(feature[,waterChemistryVariables]<0,NA,feature[,waterChemistryVariables])
  # feature[,detectedVariables] <- ifelse(feature[,detectedVariables]<0,NA,feature[,detectedVariables])

  
  feature$lake <- addLake(feature$site)
  feature_SU <- filter(feature,lake=="SU")
  validStation$Station <- as.character(validStation$Station)
  # validStation$bathymetry <- retriveBathyMetriy(validStation,"../../input/erie_lld/erie_lld.asc")
  validStation$bathymetry <- retriveBathyMetriy(validStation,"../../input/superior_lld/superior_lld.asc")
	validStation$Long <- -validStation$Long
  # feature <- subset(feature,site %in% validStation$Station)
  feature_SU <- merge(feature_SU,validStation,by.x = "site", by.y = "Station")
  
  return(feature_SU)
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
