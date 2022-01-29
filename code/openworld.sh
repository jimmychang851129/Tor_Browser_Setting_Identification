#!/bin/bash

ethtool -K eth0 tx off rx off tso off gso off gro off
python3 crawl.py --openworld --setting safest -c $1