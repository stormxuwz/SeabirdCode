extractSite<-function(meta){
	fullPath=as.character(meta[,2])
	meta[,3]=fullPath

	meta[,4]=0
	meta[,5]=fullPath
	for(i in 1:length(fullPath)){
		tmp=basename(fullPath[i])
		tmp=unlist(strsplit(tmp,"[.]"))
		tmp=unlist(strsplit(tmp,"_"))
		meta[i,3]=substr(tmp[1],1,4)
		meta[i,4]=as.numeric(tmp[2])
		meta[i,5]=substr(tmp[1],1,2)
		names(meta)[3:5]=c("Station","Year","Lake")
	}
	return(meta)
}

# # Check whether files are from 1996 to 2013
# files <- list.files(path="~/Developer/Project_IO/Seabird/csvFile/", pattern="*.csv", full.names=T, recursive=FALSE)
# meta=as.data.frame(files)
# fullPath=as.character(meta[,1])
# meta[,2]=fullPath
# meta[,3]=0
# meta[,4]=fullPath
# for(i in 1:length(files)){
# 		tmp=basename(files[i])
# 		tmp=unlist(strsplit(tmp,"[.]"))
# 		tmp=unlist(strsplit(tmp,"_"))
# 		meta[i,2]=tmp[1]
# 		meta[i,3]=as.numeric(tmp[2])
# 		meta[i,4]=substr(tmp[1],1,2)
# 	}

# table(meta[,2])

checkYear<-function(site){
	files_site=subset(meta,V2==site)
	missing=0
	missingYear=c()
	for(year in c(1996:2013)){
		if(sum(files_site[,3]==year)==0){
			missingYear=c(missingYear,year)
		}
	}
	return(missingYear)
}


sink("~/Desktop/missing_year.txt")
for(site in unique(meta[,2])){
	lake=substr(site,1,2)
	if(any(c("ER","MI","SU","HU","ON") %in% lake)){
		missing=checkYear(site)
		

		if(length(missing)>0){
			missing=c(site,missing)
			# print(missing)
			cat(missing)
			cat("\n")
			# print("/n")
		}
	}
}
sink()

combine<-function(feature,station_loc){
	feature$Long=-99
	feature$Lat=-99
	for(i in 1:nrow(station_loc)){
		station=as.character(station_loc[i,1])
		long=station_loc[i,3]
		lat=station_loc[i,2]
		# print(station)
		feature[feature$Station==station,"Long"]=long
		feature[feature$Station==station,"Lat"]=lat
	}
	return(feature)
}

