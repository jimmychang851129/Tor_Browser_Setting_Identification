import Config as cm
import csv,datetime
try:
	from stem.control import Controller
	from stem import CircStatus
except ImportError:
	print("[warning]utils.py: stem is not installed, pip3 install stem first")

import tempfile
import pathlib,os
import signal,psutil
import glob, shutil, tarfile

##############
# settimeout #
##############
class TimeExceededError(Exception):
	pass

def raise_signal(signum, frame):
	raise TimeExceededError

# set timeout given duration
def timeout(duration):
	signal.signal(signal.SIGALRM,raise_signal)
	signal.alarm(duration)

def cancel_timeout():
	signal.alarm(0)

#######################
# tor setup Exception #
#######################
class TorSetupError(Exception):
	pass

class TBBSetupError(Exception):
	pass

def writeLog(outputstr):
	with open(cm.LogFile,'a+') as f:
		f.write(outputstr+"\n")
		f.flush()

def writeStreamInfo(outputstr):
	with open(cm.StreamFile,'a+') as f:
		f.write(outputstr+"\n")
		f.flush()

################
# read WebList #
################
def ReadWebList():
	datalist,domainList = [],[]
	with open(cm.Datapath,'r') as f:
		reader = csv.DictReader(f)
		for line in reader:
			domainList.append([line['domain'].strip(),line['count']])
	for i in range(cm.INSTANCE):
		for x in domainList:
			datalist.append([x[0],x[1],i])
	return datalist

####################
# read OpenWebList #
####################
# cnt: decide how many websites for open-world DataSet
# only need one instance for each un-monitored websites
def ReadOpenWebList(st=0,ed=0,instance=1):
	top200set = set()
	with open(cm.Datapath,'r') as f:
		reader = csv.DictReader(f)
		for line in reader:
			top200set.add(line['domain'].strip())
	datalist = []
	with open(cm.OpenWorldDataPath,'r') as f:
		reader = csv.DictReader(f)
		for line in reader:
			if line['domain'].strip() in top200set or ".cn" in line['domain'].strip():
				continue
			for i in range(instance):
				datalist.append([line['domain'].strip(),line['count'],i])
	return datalist if st == 0 and ed == 0 else datalist[st:ed]

##############
# create_dir #
##############
def create_dir(dirpath):
	if not os.path.exists(dirpath):
		os.makedirs(dirpath)
		print("create directory: ",dirpath)
	pcapPath = os.path.join(dirpath,"pcap")
	if not os.path.isdir(pcapPath):
		pathlib.Path(pcapPath).mkdir(parents=True, exist_ok=True)
	return dirpath, pcapPath #imgdir, pcapdir

############
# get time #
############
def getTime():
	t = datetime.datetime.now()
	d = t.strftime("%Y-%m-%d-%H")
	return d

############
# getGuard #
############
# get stream guard
# write stream circuit path to log
# return dictionary [circ.id] -> guard addr
def getGuard(controller,CircList):
	d = dict()
	f = open(cm.LogFile,'a+')
	f.write("### stream path ###\n")
	for circ in sorted(controller.get_circuits()):
		if circ.status != CircStatus.BUILT:
			continue
		l = []
		for i, entry in enumerate(circ.path):
			div = '+' if (i == len(circ.path) - 1) else '|'
			fingerprint, nickname = entry
			desc = controller.get_network_status(fingerprint, None)
			address = desc.address if desc else 'unknown'
			l.append("%s,%s,%s,%s,%s\n" % (div,circ.id, fingerprint, nickname, address))
		if circ.id in CircList:
			for ele in l:
				f.write(ele)
			outaddr = l[0].strip().split(',')[-1]
			d[circ.id] = outaddr
	f.flush()
	f.close()
	return d

#################
# print circuit #
#################
def get_tor_circuits(controller,ip):
	guardNode = ""
	f = open(cm.LogFile,'a+')
	f.write("### circuit path ###\n")
	for circ in sorted(controller.get_circuits()):
		if circ.status != CircStatus.BUILT:
			continue
		l = []
		circuitpath = []
		for i, entry in enumerate(circ.path):
			div = '+' if (i == len(circ.path) - 1) else '|'
			fingerprint, nickname = entry
			desc = controller.get_network_status(fingerprint, None)
			address = desc.address if desc else 'unknown'
			l.append("%s,%s,%s,%s,%s\n" % (div, circ.id,fingerprint, nickname, address))
			circuitpath.append(address)
		if circuitpath[-1] == ip:
			guardNode = circuitpath[0]
			for ele in l:
				f.write(ele)
			break
	f.flush()
	f.close()
	return guardNode

