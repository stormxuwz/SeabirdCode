# bar plot timeseries for thermo-flux data
library(ggplot2)
library(reshape2)
library(dplyr)
library(gridExtra)

setwd("/Users/wenzhaoxu/Developer/Seabird/SeabirdCode/analysis/")
source("plot.R")

df <- read.csv("/Users/wenzhaoxu/Developer/Seabird/SeabirdCode/thermoFlux_SU_new.csv")%>% subset(year>1997)

stations <- unique(df$station)

for(station_ in stations){
	subdf <- subset(df, station == station_)
	
	model1 <- lm(summerSum_LEP-springSum_LEP~year,data = subdf[,c("year","summerSum_LEP","springSum_LEP")] %>% na.omit())
	pValue1 <- summary(model1)$coefficients[2,4]

	model2 <- lm(summerSum_UHY-springSum_UHY~year,data = subdf[,c("year","summerSum_UHY","springSum_UHY")] %>% na.omit())
	pValue2 <- summary(model2)$coefficients[2,4]
	
	model3 <- lm(summerSum_bottom-springSum_bottom~year,data = subdf[,c("year","summerSum_bottom","springSum_bottom")] %>% na.omit())
	pValue3 <- summary(model3)$coefficients[2,4]
	
	minDepth0 = unique(subdf$minDepth)
	maxDepth0 = unique(subdf$maxDepth)
	
	p1 <- ggplot(subdf[,c("year","summerSum_LEP","springSum_LEP")] %>% na.omit())
	p1 <- p1 + geom_bar(aes(x = year,y = summerSum_LEP),fill = "red",stat="identity")
	p1 <- p1 + geom_bar(aes(x = year,y = springSum_LEP),fill = "blue4",stat="identity")
	p1 <- p1 + geom_line(aes(x = year,y = summerSum_LEP - springSum_LEP))+geom_point(aes(x = year,y = summerSum_LEP - springSum_LEP))
	p1 <- p1 + ggtitle(sprintf("Above LEP, %s, depth range: [%.2f, %.2f], p value of the trend: %.2f", station_, 
														 minDepth0, maxDepth0, round(pValue1,2)))+ylab("Temperature sum above LEP")
	p1 <- p1 + stat_smooth(aes(x = year, y = summerSum_LEP-springSum_LEP),method = "lm")
	
	p2 <- ggplot(subdf[,c("year","summerSum_UHY","springSum_UHY")] %>% na.omit())
	p2 <- p2 + geom_bar(aes(x = year,y = summerSum_UHY),fill = "red",stat="identity")
	p2 <- p2 + geom_bar(aes(x = year,y = springSum_UHY),fill = "blue4",stat="identity")
	p2 <- p2 + geom_line(aes(x = year,y = summerSum_UHY - springSum_UHY))+geom_point(aes(x = year,y = summerSum_UHY - springSum_UHY))
	p2 <- p2 + ggtitle(sprintf("Above UHY, %s, depth range: [%.2f, %.2f], p value of the trend: %.2f", station_,
														 minDepth0, maxDepth0, round(pValue2,2)))+ylab("Temperature sum above UHY")
	p2 <- p2 + stat_smooth(aes(x = year, y = summerSum_UHY-springSum_UHY),method = "lm")
	
	
	p3 <- ggplot(subdf[,c("year","summerSum_bottom","springSum_bottom")] %>% na.omit())
	p3 <- p3 + geom_bar(aes(x = year,y = summerSum_bottom),fill = "red",stat="identity")
	p3 <- p3 + geom_bar(aes(x = year,y = springSum_bottom),fill = "blue4",stat="identity")
	p3 <- p3 + geom_line(aes(x = year,y = summerSum_bottom - springSum_bottom))+geom_point(aes(x = year,y = summerSum_bottom - springSum_bottom))
	p3 <- p3 + ggtitle(sprintf("Above bottom, %s, depth range: [%.2f, %.2f], p value of the trend: %.2f", station_,
														 minDepth0, maxDepth0, round(pValue3,2)))+ylab("Temperature sum above sampling bottom")
	p3 <- p3 + stat_smooth(aes(x = year, y = summerSum_bottom-springSum_bottom),method = "lm")
	
	png(paste0("./flux/",station_,"_thermo_flux.png"), width = 1500, height = 500)
	print(grid.arrange(p1,p2,p3,nrow = 1,ncol = 3))
	dev.off()
}