spatial_temporal_plot<-function(featureMatrix,var,valueGTzero=T){
	library(ggmap)
	for(lake in c("SU","HU","ER")){
	# for(lake in c("MI")){
		Lake_data<-subset(featureMatrix,Lake==lake)
		Lake_data[,var]<-ifelse(Lake_data[,var]==-99,NA,Lake_data[,var])
		max_var=max(Lake_data[Lake_data$Long>0,var],na.rm=T)
		min_var=min(Lake_data[Lake_data$Long>0,var],na.rm=T)
		
		for(year in c(1996:2013)){
			lake_year_data<-subset(Lake_data,Year==year & Long>0)
			lake_year_data<-lake_year_data[,c(var,"Long","Lat","Station")]
			names(lake_year_data)[1]="value"
			

			if(nrow(lake_year_data)==0){
				print(year);
				next
			}

			lake_year_data$Long=-lake_year_data$Long

			p=ggmap(lake_base_map[[lake]])+geom_point(aes(Long,Lat),data=lake_year_data,color="grey50",size=6.5)+geom_text(aes(x=Long,y=Lat,label=substr(Station,3,4)),data=lake_year_data,color="black",size=3)

			print(p)
			
			if(valueGTzero==T)
				lake_year_data<-subset(lake_year_data,value>0)

			lake_year_data=na.omit(lake_year_data)
			
			if(valueGTzero==T){
				p=p+geom_point(aes(Long,Lat,color=value,label=value),data=lake_year_data,size=6.5)+scale_color_gradientn(colours = topo.colors(10),limits=c(min_var,max_var))+geom_text(aes(x=Long,y=Lat,label=round(value,3)),data=lake_year_data,size=2,vjust=-1.3,color="black")+geom_text(aes(x=Long,y=Lat,label=substr(Station,3,4)),data=lake_year_data,color="black",size=3)+theme(plot.margin=unit(c(-10,-0.3,-10,-0.15),"cm"))+ggtitle(year)
			}else{
				p=p+geom_point(aes(Long,Lat,color=value,label=value),data=lake_year_data,size=6.5)+scale_color_gradient2(mid="white",high="blue4",low="red",midpoint=0,limits=c(min_var,max_var))+geom_text(aes(x=Long,y=Lat,label=round(value,3)),data=lake_year_data,size=2,vjust=-1.3,color="black")+geom_text(aes(x=Long,y=Lat,label=substr(Station,3,4)),data=lake_year_data,color="black",size=3)+theme(plot.margin=unit(c(-1,-0.5,-1,-0.5),"cm"))+ggtitle(year)
			}
			
			if(lake=="SU"){	
				png(paste("./summary/",lake,"_",year,"_",var,".png",sep=""),width=300*8,height=300*4.5,res=2*200)
					print(p)
				dev.off()
			}
			else if(lake=="HU")
			{
				png(paste("./summary/",lake,"_",year,"_",var,".png",sep=""),width=300*8,height=300*7,res=2*200)
					print(p+theme(plot.margin=unit(c(-0.5,-0.1,-0.5,-0.1),"cm")))
				dev.off()
			}
			else if(lake=="ER"){
				png(paste("./summary/",lake,"_",year,"_",var,".png",sep=""),width=300*8,height=300*4.5,res=2*200)
					print(p+theme(plot.margin=unit(c(-0.5,-0.1,-0.5,-0.1),"cm")))
				dev.off()		
			}
		}
	}
}




create_base_map<-function(){
	library(ggmap)
	map_range=read.csv("~/Developer/Seabird/newcode/map_range.csv",header=F)
	lake_base_map<-list()
	for(i in 1:5)
		print(i)
		lake_base_map[[i]]<-get_map(location=as.numeric(map_range[i,2:5]),source="osm")

	names(lake_base_map)<-c("MI","HU","ER","SU","ON")
	return(lake_base_map)
}





meta_expert=read.csv("~/Developer/Seabird/data_expert.csv",header=F)
meta_noExpert=read.csv("~/Developer/Seabird/data_noexpert.csv",header=F)
meta_noExpert$V2=meta_noExpert$V1

meta_noExpert<-extractSite(meta_noExpert)
meta_expert<-extractSite(meta_expert)


feature=read.csv("~/Developer/Seabird/Feature_compare.csv",header=T)
feature_no_expert=read.csv("~/Developer/Seabird/Feature_noExpert.csv",header=T)

feature<-cbind(feature,meta_expert[,3:5])
feature_no_expert<-cbind(feature_no_expert,meta_noExpert[,3:5])

feature_full<-rbind(feature,feature_no_expert)


station_loc=read.csv("~/Developer/Seabird/station_loc.csv")
lake_base_map<-readRDS("lake_base_map.rds")
feature_full<-combine(feature_full,station_loc)


# Change Station Name here !!!!!
feature_full[feature_full$Station=="S21B","Station"]="SU21"
feature_full[feature_full$Station=="S22B","Station"]="SU22"

feature_full$outlier=0
feature_full[feature_full$Station=="SU08" & feature_full$Year==1996,"outlier"]=1

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Distance between from THM to DCL
feature_full$THM2DCL=NA

for(i in (1:(nrow(feature_full)-2)))
{
	if(feature_full[i,"Algo_DCL_depth"]>0 & feature_full[i,"Algo_HMM_thm"]>0)
		feature_full[i,"THM2DCL"]<-feature_full[i,"Algo_DCL_depth"]-feature_full[i,"Algo_HMM_thm"]
}


# Difference of THM between algo and expert
feature_full$THM_diff=NA

