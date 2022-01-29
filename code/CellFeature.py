import numpy as np
from FeatureUtils import WriteLog
#############
# Reference #
#############
# k-fingerprint: https://github.com/AxelGoetz/website-fingerprinting/
# Info leak: https://arxiv.org/pdf/1710.06080.pdf

##########
# config #
##########
concentration_chunk = 20

CellFeature = {
	"Num_Packet":-1,
	"Num_outgoinging_packet":-1,
	"Num_incoming_packet":-1,
	"outgoing_ratio":-1,
	"incoming_ratio":-1,
	"std_outgoing_packetOrder":-1,
	"avg_outgoing_packetOrder":-1,
	"std_incoming_packetOrder":-1,
	"avg_incoming_packetOrder":-1,
	"Concentrate_outgoing_avg":-1,	# concentrate the outgoing packet(find peak)
	"Concentrate_incoming_med":-1,
	"Concentrate_outgoing_med":-1,
	"Concentrate_incoming_avg":-1,
	"Concentrate_outgoing_std":-1,	# concentrate the outgoing packet(find peak)
	"Concentrate_incoming_std":-1,
	"Concentrate_outgoing_max":-1,	# concentrate the outgoing packet(find peak)
	"Concentrate_incoming_max":-1,
	"Num_Flow":-1,
	"Num_Packet_flow_avg":-1,	# average number of packet between direction changes
	"Num_Packet_flow_std":-1,
	"Num_Packet_flow_max":-1,
	"Num_Packet_flow_median":-1,
	"First30_incoming":-1,	# first 30 packets: num of incoming
	"First30_outgoing":-1,	# first 30 packets: num of outgoing
	"Last30_incoming":-1,	# last 30 packets: num of incoming
	"Last30_outgoing":-1,		# last 30 packets: num of outgoing
	"burst_avg":-1,
	"burst_std":-1,
	"burst_max":-1,
	"burst_min":-1,
	"burst_median":-1,
	"num_burst":-1
}

# median of concentration(? only few chunks

# get number of cells
# It kinds of weird to say 1400 bytes packet have 3 cells (?)
# from https://drive.google.com/open?id=1NdSn-r8jD3IBJuMOa-gZtWm0ftHVDLXl
def NumOfCell(packetlen):
	return round(int(packetlen) / 512)

# flow [timestamp,srcip,srcport,dstip,dstport,packetlen]
def Flow_Recognition(data,features):
	FAILED = 0
	packet_cntList = []
	s,cnt,packet_cnt = 0,0,0
	for t in data:
		if (t[1],t[2],t[3],t[4]) != s:
			s = (t[1],t[2],t[3],t[4])
			cnt += 1
			if packet_cnt != 0:
				packet_cntList.append(packet_cnt)
			packet_cnt = 0
		packet_cnt += NumOfCell(t[-1])
	packet_cntList.append(packet_cnt)
	features['Num_Flow'] = cnt
	try:
		features['Num_Packet_flow_avg'] = sum(packet_cntList) / len(packet_cntList)
	except Exception as e:
		FAILED = 1
	try:
		features['Num_Packet_flow_std'] = np.std(packet_cntList)
	except Exception as e:
		FAILED = 1
	try:
		features['Num_Packet_flow_max'] = max(packet_cntList)
	except Exception as e:
		FAILED = 1		
	try:
		features['Num_Packet_flow_median'] = np.percentile(packet_cntList,50)
	except Exception as e:
		FAILED = 1
	return FAILED

def PacketConcentration(data,features,IPSet):
	FAILED = 0
	outgoing,incoming = [],[]
	chunks = [data[x:x+concentration_chunk] for x in range(0, len(data), concentration_chunk)]
	for chunk in chunks:
		outgoing.append(len([x for x in chunk if x[3] in IPSet]))
		incoming.append(len([x for x in chunk if x[1] in IPSet]))
	try:
		features['Concentrate_incoming_avg'] = sum(incoming) / len(incoming)
	except Exception as e:
		FAILED = 1
	try: 
		features['Concentrate_outgoing_avg'] = sum(outgoing) / len(outgoing)
	except Exception as e:
		FAILED = 1
	try:
		features['Concentrate_incoming_med'] = np.percentile(incoming,50)
	except Exception as e:
		FAILED = 1
	try:
		features['Concentrate_outgoing_med'] = np.percentile(outgoing,50)
	except Exception as e:
		FAILED = 1
	try:
		features['Concentrate_incoming_std'] = np.std(incoming)
	except Exception as e:
		FAILED = 1
	try:
		features['Concentrate_outgoing_std'] = np.std(outgoing)
	except Exception as e:
		FAILED = 1
	try:
		features['Concentrate_incoming_max'] = max(incoming)
	except Exception as e:
		FAILED = 1
	try:
		features['Concentrate_outgoing_max'] = max(outgoing)
	except Exception as e:
		FAILED = 1
	return FAILED


