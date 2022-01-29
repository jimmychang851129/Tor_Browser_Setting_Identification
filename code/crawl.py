from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.utils import start_xvfb,stop_xvfb
import subprocess,os
from tbselenium.utils import launch_tbb_tor_with_stem
import Config as cm
from utils import ReadWebList, getTime, get_tor_circuits, SetOutputPath, writeLog, RemoveTmpFile, getGuard, writeStreamInfo
from utils import TimeExceededError, timeout, cancel_timeout, TorSetupError, TBBSetupError
from utils import ReadOpenWebList, RemoveProcess
from utils import StreamProcessing, removepcapfile, tarNetworkTraffic, MoveLogFile
from stem.control import Controller
import time, sys
from os.path import join
import pathlib
from selenium import webdriver
import argparse
from selenium.webdriver import DesiredCapabilities
from pcapParser import parseAllpcap

#####################
# tor browser setup #
#####################
def TBBSetup(driverpath,controller,idx,settings,language):
	driver = 0
	try:
		if settings == 'safer':
			driver = TorBrowserDriver(driverpath,tor_cfg=cm.USE_STEM,pref_dict=cm.safersetting)
		elif settings == 'safest':
			driver = TorBrowserDriver(driverpath,tor_cfg=cm.USE_STEM,pref_dict=cm.safestsetting)
		else:
			langsetting = dict()
			if language != '':
				if language == 'ch':
					langsetting["intl.locale.requested"] = "zh-CN,en-US"
					langsetting['intl.accept_languages'] = 'zh-CN,zh,en-US,en'
				elif language == 'es':
					langsetting["intl.locale.requested"] = "es-ES,en-US"
					langsetting['intl.accept_languages'] = 'es-ES,es,en-US,en'
				elif language == 'en':
					langsetting['intl.accept_languages'] = 'en-US,en'
				driver = TorBrowserDriver(driverpath,tor_cfg=cm.USE_STEM,pref_dict=langsetting)
			else:
				driver = TorBrowserDriver(driverpath,tor_cfg=cm.USE_STEM)
	except Exception as e:
		writeLog("[crawl.py error]TBBSetup error: "+str(e))
		print("[crawl.py error]TBBSetup error")
		print(str(e))
		driver = 0
	return driver

#########################
# firefox browser setup #
#########################
def FFSetup():
    profile = webdriver.FirefoxProfile()
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.socks", "localhost")
    profile.set_preference("network.proxy.socks_port", cm.TorSocksPort)
    driver = webdriver.Firefox(profile)
    return driver

########################
# Chrome browser setup #
########################
def ChromeSetup():
    options = webdriver.ChromeOptions()
    host = 'localhost'
    port = str(cm.TorSocksPort)
    options.add_argument("--proxy-server=socks5://" + host + ":" + port)
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(chrome_options = options)
    return driver

########################
# controller ,torsetup #
########################
# setup tor process and controller
def TorSetup(tor_binary):
	tor_process,controller = 0,0
	print("in tor setup binary = ",tor_binary)
	try:
		tor_process = launch_tbb_tor_with_stem(tbb_path=cm.driverpath, torrc=cm.TorConfig,
	                                           tor_binary=tor_binary)
		controller = Controller.from_port(port=int(cm.TorConfig['ControlPort']))
		controller.authenticate()
		print("getting tor circuit...")
		print("write entry guard/ circuit to log...")
	except Exception as e:
		print("[crawl.py error]TorSetup: "+str(e)+"\n")
		writeLog("[crawl.py error]TorSetup: "+str(e)+"\n")
		tor_process,controller = 0,0
	return tor_process,controller

####################
# close all stream #
####################
# close_all_streams
# remove temp file
# xvfb
def cleanupStream(controller,crawlcnt,domain):
	l = []
	for stream in controller.get_streams():
		l.append(stream.circ_id)
	d = getGuard(controller,l)
	for stream in controller.get_streams():
		try:
			writeStreamInfo("%s,%s,%s,%s,%s,%s,%s,%s"%(domain,crawlcnt,stream.id,stream.circ_id,d[stream.circ_id],stream.target_address,stream.target,str(stream.target_port)))
			controller.close_stream(stream.id)
		except Exception as e:
			writeLog("### error in closing stream: "+str(stream.id))
			pass

