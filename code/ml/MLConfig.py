import sys
sys.path.append("../")
from CellFeature import CellFeature
from TimeFeature import TimeFeature
##################
# Random forrest #
#################
n_threshold = 60	# only retrieve websites that have amount of traffic instaces > n_threshold
k_fold = 10 			# k-fold cross validation
njobs = 8			# parllel workers for random forrest
testingsize = 0.1 	# size of testing size(0 to 1) -> train_test_split
Trees = 500			# number of trees for random forrest
treedepth = 70
#versionList = ['7','8','9','10']
versionList = ['normal','safer','safest']

######################
# Grandient Boosting #
######################
GBparams = {
    'n_estimators': 120,
    'max_depth': 3,
    'learning_rate': 0.05,
    'criterion': 'mse',
    'verbose':1
}

####################
# list of features #
####################
headerlist = []
for k in CellFeature.keys():
	headerlist.append(k)
for k in TimeFeature.keys():
	headerlist.append(k)