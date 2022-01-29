import os, pickle, csv, sys
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from FeatureUtils import parseFileName,ReadCSV,writeFeature, MergeDict
from FeatureUtils import getTarFile, RemoveUncompressDir, WriteLog
from keras.utils import np_utils
from utils import StreamProcessing
import CellFeature, TimeFeature
import Config as cm
from statistics import median
import argparse
import numpy as np
import joblib
sys.path.append("./ml")
import MLConfig as mlconfig
from randomForrest import writeLog
import browserClassifier
sys.path.append('./ml/deepfingerprint/')
import DFFeatureExtract
import train as dftrain

##########
# Config #
##########
shuffle_random_state = 9487

def ReadDFData(filepath,train=0):
    data = []
    try:
        data = pickle.load(open(filepath,'rb'))
        if train == 1:
            for i in range(len(data)):
                if len(data[i]) > 5000:
                    data[i] = data[i][:5000]
                    if len(data[i]) < 5000:
                        data[i] += [0] * (5000 - len(data[i]))
    except Exception as e:
        print("[ReadDFData error] filepath not found: ",filepath)
        print(str(e))
        data = []
    return data

def ProcessRawData(inputdir,outputdir,ver):
    browserversion = inputdir.strip("/").split("/")[-1]
    rfoutputdir = os.path.join(outputdir,"rf/%s"%(browserversion))
    dfoutputdir = os.path.join(outputdir,"df/%s"%(browserversion))
    for CrawlDate in os.listdir(inputdir):              # inputdir: Traffic/
        if "DS_Store" not in CrawlDate and CrawlDate != '':
            try:
                CrawlDir = os.path.join(inputdir,CrawlDate) # CrawlDir: 20200422/
                print("processing Dir: %s..."%(CrawlDir))
                domainDir = getTarFile(CrawlDir,ver)            # domainDir: 20200422/traces/ 
                logfile = os.path.join(CrawlDir,cm.StreamInfo)  # logfile: XXX/logs/streamInfo.txt
                if not os.path.exists(logfile):
                    logfile = os.path.join(CrawlDir,'streamInfo.txt')
                StreamList = StreamProcessing(logfile)
                for domain in os.listdir(domainDir):
                    if ".DS_Store" not in domain and domain != '':
                        domainpath = os.path.join(domainDir,domain)
                        print("parsing domain: ",domainpath)
                        for instance in os.listdir(domainpath):
                            try:
                                instancepath = os.path.join(domainpath,instance)
                                inputfilepath = instancepath.split("Traffic/")[-1]
                                cnt,domain,timestamp = parseFileName(instancepath)
                                if (domain,cnt) in StreamList:
                                    rf_datalist = ReadCSV(instancepath,StreamList[(domain,cnt)])
                                    cellsDict = CellFeature.FeatureRetrieve(rf_datalist,StreamList[(domain,cnt)],inputfilepath)
                                    TimeDict = TimeFeature.FeatureRetrieve(rf_datalist,StreamList[(domain,cnt)],inputfilepath)
                                    AllDict = MergeDict(cellsDict,TimeDict)
                                    AllDict['srcDir'] = instancepath.split("Traffic/")[-1]
                                    writeFeature(rfoutputdir,domain,AllDict)
                                    df_datalist = DFFeatureExtract.ReadCSV(instancepath,StreamList[(domain,cnt)])
                                    DFFeatureExtract.writeFeature(dfoutputdir,domain,df_datalist)
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
                RemoveUncompressDir(domainDir)              # domainDir: 20200422/<untardir>

def RemoveFailSample(inputdir,outputdir):
    versionList = ['7','8','9']
    header = ','.join(mlconfig.headerlist + ['srcDir'])
    for version in versionList:
        rfdir = os.path.join(inputdir,'rf',version)
        dfdir = os.path.join(inputdir,'df',version)
        rf_outputdir = os.path.join(outputdir,'rf/removedFailed',version)
        df_outputdir = os.path.join(outputdir,'df/removedFailed',version)
        for domain in os.listdir(rfdir):
            if domain.endswith(".csv"):
                filepath = os.path.join(rfdir,domain)
                l,data = [],[]
                cnt = 0
                with open(filepath,'r') as f:
                    for line in f:
                        if cnt == 1:
                            l.append(int(line.split(',')[0]))
                            data.append(line)
                        cnt = 1
                med = median(l)
                dffilepath = os.path.join(dfdir,domain[:-4])
                dfdata = ReadDFData(dffilepath)
                if med > 100 and len(l) > mlconfig.n_threshold:
                    realdfdata = []
                    rfoutputpath = os.path.join(rf_outputdir,domain)
                    if not os.path.isfile(rfoutputpath):
                        with open(rfoutputpath,'a+') as fw:
                            fw.write(header+"\n")
                    fw = open(rfoutputpath,'a+')
                    cnt_check = 0
                    for i in range(len(l)):
                        if l[i] > med * 0.8:
                            cnt_check += 1
                            fw.write(data[i])
                            realdfdata.append(dfdata[i])
                    dfoutputpath = os.path.join(df_outputdir,domain[:-4])   # write to df feature file
                    pickle.dump(realdfdata,open(dfoutputpath,"wb"))
                    if len(realdfdata) != cnt_check:
                        print("[two-phase-classifier]Imbalance amount of data: %s-> %d,%d"%(domain,len(realdfdata),cnt_check))