#########################
# launch tor with torrc #
#########################
# start a tor process
def launch_tor_with_custom_stem(datalist,opts):
	print("length of data: ",len(datalist))
	tor_binary = join(cm.TorProxypath, cm.DEFAULT_TOR_BINARY_PATH)
	tor_process,controller = 0,0
	try:
		TRYTOR_CNT = cm.TRYCNT
		while TRYTOR_CNT > 0 and tor_process == 0 and controller == 0:
		#	print("try to setup tor:",str(TRYTOR_CNT))
			tor_process,controller = TorSetup(tor_binary)
			TRYTOR_CNT -= 1
		if tor_process == 0:
			raise TorSetupError
		# print("finish tor proxy setup...")
		xvfb_display = start_xvfb()	# virtual display
		for ele in datalist:
			t = getTime()
			savepath,out_img = SetOutputPath(ele,t)
			p = 0
			try:
				driver,TRYCNT = 0,cm.TRYCNT
				while driver == 0 and TRYCNT != 0:
					print("try to setup tbb:",str(TRYCNT))
					args = (cm.driverpath,controller,ele[2],opts.securesetting,opts.language) if opts.browser == 'TBB' else ()
					options = {'TBB': TBBSetup, 'FF': FFSetup, 'CR': ChromeSetup}
					driver = options[opts.browser](*args)
					TRYCNT -= 1
				if driver == 0:
					raise TBBSetupError

				cmd = "tcpdump -i %s tcp and not port ssh -w %s"%(cm.netInterface,savepath)
				print('cmd = ',cmd)
				cmd = cmd.split(' ')
				p = subprocess.Popen(cmd)
				try:
					timeout(cm.VISITPAGE_TIMEOUT)
					driver.get('https://'+ele[0])
					cancel_timeout()
					time.sleep(cm.DURATION_VISIT_PAGE)
					p.terminate()
					#if(ele[2] == 0 or ele[2] == 2):
					#	driver.get_screenshot_as_file(out_img)
					writeLog(str(t)+","+ele[0]+","+str(ele[2]))
				except TimeExceededError:
					writeLog("Error crawling,"+ele[0]+","+str(ele[2])+"\n"+str("Page visit Timeout"))
				finally:
					cancel_timeout()
			except TBBSetupError:
				print("[crawl.py error]: unable to setup TBB")
				writeLog("[crawl.py error]: unable to setup TBB")
			except Exception as e:
				with open(cm.ErrorFilePath,'a+') as fw:
					fw.write(ele[0]+","+str(e)+"\n")
				writeLog("Error crawling,"+ele[0]+","+str(ele[2])+"\n"+str(e))
			finally:
				if p != 0 and p.returncode != 0:
					try:
						p.terminate()
					except Exception as e:
						writeLog("[crawl.py] tcpdump terminate error: "+str(e))
				if controller != 0:
					cleanupStream(controller,str(ele[2]),ele[0])
				if driver != 0:
					try:
						timeout(30)
						driver.quit()
						cancel_timeout()
					except Exception as e:
						cancel_timeout()
						writeLog("[crawl.py] driver quit error: "+str(e))
				if ele[2] != 3:
					time.sleep(cm.PAUSE_BETWEEN_INSTANCES)
				else:
					time.sleep(cm.PAUSE_BETWEEN_SITES)
				RemoveTmpFile()
				RemoveProcess()
	except TorSetupError:
		print("[crawl.py] unable to set up tor proxy")
		writeLog("[crawl.py] unable to set up tor proxy")
	except Exception as e:
		print("[crawl.py]launch_tor_with_custom_stem Error")
		print("Error:",str(e))
		writeLog("[crawl.py]launch_tor_with_custom_stem Error : "+str(e))
	finally:
		if tor_process != 0:
			tor_process.kill()
		stop_xvfb(xvfb_display)

