# Automatic Detection of Misconfigurations of AWS Identity and Access Management Policies
This repository contains the code for Automatic Detection of Misconfigurations of AWS Identity and Access Management Policies [[1]](#References).
Please [cite](#References) our work when using this code for academic publications.

## Introduction
Security misconfigurations are one of the biggest threats to cloud environments.
In recent years, misconfigurations of cloud services have led to major security incidents and large scale data breaches.
Proper configuration of identity and access management services is essential in maintaining a secure cloud environment.
Due to the dynamic and complex nature of cloud environments, misconfigurations can be easily introduced and often go undetected for a long period of time.
Therefore, it is critical to identify any potential misconfigurations before they can be abused.

In this work, we present a novel misconfiguration detection approach for identity and access management policies in AWS.
We base our approach on the observation that policies can be modeled as permissions between entities and objects in the form of a graph.
Our idea is that misconfigurations present overly permissive behaviors, which can be effectively detected as anomalies in such a graph representation.
We evaluate our approach on real-world identity and access management policy data from three enterprise cloud environments.
Our paper demonstrates its effectiveness to detect misconfigurations that has a slightly lower precision compared to rule-based systems, but is able to correctly detect between 3.7 and 6.4 times as many misconfigurations.

## Overview
This repository consists of multiple python scripts that each have their own purpose, namely:

- [Data Collector](collector): Code used to retrieve our required data
- [Data Loader](data_loader): Code to load data into our graph model
- [Anomaly Detector](anomaly_detection): Code to perform anomaly detection

## References
<Anonymized>
