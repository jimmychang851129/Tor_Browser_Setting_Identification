#!/bin/bash

python3 pcapParser.py -i result_902 -o traces/

tar zcvf current_traces.tar.gz traces