plot_gly_on_map <- function(newDF, global = FALSE, trend = FALSE, outputFile = "test.png"){
	# newDF$value <- newDF$summerSum_UHY - newDF$springSum_UHY
	longRange <- range(newDF$Long)
	latRange <- range(newDF$Lat)
	bbox <- make_bbox(longRange,latRange,f = 0.3)
	# myMap <- get_map(location=bbox, source="stamn",crop=TRUE,color="bw",maptype="terrain")
	myMap <- get_map(location = bbox, maptype="toner-lite", source="stamen",zoom=7,color = "bw",crop=TRUE)
	# ggmap(myMap)
	SU_locations <- unique(newDF[,c("Station","Lat","Long")])
	
	library(png)
	library(grid)

	globalYRange <- range(newDF$value)
	globalYMiddle <- mean(globalYRange)

	globalXRange <- range(newDF$year)

	height = 0.2
	width = 0.3
	p <- ggmap(myMap) + coord_cartesian() + coord_fixed(ratio = 1.5) + theme(axis.text = element_text(size=12))

	for(i in 1:nrow(SU_locations)){
		station_ <- SU_locations[i,"Station"]
		subdf <- subset(newDF, Station == station_)
		mid <- SU_locations[i,c("Long","Lat")] %>% as.numeric()

		model2 <- lm(value~year,data = subdf[,c("year","value")] %>% na.omit())
		pValue2 <- summary(model2)$coefficients[2,4]
		
		p2 <- ggplot(subdf[,c("year","value")] %>% na.omit())
		# p2 <- p2 + geom_bar(aes(x = year,y = summerSum_UHY),fill = "red",stat="identity")
		# p2 <- p2 + geom_bar(aes(x = year,y = springSum_UHY),fill = "blue4",stat="identity")
		p2 <- p2 + geom_line(aes(x = year,y = value),size=0.8) + 
				 geom_point(aes(x = year,y = value),size=2)
		
		localYRange <- range(subdf$value)

		if(trend){
			p2 <- p2 + stat_smooth(aes(x = year, y = value),method = "lm",color = "red")
		}

		if(global){
			localYRange <- globalYRange	
			p2 <- p2 + geom_line(aes(x = x, y = y),data = data.frame(x = globalXRange, y = c(globalYMiddle,globalYMiddle)),linetype="dashed") # left boundary
		}
		
		p2 <- p2 + ylim(localYRange)

		# add the bounding box
		p2 <- p2 + geom_rect(aes(xmin = x1, xmax = x2, ymin = y1, ymax = y2),data =data.frame(x1 = globalXRange[1], x2 = globalXRange[2], y1 = localYRange[1], y2 = localYRange[2]), fill = "NA", color="black", linetype = "dashed")

		# add theme
		p2 <- p2 + theme(axis.title.x=element_blank(), axis.text.x=element_blank(), axis.ticks.x=element_blank(),
			axis.title.y=element_blank(), axis.text.y=element_blank(), axis.ticks.y=element_blank(),
			panel.grid.major = element_blank(), panel.grid.minor = element_blank(), 
			panel.background = element_rect(fill = "transparent",colour = NA),
        	plot.background = element_rect(fill = "transparent",colour = NA),
        	# panel.border = element_rect(linetype = "dashed", fill = NA),
			plot.margin = unit(c(0.1,0.1,0.1,0),"cm"))

		# fname <- paste0("./flux/",station_ ,"_thermo_flux.png")
		fname <- "tmp.png"
		# png(fname, width = 80, height = 60)
		# print(p2)
		# dev.off()
		png(fname, width = 80, height = 60)
		ggsave(fname, p2, bg = "transparent")
		dev.off()

		img <- readPNG(fname)
		g <- rasterGrob(img, interpolate=TRUE)
		
		p <- p + annotation_custom(g, xmin=mid[1]-width, xmax=mid[1]+width, ymin=mid[2]-height, ymax=mid[2]+height)
	}
	png(outputFile, width = 3000, height = 1500)
	print(p)
	dev.off()
}



locations <- read.csv("/Users/wenzhaoxu/Developer/Seabird//input/station_loc.csv")
newDF <- merge(locations,df,by.x = "Station",by.y = "station") %>% na.omit()
newDF$Long <- -newDF$Long
newDF$value <- newDF$summerSum_UHY-newDF$springSum_UHY

plot_gly_on_map(newDF, outputFile = "test.png")
# print(range(newDF$fluxDiff))
# print(mean(range(newDF$fluxDiff)))
# plot_gly(newDF, "fluxDiff")
