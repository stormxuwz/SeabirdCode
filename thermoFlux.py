from seabird.tools import seabird_preprocessing
from sqlalchemy import create_engine

SQLEngine=create_engine('mysql+mysqldb://root:XuWenzhaO@localhost/Seabird')


def loadSummerData(year,site):
	data = 
	preprocessing()

def loadWinderData(year,site):
	pass


def calculateThermoFlux(year,site):
	summerData = loadSummerData(year, site)
	winterData = loadWinderData(year, site)

