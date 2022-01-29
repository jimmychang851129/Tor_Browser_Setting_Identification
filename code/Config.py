from os.path import join
import tempfile

#############
# tor setup #
#############
driverpath = "/root/nslab/torbrowser_1052"	# TBB browser path
TorProxypath = "/root/nslab/torbrowser_1052"	# Tor proxy path
DEFAULT_TOR_BINARY_PATH = join(driverpath,"Browser/TorBrowser/Tor/tor")

##########################
# dataset and output dir #
##########################
BaseDir = "/root/nslab"
Datapath = join(BaseDir,"Data/Tranco_WebList.csv")	# closed-world dataset
OpenWorldDataPath = join(BaseDir,"Data/openworlddata.csv")	# open-world dataset

pcapDir = join(BaseDir,"traces/")
ResultDir = join(BaseDir,"result")
netInterface = "eth0"
LogDir = join(BaseDir,"logs")
LogFile = join(LogDir,"log.txt")
ErrorFilePath = join(LogDir,'ErrorList.txt')
StreamFile = join(LogDir,"streamInfo.txt")
rawtrafficdir = join(BaseDir,'rawTraffic')

###################
# Feature Extract #
###################
StreamInfo = "logs/streamInfo.txt"

#########
# torrc #
#########
TorSocksPort = 9250

TorConfig = {
	'SocksPort': str(TorSocksPort),
	'ControlPort': str(9251),
	'MaxCircuitDirtiness': '600000',
	'UseEntryGuards': '0', # change entry node for every new connection
	'NumEntryGuards':'1',
	'DataDirectory':tempfile.mkdtemp()
}

safersetting = dict({
	"extensions.torbutton.security_slider":2,
	"gfx.font_rendering.graphite.enabled": False,
	"gfx.font_rendering.opentype_svg.enabled": False,
	"javascript.options.asm.js": False,
	"javascript.options.baselinejit":False,
	"javascript.options.ion": False,
	"javascript.options.native_regexp": False,
	"javascript.options.wasm": False,
	"mathml.disabled": True
})

safestsetting = dict({
	"extensions.torbutton.security_slider":1,
	"gfx.font_rendering.graphite.enabled": False,
	"gfx.font_rendering.opentype_svg.enabled": False,
	"javascript.options.asm.js": False,
	"javascript.options.baselinejit":False,
	"javascript.options.ion": False,
	"javascript.options.native_regexp": False,
	"javascript.options.wasm": False,
	"mathml.disabled": True,
	"svg.disabled": True
})

langsetting = dict({
	"app.update.download.attempts":0,
	"app.update.auto":False,
	"intl.accept_languages": "zh-CN,en-US,en",
	"intl.locale.requested": "zh-CN,en-US,en",
	"privacy.spoof_english": 1,
})

USE_STEM = 2  # use tor started with Stem
USE_RUNNING_TOR = 1  # use system tor or tor started with stem
MAX_SITES_PER_TOR_PROCESS = 400

VISITPAGE_TIMEOUT = 100
DURATION_VISIT_PAGE = 10
PAUSE_BETWEEN_SITES = 5
WAIT_IN_SITE = 10             # time to wait after the page loads

CLOST_STREAM_DURATION = 20 # close all stream in 20 sec
INSTANCE = 4
PAUSE_BETWEEN_INSTANCES = 4  # pause before visiting the same site (instances)

################
# Error handle #
################
TRYCNT = 3

#####################
# pcapParser config #
#####################
# version ip.v
# ihl: ip.hl
# protocol : ip.p
# ip.df, mf fregment
# tos: type of service
packetinfo = [
	"cnt","timestamp","srcip","dstip","id","ihl","protocol","tos","offset","packetlen",\
	"flags","srcport","dstport","seq","ack"
]