for(i in (1:(nrow(feature_full)-2)))
{
	if(feature_full[i,"Algo_HMM_thm"]>0 & feature_full[i,"Expert_thm"]>0)
		feature_full[i,"THM_diff"]<-feature_full[i,"Algo_HMM_thm"]-feature_full[i,"Expert_thm"]
}


# Difference between from  
feature_full$DCL_diff=NA

for(i in (1:(nrow(feature_full)-2)))
{
	if(feature_full[i,"Algo_DCL_depth"]>0 & feature_full[i,"Expert_DCL_depth"]>0)
		feature_full[i,"DCL_diff"]<-feature_full[i,"Algo_DCL_depth"]-feature_full[i,"Expert_DCL_depth"]
}

# Peak Size
feature_full$peak_size=NA

for(i in (1:(nrow(feature_full)-2)))
{
	if(feature_full[i,"B0_bottom_depth"]>0 & feature_full[i,"B0_Up_depth"]>0)
		feature_full[i,"peak_size"]<-feature_full[i,"B0_bottom_depth"]-feature_full[i,"B0_Up_depth"]
}

# Peak Shape
feature_full$peak_shape=NA

for(i in (1:(nrow(feature_full)-2)))
{
	if(feature_full[i,"B0_bottom_depth"]>0 & feature_full[i,"B0_Up_depth"]>0)
		feature_full[i,"peak_shape"]<-(feature_full[i,"B0_bottom_depth"]-feature_full[i,"Algo_DCL_depth"])/(feature_full[i,"Algo_DCL_depth"]-feature_full[i,"B0_Up_depth"])
}

# DCL to UHY

feature_full$DCL2UHY=NA

for(i in (1:(nrow(feature_full)-2)))
{
	if(feature_full[i,"Algo_DCL_depth"]>0 & feature_full[i,"Algo_HMM_hyp"]>0)
		feature_full[i,"DCL2UHY"]<-feature_full[i,"Algo_DCL_depth"]-feature_full[i,"Algo_HMM_hyp"]
}


feature_full$peak_chl_diff=NA

for(i in (1:(nrow(feature_full)-2)))
{
	if(feature_full[i,"B0_bottom_depth"]>0 & feature_full[i,"B0_Up_depth"]>0)
		feature_full[i,"peak_shape"]<-(feature_full[i,"B0_bottom_depth"]-feature_full[i,"Algo_DCL_depth"])/(feature_full[i,"Algo_DCL_depth"]-feature_full[i,"B0_Up_depth"])
}


# boxplot(DCL_diff~Lake,data=subset(feature_full,DCL_diff>0),outline=FALSE,xlab="Lake",ylab="Depth Differences")

require(gridExtra)

par(mfrow=c(1,2))
boxplot(DCL_diff~Lake,data=feature_full[is.na(feature_full$DCL_diff)==0,],xlab="Lake",ylab="Depth Differences (m)")
boxplot(DCL_diff~Lake,data=feature_full[is.na(feature_full$DCL_diff)==0,],outline=FALSE,xlab="Lake",ylab="Depth Differences (m)")


boxplot(Algo_DCL_depth~Station,data=subset(SU_feature,Algo_DCL_depth>0 & Station!="SUP1" & Station!="SUFO"))
boxplot(Algo_DCL_Conc~Station,data=subset(SU_feature,Algo_DCL_depth>0 & Station!="SUP1" & Station!="SUFO"))


general_p<-ggplot(data=subset(SU_feature,Algo_DCL_depth>0 & Station!="SUP1" & Station!="SUFO"))

# qrcp.df = ddply(.data = SU_feature, .variables = .(Station), transform,
#     lQntl = quantile(Algo_DCL_depth, probs = 0.25, na.rm = TRUE),
#     uQntl = quantile(Algo_DCL_depth, probs = 0.75, na.rm = TRUE))


# ## Compute the lower and upper bound which defines the outlier
# brcp.df = ddply(.data = qrcp.df, .variables = .(UNSD_MACRO_REG), transform,
#     lBound = lQntl - 1.5 * (uQntl - lQntl),
#     uBound = uQntl + 1.5 * (uQntl - lQntl))


