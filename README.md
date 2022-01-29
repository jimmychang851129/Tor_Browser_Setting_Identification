# Know your Victim: Tor Browser Setting Identification via Network Traffic Analysis

## Objective

- Implement a crawler that can collect the website traffic with different browser settings
- A naive browser classifier implementation to predict the Tor browser version and security setting given network traffic
- Code for feature extraction given the raw network pcap file
- Verify that Tor browser settings have notable impact on network traffic patterns

## Dataset

- Google drive: https://drive.google.com/drive/folders/1dB7FJGCpHzYL1CnevsV-sLqHcx-zs-l8?usp=sharing

version and security setting datasets are included in the link

## Crawler Setup

### Docker

```
$ change Config.py(torbrowser directory to either torbrowser_902 | torbrowser_806 | torbrowser_752)
$ change Dockerfile, change argument of setup.sh to the specific torbrowser version
$ docker build -t <imageName> .
$ ./run.sh <image_name> <container_name> <outputdir>(volume)
```

## Feature Exctraction

```
$ pip3 install -r requirements.txt
$ python3 FeatureExtract.py -i <TrafficDir> -o <outputdir>

<TrafficDir>: in csv form(the output of pcapParser)
```

## Random forest based Browser Setting classifier

```
$ pip3 install -r requirements.txt
$ cd code/ml/
$ configure the MLConfig.py
$ python3 browserClassifier.py -i <Traffic feature dir, the outputdir of feature extraction> -o <outputdir>
```