def CreateLabelmapping():
    versionList = ["7","8","9"]
    labeldir = os.path.join(inputdir,"labelmapping")
    labelpath = os.path.join(labeldir,"labelmapping.txt")
    labeldict = set()
    for version in versionList:
        dirpath = os.path.join(inputdir,"rf/removedFailed/",version)
        for domain in os.listdir(dirpath):
            if "DS_Store" not in domain:
                domain = domain if ".csv" not in domain else domain[:-4]
            if domain not in labeldict:
                labeldict.add(domain)
    cnt = 0
    for domain in labeldict:
        writeLog("mapping: %s -> %d"%(domain,cnt),labelpath)
        cnt += 1

def ReadRFData(filepath):
    data = []
    try:
        with open(filepath,'r') as f:
            reader = csv.DictReader(f)
            for line in reader:
                data.append([float(line[h]) for h in mlconfig.headerlist])
    except Exception as e:
        data = []
        print("[ReadRFData error] filepath not found: ",filepath)
        print(str(e))
    return data

def splitdataset(inputdir,outputdir):
    versionList = ["7","8","9"]
    for version in versionList:
        data = []
        label = []
        dirpath = os.path.join(inputdir,"rf/removedFailed/",version)
        labeldir = os.path.join(inputdir,"labelmapping")
        labeldict = dftrain.ReadLabel(labeldir)
        instancelist = dict()
        for k in labeldict.keys():
            filepath = os.path.join(dirpath,k+".csv")   # read random forest
            t = ReadRFData(filepath)
            if t != []:
                for d in t:
                    data.append(d)
                    label.append(labeldict[k])
                instancelist[k] = len(t)
        x1_train, x1_test, y1_train, y1_test = train_test_split(data,label,random_state=shuffle_random_state,stratify=label,test_size=0.1)
        rfoutputpath = os.path.join(outputdir,"rf/train_test")
        pickle.dump(x1_train,open(os.path.join(rfoutputpath,"%s-train.pkl"%(version)),"wb"))
        pickle.dump(x1_test,open(os.path.join(rfoutputpath,"%s-test.pkl"%(version)),"wb"))
        pickle.dump(y1_train,open(os.path.join(rfoutputpath,"%s-valid-train.pkl"%(version)),"wb"))
        pickle.dump(y1_test,open(os.path.join(rfoutputpath,"%s-valid-test.pkl"%(version)),"wb"))
        print("Random forrest datset split...")
        print({k: v for k, v in sorted(instancelist.items(), key=lambda item: item[1])})
    for version in versionList:
        data = []
        label = []
        dirpath = os.path.join(inputdir,"df/removedFailed/",version)
        labeldir = os.path.join(inputdir,"labelmapping")
        labeldict = dftrain.ReadLabel(labeldir)
        instancelist = dict()
        for k in labeldict.keys():
            filepath = os.path.join(dirpath,k)   # read random forest
            t = ReadDFData(filepath)
            if t != []:
                for d in t:
                    data.append(d)
                    label.append(labeldict[k])
                instancelist[k] = len(t)
        x1_train, x1_test, y1_train, y1_test = train_test_split(data,label,random_state=shuffle_random_state,stratify=label,test_size=0.1)
        dfoutputpath = os.path.join(outputdir,"df/train_test")
        pickle.dump(x1_train,open(os.path.join(dfoutputpath,"%s-train.pkl"%(version)),"wb"))
        pickle.dump(x1_test,open(os.path.join(dfoutputpath,"%s-test.pkl"%(version)),"wb"))
        pickle.dump(y1_train,open(os.path.join(dfoutputpath,"%s-valid-train.pkl"%(version)),"wb"))
        pickle.dump(y1_test,open(os.path.join(dfoutputpath,"%s-valid-test.pkl"%(version)),"wb"))
        print("DeepFingerprint datset split...")
        print({k: v for k, v in sorted(instancelist.items(), key=lambda item: item[1])})