general_depth<-general_p+geom_boxplot(aes(Station,Algo_DCL_depth))+ylab("DCL Depth (m)")+theme(axis.text.x = element_text(angle = 45, hjust = 1))
general_Conc<-general_p+geom_boxplot(aes(Station,Algo_DCL_Conc))+ylab("DCL Fluorescence Conc (ug/L)")+theme(axis.text.x = element_text(angle = 45, hjust = 1))

grid.arrange(general_depth,general_Conc)

# # Old Code
# meta=extractSite(meta)
# meta[,5]=as.factor(meta[,5])
# names(meta)=c("csvFile","ExpertFile","Station","Year","Lake")
# feature=cbind(feature,meta)


# DCL_expert=feature[feature$Expert_DCL_depth>0,]
# myDCL=DCL_expert[DCL_expert$DCL_peakNum>0,]

# myDCL_multiplePeak=myDCL[myDCL$DCL_peakNum>1,]
# myDCL_onePeak=myDCL[myDCL$DCL_peakNum==1,]

# library(ggplot2)



# boxplot_diff_expert<-ggplot(myDCL, aes(Lake, DCL_depth-Expert_DCL_depth))+ geom_boxplot()+xlab("Lake")+ylab("Depth Differences (Algorithm-Expert)")+geom_text(aes(label = paste(Station,Year)),data=subset(myDCL,abs(DCL_depth-Expert_DCL_depth)>5),size=2.5,hjust=-0.2,angle=0)
# boxplot_diff_expert
# pdf("diff_with_expert.pdf",height=8)
# print(boxplot_diff_expert)
# dev.off()


# boxplot_diff_expert_noOutlier<-ggplot(myDCL, aes(Lake, DCL_depth-Expert_DCL_depth))+ geom_boxplot(outlier.colour = NA)+xlab("Lake")+ylab("Depth Differences (Algorithm-Expert)")+ylim(c(-5,5))
# boxplot_diff_expert_noOutlier
# pdf("diff_with_expert_noOutlier.pdf",height=8)
# print(boxplot_diff_expert_noOutlier)
# dev.off()


# feature_DCL=subset(feature,DCL_depth>0)

# ggplot(subset(feature_DCL,Lake=="HU" & Station %in% c("HU06","HU09","HU12","HU15M","HU27","HU32","HU37","HU38") ),aes(x = Year, y = DCL_conc, fill = Station))+geom_bar(stat = "identity", position = "stack")+scale_fill_brewer(palette = "Set1")

# ggplot(subset(feature_DCL,Lake=="HU" & Station %in% c("HU45M","HU53","HU54M","HU61","HU93","HUFE","HUFO") ),aes(x = Year, y = DCL_conc, fill = Station))+geom_bar(stat = "identity", position = "stack")+scale_fill_brewer(palette = "Set1")

# cols<-c("1"="black","2"="cornflowerblue","3"="chartreuse3","4"="purple","5"="orange","6"="yellow")


# ggplot(subset(feature,Lake=="HU" & Station %in% c("HU06","HU09","HU12","HU15M","HU27","HU32","HU37","HU38") ),aes(x = Year, y = DCL_peakNum, fill = Station))+geom_bar(stat = "identity", position = "stack")+scale_fill_brewer(palette = "Set1")

# ggplot(subset(feature,Lake=="HU" & Station %in% c("HU45M","HU53","HU54M","HU61","HU93","HUFE","HUFO") ),aes(x = Year, y = Surface_Chl, fill = Station))+geom_bar(stat = "identity", position = "stack")+scale_fill_brewer(palette = "Set1")

# ggplot(subset(feature,Lake=="HU" & Station %in% c("HU45M","HU53","HU54M","HU61","HU93","HUFE","HUFO") ),aes(x = Year, y = Surface_Chl, color = Station))+geom_line()+geom_point()

# qplot(Year,factor(Station),data=subset(feature_DCL,Lake=="HU"),color=factor(DCL_peakNum),size=DCL_conc,label=as.character(index_peak_index))+theme(axis.text.x=element_text(angle=45,hjust=1))+geom_text(aes(label = as.character(index_peak_index)))+ylab("DCL Concentration (m)")+scale_colour_manual(values=cols,name="Number of Peaks")+xlab("Station")



