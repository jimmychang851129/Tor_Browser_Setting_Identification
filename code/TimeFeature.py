import numpy as np
import math
from FeatureUtils import WriteLog
import pywt

#############
# Reference #
#############
# k-fingerprint: https://github.com/AxelGoetz/website-fingerprinting/
# info-leak: https://arxiv.org/pdf/1710.06080.pdf
# time-based feature: https://drive.google.com/open?id=1V9a9xd18HTQ5uhfKKrc7cawxTtsX2Rri


TimeFeature = {
	"TotalTime":-1,
	"Packet_Second_avg":-1,		# packet per second
	"Packet_Second_std":-1,
	"Packet_Second_median":-1,
	"Packet_Second_min":-1,
	"Packet_Second_max":-1,
	"Flow_duration_avg":-1,
	"Flow_duration_std":-1,
	"Flow_duration_median":-1,
	"Flow_duration_min":-1,
	"Flow_duration_max":-1,
	"Flow_duration_1stQuartile":-1,
	"Flow_duration_3rdQuartile":-1,
	"Packet_Interval_avg":-1,
	"Packet_Interval_std":-1,
	"Packet_Interval_max":-1,
	"Packet_Interval_min":-1,
	"Packet_Interval_median":-1,
	"Packet_Interval_1stQuartile":-1,
	"Packet_Interval_3rdQuartile":-1,
	"Packet_outgoing_Interval_avg":-1,
	"Packet_outgoing_Interval_std":-1,
	"Packet_outgoing_Interval_max":-1,
	"Packet_outgoing_Interval_median":-1,
	"Packet_outgoing_Interval_min":-1,
	"Packet_outgoing_Interval_1stQuartile":-1,
	"Packet_outgoing_Interval_3rdQuartile":-1,
	"Packet_incoming_Interval_avg":-1,
	"Packet_incoming_Interval_std":-1,
	"Packet_incoming_Interval_max":-1,
	"Packet_incoming_Interval_median":-1,
	"Packet_incoming_Interval_min":-1,
	"Packet_incoming_Interval_1stQuartile":-1,
	"Packet_incoming_Interval_3rdQuartile":-1,
	'wavelet_All_Interval_avg_ca':-1,
	'wavelet_All_Interval_std_ca':-1,
	'wavelet_All_Interval_max_ca':-1,
	'wavelet_All_Interval_min_ca':-1,
	'wavelet_All_Interval_median_ca':-1,
	'wavelet_incoming_Interval_avg_ca':-1,
	'wavelet_incoming_Interval_std_ca':-1,
	'wavelet_incoming_Interval_max_ca':-1,
	'wavelet_incoming_Interval_min_ca':-1,
	'wavelet_incoming_Interval_median_ca':-1,
	'wavelet_outgoing_Interval_avg_ca':-1,
	'wavelet_outgoing_Interval_std_ca':-1,
	'wavelet_outgoing_Interval_max_ca':-1,
	'wavelet_outgoing_Interval_min_ca':-1,
	'wavelet_outgoing_Interval_median_ca':-1,
	'wavelet_All_Interval_avg_cd':-1,
	'wavelet_All_Interval_std_cd':-1,
	'wavelet_All_Interval_max_cd':-1,
	'wavelet_All_Interval_min_cd':-1,
	'wavelet_All_Interval_median_cd':-1,
	'wavelet_incoming_Interval_avg_cd':-1,
	'wavelet_incoming_Interval_std_cd':-1,
	'wavelet_incoming_Interval_max_cd':-1,
	'wavelet_incoming_Interval_min_cd':-1,
	'wavelet_incoming_Interval_median_cd':-1,
	'wavelet_outgoing_Interval_avg_cd':-1,
	'wavelet_outgoing_Interval_std_cd':-1,
	'wavelet_outgoing_Interval_max_cd':-1,
	'wavelet_outgoing_Interval_min_cd':-1,
	'wavelet_outgoing_Interval_median_cd':-1,
	"Timestamp_All_1Quartile":0,
	"Timestamp_All_2Quartile":0,
	"Timestamp_All_3Quartile":0,
	"Timestamp_Incoming_1Quartile":0,
	"Timestamp_Incoming_2Quartile":0,
	"Timestamp_Incoming_3Quartile":0,
	"Timestamp_Outgoing_1Quartile":0,
	"Timestamp_Outgoing_2Quartile":0,
	"Timestamp_Outgoing_3Quartile":0,
	"incoming_Flow_duration_avg":0,
	"incoming_Flow_duration_max":0,
	"incoming_Flow_duration_min":0,
	"incoming_Flow_duration_std":0,
	"incoming_Flow_duration_1stQuartile":0,
	"incoming_Flow_duration_3rdQuartile":0,
	"outgoing_Flow_duration_avg":0,
	"outgoing_Flow_duration_max":0,
	"outgoing_Flow_duration_min":0,
	"outgoing_Flow_duration_std":0,
	"outgoing_Flow_duration_1stQuartile":0,
	"outgoing_Flow_duration_3rdQuartile":0,
}

