#!/bin/bash

# run in sudo mode
if [ $1 == "init" ] ; then
	groupadd pcap
	usermod -a -G pcap nonrootuser
	chgrp pcap /usr/sbin/tcpdump
	chmod 750 /usr/sbin/tcpdump
	setcap cap_net_raw,cap_net_admin=eip /usr/sbin/tcpdump
fi

sudo ifconfig eth0 mtu 1500
sudo ethtool -K eth0 tx off rx off tso off gso off gro off lro off
