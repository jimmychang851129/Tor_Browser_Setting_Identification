import csv, pickle, os, argparse, sys
import sklearn
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

def plotdomainFeature(inputdir,outputdir,targetFeature=[],url=""):
	VersionList = ['7','8','9']
	versiondir = os.path.join(inputdir,'7')
	for domain in os.listdir(versiondir):
		domaindata = dict({domain:dict()})
		for feature in targetFeature:
			domaindata[domain][feature] = [[],[],[]]
		if domain.endswith('.csv'):
			cnt = 0
			for version in VersionList:
				filepath = os.path.join(inputdir,version,domain)
				try:
					with open(filepath,'r') as f:
						reader = csv.DictReader(f)
						for line in reader:
							for feature in targetFeature:
								domaindata[domain][feature][cnt].append(float(line[feature]))
				except Exception as e:
					print("Error domain:",domain)
					pass
				finally:
					cnt += 1
		if url != "" and url in domain:
			boxplotDict(domain,domaindata,outputdir,targetFeature)
			break

# only retrieve features: avg_outgoing_packetOrder
# save in <outputdir>/blockplt/<domain.png>
# for boxplot
def boxplotDict(domain,domaindata,outputdir,targetFeature):
	blockplotdir = os.path.join(outputdir,"blockplot",domain)
	if not os.path.exists(blockplotdir):
		os.makedirs(blockplotdir, exist_ok=True)
	for feature in targetFeature:
		data = [domaindata[domain][feature][0],domaindata[domain][feature][1],domaindata[domain][feature][2]]
		plt.suptitle(feature, fontsize=12)
		plt.tick_params(labelsize=10)
		box = plt.boxplot(data, patch_artist=True)
		colors = ['cyan', 'lightblue', 'lightgreen', 'tan', 'pink']
		for patch, color in zip(box['boxes'], colors):
		    patch.set_facecolor(color)
		outputpath = os.path.join(blockplotdir,"%s_%s"%(domain,feature)+".png")
		plt.savefig(outputpath)
		plt.clf()
	images = [Image.open(os.path.join(blockplotdir,x)) for x in os.listdir(blockplotdir)]
	widths, heights = zip(*(i.size for i in images))
	total_width = sum(widths)
	max_height = max(heights)
	new_im = Image.new('RGB', (total_width, max_height))
	x_offset = 0
	for im in images:
	  new_im.paste(im, (x_offset,0))
	  x_offset += im.size[0]
	new_im.save(os.path.join(blockplotdir,domain+".jpg"))
	for d in images:
		d.close()

# retrieve top 10 features for each version classifier
# then retrieve top 9 features with most appearance
# top 9 features appears more than 100 times among 200 classifier
# return target features(top 9)
# parameter of this function should be renamed(in browsercmp)
def RetrieveTop9Features(outputdir):
	d = dict()
	targetFeature = []
	basedir = os.path.join(outputdir,"domainFeatureIMP")
	for domain in os.listdir(basedir):
		if domain.endswith(".pkl"):
			filepath = os.path.join(basedir,domain)
			with open(filepath,'rb') as f:
				data = pickle.load(f)
			for k in data.keys():
				if k not in d:
					d[k] = 1
				else:
					d[k] += 1
	for k in sorted(d, key=d.get, reverse=True):
		if d[k] > 100:
			targetFeature.append(k)
		print(k,d[k])
	return targetFeature

def parseCommand():
	parser = argparse.ArgumentParser()
	parser.add_argument('--inputdir','-i',type=str,default=None, help='Direcotry of Features, EX: directory path of TrafficResult-3')
	parser.add_argument('--outputdir','-o',type=str,default="./", help='path of output Directory')
	parser.add_argument("--url",'-u',type=str,default="",help='Visualization of domain')
	args = parser.parse_args()
	if args.inputdir == None:
		print("inputdir argument should be specified")
		return 0
	return args

def main(args):
	args = parseCommand()
	targetFeature = RetrieveTop9Features(args.outputdir)
	plotdomainFeature(args.inputdir,args.outputdir,targetFeature,args.url)

if __name__ == '__main__':
	args = parseCommand()
	main(args)


#############
# reference #
#############
# boxplot with variable-lenght list: https://stackoverflow.com/questions/4842805/boxplot-with-variable-length-data-in-matplotlib
# boxplot label tick size: https://www.geeksforgeeks.org/matplotlib-pyplot-tick_params-in-python/
# colorize boxplot: https://stackoverflow.com/questions/20289091/python-matplotlib-filled-boxplots