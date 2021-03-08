# Collecting IAM policies and the attached entities

This research project addresses the problem of detecting identity and access management misconfigurations in cloud
environments, more specifically AWS environments. Our goal is to develop a novel misconfiguration detection system that
is able to detect misconfigurations in a fully automated, proactive and generic way.

In order to develop this system, we first need to collect data. Therefore, we have written this python code. In this
document we will further elaborate on what will be collected and how to run to data collection code.

## Table of contents

1. [Goal](#goal)
1. [Data Collection](#data)
2. [Requirements](#requirements)
3. [Usage](#usage)

## Goal

The goal of this research project is to develop a novel detection system to detect identity and access management (IAM)
misconfigurations in cloud resources. We want to do this in a fully automated, proactive, generic and low effort way.
Therefore, detecting the misconfigurations before they can be abused to become major breaches. By running this program
you will be contributing in the development and validation of the detection system.

## Data Collection <a name="data"></a>

For the creation and validation of our proposed misconfiguration detection system, some prior data collection is needed.
The provided python code will collect the following data:

- Identity and Access Management (IAM) Policies
    * Policy name
    * Policy ID
    * Policy object
    * Date created
    * Date modified

And the entities attached to the policies which can be one of the following:

- Users
- Groups
- Roles

This data will be used to model the policies and the development of the detection system. 

TODO: Look at anonymizing the data, specifically the users.

## Requirements

First, to interact with the AWS environment, the installation and proper configuration of the AWS CLI is required. Also,
make sure to have the proper credentials for the AWS environment set in the ```credentials``` file in the ```~/.aws/```
directory. If you have not yet done this before, follow the instructions provided
here: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html

To run the code, [Python 3](https://www.python.org/) is required.

Furthermore, there is one required python package,
namely [pandas](https://pandas.pydata.org/pandas-docs/stable/index.html). In case you don't have pandas installed yet,
you can run the following command in your terminal:

```
pip install pandas 
```

If pip is not yet installed, you can find instructions here: https://pip.pypa.io/en/stable/installing/

## Usage

To execute the code, simply navigate to the directory where this project is saved and run the following command in your
terminal:

```
python retrieve_policydata.py
```

If you prefer to run the program from within your preferred IDE, you can also create run configuration in the IDE.

**Important**:
Depending on the size of the environment and the active services, the execution may take a while. Do not close the
terminal window or turn off your computer while the program is running. Once it is completed, a CSV file will be
exported to the output directory of this project, and the program will terminate itself.  
