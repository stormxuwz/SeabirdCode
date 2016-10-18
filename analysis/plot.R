library(GGally)
library(ggplot2)
library(dplyr)
library(ggmap)

plot_gly <- function(feature,variable, reverse = TRUE){
	# plot the gly plots
	feature <- arrange(feature,year)
	feature[,variable] <- ifelse(feature[,variable]<0,NA,feature[,variable])
	
	if(reverse){
		feature[,variable] <- -feature[,variable]
	}
	temp.gly <- glyphs(feature, "Long", "year", "Lat", variable , height=0.25,width = 0.5)
	
	pdf(sprintf("../../output/%s_glymaps.pdf",variable),height = 5, width = 8)
	print(ggplot(temp.gly, ggplot2::aes(gx, gy, group = gid)) +add_ref_lines(temp.gly, color = "grey90") +add_ref_boxes(temp.gly, color = "grey90") +geom_path() + geom_point(size = 0.8)+theme_bw() + labs(x = "lon", y = "lat"))
	dev.off()
	
}


visGeoLocations <- function(locations){
	# plot the location of each sensor
  leaflet(data = locations) %>% addTiles() %>% addMarkers(~Long, ~Lat, popup = ~as.character(Station))
}


plotSPData <- function(data,varName){
	# plot the varName data spatially, with color as the value
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


labeledBoxplot_ggplot <- function(df,diffVar,label = TRUE,outlier=TRUE){
	# boxplot
	if(outlier){
		p <- qplot(lake,df[,diffVar],data = df)+geom_boxplot()
	}else{
		p <- qplot(lake,df[,diffVar],data = df)+geom_boxplot(outlier.shape = NA)+scale_y_continuous(limits = quantile(df[,diffVar], c(0.1, 0.9),na.rm = TRUE))
	}
	
	if(label){
		p <- p+	geom_text(aes(lake,df[,diffVar],label = paste(site,year)),data = df)
	}
	
	return(p)
}

boxplot_base <- function(df,diffVar, outlier = TRUE){
	boxplot(TRM_diff~lake,data = subset(df, is.na(TRM_diff)<1),outline = FALSE)
}








