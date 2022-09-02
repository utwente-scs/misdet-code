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

- [Anomaly Detector](anomaly_detection): Code to perform anomaly detection (Sections 5.2-5.5 of paper).
- [Cloud Custodian](cloud_custodian): Code used for the cloud custodian experiment (Section 5.2 of paper).
- [Data Collector](collector): Code used to retrieve our required data (Sections 3.2-3.3 and 4.1-4.2 of paper).
- [Data Loader](data_loader): Code to load data into our graph model (Sections 3.2-3.3 and 4.1-4.2 of paper).

Each directory contains a `README.md` file explaining how to use the artifacts of that directory.

### Workflow
Our approach works in the following steps:
 1. Collect data from the AWS environment using the [Data Collector](collector).
 2. Load the collected data into the Neo4j database using the [Data Loader](data_loader).
 3. Apply the graph embedding in the Neo4j database (see [Data Loader](data_loader) README.md file).
 4. Perform the anomaly detection using the [Anomaly Detector](anomaly_detection).

## Download and installation
Currently, you can only download our code from this GitHub repository.
To download the code, please clone this repository or [download](https://github.com/utwente-scs/misdet-code/archive/refs/heads/master.zip) the repository as a zip archive.

```
git clone git@github.com:utwente-scs/misdet-code.git
```

### Dependencies

#### AWS
First, to interact with the AWS environment, the installation and proper configuration of the AWS CLI is required. Also,
make sure to have the proper credentials for the AWS environment set in the ```credentials``` file in the ```~/.aws/```
directory. If you have not yet done this before, follow the instructions provided
here: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html.  
The easiest way to verify whether the CLI is configured properly, is by running the following command:

```
aws sts get-caller-identity
```

#### Neo4j database
Our code works with a Neo4j database including the Graph Data Science plugin.
The most straightforward way of setting up such a database is with [docker](https://neo4j.com/developer/docker/):
```
docker run -p7474:7474 -p7687:7687 -e NEO4J_AUTH=neo4j/password --env NEO4JLABS_PLUGINS='["graph-data-science"]' neo4j
```

Note that in our code, we use the credentials:
```
username: neo4j
password: password
```
In case you setup your own database using different credentials, please change the credentials in the code as well.
The README.md files of each individual directory indicate which lines have to be changed.

#### Python environment
Our code requires [Python3](https://www.python.org/) and the following Python libraries to be installed (see individual directories for specific requirements of experiments):
 * [argformat](https://pypi.org/project/argformat/)
 * [neo4j](https://pypi.org/project/neo4j/)
 * [numpy](https://numpy.org/)
 * [openpyxl](https://openpyxl.readthedocs.io/en/stable/)
 * [pandas](https://pandas.pydata.org/)
 * [py2neo](https://py2neo.org/2021.1/)
 * [scikit-learn](https://scikit-learn.org/stable/index.html)
 * [tqdm](https://tqdm.github.io/)

```
pip install argformat neo4j numpy openpyxl pandas py2neo scikit-learn tqdm
```

## Usage
Please see the `README.md` files in each individual directory for instructions on how to use the separate artifacts.

## References
[1] `Thijs van Ede, Niek Khasuntsev, Bas Steen, and Andrea Continella. 2022. Detecting Anomalous Misconfigurations in AWS Identity and Access Management Policies. In Proceedings of CCSW 2022.`

### Bibtex
```
@inproceedings{vanede2022misdet,
  title={Detecting Anomalous Misconfigurations in AWS Identity and Access Management Policies},
  author={van Ede, Thijs and Khasuntsev, Niek and Steen, Bas and Continella, Andrea},
  booktitle={Proceedings of CCSW 2022},
  year={2022},
  organization={ACM}
}
```