def TrainDFModel(inputdir,outputdir,version="9",trainall=0):
    if trainall == 0:
        trainfilepath = os.path.join(inputdir,"%s-train.pkl"%(version))
        labelfilepath =os.path.join(inputdir,"%s-valid-train.pkl"%(version))
        dfdata = ReadDFData(trainfilepath,train=1)
        dflabel = ReadDFData(labelfilepath)
        dfdata = np.array(dfdata)
        dfdata = dfdata[:, :,np.newaxis]
        dflabel = np_utils.to_categorical(dflabel,max(dflabel)+1)
        x1_train, x1_test, y1_train, y1_test = train_test_split(dfdata,dflabel,test_size=0.1, stratify=dflabel)
        dfnet = dftrain.DFNet(len(y1_train[0]))
        dfnet.CallbackList(outputdir)
        dfnet.Training(x1_train,y1_train,outputdir)
        dfnet.Testing(x1_test,y1_test)
    else:
        print("training all data...")
        VersionList = ['7','8','9']
        dfdata,dflabel = [],[]
        for version in VersionList:
            trainfilepath = os.path.join(inputdir,"%s-train.pkl"%(version))
            labelfilepath =os.path.join(inputdir,"%s-valid-train.pkl"%(version))
            dfdata += ReadDFData(trainfilepath,train=1)
            dflabel += ReadDFData(labelfilepath)
        dfdata = np.array(dfdata)
        dfdata = dfdata[:, :,np.newaxis]
        dflabel = np_utils.to_categorical(dflabel,max(dflabel)+1)
        x1_train, x1_test, y1_train, y1_test = train_test_split(dfdata,dflabel,test_size=0.1, stratify=dflabel)
        del dfdata
        del dflabel
        dfnet = dftrain.DFNet(len(y1_train[0]))
        dfnet.CallbackList(outputdir)
        dfnet.Training(x1_train,y1_train,outputdir)
        dfnet.Testing(x1_test,y1_test)

def VersionClassifier(inputdir,outputdir):
    rftraindata = []
    labeldata = []
    versionList = ["7","8","9"]
    for version in versionList:
        tmp = pickle.load(open(os.path.join(inputdir,"%s-train.pkl"%(version)),'rb'))
        labeldata += [int(version) - 7 ]*len(tmp)
        rftraindata += tmp
    rftraindata = np.array(rftraindata)
    labeldata = np.array(labeldata)
    rftraindata = browserClassifier.Preprocessing(rftraindata)
    x1_train, x1_test, y1_train, y1_test = train_test_split(rftraindata,labeldata,random_state=shuffle_random_state,stratify=labeldata,test_size=0.1)
    clf = browserClassifier.Training(x1_train,y1_train)
    ans = clf.predict(x1_test)
    fail = 0
    for a,b in zip(ans,y1_test):
        if a != b:
            fail += 1
    print("accuracy in one-fold verification = %f"%(1 - fail/len(ans)))
    print("training with whole data....")
    clf = browserClassifier.Training(rftraindata,labeldata)
    joblib.dump(clf,os.path.join(outputdir,"versionClassifier.pkl"))

################
# test 2-phase #
################
# /home/jimmy/twophase
def loadModel(inputdir):
    versionmodel = os.path.join(inputdir,"versionclassifier/versionClassifier-90-split.pkl")
    clf = joblib.load(versionmodel)
    dfdir = [os.path.join(inputdir,"df/train_test/7"),os.path.join(inputdir,"df/train_test/8"),os.path.join(inputdir,"df/train_test/9")]
    dfmodel = [dftrain.DFNet(196),dftrain.DFNet(198),dftrain.DFNet(197)]
    modelpath = dftrain.findBestModel(dfdir[0])
    dfmodel[0].model.load_weights(modelpath)
    modelpath = dftrain.findBestModel(dfdir[1])
    dfmodel[1].model.load_weights(modelpath)
    modelpath = dftrain.findBestModel(dfdir[2])
    dfmodel[2].model.load_weights(modelpath)
    return clf,dfmodel

# /home/jimmy/twophase
def ReadTestData(inputdir):
    versionList = ["7","8","9"]
    testdfdata,testrfdata = [],[]
    testdflabel,testrflabel = [],[]
    rfinputdir = os.path.join(inputdir,"rf/train_test")
    dfinputdir = os.path.join(inputdir,"df/train_test")
    for version in versionList:
        testfilepath = os.path.join(rfinputdir,"%s-test.pkl"%(version))
        labelfilepath =os.path.join(rfinputdir,"%s-valid-test.pkl"%(version))
        testrfdata += ReadDFData(testfilepath)
        testrflabel += ReadDFData(labelfilepath)
    for version in versionList:
        testfilepath = os.path.join(dfinputdir,"%s-test.pkl"%(version))
        labelfilepath =os.path.join(dfinputdir,"%s-valid-test.pkl"%(version))
        testdfdata += ReadDFData(testfilepath,train=1)
        testdflabel += ReadDFData(labelfilepath)
    return np.array(testrfdata),np.array(testrflabel),np.array(testdfdata),np.array(testdflabel)

