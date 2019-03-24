columns = c("fileId","TRM_segment","expert_TRM","expert_UHY","expert_LEP","LEP_segment","UHY_segment")
bottomUpResDf = read.csv("/Users/wenzhaoxu/Developer/Seabird/output/detectedFeatures.csv")[,columns]
splitMergeResDf2 = read.csv("/Users/wenzhaoxu/Developer/Seabird/output_splitMerge2/detectedFeatures.csv")[,columns]