# get number of cells
def NumOfCell(packetlen):
	return round(int(packetlen) / 512)	# weird why not int(packetlen) // 500

# flow duration
# time-based feature: https://drive.google.com/open?id=1V9a9xd18HTQ5uhfKKrc7cawxTtsX2Rri
def FlowFeature(data,features,IPSet):
	FlowList = []
	incomingList,outgoingList = [],[]
	FAILED = 0
	s,flow_starttime = (data[0][1],data[0][2],data[0][3],data[0][4]),float(data[0][0])
	for i in range(1,len(data)):
		if (data[i][1],data[i][2],data[i][3],data[i][4]) != s:
			s = (data[i][1],data[i][2],data[i][3],data[i][4])
			FlowList.append(float(data[i-1][0]) - flow_starttime)
			if data[i-1][1] in IPSet:	#incoming
				incomingList.append(float(data[i-1][0]) - flow_starttime)
			else:	# outgoing
				outgoingList.append(float(data[i-1][0]) - flow_starttime)
			flow_starttime = float(data[i-1][0])
	FlowList.append(float(data[-1][0])-flow_starttime)
	if data[-1][1] in IPSet:	# incoming
		incomingList.append(float(data[-1][0]) - flow_starttime)
	else:	# outgoing
		outgoingList.append(float(data[-1][0]) - flow_starttime)
	try:
		features['Flow_duration_avg'] = sum(FlowList) / len(FlowList)
	except Exception as e:
		FAILED = 1
	try:
		features['Flow_duration_max'] = max(FlowList)
	except Exception as e:
		FAILED = 1
	try:
		features['Flow_duration_min'] = min(FlowList)
	except Exception as e:
		FAILED = 1
	try:
		features['Flow_duration_std'] = np.std(FlowList)
	except Exception as e:
		FAILED = 1
	try:
		features['Flow_duration_median'] = np.percentile(FlowList,50)
		features['Flow_duration_1stQuartile'] = np.percentile(FlowList,25)
		features['Flow_duration_3rdQuartile'] = np.percentile(FlowList,75)
	except Exception as e:
		FAILED = 1
	try:
		if len(incomingList) != 0:
			features['incoming_Flow_duration_avg'] = sum(incomingList) / len(incomingList) if len(incomingList) != 0 else -1
			features['incoming_Flow_duration_max'] = max(incomingList)
			features['incoming_Flow_duration_min'] = min(incomingList)
			features['incoming_Flow_duration_std'] = np.std(incomingList)
			features['incoming_Flow_duration_1stQuartile'] = np.percentile(incomingList,25)
			features['incoming_Flow_duration_3rdQuartile'] = np.percentile(incomingList,75)
		if len(outgoingList) != 0:
			features['outgoing_Flow_duration_avg'] = sum(outgoingList) / len(outgoingList) if len(incomingList) != 0 else -1
			features['outgoing_Flow_duration_max'] = max(outgoingList)
			features['outgoing_Flow_duration_min'] = min(outgoingList)
			features['outgoing_Flow_duration_std'] = np.std(outgoingList)
			features['outgoing_Flow_duration_1stQuartile'] = np.percentile(outgoingList,25)
			features['outgoing_Flow_duration_3rdQuartile'] = np.percentile(outgoingList,75)			
	except Exception as e:
		print("incoming,outgoing flow duration failed",e)
		FAILED = 1
	return FAILED