# lake="SU"


# a=by(feature_DCL, feature_DCL$Station, function(X) X[which.max(X$DCL_depth),])

# qplot(Year,factor(Station),data=subset(feature_DCL,Lake==lake),color=DCL_conc,size=DCL_depth)+theme(axis.text.x=element_text(angle=45,hjust=1))+geom_text(aes(label = paste(as.character(index_peak_index+1),as.character(DCL_peakNum),sep="/")),data=subset(feature_DCL,Lake==lake & DCL_peakNum>1),size=2.5,hjust=-0.8,angle=0,color="black")+ylab("Station")+xlab("Year")+scale_color_gradient2(midpoint=mean(subset(feature_DCL,Lake==lake)$DCL_conc),mid="yellow",low="green",high="red")+scale_x_continuous(breaks=seq(from = 1996,to = 2011, by=1))



# ggplot(subset(feature_DCL,Lake=="HU"),aes(x = Year, y = DCL_depth, fill = Station))+geom_bar(stat = "identity", position = "stack")+scale_fill_brewer(palette = "Set1")
# 
# ggplot(subset(feature,Lake=="HU"),aes(x = Year, y = DCL_depth, fill = Station))+geom_bar(stat = "identity", position = "stack")+scale_fill_brewer(palette = "Set1")

# boxplot_conc <- ggplot(feature_DCL, aes(Lake, DCL_conc))+ geom_boxplot()+xlab("Lake")+ylab("DCL Concentration")+geom_text(aes(label = paste(Station,Year)),data=subset(feature_DCL,abs(DCL_conc)>10),size=2.5,hjust=-0.2,angle=0)
# boxplot_conc
	

# boxplot_depth <- ggplot(feature_DCL, aes(Lake, DCL_depth))+ geom_boxplot()+xlab("Lake")+ylab("DCL Depth")
# boxplot_depth


# boxplot_diff_thm_DCL<-ggplot(myDCL,aes(Lake,DCL_depth-Algo_full_thm))+geom_boxplot()+xlab("Lake")+ylab("Depth Differences of (DCL-THM)")
# boxplot_diff_thm_DCL


# boxplot_diff_Bo<-ggplot(myDCL_onePeak,aes(Lake,B0_down_depth-B0_up_depth))+geom_boxplot()

# boxplot_diff_SurBom<-ggplot(myDCL_onePeak,aes(Lake,B0_down-B0_up))+geom_boxplot()

# barplot_multiple<-ggplot(myDCL_multiplePeak,aes(factor(Station)))+geom_bar()+theme(axis.text.x = element_text(angle = 90, hjust = 1))






# ER=subset(myDCL,Lake=="ER")
# MI=subset(myDCL,Lake=="MI")
# HU=subset(myDCL,Lake=="HU")
# SU=subset(myDCL,Lake=="SU")
# ON=subset(myDCL,Lake=="ON")

# cols<-c("1"="black","2"="cornflowerblue","3"="chartreuse3","4"="purple","5"="orange","6"="yellow")

# plot_Lake<-function(lake="MI"){
# 	peakSize=qplot(factor(Station),B0_down_depth-B0_up_depth,data=subset(feature_DCL,Lake==lake),label=Year,color=factor(DCL_peakNum))+geom_text(size=2.5,hjust=-0.2,angle=0)+theme(axis.text.x=element_text(angle=45,hjust=1))+ylab("Peak Size (m)")+scale_colour_manual(values=cols,name="Number of Peaks")+xlab("Station")
	
# 	B0_diff=qplot(factor(Station),B0_up-B0_down,data=subset(feature_DCL,Lake==lake),label=Year,color=factor(DCL_peakNum))+geom_text(size=2.5,hjust=-0.2,angle=0)+theme(axis.text.x=element_text(angle=45,hjust=1))+ylab("Concentration of Peak_top-Peak_bottom")+scale_colour_manual(values=cols,name="Number of Peaks")+xlab("Station")
	