def twophaseclassifier(inputdir):
    testrfdata,testrflabel,testdfdata,testdflabel = ReadTestData(inputdir)
    testrfdata = browserClassifier.Preprocessing(testrfdata)
    clf,dfmodel = loadModel(inputdir)
    browserVersionPredict = clf.predict(testrfdata)
    del testrfdata
    del testrflabel
    testdata = [[],[],[]]
    for i in range(len(browserVersionPredict)):
        testdata[browserVersionPredict[i]].append((testdfdata[i]))
    del testdfdata
    for i in range(len(testdata)):
        testdata[i] = np.array(testdata[i])
        testdata[i] = testdata[i][:, :,np.newaxis]
    finalans = []
    cnt = [0,0,0]
    for i in range(3):
        finalans.append(dfmodel[i].model.predict(testdata[i]))
    for i in range(3):
        finalans[i] = finalans[i].argmax(axis=-1)
    success = 0
    for i in range(len(browserVersionPredict)):
        if finalans[browserVersionPredict[i]][cnt[browserVersionPredict[i]]] == testdflabel[i]:
            success += 1
        cnt[browserVersionPredict[i]] += 1
    print("success rate = %f"%(success / len(testdflabel)))

###########
# test df #
###########
# inputdir = "/home/jimmy/twophase"
def testcmpmodel(inputdir):
    modeldir = os.path.join(inputdir,"df/train_test/cmpdfmodel/")
    datadir = os.path.join(inputdir,"df/train_test")
    dfmodel = dftrain.DFNet(198)
    modelpath = dftrain.findBestModel(modeldir)
    dfmodel.model.load_weights(modelpath)
    VersionList = ['7','8','9']
    dfdata,dflabel = [],[]
    for version in VersionList:
        testfilepath = os.path.join(datadir,"%s-test.pkl"%(version))
        labelfilepath =os.path.join(datadir,"%s-valid-test.pkl"%(version))
        dfdata += ReadDFData(testfilepath,train=1)
        dflabel += ReadDFData(labelfilepath)
    dfdata = np.array(dfdata)
    dfdata = dfdata[:, :,np.newaxis]
    ans = dfmodel.model.predict(dfdata)
    ans = ans.argmax(axis=-1)
    success = 0
    for i in range(len(ans)):
        if ans[i] == dflabel[i]:
            success += 1
    print("success rate = %f"%(success/len(ans)))

def main(args):
    if args.extractRaw == True:
        ProcessRawData(args.inputdir,args.outputdir,args.version)
    if args.removefail == True:
        RemoveFailSample(args.inputdir,args.outputdir)
    if args.splitdata == True:
        splitdataset(args.inputdir,args.outputdir)
    if args.trainversionClassifier == True:
        VersionClassifier(args.inputdir,args.outputdir)
    if args.trainDFModel == True:
        if args.trainall == True:
            TrainDFModel(args.inputdir,args.outputdir,args.version,trainall=1)
        else:
            TrainDFModel(args.inputdir,args.outputdir,args.version)
    if args.cmp == True:
        testcmpmodel(inputdir)

def ParseArg():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputdir",'-i',type=str,required=True, help='input traces dir, EX: traces')
    parser.add_argument("--outputdir",'-o',type=str,required=True, help='outputdir')
    parser.add_argument("--version",'-v',type=str,default="new",help="new Version Crawler or old one")
    parser.add_argument("--extractRaw",'-e',help='extract features for rf/df from raw data',action='store_true')
    parser.add_argument("--removefail",'-r',help='remove failed sample in raw data',action='store_true')
    parser.add_argument("--splitdata",'-s',help='split dataset to train,test data',action='store_true')
    parser.add_argument("--trainversionClassifier",'-b',help="train version classifier(random forrest)",action='store_true')
    parser.add_argument("--trainDFModel",'-d',help="train a Deepfingerprint model for specific version",action='store_true')
    parser.add_argument("--trainall",'-a',help="train df model with all version data(for comparison)",action='store_true')
    parser.add_argument("--cmp",'-c',help="results of pure deepfingerprint(for comparison)",action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = ParseArg()
    main(args)
