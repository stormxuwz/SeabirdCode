from Tkinter import *
import tkMessageBox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import tkFileDialog
import matplotlib.pyplot as plt;
import os
from seabird_class import seabird
import json

class SeabirdGUI:
	def __init__(self,ini_dir="./test/",master=None):
		self.master=master
		self.seabird=None	# Seabird Class
		self.filename=None	# Input file name
		self.initialdir=ini_dir # Initial directory
		self.feature=None # 
		
		self.threshold=None # Threshold for threshold methods
		self.smoothPar=[1,0] # Smoothing parameters for temperature and fluorescence

		self.feature_THM=-99
		self.feature_EPI=-99
		self.feature_HYP=-99
		self.feature_DCL=-99

		self.config = json.load(open('./config/config.json'))

	# 	GUI elements
		master.title("Seabird Thermocline/DCL Detection")
		self.plotObj=plt.figure(figsize=(7,7.5))

		# Frames
		self.left_frame=Frame(master) # Left frame to input
		self.middle_frame=Frame(master) # Middle Frame to plot
		self.right_frame=Frame(master) # Right frame to show features

		# GUI layout
		self.left_frame.grid(row=0,column=0)
		self.middle_frame.grid(row=0,column=1)
		self.right_frame.grid(row=0,column=2)
	
		# Left Panel
		self.button_chooseFile=Button(self.left_frame,text="Choose Seabird File",command=self.getFile,width=30)
		self.button_showDepthProfile=Button(self.left_frame,text="Show Depth Profile",command=self.showDepthProfile,width=15)
		self.button_setting=Button(self.left_frame,text="Setting",command=self.advSetting,width=15)
		self.button_detect=Button(self.left_frame,text="Detect",command=self.detect,width=30)		
		self.button_quit=Button(self.left_frame,text="Quit App",command=master.quit)
		self.button_lic=Button(self.left_frame,text="Licenses",command=lambda: os.system('open LICENSE'))
		self.button_instruction=Button(self.left_frame,text="Instruction",command=lambda: os.system('open LICENSE'))

		# Layout
		self.button_chooseFile.grid(row=0, column=0,columnspan=2)
		self.button_showDepthProfile.grid(row=2,column=0)
		self.button_setting.grid(row=2,column=1)
		self.button_detect.grid(row=4,column=0,columnspan=2)
		self.button_quit.grid(row=12,column=0,columnspan=2)
		self.button_instruction.grid(row=11,column=0)
		self.button_lic.grid(row=11,column=1)
		
		# Middle Panel
		self.canvas_background = FigureCanvasTkAgg(plt.figure(figsize=(7,7.5)), master=self.middle_frame)
		self.canvas_background.show()
		self.canvas_background.get_tk_widget().grid(row=0,column=0)
		self.canvas = FigureCanvasTkAgg(self.plotObj, master=self.middle_frame)
		self.canvas.show()
		self.canvas.get_tk_widget().grid(row=0,column=0)

		# Layout
		self.filelabel=Label(self.middle_frame,text="File Not Chosen") 
		self.filelabel.grid(row=1,column=0)
		
		# Right Panel
		self.button_show_thermByPower=Button(self.right_frame,text="Power Spectra",command=lambda: self.show_thermocline("power"))
		self.button_show_thermByHMM=Button(self.right_frame,text="HMM",command=lambda: self.show_thermocline("HMM"))
		# self.button_show_DCL=Button(self.right_frame,text="DCL",command=lambda: self.show_thermocline("HMM"))

		self.button_change_epi=Button(self.right_frame,text="Change",command=lambda:self.change_legend("EPI"))
		self.button_change_thm=Button(self.right_frame,text="Change",command=lambda:self.change_legend("THM"))
		self.button_change_hyp=Button(self.right_frame,text="Change",command=lambda:self.change_legend("HYP"))
		self.button_change_dcl=Button(self.right_frame,text="Change",command=lambda:self.change_legend("DCL"))

		self.label_thermMethod=Label(self.right_frame,text="Method:")
		self.Thermocline=Label(self.right_frame, text="Thermocline Features")
		self.deepChlorophyllLayer=Label(self.right_frame, text="DCL Features")
		self.text_note=Text(self.right_frame,width=35,height=5)
		self.label_note=Label(self.right_frame,text="Notes")

		self.epi_label=Label(self.right_frame, text="LEP")
		self.thm_label=Label(self.right_frame, text="THM")
		self.hyp_label=Label(self.right_frame, text="UHY")
		self.DCL_label=Label(self.right_frame, text="DCL")

		# Show the depths
		self.epi_depth=Text(self.right_frame, height=1, width=10)
		self.thm_depth=Text(self.right_frame, height=1, width=10)
		self.hyp_depth=Text(self.right_frame, height=1, width=10)
		self.DCL_depth=Text(self.right_frame, height=1, width=10)

		self.epi_depth.insert(INSERT, "NA")
		self.thm_depth.insert(INSERT, "NA")
		self.hyp_depth.insert(INSERT, "NA")
		self.DCL_depth.insert(INSERT, "NA")
		self.text_note.insert(INSERT,"Machine Results will be here")
		

		# Save Layout
		self.button_saveDepths=Button(self.right_frame,text="Save all results",command=self.saveResult,width=30)
		self.button_saveNotes=Button(self.right_frame,text="Save Notes",command=self.saveNotes,width=30)

		self.button_saveDepths.grid(row=10,column=0,columnspan=3)
		self.button_saveNotes.grid(row=11,column=0,columnspan=3)

		self.label_note.grid(row=8,column=0,columnspan=3)
		self.text_note.grid(row=9,column=0,columnspan=3)
		
		# Thermocline Layout
		self.Thermocline.grid(row=1,column=0,columnspan=3)
		self.label_thermMethod.grid(row=2,column=0)
		self.button_show_thermByPower.grid(row=2,column=1)
		self.button_show_thermByHMM.grid(row=2,column=2)
		
		self.epi_label.grid(row=3,column=0)
		self.thm_label.grid(row=4,column=0)
		self.hyp_label.grid(row=5,column=0)
		
		self.epi_depth.grid(row=3,column=1)
		self.thm_depth.grid(row=4,column=1)
		self.hyp_depth.grid(row=5,column=1)
		
		self.button_change_epi.grid(row=3,column=2)
		self.button_change_thm.grid(row=4,column=2)
		self.button_change_hyp.grid(row=5,column=2)
		
		# DCL Layout
		self.deepChlorophyllLayer.grid(row=6,columnspan=3)
		# self.button_show_DCL.grid(row=7,column=2)
		self.DCL_label.grid(row=7,column=0)
		
		self.DCL_depth.grid(row=7,column=1)
		self.button_change_dcl.grid(row=7,column=2)

		
	def getFile(self):
		oldname=self.filename
		self.filename = tkFileDialog.askopenfilename(parent=self.master, initialdir=self.initialdir,title="Please select the seabird file")
		if(self.filename.lower().endswith(".cnv") or self.filename.lower().endswith(".csv")):
			
			self.filelabel["text"]=self.filename
			self.initialdir=os.path.split(self.filename)[0]
			
			self.seabird=seabird(fileName=self.filename,config=self.config)	

		elif self.filename is "":
			self.filename=oldname
			return
		else:
			tkMessageBox.showinfo("File Type Wrong", "Please choose file ending with .cnv")
		

		self.showDepthProfile();
	

	def showDepthProfile(self):
		if self.seabird is None:
			tkMessageBox.showinfo("No Data", "Please choose file ending with .cnv first")
			return
		else:
			self.canvas.get_tk_widget().grid_remove()
			plt.close(self.plotObj)

			self.plotObj=plt.figure(figsize=(7,7.5))
			self.seabird.plot(legend=False,pt=self.plotObj)

			self.canvas = FigureCanvasTkAgg(self.plotObj, master=self.middle_frame)
			self.canvas.show()
			self.canvas.get_tk_widget().grid(row=0,column=0)

	def show_thermocline(self,method="None"):
		# Change the text
		if method=="power":
			index="threshold_thermocline"
		elif method=="HMM":
			index="hmm_thermocline"

		self.THM=self.feature[index][0]
		self.EPI=self.feature[index][1]
		self.HYP=self.feature[index][2]

		self.epi_depth.delete(1.0, END)
		self.hyp_depth.delete(1.0, END)
		self.thm_depth.delete(1.0, END)

		self.thm_depth.insert(INSERT,"%8.2f" %(self.THM))
		self.hyp_depth.insert(INSERT,"%8.2f" %(self.HYP))
		self.epi_depth.insert(INSERT,"%8.2f" %(self.EPI))
		# self.DCL_depth.insert(INSERT,"%8.2f m" %(self.DCL))

		self.adding_legend()
		self.text_note.delete(1.0, END)
		self.text_note.insert(INSERT,"Machine results:\nLEP=%8.2f m,\nTHM=%8.2f m,\nUHY=%8.2f m,\nDCL=%8.2f m" %(self.EPI,self.THM,self.HYP,self.DCL))

	def saveResult(self):
		if self.feature is None:
			tkMessageBox.showinfo("No Results", "Please Detect Legend First")
			return
		saveFile_name_initial=self.seabird.site+"_"+self.seabird.time.split("_")[0]+".csv"
		saveFile=tkFileDialog.asksaveasfile(mode='w',defaultextension=".csv",title="Choose location to save",initialfile=saveFile_name_initial)

		if saveFile is not None:
			maxPeak=self.feature[4][1]
			saveFile.write("Site,Time,THM,LEP,UHY,DCL,THM (algo),LEP(algo-thres),HYP(algo_thres),LEP(algo-HMM),HYP(algo_HMM),DCL(algo),Notes\n");
			saveFile.write("%s,%s,%8.2f,%8.2f,%8.2f,%8.2f,%8.2f,%8.2f,%8.2f,%8.2f,%8.2f,%8.2f" %(self.seabird.site,self.seabird.time,self.THM,self.EPI,self.HYP,self.DCL,self.feature[1][0],self.feature[1][1],self.feature[1][2],self.feature[2][1],self.feature[2][2],self.feature[4][2][maxPeak]))


			# saveFile.write(self.text_note.get())
			saveFile.close()
			tkMessageBox.showinfo("File Saved", "File Saved")

	def saveNotes(self):
		saveFile_name_initial=self.seabird.site+"_"+self.seabird.time.split("_")[0]+"_notes.txt"
		saveFile=tkFileDialog.asksaveasfile(mode='w',defaultextension=".txt",title="Choose location to save",initialfile=saveFile_name_initial)

		if saveFile is not None:
			maxPeak=self.feature[4][1]
			saveFile.write(self.seabird.site+":"+self.seabird.time+"\n");
			saveFile.write(self.text_note.get(1.0, END));
			saveFile.close()
			tkMessageBox.showinfo("File Saved", "File Saved")


	def advSetting(self):
		advSettingsWindow =Toplevel()
		advSettingsWindow.geometry("300x400")
		advSettingsWindow.title("Seabird script advanced settings")
		
		def saveSettings():
			newConfig=self.seabird.config.copy()

			if textBox_thres.get()=="":
				self.threshold = None
			else:
				self.threshold = float(textBox_thres.get())

			newConfig["Algorithm"]["Spectrum"]["threshold"]=self.threshold
			
			## Temperature smooth parameter
			if textBox_smooth_temperature.get()=="": 
				newConfig["SmoothingMethod"]["Temperature"][1] = 1
			else:
				newConfig["SmoothingMethod"]["Temperature"][1] =float(textBox_smooth_temperature.get())
			
			## Fluorescence smooth parameter
			if textBox_smooth_chl.get()=="":	
				newConfig["SmoothingMethod"]["Fluorescence"][2]=0
			else:
				newConfig["SmoothingMethod"]["Fluorescence"][2]=int(textBox_smooth_chl.get())

			# Update the smoothing results
			if(self.seabird.rawData is not None):
				self.seabird.updateConfig(newConfig)
				self.seabird.updateData()
				self.showDepthProfile();

			advSettingsWindow.quit()
			advSettingsWindow.destroy()
					

		label1 = Label(advSettingsWindow,text="Enter threshold value for power spectra method \n (Left blank means automatic)")
		label1.grid(row=0,column=0)
		textBox_thres = Entry(advSettingsWindow)
		textBox_thres.grid(row=1,column=0)

		label2 = Label(advSettingsWindow,text="Smoothing parameters for temperature \n higher value will smooth data more \n(left blank to use default setting)")
		label2.grid(row=2,column=0)

		textBox_smooth_temperature = Entry(advSettingsWindow)
		textBox_smooth_temperature.grid(row=3)

		label3 = Label(advSettingsWindow,text="Smoothing parameters for Fluorescence \n higher value will smooth data more \n(left blank to use default setting)")
		label3.grid(row=4,column=0)

		textBox_smooth_chl = Entry(advSettingsWindow)
		textBox_smooth_chl.grid(row=5)

		
		if self.threshold is None:
			textBox_thres.insert(0,"")
		else:
			textBox_thres.insert(0,self.threshold)
		
		textBox_smooth_temperature.insert(0,self.smoothPar[0])
		textBox_smooth_chl.insert(0,self.smoothPar[1])
		
		button3 = Button(advSettingsWindow,text="Save/Update",command=saveSettings)
		button3.grid(row=6)
		advSettingsWindow.mainloop()


	def adding_legend(self):
		self.canvas.get_tk_widget().grid_remove()
		plt.close(self.plotObj)

		self.plotObj=plt.figure(figsize=(7,7.5))
		self.seabird.plot(legend=False,pt=self.plotObj)
		ax1=self.plotObj.add_subplot(111)
		ax2=ax1.twiny()

		ax1.axhline(y=-self.THM,color="r")
		ax1.axhline(y=-self.EPI,color="b",ls="--")
		ax1.axhline(y=-self.HYP,color="y",ls="--")
		ax2.axhline(y=-self.DCL,color="g",ls="--")
		ax2.get_xaxis().set_visible(False)

		self.canvas = FigureCanvasTkAgg(self.plotObj, master=self.middle_frame)
		self.canvas.show()
		self.canvas.get_tk_widget().grid(row=0,column=0)

	def detect(self):
		self.seabird.identify()
		self.feature=self.seabird.feature
		# print self.feature
		self.THM=self.feature["THM_segment"]
		self.EPI=self.feature["LEP_segment"]
		self.HYP=self.feature["UHY_segment"]
		DCLexist = self.feature["DCL_exist"]

		if(DCLexist == 0):
			self.DCL=-99
		else:
			self.DCL=self.feature["DCL_depth"]

		# Delete the previous texts
		self.epi_depth.delete(1.0, END) 
		self.hyp_depth.delete(1.0, END)
		self.thm_depth.delete(1.0, END)
		self.DCL_depth.delete(1.0, END)

		# Add new results
		self.thm_depth.insert(INSERT,"%8.2f" %(self.THM))
		self.hyp_depth.insert(INSERT,"%8.2f" %(self.HYP))
		self.epi_depth.insert(INSERT,"%8.2f" %(self.EPI))
		self.DCL_depth.insert(INSERT,"%8.2f" %(self.DCL))

		self.adding_legend()
		print("%2f"% (356.08977))

		self.text_note.delete(1.0, END)
		self.text_note.insert(INSERT,"Machine results:\nLEP=%8.2f m,\nTHM=%8.2f m,\nUHY=%8.2f m,\nDCL=%8.2f m" %(self.EPI,self.THM,self.HYP,self.DCL))

	def change_legend(self,type="EPI"):
		if type=="EPI":
			self.EPI = float(self.epi_depth.get(1.0, END))
			self.adding_legend()
			# Replot 
		elif type=="HYP":
			self.HYP = float(self.hyp_depth.get(1.0, END))
			self.adding_legend()
		elif type=="THM":
			self.THM = float(self.thm_depth.get(1.0, END))
			self.adding_legend()
		elif type=="DCL":
			self.DCL = float(self.DCL_depth.get(1.0, END))
			self.adding_legend()


