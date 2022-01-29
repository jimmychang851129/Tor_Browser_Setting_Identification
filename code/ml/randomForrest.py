import csv, os
import argparse
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import MLConfig as cm
import argparse

#############
# Reference # 
#############
# [random forrest sklearn]: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
# [cross validation skelarn]: https://scikit-learn.org/stable/modules/cross_validation.html
# [random forest & visualize]: https://www.datacamp.com/community/tutorials/random-forests-classifier-python

# scoring = ['precision_macro', 'recall_macro']

def writeLog(output,outputpath):
	with open(outputpath,'a+') as fw:
		fw.write(output+"\n")

# only read data with more than n_threshold features
def ReadAllFeatures(inputdir,outputdir,domainMapping=None):
	x,y = [],[]
	cnt = 0
	NotFoundDomain = set()
	labelpath = os.path.join(outputdir,"labelmapping.txt")
	print("inputdir = ",inputdir)
	for domain in os.listdir(inputdir):
		if domain.endswith(".csv"):
			filepath = os.path.join(inputdir,domain)
			t = []
			with open(filepath,'r') as f:
				reader = csv.DictReader(f)
				for line in reader:
					# t.append([float(line[h]) for h in cm.headerlist])
					tmp = []
					for h in cm.headerlist:
						try:
							tmp.append(float(line[h]))
						except Exception as e:
							# print("exception: ",f)
							# print("header not found",h)
							continue
					t.append(tmp)
			if domainMapping != None:
				for d in t:
					try:
						y.append(domainMapping[domain.strip(".csv")])
						x.append(d)
					except Exception as e:
						NotFoundDomain.add(domain.strip(".csv"))
						pass
			else:
				if len(t) >= cm.n_threshold:
					instancecnt = 0
					writeLog("mapping: %s -> %d"%(domain.strip(".csv"),cnt),labelpath)
					for d in t:
						x.append(d)
						y.append(cnt)
						instancecnt += 1
						if instancecnt > 130:
							break
					cnt += 1
	if domainMapping != None:
		print("Not found domain = ",len(NotFoundDomain),NotFoundDomain)
	return shuffle(np.array(x),np.array(y))

def ReadMapping(inputpath):
	domainMapping = dict()
	with open(inputpath,'r') as f:
		for line in f:
			line = line.strip().split(' ')
			domainMapping[line[1]] = int(line[-1])
	return domainMapping

###################
# Normalized data #
###################
def NormalizeData(x):
	scalar = StandardScaler()
	scalar.fit(x)
	return scalar.transform(x)

######################################
# preprocessing data befor trainging #
######################################
def Preprocessing(x):
	x = NormalizeData(x)
	return x

#########################################
# random forrest capable of multi-class #
#########################################
def Training(x_train,y_train):
	clf = RandomForestClassifier(n_estimators=cm.Trees, n_jobs=cm.njobs,max_depth=cm.treedepth, criterion='gini',oob_score=True, verbose=0)
	clf.fit(x_train,y_train)
	return clf

###########################
# k-fold cross validation #
###########################
def Validation(x_train,y_train):
	clf = RandomForestClassifier(n_estimators=cm.Trees, n_jobs=cm.njobs, criterion='gini', verbose=0)
	scores = cross_val_score(clf,x_train,y_train,cv=cm.k_fold,scoring='accuracy')
	print("cross-validation score: %s"%(str(scores)))
	print("cross-validation Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

################################
# test model with testing data #
################################
def Testing(clf,x_test,y_test,outputdir):
	acc = clf.score(x_test,y_test)
	print("model score = ",acc)
	ans = clf.predict(x_test)
	failcnt = []
	failpath = os.path.join(outputdir,"failedCase.txt")
	for a,b in zip(ans,y_test):
		if a != b:
			failcnt.append([a,b])
	print("Testing Accuracy: %f"%(1-(len(failcnt)/len(y_test))))
	s = ""
	for d in failcnt:
		s += "failed: %d,%d\n"%(d[0],d[1])	# the latter one is the correct class
	writeLog(s,failpath)

###################################
# show the importance of features #
###################################
def VisualizeFeatures(clf,outputdir):
	pklpath = os.path.join(outputdir,"featureImportance.pkl")
	imgpath = os.path.join(outputdir,"rfVisualize.png")
	feature_imp = pd.Series(clf.feature_importances_,index=cm.headerlist).sort_values(ascending=False)
	feature_imp.to_pickle(pklpath)
	sns.barplot(x=feature_imp, y=feature_imp.index)
	plt.xlabel('Feature Importance Score')
	plt.ylabel('Features')
	plt.title("Important Features Visualization")
	plt.legend()
	plt.savefig(imgpath)

def parseCommand():
	parser = argparse.ArgumentParser()
	parser.add_argument('--inputdir','-i',type=str,default=None, help='Direcotry of Features, EX: directory path of TrafficResult-3')
	parser.add_argument('--outputdir','-o',type=str,default="./", help='path of output Directory')
	parser.add_argument('--version','-v',type=str,default=None)
	parser.add_argument('--validate','-c',action='store_true')
	args = parser.parse_args()
	if args.inputdir == None:
		print("inputdir argument should be specified")
		return 0
	return args

def main(args=0):
	if args == 0:
		return 0
	print("argsversion = ",args.version)
	if args.version != None:
		v1,v2 = args.version.split(",")
		inputdir1,inputdir2 = args.inputdir.split(',')
		print("inputdir = ",inputdir1,inputdir2)
		dirpath = os.path.join(args.outputdir,"mlresult/%s-%s/"%(v1,v2))
		if not os.path.exists(dirpath):
			os.makedirs(dirpath, exist_ok=True)
		x1,y1 = ReadAllFeatures(inputdir1.strip(),dirpath)
		print("len x1 = ",len(x1))
		domainMapping = ReadMapping(os.path.join(dirpath,"labelmapping.txt"))
		x2,y2 = ReadAllFeatures(inputdir2.strip(),args.outputdir,domainMapping)
		print("len x2 = ",len(x2))
		x1_train, x1_test, y1_train, y1_test = train_test_split(x1,y1,test_size=cm.testingsize, stratify=y1)
		# x1 = Preprocessing(x1)
		clf = Training(x1_train,y1_train)
		# print("len x2_test = ",len(x2_test))
		#Testing(clf,x1_test,y1_test,dirpath)
		Testing(clf,x2,y2,dirpath)
		VisualizeFeatures(clf,dirpath)
	else:
		version = args.inputdir.split('/')[-1]
		dirpath = os.path.join(args.outputdir,"mlresult/%s"%(version))
		if not os.path.exists(dirpath):
			os.makedirs(dirpath, exist_ok=True)
		x,y = ReadAllFeatures(args.inputdir,dirpath)
		print("feature size = ",len(x))
		if args.validate == True:
			Validation(x,y)
		else:
			x_train, x_test, y_train, y_test = train_test_split(x,y,test_size=cm.testingsize, stratify=y) # split data(ensure every classes appears in training set and testing set)
			#x_train = Preprocessing(x_train)
			#x_test = Preprocessing(x_test)
			print("start training...")
			clf = Training(x_train,y_train)
			print("start testing...")
			Testing(clf,x_test,y_test,dirpath)
			#VisualizeFeatures(clf,dirpath)

if __name__ == '__main__':
	args = parseCommand()
	main(args)