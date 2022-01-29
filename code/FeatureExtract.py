import os
import argparse
from FeatureUtils import parseFileName,ReadCSV,writeFeature, MergeDict
from FeatureUtils import getTarFile, RemoveUncompressDir, WriteLog
from utils import StreamProcessing
import CellFeature, TimeFeature
import Config as cm

# 20200420: former streamInfo format + random streamInfo logs in the domain
# 20200422: random streamInfo logs in the domain

############
# testfile #
############
testfile = ""
logfile = ""
outputdir = ""

###########
# testrun #
###########
def testrun():
	inputfilepath = testfile.split("Traffic/")[-1]
	cnt,domain,timestamp = parseFileName(testfile)
	StreamList = StreamProcessing(logfile)
	datalist = ReadCSV(testfile,StreamList[(domain,cnt)])
	print("len datalist = ",len(datalist))
	cellsDict = CellFeature.FeatureRetrieve(datalist,StreamList[(domain,cnt)],inputfilepath)
	TimeDict = TimeFeature.FeatureRetrieve(datalist,StreamList[(domain,cnt)],inputfilepath)
	AllDict = MergeDict(cellsDict,TimeDict)
	writeFeature(outputdir,domain,AllDict)

########
# main #
########
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--inputdir','-i',type=str,default=None, help='input traces dir, EX: traces')
	parser.add_argument('--test', '-t', help='test pcap file',action='store_true')
	parser.add_argument("--outputdir",'-o',type=str,required=True, help='outputdir')
	parser.add_argument("--version",'-v',type=str,default="new",help="new Version Crawler or old one")
	args = parser.parse_args()
	ISTEST = args.test
	inputdir = args.inputdir
	outputdir = args.outputdir
	ver = args.version
	if ISTEST == False and inputdir == None:
		print("At least testfile or inputdir argument should be specified")
		return 0
	if ISTEST != False and inputdir != None:
		print("only one of the argument: testfile, inputdir could have value")
		return 0
	if ISTEST:
		testrun()
	else:
		inputfilepath = testfile.split(args.inputdir)[-1]
		for CrawlDate in os.listdir(inputdir):				# inputdir: Traffic/
			if  "DS_Store" not in CrawlDate and CrawlDate != '':
				try:
					CrawlDir = os.path.join(inputdir,CrawlDate)	# CrawlDir: 20200422/
					print("processing Dir: %s..."%(CrawlDir))
					domainDir = getTarFile(CrawlDir,ver)			# domainDir: 20200422/traces/ 
					logfile = os.path.join(CrawlDir,cm.StreamInfo)	# logfile: XXX/logs/streamInfo.txt
					if not os.path.exists(logfile):
						logfile = os.path.join(CrawlDir,'streamInfo.txt')
					StreamList = StreamProcessing(logfile)
					for domain in os.listdir(domainDir):
						if ".DS_Store" not in domain and domain != '':
							domainpath = os.path.join(domainDir,domain)
							for instance in os.listdir(domainpath):
								try:
									instancepath = os.path.join(domainpath,instance)
									cnt,domain,timestamp = parseFileName(instancepath)
									if (domain,cnt) in StreamList:
										datalist = ReadCSV(instancepath,StreamList[(domain,cnt)])
										cellsDict = CellFeature.FeatureRetrieve(datalist,StreamList[(domain,cnt)],inputfilepath)
										TimeDict = TimeFeature.FeatureRetrieve(datalist,StreamList[(domain,cnt)],inputfilepath)
										AllDict = MergeDict(cellsDict,TimeDict)
										AllDict['srcDir'] = instancepath.split("Traffic/")[-1]
										writeFeature(outputdir,domain,AllDict)
									else:
										WriteLog("Not found: %s in streamInfo"%(instancepath))
								except Exception as e:
									print("Error string: ",str(e))
									WriteLog(str(e))
									pass
				except Exception as e:
					print(str(e))
					WriteLog(str(e))
				finally:
					RemoveUncompressDir(domainDir)				# domainDir: 20200422/<untardir>


if __name__ == '__main__':
	main()
