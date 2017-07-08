
#### Function to preprocess the feature matrix
preprocessing <- function(features,locations,waterChemistry, startYear = 1996){
	features$lake <- substr(features$site,1,2) # adding lake features
	locations$Long <- -locations$Long
	
	features <- features %>% 
		addingMoreFeatures() %>% # adding more features
		merge(locations,by.x = "site",by.y = "Station") %>% # appending location features
		subset(year>=startYear & lake %in% c("ER","HU","SU","ON","MI") & !is.na(fileId)) %>% # cleaning data
		merge(waterChemistry,by.x = c("fileId","site","year"),by.y = c("fid","site","year")) %>% # merge with water chemistry data
		arrange(site,year) # rearrange data
	
	return(features)
}

addingMoreFeatures <- function(features){
	features$TRM2UHY_segNum <- features$TRM_num_segment-(features$TRM_idx+1)  # The smoothness of from TRM to UHY
	
	return(features)
}


