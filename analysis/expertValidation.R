# scripts to validate expert notes


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
	
	pdf(sprintf("../../output/%s_diff_meta.pdf",varName),height = 50, width = 30)
	print(qplot(lake,df[,diffVar],data = df)+geom_boxplot()+geom_text(aes(lake,df[,diffVar],label = paste(site,year)),data =df))
	dev.off()
	
	pdf(sprintf("../../output/%s_diff.pdf",varName),height = 4, width = 7)
	print(
		qplot(lake,df[,diffVar],data = df)+geom_boxplot(size = 1)+theme_bw()+xlab("Lake")+ylab("Absolute Depth Differences (m)")
	)
	dev.off()

	pdf(sprintf("../../output/%s_diff_NoOutlier.pdf",varName),height = 4, width = 7)
	print(
		boxplot(as.formula(paste(diffVar,"lake",sep="~")),data = df,outline = FALSE,xlab = "Lake",ylab = "Depth Differences")
	)
	dev.off()
}


scatterPlot2 <- function(features, lake_, note = FALSE){
	subFeatures <- subset(features, lake == lake_)

	TRMSub <- subFeatures[,c("year","site","expert_TRM","TRM_HMM")] %>% rename(Algorithm = TRM_HMM, Human = expert_TRM) %>% na.omit()
	LEPSub <- subFeatures[,c("year","site","expert_LEP","LEP_HMM")] %>% rename(Algorithm = LEP_HMM, Human = expert_LEP) %>% na.omit()
	UHYSub <- subFeatures[,c("year","site","expert_UHY","UHY_HMM")] %>% rename(Algorithm = UHY_HMM, Human = expert_UHY) %>% na.omit()

	if(lake_ == "SU"){
		UHYSub <- subset(UHYSub, year!= 2002)
	}

	p_TRM <- ggplot(TRMSub) + 
		geom_point(aes(Human, Algorithm)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
		xlim(range(TRMSub[,c("Human","Algorithm")])) + ylim(range(TRMSub[,c("Human","Algorithm")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, err: %.2f m)", "TRM", cor(TRMSub[,c("Human","Algorithm")])[1,2]^2, mean(TRMSub$Algorithm-TRMSub$Human)))

	if(note){
		p_TRM = p_TRM + geom_text(aes(Human,Algorithm, label = paste(year,site)))
	}


	p_LEP <- ggplot(LEPSub) + 
		geom_point(aes(Human, Algorithm)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
		xlim(range(LEPSub[,c("Human","Algorithm")])) + ylim(range(LEPSub[,c("Human","Algorithm")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, err: %.2f m)", "LEP", cor(LEPSub[,c("Human","Algorithm")])[1,2]^2, mean(LEPSub$Algorithm-LEPSub$Human)))

	if(note){
		p_LEP = p_LEP + geom_text(aes(Human,Algorithm, label = paste(year,site)))
	}	

	p_UHY <- ggplot(UHYSub) + 
		geom_point(aes(Human, Algorithm)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
		xlim(range(UHYSub[,c("Human","Algorithm")])) + ylim(range(UHYSub[,c("Human","Algorithm")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, err: %.2f m)", "UHY", cor(UHYSub[,c("Human","Algorithm")])[1,2]^2, mean(UHYSub$Algorithm-UHYSub$Human)))

	if(note){
		p_UHY = p_UHY + geom_text(aes(Human,Algorithm, label = paste(year,site)))
	}


	if(note){
		pdf(sprintf("../../output/%s_algorithmScatterPlot_HMM_%s.pdf",lake_,note),height = 20, width = 20)
		print(grid.arrange(p_TRM, p_LEP, p_UHY, nrow = 2))
		dev.off()
	}else{
		pdf(sprintf("../../output/%s_algorithmScatterPlot_HMM_%s.pdf",lake_,note),height = 6, width = 6)
		print(grid.arrange(p_TRM, p_LEP, p_UHY, nrow = 2))
		dev.off()
	}
}



scatterPlot <- function(features, lake_, note = FALSE){
	subFeatures <- subset(features, lake == lake_)

	TRMSub <- subFeatures[,c("year","site","expert_TRM","TRM_segment")] %>% rename(Algorithm = TRM_segment, Human = expert_TRM) %>% na.omit()
	LEPSub <- subFeatures[,c("year","site","expert_LEP","LEP_segment")] %>% rename(Algorithm = LEP_segment, Human = expert_LEP) %>% na.omit()
	UHYSub <- subFeatures[,c("year","site","expert_UHY","UHY_segment")] %>% rename(Algorithm = UHY_segment, Human = expert_UHY) %>% na.omit()
	DCLSub <- subFeatures[,c("year","site","expert_DCL","DCL_depth")] %>% rename(Algorithm = DCL_depth, Human = expert_DCL) %>% na.omit()

	if(lake_ == "SU"){
		UHYSub <- subset(UHYSub, year!= 2002)
	}

	p_TRM <- ggplot(TRMSub) + 
		geom_point(aes(Human, Algorithm)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
		xlim(range(TRMSub[,c("Human","Algorithm")])) + ylim(range(TRMSub[,c("Human","Algorithm")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, err: %.2f m)", "TRM", cor(TRMSub[,c("Human","Algorithm")])[1,2]^2, mean(TRMSub$Algorithm-TRMSub$Human)))

	if(note){
		p_TRM = p_TRM + geom_text(aes(Human,Algorithm, label = paste(year,site)))
	}


	p_LEP <- ggplot(LEPSub) + 
		geom_point(aes(Human, Algorithm)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
		xlim(range(LEPSub[,c("Human","Algorithm")])) + ylim(range(LEPSub[,c("Human","Algorithm")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, err: %.2f m)", "LEP", cor(LEPSub[,c("Human","Algorithm")])[1,2]^2, mean(LEPSub$Algorithm-LEPSub$Human)))

	if(note){
		p_LEP = p_LEP + geom_text(aes(Human,Algorithm, label = paste(year,site)))
	}	

	p_UHY <- ggplot(UHYSub) + 
		geom_point(aes(Human, Algorithm)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
		xlim(range(UHYSub[,c("Human","Algorithm")])) + ylim(range(UHYSub[,c("Human","Algorithm")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, err: %.2f m)", "UHY", cor(UHYSub[,c("Human","Algorithm")])[1,2]^2, mean(UHYSub$Algorithm-UHYSub$Human)))

	if(note){
		p_UHY = p_UHY + geom_text(aes(Human,Algorithm, label = paste(year,site)))
	}

	p_DCL <- ggplot(DCLSub) + 
		geom_point(aes(Human, Algorithm)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human (m)") + ylab("Algorithm (m)") + 
		xlim(range(DCLSub[,c("Human","Algorithm")])) + ylim(range(DCLSub[,c("Human","Algorithm")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, err: %.2f m)", "DCL", cor(DCLSub[,c("Human","Algorithm")])[1,2]^2, mean(DCLSub$Algorithm-DCLSub$Human)))

	

	if(note){
		p_DCL = p_DCL + geom_text(aes(Human,Algorithm, label = paste(year,site)))
	}



	UHY_DCL <- subFeatures[,c("year","site","expert_UHY","DCL_depth")] %>% rename(Human_UHY = expert_UHY, Algorithm_DCL = DCL_depth) %>% na.omit()
	p_UHY_DCL <- ggplot(UHY_DCL) + geom_point(aes(Human_UHY, Algorithm_DCL)) + 
		coord_fixed(ratio = 1) + theme_bw() + 
		geom_abline(intercept = 0, slope = 1) + xlab("Human UHY (m)") + ylab("Algorithm DCL (m)") + 
		xlim(range(UHY_DCL[,c("Human_UHY","Algorithm_DCL")])) + ylim(range(UHY_DCL[,c("Human_UHY","Algorithm_DCL")])) + 
		ggtitle(sprintf("%s (r^2:%.2f, err: %.2f m)", "UHY_DCL", cor(UHY_DCL[,c("Human_UHY","Algorithm_DCL")])[1,2]^2, mean(UHY_DCL$Human_UHY-UHY_DCL$Algorithm_DCL)))
		

	if(note){
		p_UHY_DCL = p_UHY_DCL + geom_text(aes(Human_UHY,Algorithm_DCL, label = paste(year,site)))
		pdf(sprintf("../../output/%s_algorithmScatterPlot_%s_UHYDCL.pdf",lake_,note),height = 10, width = 10)
		print(p_UHY_DCL)
		dev.off()
	}else{
		pdf(sprintf("../../output/%s_algorithmScatterPlot_%s_UHYDCL.pdf",lake_,note),height = 5, width = 5)
		print(p_UHY_DCL)
		dev.off()
	}


	if(note){
		pdf(sprintf("../../output/%s_algorithmScatterPlot_%s.pdf",lake_,note),height = 20, width = 20)
		print(grid.arrange(p_TRM, p_LEP, p_UHY, p_DCL, nrow = 2))
		dev.off()
	}else{
		pdf(sprintf("../../output/%s_algorithmScatterPlot_%s.pdf",lake_,note),height = 6, width = 6)
		print(grid.arrange(p_TRM, p_LEP, p_UHY, p_DCL, nrow = 2))
		dev.off()
	}
}

main_expertValidation <- function(features){
	# only use data from 1998 to 2012
	features <- subset(features, year < 2013 & year > 1997) 
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

	for(lake in allLakes){
		scatterPlot2(features, lake)
		scatterPlot2(features, lake, note = TRUE)
	}


}


