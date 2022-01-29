#!/bin/bash

docker run --privileged -v $2:/root/nslab/rawTraffic -d $1
