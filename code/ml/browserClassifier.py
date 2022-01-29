import os,csv, joblib
import MLConfig as cm
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from randomForrest import writeLog
import argparse
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import pandas as pd
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import itertools
from collections import Counter
######################################
# preprocessing data befor trainging #
######################################
def Preprocessing(x):
	x = NormalizeData(x)
	return x

def NormalizeData(x):
	scalar = StandardScaler()
	scalar.fit(x)
	return scalar.transform(x)

#########################################
# random forrest capable of multi-class #
#########################################
def Training(x_train,y_train):
	clf = RandomForestClassifier(n_estimators=cm.Trees, n_jobs=cm.njobs, criterion='gini', verbose=0)
	clf.fit(x_train,y_train)
	return clf

def ReadOpenworldData(inputdir):
	x,y = [],[]
	for i in range(len(cm.versionList)):
		filepath = os.path.join(inputdir,cm.versionList[i],"openworld.csv")
		with open(filepath,'r') as f:
			reader = csv.DictReader(f)
			for line in reader:
				tmp = [float(line[h]) for h in cm.headerlist]
				if tmp[0] > 2000:
					x.append(tmp)
					y.append(i)
	return shuffle(np.array(x),np.array(y))


def ReadCSV(inputdir,outputdir):
	x,y = [],[]
	for i in range(len(cm.versionList)):
		dirpath = os.path.join(inputdir,cm.versionList[i])
		for domain in os.listdir(dirpath):
			if domain.endswith(".csv"):
				filepath = os.path.join(dirpath,domain)
				t = []
				with open(filepath,'r') as f:
					reader = csv.DictReader(f)
					for line in reader:
						t.append([float(line[h]) for h in cm.headerlist])
					if len(t) > cm.n_threshold:
						for d in t:
							x.append(d)
							y.append(i)
	return shuffle(np.array(x),np.array(y))