# 	PeakLocation=qplot(factor(Station),Year,data=subset(feature_DCL,Lake==lake),label=Year,color=factor(index_peak_index))+geom_text()+theme(axis.text.x = element_text(angle = 45, hjust = 1))+scale_colour_manual(values=cols,name="Number of Peaks")
	
# 	ratio=qplot(factor(Station),(B0_down_depth-DCL_depth)/(DCL_depth-B0_up_depth),data=subset(feature_DCL,Lake==lake),label=Year,color=factor(DCL_peakNum))+geom_text(size=2.5,hjust=-0.2,angle=0)+theme(axis.text.x=element_text(angle=45,hjust=1))+ylab("Peak Bottom Range/Peak Top Range")+scale_colour_manual(values=cols,name="Number of Peaks")+xlab("Station")+geom_hline(yintercept=1,alpha=0.5,linetype=4)


# 	B0_up_depth=qplot(factor(Station),B0_up_depth,data=subset(feature_DCL,Lake==lake),label=Year,color=factor(DCL_peakNum))+geom_text(size=2.5,hjust=-0.2,angle=0)+theme(axis.text.x=element_text(angle=45,hjust=1))+ylab("Peak Forming Depth")+scale_colour_manual(values=cols,name="Number of Peaks")+xlab("Station")

# 	DCL=qplot(factor(Station),DCL_depth,data=subset(feature_DCL,Lake==lake),label=Year,color=factor(DCL_peakNum))+geom_text(size=2.5,hjust=-0.2,angle=0)+theme(axis.text.x=element_text(angle=45,hjust=1))+ylab("DCL depth")+scale_colour_manual(values=cols,name="Number of Peaks")+xlab("Station")

# 	DCL_conc=qplot(factor(Station),DCL_conc,data=subset(feature_DCL,Lake==lake),label=Year,color=factor(DCL_peakNum))+geom_text(size=2.5,hjust=-0.2,angle=0)+theme(axis.text.x=element_text(angle=45,hjust=1))+ylab("DCL Concentration")+scale_colour_manual(values=cols,name="Number of Peaks")+xlab("Station")

# 	pdf(paste("./plot/PeakSize_",lake,".pdf",sep=""),width=10,height=5)
# 	print(peakSize)
# 	dev.off()

# 	pdf(paste("./plot/ratio_",lake,".pdf",sep=""),width=10,height=5)
# 	print(ratio)
# 	dev.off()

# 	pdf(paste("./plot/B0_up_depth_",lake,".pdf",sep=""),width=10,height=5)
# 	print(B0_up_depth)
# 	dev.off()

# 	pdf(paste("./plot/B0_diff_",lake,".pdf",sep=""),width=10,height=5)
# 	print(B0_diff)
# 	dev.off()

# 	pdf(paste("./plot/DCL_depth_",lake,".pdf",sep=""),width=10,height=5)
# 	print(DCL)
# 	dev.off()

# 	pdf(paste("./plot/DCL_conc_",lake,".pdf",sep=""),width=10,height=5)
# 	print(DCL_conc)
# 	dev.off()
# }


# for (name in c("MI","ER","HU","SU","ON"))
# 	plot_Lake(name)







# qplot(factor(Station),B0_down_depth-B0_up_depth,data=SU,label=Year,color=factor(DCL_peakNum))+geom_text()
# qplot(factor(Station),B0_down_depth-B0_up_depth,data=MI,label=Year,color=factor(DCL_peakNum))+geom_text()
# qplot(factor(Station),B0_down_depth-B0_up_depth,data=HU,label=Year,color=factor(DCL_peakNum))+geom_text()
# qplot(factor(Station),B0_down_depth-B0_up_depth,data=ON,label=Year,color=factor(DCL_peakNum))+geom_text()
# qplot(factor(Station),B0_down_depth-B0_up_depth,data=ER,label=Year,color=factor(DCL_peakNum))+geom_text()







