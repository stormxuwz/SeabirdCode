library(GGally)
library(ggplot2)
library(dplyr)

plot_gly <- function(feature,variable){
	feature <- arrange(feature,year)
	feature[,variable] <- ifelse(feature[,variable]<0,NA,feature[,variable])
	temp.gly <- glyphs(feature, "Long", "year", "Lat", variable , height=0.25,width = 0.5)
	ggplot(temp.gly, ggplot2::aes(gx, gy, group = gid)) +add_ref_lines(temp.gly, color = "grey90") +add_ref_boxes(temp.gly, color = "grey90") +geom_path() + geom_point()+theme_bw() + labs(x = "", y = "")
}

#plot_gly(feature,"DCL_depth")
#plot_gly(feature,"DCL_magnitude")
#plot_gly(feature,"THM_segment")


plotSPData <- function(data,varName){
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


boxplot <- function(feature,varName){
	ggplot(subset(totalSU,DCL_depth>0))+geom_boxplot(aes(x=as.factor(year),y=DCL_depth))+geom_text(aes(x=factor(year),y=DCL_depth,label = year))
}