###################
# set output path #
###################
def SetOutputPath(ele,t):
	saveDir = os.path.join(cm.ResultDir,ele[0])
	imgDir,saveDir = create_dir(saveDir)
	savepath = os.path.join(saveDir,"%s_%s_%s.pcap"%(str(ele[2]),ele[0],t))
	out_img = os.path.join(imgDir,"%s_%s_%s.png"%(str(ele[2]),str(ele[1]),t))
	return savepath,out_img

####################
# cleanup tempfile #
####################
def RemoveTmpFile():
	try:
		print("start remove temp file...")
		dirlist = glob.iglob("/tmp/tmp*")
		for d in dirlist:
			shutil.rmtree(d)
		dirlist = glob.iglob("/tmp/Temp*")
		for d in dirlist:
			shutil.rmtree(d)
		dirlist = glob.iglob("/tmp/rust*")
		for d in dirlist:
			shutil.rmtree(d)
		print("finish removing dummy file...")
	except Exception as e:
		print("[Error utils.py] remove TempFile error")
		writeLog("[Error utils.py] remove TempFile error")

def RemoveProcess():
	blacklist = ["firefox","geckodriver","Web Content"]
	for proc in psutil.process_iter():
		for b in blacklist:
			if b in proc.name():
				proc.kill()
				break

####################
# remove pcap file #
####################
# remove pcap file in result_902
# remove raw traces(csv) in traces(we have created a tar.gz file in rawTraffic dir)
def removepcapfile(dirlist=["result,traces"]):
	for dirpath in dirlist:
		print("start remove pcap directory: %s"%(dirpath))
		removedir = glob.iglob(os.path.join(dirpath,'*'))
		for t in removedir:
			try:
				shutil.rmtree(t)
			except Exception as e:
				print("[utils.py]removepcapfile: unable to remove dir %s"%(t))
				writeLog("[utils.py]removepcapfile: unable to remove dir %s"%(t))

#######################
# tar network traffic #
#######################
# return outputdir
# Ex inputdir: XXX
# Ex: outputdir: XXX/rawTraffic/1/
def tarNetworkTraffic(inputdir, outputdir):
	dtime = getTime()
	outputtardir = os.path.join(outputdir,dtime)
	if not os.path.exists(outputtardir):
		pathlib.Path(outputtardir).mkdir(parents=True, exist_ok=True)
	outputtarfile = os.path.join(outputtardir,"%s_traces.tar.gz"%(dtime))
	with tarfile.open(outputtarfile, "w:gz") as tar:
		tar.add(inputdir, arcname=os.path.basename(inputdir))
	return outputtardir

def MoveLogFile(rawtrafficdir):
	print("move log file to %s..."%(rawtrafficdir,))
	if not os.path.exists(cm.StreamFile):
		print("[utils.py]MoveLogFile: unable to locate file: %s\n"%(cm.StreamFile))
		writeLog("[utils.py]MoveLogFile: unable to locate file: %s\n"%(cm.StreamFile))
	else:
		shutil.move(cm.StreamFile,os.path.join(rawtrafficdir,"streamInfo.txt"))
	if not os.path.exists(cm.ErrorFilePath):
		print("[utils.py]MoveLogFile: unable to locate file: %s\n"%(cm.ErrorFilePath))
		writeLog("[utils.py]MoveLogFile: unable to locate file: %s\n"%(cm.ErrorFilePath))
	else:
		shutil.move(cm.ErrorFilePath,os.path.join(rawtrafficdir,"ErrorList.txt"))
	if not os.path.exists(cm.LogFile):
		print("[utils.py]MoveLogFile: unable to locate file: %s\n"%(cm.LogFile))
		writeLog("[utils.py]MoveLogFile: unable to locate file: %s\n"%(cm.LogFile))
	else:
		shutil.move(cm.LogFile,os.path.join(rawtrafficdir,"log.txt"))

#######################
# read StreamInfo.txt #
#######################
# not sure if there will be memory issue(probably 200 * 4 keys, values)
# read all the domain, stream guard node at once
# return format: dict(key,value) = dict((domain,cnt),set(guard IP))
def StreamProcessing(logfile):
	outputdict = dict()
	with open(logfile,'r') as f:
		for line in f:
			t = line.split(',')
			if (t[0],t[1]) not in outputdict:
				outputdict[(t[0],t[1])] = set()
			if t[4] not in outputdict[(t[0],t[1])]:
				outputdict[(t[0],t[1])].add(t[4])	# get guard IP
	return outputdict

#############################
# parse raw guard node info #
#############################
# def rawInfo(controller):
# 	print("get entry guard ###")
# 	guardnode = controller.get_info("entry-guards").split("\n")
# 	for i in range(len(guardnode)):
# 		guard = guardnode[i].split("~")[0].strip("$")
# 		print("guard = ",guard)
# 		d = controller.get_network_status(guard, None)
# 		addrList = (guardnode[i],d.address) if d else (guardnode[i],'unknown')
# 		print(addrList)
# 	print("guardnode: ",guardnode)