# start from first packet
# interval: time[1] - time[0], time[2] - time[1]......
# neglect time[0] - 0
def PacketIntervalFeature(data,features,IPSet):
	AllInterval,incoming,outgoing = [],[],[]
	FAILED = 0
	for x,y in zip(data[:-1],data[1:]):
		AllInterval.append(float(y[0])-float(x[0]))

	tmp = [x for x in data if x[1] in IPSet]
	for x,y in zip(tmp[:-1],tmp[1:]):
		incoming.append(float(y[0])-float(x[0]))

	tmp = [x for x in data if x[3] in IPSet]
	for x,y in zip(tmp[:-1],tmp[1:]):
		outgoing.append(float(y[0])-float(x[0]))
	try:
		features['Packet_Interval_avg'] = sum(AllInterval) / len(AllInterval)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_Interval_std'] = np.std(AllInterval)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_Interval_median'] = np.percentile(AllInterval,50)
	except Exception as e:
		FAILED = -1
	try:
		features['Packet_Interval_1stQuartile'] = np.percentile(AllInterval,25)
		features['Packet_Interval_3rdQuartile'] = np.percentile(AllInterval,75)
	except Exception as e:
		FAILED = -1
	try:
		features['Packet_Interval_max'] = max(AllInterval)
	except Exception as e:
		FAILED = -1
	try:
		features['Packet_Interval_min'] = min(AllInterval)
	except Exception as e:
		FAILED = -1
	try:
		features['Packet_outgoing_Interval_avg'] = sum(outgoing) / len(outgoing)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_outgoing_Interval_std'] = np.std(outgoing)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_outgoing_Interval_median'] = np.percentile(outgoing,50)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_outgoing_Interval_max'] = max(outgoing)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_outgoing_Interval_min'] = min(outgoing)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_outgoing_Interval_1stQuartile'] = np.percentile(outgoing,25)
		features['Packet_outgoing_Interval_3rdQuartile'] = np.percentile(outgoing,75)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_incoming_Interval_avg'] = sum(incoming) / len(incoming)
	except Exception as e:
		FAILED = 1
	try:	
		features['Packet_incoming_Interval_std'] = np.std(incoming)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_incoming_Interval_median'] = np.percentile(incoming,50)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_incoming_Interval_max'] = max(incoming)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_incoming_Interval_min'] = min(incoming)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_incoming_Interval_1stQuartile'] = np.percentile(incoming,25)
		features['Packet_incoming_Interval_3rdQuartile'] = np.percentile(incoming,75)
	except Exception as e:
		FAILED = 1
	try:
		(ca,cd) = pywt.dwt(AllInterval,'db1',mode='sym')
		features['wavelet_All_Interval_avg_ca'] = sum(ca) / len(ca)
		features['wavelet_All_Interval_std_ca'] = np.std(ca)
		features['wavelet_All_Interval_max_ca'] = max(ca)
		features['wavelet_All_Interval_min_ca'] = min(ca)
		features['wavelet_All_Interval_median_ca'] = np.percentile(ca,50)
		features['wavelet_All_Interval_avg_cd'] = sum(cd) / len(cd)
		features['wavelet_All_Interval_std_cd'] = np.std(cd)
		features['wavelet_All_Interval_max_cd'] = max(cd)
		features['wavelet_All_Interval_min_cd'] = min(cd)
		features['wavelet_All_Interval_median_cd'] = np.percentile(cd,50)
	except Exception as e:
		FAILED = 1
	try:
		(ca,cd) = pywt.dwt(incoming,'db2',mode='sym')
		features['wavelet_incoming_Interval_avg_ca'] = sum(ca) / len(ca)
		features['wavelet_incoming_Interval_median_ca'] = np.percentile(ca,50)
		features['wavelet_incoming_Interval_max_ca'] = max(ca)
		features['wavelet_incoming_Interval_min_ca'] = min(ca)
		features['wavelet_incoming_Interval_std_ca'] = np.std(ca)
		features['wavelet_incoming_Interval_avg_cd'] = sum(cd) / len(cd)
		features['wavelet_incoming_Interval_median_cd'] = np.percentile(cd,50)
		features['wavelet_incoming_Interval_max_cd'] = max(cd)
		features['wavelet_incoming_Interval_min_cd'] = min(cd)
		features['wavelet_incoming_Interval_std_cd'] = np.std(cd)
	except Exception as e:
		FAILED = 1
	try:
		(ca,cd) = pywt.dwt(outgoing,'db3',mode='sym')
		features['wavelet_outgoing_Interval_avg_ca'] = sum(ca) / len(ca)
		features['wavelet_outgoing_Interval_median_ca'] = np.percentile(ca,50)
		features['wavelet_outgoing_Interval_max_ca'] = max(ca)
		features['wavelet_outgoing_Interval_min_ca'] = min(ca)
		features['wavelet_outgoing_Interval_std_ca'] = np.std(ca)
		features['wavelet_outgoing_Interval_avg_cd'] = sum(cd) / len(cd)
		features['wavelet_outgoing_Interval_median_cd'] = np.percentile(cd,50)
		features['wavelet_outgoing_Interval_max_cd'] = max(cd)
		features['wavelet_outgoing_Interval_min_cd'] = min(cd)
		features['wavelet_outgoing_Interval_std_cd'] = np.std(cd)
	except Exception as e:
		FAILED = 1		
	return FAILED