###########################
# k-fold cross validation #
###########################
def Validation(x_train,y_train):
	clf = RandomForestClassifier(n_estimators=cm.Trees, n_jobs=cm.njobs, criterion='gini', verbose=0)
	scores = cross_val_score(clf,x_train,y_train,cv=cm.k_fold,scoring='accuracy')
	print("cross-validation score: %s"%(str(scores)))
	print("cross-validation Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

##################
# ret all domain #
##################
def retDomain(inputdir):
	setlist = []
	versionList = os.listdir(inputdir)
	for v in versionList:
		tmp = set()
		dirpath = os.path.join(inputdir,v)
		for domain in os.listdir(dirpath):
			if domain.endswith(".csv"):
				tmp.add(domain[:-4])
		setlist.append(tmp)
	return setlist[0] & setlist[1] & setlist[2]

###########################
# test only single domain #
###########################
def ReadSingleDomain(inputdir,testdomain):
	x,y = [],[]
	for i in range(len(cm.versionList)):
		dirpath = os.path.join(inputdir,cm.versionList[i])
		filepath = os.path.join(dirpath,testdomain+".csv")
		t = []
		if os.path.isfile(filepath):
			with open(filepath,'r') as f:
				reader = csv.DictReader(f)
				for line in reader:
					t.append([float(line[h]) for h in cm.headerlist])
				if len(t) > cm.n_threshold:
					for d in t:
						x.append(d)
						y.append(i)
				else:
					return [],[]
	return shuffle(np.array(x),np.array(y))

def parseCommand():
	parser = argparse.ArgumentParser()
	parser.add_argument('--inputdir','-i',type=str,default=None, help='Direcotry of Features, EX: directory path of TrafficResult-3')
	parser.add_argument('--outputdir','-o',type=str,default="./", help='path of output Directory')
	parser.add_argument('--testsingle', '-s', help='train rf for every domain',action='store_true')
	parser.add_argument('--openworld','-p',help='openworld classification',action='store_true')
	parser.add_argument('--verbose', '-v',default=False, help='train rf for every domain',action='store_true')
	parser.add_argument('--modeldir','-m',type=str,help='model dir path for closed-world model')
	args = parser.parse_args()
	if args.inputdir == None:
		print("inputdir argument should be specified")
		return 0
	return args

def VisualizeFeatures(clf,outputdir):
	pklpath = os.path.join(outputdir,"featureImportance.pkl")
	feature_imp = pd.Series(clf.feature_importances_,index=cm.headerlist).sort_values(ascending=False)
	feature_imp.to_pickle(pklpath)

def plot_confusion_matrix(confmatrix, classes,
                          normalize=False,
                          title='',
						  xlabel='Prediction label',
						  ylabel= 'True label',
                          cmap=plt.cm.Blues):
    if normalize:
        confmatrix = confmatrix.astype('float') / confmatrix.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')
    print(confmatrix)
    plt.imshow(confmatrix, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    for i in range(len(classes)):
        if classes[i] == 'normal':
            classes[i] = 'standard'
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks,classes,fontsize=14)
    plt.yticks(tick_marks,classes,fontsize=14)
    fmt = '.2f' if normalize else '.2f'
    thresh = confmatrix.max() / 2.
    for i, j in itertools.product(range(confmatrix.shape[0]), range(confmatrix.shape[1])):
        plt.text(j, i, format(confmatrix[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if confmatrix[i, j] > thresh else "black")

    plt.ylabel(ylabel,fontsize=16)
    plt.xlabel(xlabel,fontsize=16)

def Testing(clf,x_test,y_test,outputdir,testdomain = False):
	ans = clf.predict(x_test)
	failcnt = []
	pairfail = {}
	totalfail = {'7':0,'8':0,'9':0,'10':0}
	versiondict = {0:'7',1:'8',2:'9',3:'10'}
	failpath = os.path.join(outputdir,"failedCase.txt")
	for a,b in zip(ans,y_test):
		if a != b:
			if (a,b) not in pairfail:
				pairfail[(a,b)] = 0
			pairfail[(a,b)] += 1
			totalfail[versiondict[b]] += 1
			failcnt.append([a,b])
	print("fail case:",totalfail)
	print("pair fail: ",pairfail)
	print("Testing Accuracy: %f"%(1-(len(failcnt)/len(y_test))))
	plt.figure()
	confmatrix = confusion_matrix(y_test,ans)
	plot_confusion_matrix(confmatrix,classes=cm.versionList,normalize=True,title="Open-world classification error")
	plt.savefig(os.path.join(outputdir,"confusionmatrix.png"),bbox_inches = 'tight')
	if testdomain != False:
		l = []
		logfile = os.path.join(outputdir,"log.txt")
		writeLog("%s -> Testing Accuracy: %f"%(testdomain,1-(len(failcnt)/len(y_test))),logfile)

def txtTocsv(outputdir):
	filepath = os.path.join(outputdir,"log.txt")
	outputpath = os.path.join(outputdir,"domain_acc.csv")
	l = []
	with open(filepath,'r') as f:
		for line in f:
			line = line.strip().split(' ')
			domain = line[0]
			acc = line[-1]
			l.append([domain,acc])
	with open(outputpath,'w') as fw:
		fw.write("domain,acc\n")
		for ele in l:
			fw.write("%s,%s\n"%(ele[0],ele[1]))

def SaveFeatureImportance(outputdir,domain,data):
	dirpath = os.path.join(outputdir,"domainFeatureIMP")
	if not os.path.exists(dirpath):
			os.makedirs(dirpath, exist_ok=True)
	filepath = os.path.join(dirpath,domain+".pkl")
	print("filepath = ",filepath)
	data = data.nlargest(n=10)
	data.to_pickle(filepath)

def loadModel(filepath):
	return joblib.load(filepath)

def main(args):
	if args.openworld == True:
		x,y = ReadOpenworldData(args.inputdir)
		print("openworld data counter:",Counter(y))
		clf = loadModel(os.path.join(args.modeldir,"closedworld_classifier.joblib"))
		Testing(clf,x,y,args.outputdir)
		VisualizeFeatures(clf,args.outputdir)
	elif args.testsingle == True:
		domainList = retDomain(args.inputdir)
		for domain in domainList:
			print("reading domain %s..."%(domain))
			x,y = ReadSingleDomain(args.inputdir,domain)
			if x == [] and y == []:
				print("not enough train instance %s"%(domain))
				continue
			x_train, x_test, y_train, y_test = train_test_split(x,y,test_size=cm.testingsize, stratify=y) # split data(ensure every classes appears in training set and testing set)
			x_train = Preprocessing(x_train)
			x_test = Preprocessing(x_test)
			print("training domain %s..."%(domain))
			clf = Training(x_train,y_train)
			print("testing domain %s... "%(domain))
			Testing(clf,x_test,y_test,args.outputdir,testdomain = domain)
			if args.verbose == True:
				feature_imp = pd.Series(clf.feature_importances_,index=cm.headerlist).sort_values(ascending=False)
				SaveFeatureImportance(args.outputdir,domain,feature_imp)
		txtTocsv(args.outputdir)
	else:
		x,y = ReadCSV(args.inputdir,args.outputdir)
		x_train, x_test, y_train, y_test = train_test_split(x,y,test_size=cm.testingsize, stratify=y) # split data(ensure every classes appears in training set and testing set)
		#x_train = Preprocessing(x_train)
		#x_test = Preprocessing(x_test)
		#Validation(x,y)
		clf = Training(x_train,y_train)
		#joblib.dump(clf, os.path.join(args.outputdir,"closedworld_classifier.joblib"))
		Testing(clf,x_test,y_test,args.outputdir)
		VisualizeFeatures(clf,args.outputdir)

if __name__ == '__main__':
	args = parseCommand()
	main(args)