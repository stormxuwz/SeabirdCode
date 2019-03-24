# scripts to validate expert notes
require(Metrics)

lakeToPlotMapper <- list(
	ER = "(a) Lake Erie (ER)",
	HU = "(b) Lake Huron (HU) ",
	MI = "(c) Lake Michigan (MI)",
	ON = "(d) Lake Ontario (ON)",
	SU = "(e) Lake Superior (SU)"
)


addingFeatures_expertDiff <- function(features){
	features$TRM_diff <- features$TRM_segment-features$expert_TRM
	features$LEP_diff <- features$LEP_segment-features$expert_LEP
	features$UHY_diff <- features$UHY_segment-features$expert_UHY
	features$DCL_diff <- features$DCL_depth-features$expert_DCL
	
	return(features)
}


feature_stat <- function(df,varName = "TRM"){
	
	predVar <- paste(varName,"segment",sep = "_")
	
	if(varName == "DCL"){
		predVar <- "DCL_depth"
	}
	expertVar <- paste("expert",varName, sep = "_")
	
	diffVar <- paste(varName,"diff",sep ="_")
	
	for(lake_ in allLakes){
		data <- subset(df,lake==lake_)
		print("print difference with expert ")
		arrange_(data,sprintf("desc(abs(%s))",diffVar))[,c("site","year",diffVar,"fileId")]%>% head(20)%>%print()
	}
	
	print(tapply(df[,diffVar], df$lake, summary))
	
	expertExist <- !is.na(df[,expertVar])
	predExist <- !is.na(df[,predVar])
	
	df$only_pred <- predExist == TRUE & expertExist !=TRUE  # you only have expert
	df$only_expert <- predExist == FALSE & expertExist == TRUE # you only have predication
	df$pred_expert <- predExist == TRUE & expertExist == TRUE
	
	
	print(subset(df,only_expert)[,c("site","year","fileId",expertVar,diffVar,predVar)])
	
	print(varName)
	res <- group_by(df,lake) %>% summarise(totalN = n(),only_pred = sum(only_pred),only_expert = sum(only_expert),allExist = sum(pred_expert))
	print(res)
	
	pdf(sprintf("%s/%s_diff_meta.pdf",outputFolder,varName),height = 50, width = 30)
	print(qplot(lake,df[,diffVar],data = df)+geom_boxplot()+geom_text(aes(lake,df[,diffVar],label = paste(site,year)),data =df))
	dev.off()
	
	pdf(sprintf("%s/%s_diff.pdf",outputFolder,varName),height = 4, width = 7)
	print(
		qplot(lake,df[,diffVar],data = df)+geom_boxplot(size = 1)+theme_bw()+xlab("Lake")+ylab("Absolute Depth Differences (m)")
	)
	dev.off()

	pdf(sprintf("%s/%s_diff_NoOutlier.pdf",outputFolder,varName),height = 4, width = 7)
	print(
		boxplot(as.formula(paste(diffVar,"lake",sep="~")),data = df,outline = FALSE,xlab = "Lake",ylab = "Depth Differences")
	)
	dev.off()
}