def getPacketCount(data,features,IPSet):
	incoming,outgoing = [],[]
	sum_incoming = 0
	sum_outgoing = 0
	Allcnt = 0
	FAILED = 0
	for t in data:
		cnt = NumOfCell(t[5])
		if t[1] in IPSet:	# srcIP
			incoming += [x+Allcnt for x in range(cnt)]
		else:
			outgoing += [x+Allcnt for x in range(cnt)]
		Allcnt += cnt
	features['Num_Packet'] = len(incoming) + len(outgoing)
	features['Num_outgoinging_packet'] = len(outgoing)
	features['Num_incoming_packet'] = len(incoming)
	features['outgoing_ratio'] = len(outgoing) / features['Num_Packet']
	features['incoming_ratio'] = len(incoming) / features['Num_Packet']
	try:
		features['avg_incoming_packetOrder'] = sum(incoming) / len(incoming)
	except Exception as e:
		FAILED = 1
	try:
		features['std_incoming_packetOrder'] = np.std(incoming)
	except Exception as e:
		FAILED = 1
	try:
		features['avg_outgoing_packetOrder'] = sum(outgoing) / len(outgoing)
	except Exception as e:
		FAILED = 1
	try:
		features['std_outgoing_packetOrder'] = np.std(outgoing)
	except Exception as e:
		FAILED = 1
	features['First30_incoming'] = len([x for x in data[:30] if x[1] in IPSet])
	features['First30_outgoing'] = len([x for x in data[:30] if x[3] in IPSet])
	features['Last30_incoming'] = len([x for x in data[-30:] if x[1] in IPSet])
	features['Last30_outgoing'] = len([x for x in data[-30:] if x[3] in IPSet])
	return FAILED

def getBurst(data,features,IPSet):
	cur_burst,should_stop = 0,0
	FAILED = 0
	burstlist = []
	for c in data:
		if c[3] in IPSet:
			cur_burst += NumOfCell(int(c[5]))
			should_stop = 0
		if c[1] in IPSet:
			should_stop += NumOfCell(int(c[5]))
			if should_stop > 0:
				if cur_burst != 0:
					burstlist.append(cur_burst)
					cur_burst = 0
				should_stop = 0
	if cur_burst != 0:
		burstlist.append(cur_burst)
	try:
		features['burst_avg'] = sum(burstlist) / len(burstlist)
		features['burst_std'] = np.std(burstlist)
		features['burst_max'] = max(burstlist)
		features['burst_min'] = min(burstlist)
		features['burst_median'] = np.percentile(burstlist,50)
		features['num_burst'] = len(burstlist)
		# print("feature = ",features['burst_avg'],features['burst_std'],features['burst_median'])
	except Exception as e:
		FAILED = 1
	return FAILED

#######################
# retrieve cells info #
#######################
# https://witestlab.poly.edu/blog/de-anonymizing-tor-traffic-with-website-fingerprinting/
def FeatureRetrieve(data,IPSet,inputfilepath):
	cellsDict = dict(CellFeature)
	if len(data) == 0:
		WriteLog("%s : Error occur: zero data"%(inputfilepath))
		return cellsDict
	try:
		if getPacketCount(data,cellsDict,IPSet) == 1:
			WriteLog("%s : Error occur in getPacketCount"%(inputfilepath))
	except Exception as e:
		print("[getPacketCount] caught division zero")
	try:
		if PacketConcentration(data,cellsDict,IPSet) == 1:
			WriteLog("%s : Error occur in PacketConcentration"%(inputfilepath))
	except Exception as e:
		print("[PacketConcentration] caught division zero")
	try:
		if Flow_Recognition(data,cellsDict) == 1:
			WriteLog("%s : Error occur in Flow_Recognition"%(inputfilepath))
	except Exception as e:
		print("[Flow_Recognition] caught division zero")
	try:
		if getBurst(data,cellsDict,IPSet) == 1:
			WriteLog("%s : Error occur in getBurst"%(inputfilepath))
	except Exception as e:
		print("[getBurst] caught division zero")
	return cellsDict
