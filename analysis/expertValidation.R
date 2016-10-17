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
		arrange_(data,sprintf("desc(abs(%s))",diffVar))[,c("site","year",diffVar,"fileId")]%>%head(20)%>%print()
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

main_expertValidation <- function(features){
	features <- addingFeatures_expertDiff(features)
	feature_stat(features,varName = "DCL")
	feature_stat(features,varName = "TRM")
	feature_stat(features,varName = "UHY")
	feature_stat(features,varName = "LEP")
}