scatterPlot2 <- function(features, lake_, note = FALSE){
	# functions to compare HMM and PLR

	if(lake_ != "all"){
		subFeatures <- subset(features, lake == lake_)
	}else{
		subFeatures <- features
	}

	TRMSub <- subFeatures[,c("year","site","expert_TRM","TRM_HMM")] %>% rename(Algorithm = TRM_HMM, Human = expert_TRM) %>% na.omit()
	LEPSub <- subFeatures[,c("year","site","expert_LEP","LEP_HMM")] %>% rename(Algorithm = LEP_HMM, Human = expert_LEP) %>% na.omit()
	UHYSub <- subFeatures[,c("year","site","expert_UHY","UHY_HMM")] %>% rename(Algorithm = UHY_HMM, Human = expert_UHY) %>% na.omit()

	# if(lake_ == "SU"){
		# UHYSub <- subset(UHYSub, year!= 2002)
	# }

	p_TRM <- ggplot(TRMSub) + 
		geom_point(aes(Human, Algorithm)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
		xlim(range(TRMSub[,c("Human","Algorithm")])) + ylim(range(TRMSub[,c("Human","Algorithm")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, RMSE: %.2f m^2)", "TRM", 
										cor(TRMSub[,c("Human","Algorithm")])[1,2]^2, rmse(TRMSub$Algorithm-TRMSub$Human)))

	if(note){
		p_TRM = p_TRM + geom_text(aes(Human,Algorithm, label = paste(year,site)))
	}


	p_LEP <- ggplot(LEPSub) + 
		geom_point(aes(Human, Algorithm)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
		xlim(range(LEPSub[,c("Human","Algorithm")])) + ylim(range(LEPSub[,c("Human","Algorithm")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, err: %.2f m^2)", "LEP", 
										cor(LEPSub[,c("Human","Algorithm")])[1,2]^2, rmse(LEPSub$Algorithm-LEPSub$Human)))

	if(note){
		p_LEP = p_LEP + geom_text(aes(Human,Algorithm, label = paste(year,site)))
	}	

	p_UHY <- ggplot(UHYSub) + 
		geom_point(aes(Human, Algorithm)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
		xlim(range(UHYSub[,c("Human","Algorithm")])) + ylim(range(UHYSub[,c("Human","Algorithm")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, err: %.2f m)", "UHY", 
										cor(UHYSub[,c("Human","Algorithm")])[1,2]^2, rmse(UHYSub$Algorithm-UHYSub$Human)))

	if(note){
		p_UHY = p_UHY + geom_text(aes(Human,Algorithm, label = paste(year,site)))
	}


	if(note){
		pdf(sprintf("%s/%s_algorithmScatterPlot_HMM_%s.pdf",outputFolder,lake_,note),height = 20, width = 20)
		print(grid.arrange(p_TRM, p_LEP, p_UHY, nrow = 2))
		dev.off()
	}else{
		pdf(sprintf("%s/%s_algorithmScatterPlot_HMM_%s.pdf",outputFolder,lake_,note),height = 6, width = 6)
		print(grid.arrange(p_TRM, p_LEP, p_UHY, nrow = 2))
		dev.off()
	}
}



scatterPlot <- function(features, lake_, note = FALSE){
	# functions to compare human and PLR

	if(lake_ != "all"){
		subFeatures <- subset(features, lake == lake_)
	}else{
		subFeatures <- features
	}
	
	

	TRMSub <- subFeatures[,c("year","site","expert_TRM","TRM_segment")] %>% rename(Algorithm = TRM_segment, Human = expert_TRM) %>% na.omit()
	LEPSub <- subFeatures[,c("year","site","expert_LEP","LEP_segment")] %>% rename(Algorithm = LEP_segment, Human = expert_LEP) %>% na.omit()
	UHYSub <- subFeatures[,c("year","site","expert_UHY","UHY_segment")] %>% rename(Algorithm = UHY_segment, Human = expert_UHY) %>% na.omit()
	DCLSub <- subFeatures[,c("year","site","expert_DCL","DCL_depth")] %>% rename(Algorithm = DCL_depth, Human = expert_DCL) %>% na.omit()

	# if(lake_ == "SU"){
		# UHYSub <- subset(UHYSub, year!= 2002)
	# }

	
	allSubs <- list(
		TRM = TRMSub,
		LEP = LEPSub,
		UHY = UHYSub,
		DCL = DCLSub
	)
	
	allP = list()
	
	for(subName in c("TRM","LEP","UHY","DCL")){
		data <- allSubs[[subName]]
		
		d_cor <- cor(data[,c("Human","Algorithm")])[1,2]^2 %>% sprintf("%.2f",.)
		d_rmse <- rmse(data$Algorithm,data$Human) %>% sprintf("%.1f",.)
		
		p <- ggplot(data) + 
			geom_point(aes(Human, Algorithm)) + 
			coord_fixed(ratio = 1) + theme_bw() + 
			geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
			xlim(range(data[,c("Human","Algorithm")])) + ylim(range(data[,c("Human","Algorithm")])) + 
			ggtitle(bquote(.(subName) ~" ("~r^2:~.(d_cor) ~"," ~"RMSE:"~.(d_rmse)~"m"~")")) + 
			theme(plot.title = element_text(size = 12, face = "bold"))
		
		allP[[subName]] <- p
	}
	
	if(lake_ == "SU"){
		if(note == FALSE){
			print("bug point")
		}
	}
	
	if(note){
		pdf(sprintf("%s/%s_algorithmScatterPlot_%s.pdf",outputFolder,lake_,note),height = 20, width = 20)
		print(grid.arrange(allP[[1]], allP[[2]], allP[[3]], allP[[4]], nrow = 2, 
											 bottom = textGrob(lakeToPlotMapper[[lake_]], gp=gpar(fontsize=15))
											 ))
		dev.off()
	}else{
		pdf(sprintf("%s/%s_algorithmScatterPlot_%s.pdf",outputFolder,lake_,note),height = 6, width = 6)
		print(grid.arrange(allP[[1]], allP[[2]], allP[[3]], allP[[4]], nrow = 2, 
											 bottom = textGrob(lakeToPlotMapper[[lake_]],gp=gpar(fontsize=15))
											 ))
		dev.off()
	}

}

main_expertValidation <- function(features){
	# only use data from 1998 to 2012
	features <- addingFeatures_expertDiff(features)
	feature_stat(features,varName = "DCL")
	feature_stat(features,varName = "TRM")
	feature_stat(features,varName = "UHY")
	feature_stat(features,varName = "LEP")

	# plot the comparision
	for(lake in allLakes){
		scatterPlot(features, lake)
		scatterPlot(features, lake, note = TRUE)
	}

	for(lake in c("all")){
		scatterPlot(features, lake)
		scatterPlot(features, lake, note = TRUE)
		# scatterPlot2(features, lake)
		# scatterPlot2(features, lake, note = TRUE)
	}
}


