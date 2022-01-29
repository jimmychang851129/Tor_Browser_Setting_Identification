import os,csv, argparse
from statistics import median
import MLConfig as cm
import numpy as np
from os.path import join

# inputdir = "/Users/jimmy/Desktop/WF_Result/WFfeature/9"
# outputdir = "/Users/jimmy/Desktop/WF_Result/WFfeature/removeFailed/9"

# parse the log file to get all the page timeout instance
# key = %wf6-2021-10-25-01,domain,instancecnt%
def logparser(inputdir):
	errlist = set()
	for folder in os.listdir(inputdir):
		with open(join(inputdir,folder,"log.txt")) as f:
			for line in f:
				if "Error crawling" in line:
					key = folder+','+','.join([x for x in line.strip().split(',')[1:]])
					errlist.add(key)
	return errlist

def checkdate(web):
	web = web.split('_')[-1][5:-3]
	return True if web[:2] == "09-2" or web[:2] == "10" else False

def removefail(inputdir,outputdir,iter):
	for domain in os.listdir(inputdir):
		if domain.endswith(".csv"):
			filepath = os.path.join(inputdir,domain)
			l,data = [],[]
			with open(filepath,'r') as f:
				for line in f:
					l.append(line.split(',')[0])
					data.append(line)
			if len(l) == 0:
				continue
			l = [int(x) for x in l[1:]]	# remove header
			med = median(l)
			qual1 = np.percentile(l,25)
			qual3 = np.percentile(l,75)
			irq = 0.5*(qual3 - qual1)
			if med > cm.n_threshold and len(l) > cm.n_threshold:
				outputpath = os.path.join(outputdir,domain)
				fw = open(outputpath,'w')
				fw.write(data[0])
				if iter == 0:
					for i in range(1,len(data)):
						if l[i-1] > med*0.4 and l[i-1] < med*1.3 and l[i-1] > cm.n_threshold:
							fw.write(data[i])
				if iter == 1:
					for i in range(1,len(data)):
						if l[i-1] >= qual1-irq and l[i-1] <= qual3+irq:
							fw.write(data[i])
				fw.close()					

def getKey(line):
	return line.split('/')[-4] +','+line.split('/')[-2]+','+line.split('/')[-1].split('_')[0]

def removefailPageLoadTimeout(inputdir,outputdir,failset):
	for domain in os.listdir(inputdir):
		if domain.endswith(".csv"):
			filepath = os.path.join(inputdir,domain)
			data = []
			with open(filepath,'r') as f:
				for line in f:
					data.append(line)
			medlist = []
			for i in range(1,len(data)):
				key = getKey(data[i].split(',')[-1])
				if key not in failset:
					medlist.append(data[i].split(',')[0])
			try:
				medlist = [int(x) for x in medlist]
				med = median(medlist)
				qual1 = np.percentile(medlist,25)
				qual3 = np.percentile(medlist,75)
				irq = 0.5*(qual3 - qual1)
				print("irq = ",irq)
			except Exception as e:
				print("calculate median error: ",domain)
				print(e)
				continue
			if med > cm.n_threshold:
				outputpath = os.path.join(outputdir,domain)
				fw = open(outputpath,'w')
				fw.write(data[0])
				for i in range(1,len(data)):
					if int(data[i].split(',')[0]) > med-irq and int(data[i].split(',')[0]) < med +irq:
						fw.write(data[i])
				fw.close()			


def removeoutdated(inputdir,outputdir):
	for domain in os.listdir(inputdir):
		if domain.endswith(".csv"):
			filepath = os.path.join(inputdir,domain)
			data = []
			with open(filepath,'r') as f:
				for line in f:
					data.append(line)
			outputpath = os.path.join(outputdir,domain)
			fw = open(outputpath,'w')
			fw.write(data[0])
			for i in range(1,len(data)):
				if checkdate(data[i].split(',')[-1]) == True:
					fw.write(data[i])

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--inputdir','-i',type=str,default=None, help='input traces dir, EX: traces')
	parser.add_argument('--logdir','-l',type=str,default=None,help='input directory contining log.txt file')
	parser.add_argument("--outputdir",'-o',type=str,required=True, help='outputdir')
	args = parser.parse_args()
	failset = logparser(args.logdir)
	removefailPageLoadTimeout(args.inputdir,args.outputdir,failset)
	#removefail(args.inputdir,args.outputdir,0)
	#removefail(args.outputdir,args.outputdir,1)

if __name__ == '__main__':
	main()