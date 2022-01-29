#!/bin/bash

if [ $2 == "aws" ] ; then
	sudo apt update
	sudo apt install -y python3-pip xvfb x11-utils firefox
	sudo apt install -y chromium-chromedriver chromium-browser
elif [ $2 == "docker" ] ; then
	apt-get update && apt-get install -y net-tools tcpdump python3-pip xvfb x11-utils firefox wget ethtool libgtk2.0-0
fi

mkdir result
mkdir logs
mkdir rawTraffic
mkdir traces
pip3 install -r requirements.txt

if [ $1 == "10" ] ; then
	mv /usr/sbin/tcpdump /usr/bin/tcpdump
	wget https://www.dropbox.com/s/446kgtw3w60luni/driverSetup_1052.tar.gz
	driverTar=driverSetup_1052.tar.gz
	driverfile=driverSetup_1052
	fname=torbrowser_1052
	tarname=tor-browser-linux64-10.5.2_en-US.tar.xz
	fullpathgeckdriver=driverSetup_1052/geckodriver.tar.gz
	geckdriver=geckodriver.tar.gz
elif [ $1 == "9" ] ; then
	mv /usr/sbin/tcpdump /usr/bin/tcpdump
	wget https://www.dropbox.com/s/h6ui9b1j73bbm1z/driverSetup_902.tar.gz
	driverTar=driverSetup_902.tar.gz
	driverfile=driverSetup_902
	fname=torbrowser_902
	tarname=tor-browser-linux64-9.0.2_en-US.tar.xz
	fullpathgeckdriver=driverSetup_902/geckodriver-v0.23.0-linux64.tar.gz
	geckdriver=geckodriver-v0.23.0-linux64.tar.gz
elif [ $1 == "8" ] ; then
	wget https://www.dropbox.com/s/erw7wdnnjxy92f4/driverSetup_806.tar.gz
	driverTar=driverSetup_806.tar.gz
	driverfile=driverSetup_806
	tarname=tor-browser-linux64-8.0.6_en-US.tar.xz
	fname=torbrowser_806
	fullpathgeckdriver=driverSetup_806/geckodriver-v0.23.0-linux64.tar.gz
	geckdriver=geckodriver-v0.23.0-linux64.tar.gz
elif [ $1 == "7" ] ; then
	wget https://www.dropbox.com/s/kmxfs2okxwjb0pk/driverSetup_752.tar.gz
	driverTar=driverSetup_752.tar.gz
	driverfile=driverSetup_752
	fname=torbrowser_752
	tarname=tor-browser-linux64-7.5.2_en-US.tar.xz
	fullpathgeckdriver=driverSetup_752/geckodriver-v0.17.0-linux64.tar.gz
	geckdriver=geckodriver-v0.17.0-linux64.tar.gz
fi

tar zxvf $driverTar
rm $driverTar
mv $driverfile/$tarname .
mv $fullpathgeckdriver .
mv $driverfile/profile.default.tar.gz .
tar Jxvf $tarname
tar zxvf $geckdriver

if [ $2 == "aws" ] ; then
	sudo mv geckodriver /usr/local/bin
elif [ $2 == "docker" ] ; then
	mv geckodriver /bin/
fi

mv tor-browser_en-US $fname
rm -rf $fname/Browser/TorBrowser/Data/Browser/profile.default
tar zxvf profile.default.tar.gz
mv profile.default $fname/Browser/TorBrowser/Data/Browser/
rm $tarname
rm $geckdriver
rm -rf $driverfile
rm profile.default.tar.gz

echo $fname
echo "Finish initialize: tbb version ${1}" > finish.txt
