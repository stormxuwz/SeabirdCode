# The script contains several scripts to plot

labeledBoxplot_ggplot <- function(df,diffVar,label = TRUE,outlier=TRUE){
	if(outlier){
		p <- qplot(lake,df[,diffVar],data = df)+geom_boxplot()
	}else{
		p <- qplot(lake,df[,diffVar],data = df)+geom_boxplot(outlier.shape = NA)+scale_y_continuous(limits = quantile(df[,diffVar], c(0.1, 0.9),na.rm = TRUE))
	}
	
	if(label){
		p <- p+	geom_text(aes(lake,df[,diffVar],label = paste(site,year)),data =df)
	}
	
	return(p)
}


boxplot_base <- function(df,diffVar, outlier = TRUE){
	df <- rename(df, value = ~diffVar)
	boxplot(TRM_diff~lake,data = subset(df, is.na(TRM_diff)<1),outline = FALSE)
}