def ParsePcapFile():
	StreamList = StreamProcessing(cm.StreamFile)
#	print("start parsing pcap file in %s to %s"%(cm.ResultDir,cm.pcapDir,))
	parseAllpcap(cm.ResultDir,StreamList,cm.pcapDir)
#	print("start compress traces...")
	outputtardir = tarNetworkTraffic(cm.pcapDir,cm.rawtrafficdir)	# tar the netowrk traffic save in rawtrafficdir
#	print("remove result_902/* , traces/* ...")
	removepcapfile([cm.ResultDir,cm.pcapDir])	# remove pcap and csv(with have tar the csv in rawTraffic)
#	print("move logs to %s"%(outputtardir))
	MoveLogFile(outputtardir)

#################
# main function #
#################
def main(opts):
	if opts.openworld == False:
		datalist = ReadWebList()
		datalen = len(datalist)
		for i in range(0,datalen,cm.MAX_SITES_PER_TOR_PROCESS):
			if i + cm.MAX_SITES_PER_TOR_PROCESS < datalen:
				writeLog("data start from %s to %s"%(datalist[i][0],datalist[i+cm.MAX_SITES_PER_TOR_PROCESS-1][0]))
				print("data start from %s to %s\n"%(datalist[i][0],datalist[i+cm.MAX_SITES_PER_TOR_PROCESS-1][0]))
				launch_tor_with_custom_stem(datalist[i:i+cm.MAX_SITES_PER_TOR_PROCESS], opts)
				ParsePcapFile()
			else:
				writeLog("data start from %s to %s"%(datalist[i][0],datalist[-1][0]))
				print("data start from %s to %s\n"%(datalist[i][0],datalist[-1][0]))
				launch_tor_with_custom_stem(datalist[i:], opts)
				ParsePcapFile()
	else:
		if opts.sted != "":
			st = int(opts.sted.split(',')[0])
			ed = int(opts.sted.split(',')[1])
			print("read open world data %d to %d\n"%(st,ed))
			datalist = ReadOpenWebList(st,ed,1)
		else:
			datalist = ReadOpenWebList(0,7000,1)	# 5000 sites for open world dataset, each with 1 instance
		datalen = len(datalist)
		print("len datalist for openworld = ",len(datalist))
		for i in range(0,datalen,cm.MAX_SITES_PER_TOR_PROCESS):
			if i + cm.MAX_SITES_PER_TOR_PROCESS < datalen:
				writeLog("data start from %s to %s"%(datalist[i][0],datalist[i+cm.MAX_SITES_PER_TOR_PROCESS-1][0]))
				print("data start from %s to %s\n"%(datalist[i][0],datalist[i+cm.MAX_SITES_PER_TOR_PROCESS-1][0]))
				launch_tor_with_custom_stem(datalist[i:i+cm.MAX_SITES_PER_TOR_PROCESS], opts)
				ParsePcapFile()
			else:
				writeLog("data start from %s to %s"%(datalist[i][0],datalist[-1][0]))
				print("data start from %s to %s\n"%(datalist[i][0],datalist[-1][0]))
				launch_tor_with_custom_stem(datalist[i:], opts)
				ParsePcapFile()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Crawler with Tor Proxy')
	parser.add_argument('--browser', default='TBB', 
			type=str, choices=['TBB','FF','CR'], dest='browser')
	parser.add_argument('--openworld',help='crawl OpenWorld Dataset',action='store_true')
	parser.add_argument('--test', '-t', help='test pcap file',action='store_true')
	parser.add_argument('--settings', '-s', help='security setting',type=str, choices=['','normal','safer','safest'], default='', dest='securesetting')
	parser.add_argument('--sted','-c',help='start and end of open world dataset',type=str,dest='sted')
	parser.add_argument('--language','-l', help="change language settings", type=str, default='', choices=['','ch','en','es'], dest='language')
	opts = parser.parse_args()
	main(opts)
