	def plot_slides(self, filename=None, legend=True):
		pt = plt.figure(figsize=(6, 7), dpi=80)
		ax1 = pt.add_subplot(111)
		ax2 = ax1.twiny()

		# ax1.plot(self.cleanData[:, self.varDic["Temperature"]], -self.cleanData[:, 0], "r", label="Temperature")
		# ax1.plot(self.rawData_downcast[:, self.varDic["Temperature"]], -self.rawData_downcast[:, 0], "r--", alpha=0.5)
		ax2.plot(self.cleanData[:, self.varDic["Fluorescence"]], -self.cleanData[:, 0], "g", label="Fluorescence")
		ax2.plot(self.rawData_downcast[:, self.varDic["Fluorescence"]], -self.rawData_downcast[:, 0], "g--", alpha=0.5)

		ax1.set_xlabel("Temperature (C)")
		ax1.set_ylabel("Depth (m)")
		ax2.set_xlabel("Fluorescence (ug/L)")
		ax2.set_xlim((max(0, min(self.rawData_downcast[:, self.varDic["Fluorescence"]]))),
		             max(self.rawData_downcast[:, self.varDic["Fluorescence"]]))
		ax1.set_ylim((-max(self.cleanData[:, self.varDic["Depth"]]) - 5, 0))

		if legend == False:  # Don't plot thermocline and DCL identification
			pass;

		else:

			# ax2.axhline(y=-self.DCL_expert.peakDepth, color="b", ls="--", label="Expert DCL", linewidth=2)

			for peakDepth in self.DCL_algo.peakDepth:
				ax2.axhline(y=-peakDepth, color="b", label="Algo DCL", linewidth=2)

			ax1.set_ylim((-max(self.cleanData[:, 0]), 0))
			ax2.plot(self.DCL_algo.B0, -np.array(self.DCL_algo.B0_depth), "ro")  # Plot biggest peak

		h1, l1 = ax1.get_legend_handles_labels()
		h2, l2 = ax2.get_legend_handles_labels()
		ax1.legend(h1 + h2, l1 + l2, loc=4)

		# ax2.legend(loc=4)
		if filename is None:
			pass;
		else:
			plt.savefig(filename)
			plt.close()

	

	