##########################################
# get number of packet sent every second #
##########################################
def PacketSecondFeature(data,features):
	FAILED = 0
	starttime = float(data[0][0])
	packetSecond = [0] * max(1,(math.ceil(float(data[-1][0]) - starttime)))
	for t in data:
		roundt = math.floor(float(t[0])-starttime)
		packetSecond[roundt] += 1
	try:
		features['Packet_Second_avg'] = sum(packetSecond) / len(packetSecond)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_Second_max'] = max(packetSecond)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_Second_min'] = min(packetSecond)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_Second_std'] = np.std(packetSecond)
	except Exception as e:
		FAILED = 1
	try:
		features['Packet_Second_median'] = np.percentile(packetSecond,50)
	except Exception as e:
		FAILED = 1
	return FAILED

def TimestampFeature(data,features,IPSet):
	FAILED = 0
	Alltrace = [float(x[0]) for x in data]
	Intrace = [float(x[0]) for x in data if x[1] in IPSet]
	Outtrace = [float(x[0]) for x in data if x[3] in IPSet]
	try:
		features['Timestamp_All_1Quartile'] = np.percentile(Alltrace,25)
		features['Timestamp_All_2Quartile'] = np.percentile(Alltrace,50)
		features['Timestamp_All_3Quartile'] = np.percentile(Alltrace,75)
	except Exception as e:
		FAILED = 1
	try:
		features['Timestamp_Incoming_1Quartile'] = np.percentile(Intrace,25)
		features['Timestamp_Incoming_2Quartile'] = np.percentile(Intrace,50)
		features['Timestamp_Incoming_3Quartile'] = np.percentile(Intrace,75)
	except Exception as e:
		FAILED = 1
	try:
		features['Timestamp_Outgoing_1Quartile'] = np.percentile(Outtrace,25)
		features['Timestamp_Outgoing_2Quartile'] = np.percentile(Outtrace,50)
		features['Timestamp_Outgoing_3Quartile'] = np.percentile(Outtrace,75)
	except Exception as e:
		FAILED = 1
	try:
		features['TotalTime'] = Alltrace[-1] - Alltrace[0]
	except Exception as e:
		FAILED = 1
	return FAILED

def FeatureRetrieve(data,IPSet,inputfilepath):
	TimeDict = dict(TimeFeature)
	if len(data) == 0:
		WriteLog("%s :Error occur in FlowFeature"%(inputfilepath))
		return TimeDict
	try:
		if PacketSecondFeature(data,TimeDict) == 1:
			WriteLog("%s :Error occur in PacketSecondFeature"%(inputfilepath))
	except Exception as e:
		print("[TimeFeature]PacketSecondFeature caught division zero")
	try:
		if FlowFeature(data,TimeDict,IPSet) == 1:
			WriteLog("%s :Error occur in FlowFeature"%(inputfilepath))
	except Exception as e:
		print("[TimeFeature]FlowFeature caught division zero")
	try:
		if PacketIntervalFeature(data,TimeDict,IPSet) == 1:
			WriteLog("%s : Error occur in PacketIntervalFeature"%(inputfilepath))
	except Exception as e:
		print("[TimeFeature]PacketIntervalFeature caught division zero")
	try:
		if TimestampFeature(data,TimeDict,IPSet) == 1:
			WriteLog("%s : Error occur in PacketIntervalFeature"%(inputfilepath))
	except Exception as e:
		print("[TimeFeature]TimestampFeature caught Exception")		
	return TimeDict
