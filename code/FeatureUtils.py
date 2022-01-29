import csv,os
import pathlib
import tarfile, shutil

FilterFlag = [1,2] # SYN, FIN
HalfCell = 256	   # round packetlen to the closest multiple 512, less than 256 = 0
# handle ack,encryption, macoverhead, refer to data collection paper

###################
# parse filename  #
###################
def parseFileName(filepath):
	cnt,domain,timestamp = filepath.split('/')[-1].strip('.csv').split('_')
	return cnt,domain,timestamp

def ReadCSV(filepath,StreamList=[]):
	cnt,domain,timestamp = parseFileName(filepath)
	nt = []
	with open(filepath,'r') as f:
		reader = csv.DictReader(f)
		for line in reader:
			if int(line['flags']) not in FilterFlag and int(line['packetlen']) > HalfCell:
				if StreamList == [] or line['dstip'] in StreamList or line['srcip'] in StreamList:
					nt.append([line['timestamp'],line['srcip'],line['srcport'],line['dstip'],line['dstport'],line['packetlen']])
	return nt

def FeatureValueToString(output):
	for key,value in output.items():
		output[key] = str(value)

##########################
# write features to file #
##########################
def writeFeature(outputdir,domain,output):
	filepath = os.path.join(outputdir,"openworld.csv")
	FeatureValueToString(output)
	output_key = ','.join(output.keys())
	output_value = ','.join(output.values())
	if not os.path.isfile(filepath):		# write header
		pathlib.Path(outputdir).mkdir(parents=True, exist_ok=True)
		with open(filepath,'a+') as fw:
			fw.write(output_key+"\n")
			fw.write(output_value+"\n")
	else:									# don't write header
		with open(filepath,'a+') as fw:
			fw.write(output_value+"\n")		

def MergeDict(dictA,dictB):
	AllDict = {}
	AllDict.update(dictA)
	AllDict.update(dictB)
	return AllDict

# un-compress the targz file in directory, return the result directory #
# input: 20200422
# output: 20200422/traces  # traces containse the domain lists
def getTarFile(dirpath,ver):
	s = os.listdir(dirpath)
	filepath = ""
	for file in os.listdir(dirpath):
		if file.endswith(".tar.gz"):
			f = os.path.join(dirpath,file)
			tf = tarfile.open(f)
			if ver == "new":
				outputpath = os.path.join(dirpath,"trace")
				os.makedirs(outputpath,exist_ok=True)
			else:
				outputpath = dirpath
			tf.extractall(path=outputpath)
	for file in os.listdir(dirpath):
		if file not in s:
			filepath = os.path.join(dirpath,file)
	return filepath

def RemoveUncompressDir(dirpath):
	try:
		shutil.rmtree(dirpath)
	except Exception as e:
		print("[FeatureUtils error]RemoveUncompressDir: unable to remove dirpath: ",dirpath)
		WriteLog(str(e))
		print(e)

def WriteLog(output):
	with open("./Feature.log",'a') as fw:
		output = output if output[-1] == '\n' else output+"\n"
		fw.write(output)
