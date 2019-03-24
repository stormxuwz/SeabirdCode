library(GGally)
library(ggplot2)
library(dplyr)
library(ggmap)
library(png)
library(grid)

getSUmap <- function(df){
	longRange <- range(df$Long)
	latRange <- range(df$Lat)
	bbox <- make_bbox(longRange,latRange,f = 0.3)
	myMap <- get_map(location=bbox, source="stamn",crop=TRUE,color="bw",maptype="terrain")
	myMap <- get_map(location = bbox, maptype="toner-lite", source="stamen",zoom=7,color = "bw",crop=TRUE)
	saveRDS(myMap, "SUMap.rds")
}

plot_gly_on_map <- function(newDF, global = FALSE, trend = FALSE, outputFile = "test.png", reverse = TRUE){
	# function to plot glygraph
	myMap <- readRDS("SU_map.rds")
	SU_locations <- unique(newDF[,c("Station","Lat","Long")])
	
	if(reverse){
		newDF$value <- -1*newDF$value
	}

	globalYRange <- range(newDF$value, na.rm = TRUE)
	globalYMiddle <- mean(globalYRange, na.rm = TRUE)
	globalXRange <- range(newDF$year, na.rm = TRUE)

	height = 0.2
	width = 0.3
	p <- ggmap(myMap) + coord_cartesian() + coord_fixed(ratio = 1.5) + theme(axis.text = element_text(size=12))
	pValueList <- list()

	for(i in 1:nrow(SU_locations)){
		station_ <- SU_locations[i,"Station"] %>% as.character()
		print(station_)
		
		subdf <- subset(newDF, Station == station_)
		subdf <- merge(subdf, data.frame(year = c(globalXRange[1]:globalXRange[2])), by = "year", all.y = TRUE)
		
		mid <- SU_locations[i,c("Long","Lat")] %>% as.numeric()

		model <- lm(value~year,data = na.omit(subdf[,c("year","value")]))
		pValue <- summary(model)$coefficients[2,4]

		pValueList[[station_]] <- c(p=pValue,alpha = model$coefficients["year"])
	
		# plot the dotted line
		p2 <- ggplot(subdf[,c("year","value")])
		p2 <- p2 + geom_line(aes(x = year,y = value),size=0.8) + 
				 geom_point(aes(x = year,y = value),size=1.5)
		
		localYRange <- range(subdf$value, na.rm = TRUE)

		if(trend){
			p2 <- p2 + geom_smooth (aes(x = year, y = value),method = "lm", alpha=0.4, linetype=0) + 
				stat_smooth (geom="line",aes(x = year, y = value),method = "lm",color = "red", size = 0.8, alpha = 0.5)
		}

		if(global){
			localYRange <- globalYRange	
			p2 <- p2 + geom_line(aes(x = x, y = y),data = data.frame(x = globalXRange, y = c(globalYMiddle,globalYMiddle)),linetype="dashed") # left boundary
		}
		
		p2 <- p2 + ylim(localYRange)

		# add the bounding box
		p2 <- p2 + geom_rect(aes(xmin = x1, xmax = x2, ymin = y1, ymax = y2),
												 data =data.frame(x1 = globalXRange[1], x2 = globalXRange[2], y1 = localYRange[1], y2 = localYRange[2]), fill = "NA", color="black", linetype = "dashed")
		# add theme
		p2 <- p2 + theme(axis.title.x=element_blank(), axis.text.x=element_blank(), axis.ticks.x=element_blank(),
			axis.title.y=element_blank(), axis.text.y=element_blank(), axis.ticks.y=element_blank(),
			panel.grid.major = element_blank(), panel.grid.minor = element_blank(), 
			panel.background = element_rect(fill = "transparent",colour = NA),
        	plot.background = element_rect(fill = "transparent",colour = NA),
			plot.margin = unit(c(0.1,0.1,0.1,0),"cm"))

		fname <- "tmp.png"
		png(fname, width = 80, height = 60)
		ggsave(fname, p2, bg = "transparent")
		dev.off()

		img <- readPNG(fname)
		g <- rasterGrob(img, interpolate=TRUE)
		
		p <- p + annotation_custom(g, xmin=mid[1]-width, xmax=mid[1]+width, ymin=mid[2]-height, ymax=mid[2]+height)
	}
	
	# save alpha and p
	data.frame(pValueList) %>% t() %>% data.frame() %>% write.csv(paste0(outputFile, "_pValues.csv"))
	
	png(paste0(outputFile, ".png"), width = 3000, height = 1500)
	print(p)
	dev.off()
}


plot_gly <- function(feature,variable, reverse = TRUE){
	# plot the gly plots
	feature <- arrange(feature,year)
	feature[,variable] <- ifelse(feature[,variable]<0,NA,feature[,variable])
	
	if(reverse){
		feature[,variable] <- -feature[,variable]
	}
	temp.gly <- glyphs(feature, "Long", "year", "Lat", variable , height=0.25,width = 0.5)
	
	pdf(sprintf("%s/%s_glymaps.pdf",outputFolder, variable),height = 5, width = 8)
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

# plot Figure 4. The gradients at the depth in LEP and UHY found in the operator's note
plotExpertDepthGradient <- function(featuresAtExpertDepths){
	data <- featuresAtExpertDepths[,c("LEP","UHY")]
	pdf(file.path(outputFolder, "Figure 4.pdf"), width = 5, height = 4)
	print(boxplot(data, outline = FALSE,  whisklty = 0, staplelty = 0, ylim = c(0, 0.4), ylab = "°C/meter"))
	dev.off()
}


