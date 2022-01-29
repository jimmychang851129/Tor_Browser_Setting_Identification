from os.path import join
inputdir = "/mnt/c/Users/LICON/nslab/data2021/settings/2021-11data/trafficfeature/rfresult/mlresult/safer"

def readlabelmapping(inputdir):
	domaindict = dict()
	labelpath = join(inputdir,"labelmapping.txt")
	with open(labelpath,'r') as f:
		for line in f:
			line = line.split(' ')
			domaindict[int(line[-1].strip())] = line[1].strip()
	return domaindict

def readfailcase(inputdir,domaindict):
	faildict = dict()
	failcnt = dict()
	filepath = join(inputdir,"failedCase.txt")
	with open(filepath,'r') as f:
		for line in f:
			try:
				line = line.strip().split(' ')[1]
				f1,f2 = int(line.split(',')[0]),int(line.split(',')[1])
				if domaindict[f2] not in failcnt:
					failcnt[domaindict[f2]] = 0
				failcnt[domaindict[f2]] += 1
				if domaindict[f1] +','+domaindict[f2] not in faildict:
					faildict[domaindict[f1] +','+domaindict[f2]] = 0
				faildict[domaindict[f1] +','+domaindict[f2]] += 1
			except Exception as e:
				print(e)
				continue
	return faildict,failcnt

def inspectDomain(inputdir,domaindict,domain):
	dlist = dict()
	filepath = join(inputdir,"failedCase.txt")
	with open(filepath,'r') as f:
		for line in f:
			try:
				line = line.strip().split(' ')[1]
				f1,f2 = int(line.split(',')[0]),int(line.split(',')[1])
				d1,d2 = domaindict[f1],domaindict[f2]
				if d1 == domain:
					if d2 not in dlist:
						dlist[d2] = 0
					dlist[d2] += 1
			except Exception as e:
				print("error",e)
				continue
	return dlist

def main():
	args = parseCommand()
	domaindict = readlabelmapping()

def parseCommand():
	parser = argparse.ArgumentParser()
	parser.add_argument('--inputdir','-i',type=str,default=None, help='Direcotry of Features, EX: directory path of TrafficResult-3')
	args = parser.parse_args()
	if args.inputdir == None:
		print("inputdir argument should be specified")
		return 0
	return args

if __name__ == '__main__':
	args = parseCommand()
	main(args)