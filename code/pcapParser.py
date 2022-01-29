import pcaputils
import Config as cm
import os
import argparse
from utils import StreamProcessing
# Todo: Error Domain parsing

##############
# create dir #
##############
# create csv file for traces
# sample: 0_163.com_2020-03-31-07
def CreateFile(outputdir,cnt,domain,ts):
	dirpath = os.path.join(outputdir,domain)
	if not os.path.exists(dirpath):
		os.makedirs(dirpath, exist_ok=True)
	filepath = os.path.join(dirpath,"%d_%s_%s.csv"%(cnt,domain,ts))
	return filepath

#########################
# not yet done, fix pls #
#########################
def getErrorDomain():
    errorDomain = []
    with open(cm.ErrorFilePath,'r') as f:
        for line in f:
        	if line.strip() != '':
	            errorDomain.append(line.strip().split(",")[0])
    return errorDomain

#################
# list all pcap #
#################
def ListPcapFile(inputdir):
	pcapList = os.listdir(inputdir)
	return pcapList

def parseAllpcap(inputdir, StreamList, outputdir):
	pcapList = ListPcapFile(inputdir)
	for domain in pcapList:
		if domain == "nohup.out" or domain == "ErrorList.txt" or domain == "log.txt":
			continue
		try:
			pcappath = os.path.join(inputdir,domain.strip())
			pcappath = os.path.join(pcappath,"pcap")
			flist = os.listdir(pcappath)
			for f in flist:
				if f.endswith(".pcap"):
					outputpath = getTraceName(outputdir,f)
					cnt,domain,timestamp = f.split("_")
					pcaputils.ParsePcapFile(os.path.join(pcappath,f),StreamList[(domain,cnt)],outputpath)
		except Exception as e:
			print(str(e))
			pass

##########################################
# get the traces filename from pcap file #
##########################################
# get filename of pcap to retrieve domain & timestamp
# return the csv file
def getTraceName(outputdir,filepath):
	filename = filepath.strip(".pcap").split("/")[-1]
	fList = filename.split("_")
	cnt,domain,Timestamp = int(fList[0]), fList[1], fList[2]
	filepath = CreateFile(outputdir,cnt,domain,Timestamp)
	return filepath

#################
# main function #
#################
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--inputdir','-i',type=str,default=None,help='input pcap dir, EX:result_902')
	parser.add_argument('--test', '-t', type=str, default=None, help='test pcap file, format:[cnt]_[domain]_[timestamp].pcap')
	parser.add_argument('--streamInfo','-s', type=str, default=cm.StreamFile, help="streamInfo path")
	parser.add_argument("--outputdir",'-o',type=str,default=None,help='output of traces')
	args = parser.parse_args()
	dirpath = args.inputdir
	streamPath = args.streamInfo
	print("dirpath = ",dirpath)
	testfile = args.test
	outputdir = cm.pcapDir if args.outputdir == None else args.outputdir
	if dirpath == None and testfile == None:
		print("[pcapParser Error]: both Inputdir and test are None")
		return 
	elif dirpath != None and testfile != None:
		print("[pcapParser Error]: only one of them can be sepcified")
		return 
	StreamList = StreamProcessing(streamPath)
	# errorDomain = getErrorDomain()
	if dirpath != None:
		parseAllpcap(dirpath, StreamList, outputdir)
	if testfile != None:
		cnt,domain,timestamp = testfile.split("/")[-1].split("_")	# XXX/0_google.com_2020-05-05-00.pcap
		pcaputils.ParsePcapFile(testfile,StreamList[(domain,cnt)],os.path.join(outputdir,"tmp.csv"))

if __name__ == '__main__':
	main()
