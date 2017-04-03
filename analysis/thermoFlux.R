# bar plot timeseries for thermo-flux data
library(ggplot2)
library(reshape2)
library(dplyr)
library(gridExtra)

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



locations <- read.csv("../../input/station_loc.csv")
newDF <- merge(locations,df,by.x = "Station",by.y = "station") %>% na.omit()
newDF$Long <- -newDF$Long
newDF$fluxDiff <- newDF$summerSum_UHY-newDF$springSum_UHY

print(range(newDF$fluxDiff))
print(mean(range(newDF$fluxDiff)))
# plot_gly(newDF, "fluxDiff")
