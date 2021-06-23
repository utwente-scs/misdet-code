# Automatically detecting IAM misconfigurations in cloud resources

This research project addresses the problem of detecting identity and access management misconfigurations in cloud
environments, more specifically AWS environments. Our goal is to develop a novel misconfiguration detection system that
is able to detect misconfigurations in a fully automated, proactive and generic way.

This repository consists of multiple python scripts that each have their own purpose, namely:

- [Data Collector](collector): Code to retrieve the needed data 
- [Data Loader](data_loader): Code to load the data into the graph model
- [Anomaly Detector](anomaly_detection): Code to perform anomaly detection