# qplot(factor(Station),B0_down_depth-B0_up_depth,data=subset(feature,Lake=="ER"),label=Year,color=factor(DCL_peakNum))+geom_text()+theme(axis.text.x = element_text(angle = 90, hjust = 1))
# qplot(factor(Station),B0_down_depth-B0_up_depth,data=subset(feature,Lake=="MI"),label=Year,color=factor(DCL_peakNum>2))+geom_text()+theme(axis.text.x = element_text(angle = 90, hjust = 1))
# qplot(factor(Station),B0_down_depth-B0_up_depth,data=subset(feature,Lake=="SU"),label=Year,color=factor(DCL_peakNum>2))+geom_text()+theme(axis.text.x = element_text(angle = 90, hjust = 1))
# qplot(factor(Station),B0_down_depth-B0_up_depth,data=subset(feature,Lake=="ON"),label=Year,color=factor(DCL_peakNum>2))+geom_text()+theme(axis.text.x = element_text(angle = 90, hjust = 1))
# qplot(factor(Station),B0_down_depth-B0_up_depth,data=subset(feature,Lake=="HU"),label=Year,color=factor(DCL_peakNum>2))+geom_text()+theme(axis.text.x = element_text(angle = 90, hjust = 1))



# qplot(factor(Station),(B0_down_depth-DCL_depth)/(DCL_depth-B0_up_depth),data=subset(feature,Lake=="ER" & DCL_depth>0),label=Year,color=factor(DCL_peakNum))+geom_text()+theme(axis.text.x = element_text(angle = 90, hjust = 1))
# qplot(factor(Station),(B0_down_depth-DCL_depth)/(DCL_depth-B0_up_depth),data=subset(feature,Lake=="MI"& DCL_depth>0),label=Year,color=factor(DCL_peakNum))+geom_text()+theme(axis.text.x = element_text(angle = 90, hjust = 1))
# qplot(factor(Station),(B0_down_depth-DCL_depth)/(DCL_depth-B0_up_depth),data=subset(feature,Lake=="SU"& DCL_depth>0),label=Year,color=factor(DCL_peakNum))+geom_text()+theme(axis.text.x = element_text(angle = 90, hjust = 1))
# qplot(factor(Station),(B0_down_depth-DCL_depth)/(DCL_depth-B0_up_depth),data=subset(feature,Lake=="ON"& DCL_depth>0),label=Year,color=factor(DCL_peakNum))+geom_text()+theme(axis.text.x = element_text(angle = 90, hjust = 1))
# qplot(factor(Station),(B0_down_depth-DCL_depth)/(DCL_depth-B0_up_depth),data=subset(feature,Lake=="HU"& DCL_depth>0),label=Year,color=factor(DCL_peakNum))+geom_text()+theme(axis.text.x = element_text(angle = 90, hjust = 1))

# qplot(factor(Station),Year,data=subset(feature,Lake=="ER"& DCL_depth>0 & DCL_peakNum>1),label=Year,color=factor(index_peak_index))+geom_text()+theme(axis.text.x = element_text(angle = 45, hjust = 1))
# qplot(factor(Station),Year,data=subset(feature,Lake=="MI"& DCL_depth>0 & DCL_peakNum>1),label=Year,color=factor(index_peak_index))+geom_text()+theme(axis.text.x = element_text(angle = 45, hjust = 1))
# qplot(factor(Station),Year,data=subset(feature,Lake=="SU"& DCL_depth>0 & DCL_peakNum>1),label=Year,color=factor(index_peak_index))+geom_text()+theme(axis.text.x = element_text(angle = 45, hjust = 1))
# qplot(factor(Station),Year,data=subset(feature,Lake=="ON"& DCL_depth>0 & DCL_peakNum>1),label=Year,color=factor(index_peak_index))+geom_text()+theme(axis.text.x = element_text(angle = 45, hjust = 1))
# qplot(factor(Station),Year,data=subset(feature,Lake=="HU"& DCL_depth>0 & DCL_peakNum>1),label=Year,color=factor(index_peak_index))+geom_text()+theme(axis.text.x = element_text(angle = 45, hjust = 1))


# library(rgl)

# plot(DCL_Conc,Surface_Chl,Bottom_Chl)

# # qplot(DCL_depth,Surface_Chl,data=subset(feature,Lake="ER"))


# qplot(Num,DCL_peakNum,data=myDCL,color=Lake)




