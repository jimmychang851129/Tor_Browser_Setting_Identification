# create raw traces
# only retrieve tor node list ip
import dpkt
import socket
import random
import csv,os
import Config as cm
from utils import writeLog

def inet_to_str(inet):
  """ Convert inet object to a string """
  return socket.inet_ntop(socket.AF_INET, inet)

def retrieveInfo(cnt,ts,ip):
  output = [
      cnt,ts,inet_to_str(ip.src),inet_to_str(ip.dst),\
      ip.id,ip.hl,ip.p,ip.tos,ip.off,ip.len,ip.tcp.flags,\
      ip.tcp.sport,ip.tcp.dport,ip.tcp.seq,ip.tcp.ack
  ]
  return output

def ParsePcapFile(filepath,NodeList,outputpath):
  fw = open(outputpath,'w')
  fw.write(','.join(cm.packetinfo)+'\n')  # write header
  writeLog("parse filepath = %s"%(filepath))
  fp = open(filepath,'rb')
  try:
    pcap = dpkt.pcap.Reader(fp)
    cnt  = 0
    for ts,buf in pcap:
        eth = dpkt.ethernet.Ethernet(buf)
        ip = eth.ip
        ipsrc = inet_to_str(ip.src)
        ipdst = inet_to_str(ip.dst)
        if ipsrc in NodeList or ipdst in NodeList:
            output = retrieveInfo(cnt,ts,ip)
            fw.write(','.join([str(x) for x in output])+"\n")
            # fw.write('%s,%s,%s,%s,%s\n'%(str(ts),str(ipaddr),str(dstaddr),str(flag),str(datalen)))
        cnt += 1
  except Exception as e:
    writeLog("[pcaputils.py]ParsePcapFile error: %s"%(str(e)))
  finally:
    fp.close()