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

### Anonymization

All personally identifiable data is being anonymized before it is saved in the export. More specifically, all the data
in regard to users, groups, and roles is cryptographically hashed using SHA256.

An example of the excel export of collected data can be found in the [example directory ](example) of this repository.

## Requirements

First, to interact with the AWS environment, the installation and proper configuration of the AWS CLI is required. Also,
make sure to have the proper credentials for the AWS environment set in the ```credentials``` file in the ```~/.aws/```
directory. If you have not yet done this before, follow the instructions provided
here: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html.  
The easiest way to verify whether the CLI is configured properly, is by running the following command:

```
aws sts get-caller-identity
```

This command will return the details about the IAM user or role whose credentials are used to call the operation.
Therefore, it will only succeed if the CLI is configured correctly.

To run the code, [Python 3](https://www.python.org/) is required.

Furthermore, there are two required python package:

[Pandas](https://pandas.pydata.org/pandas-docs/stable/index.html). In case you don't have pandas installed yet, you can
run the following command in your terminal:

```
pip install pandas 
```

[Openpyxl](https://openpyxl.readthedocs.io/en/stable/). In case you don't have openpyxl installed yet, you can run the
following command in your terminal:

```
pip install openpyxl 
```

If pip is not yet installed, you can find instructions here: https://pip.pypa.io/en/stable/installing/

If you are not using pip, install the above mentioned packages with the method of your choice (conda, VirtualEnv, etc.).

## Usage

To execute the code, simply navigate to the directory where this project is saved and run the following command in your
terminal:

```
python retrieve_policydata.py
```

If you prefer to run the program from within your preferred IDE, you can also create run configuration in the IDE.

### Timer

When running the code, there is also the possibility to run the code periodically by setting a timer. This can be simply
achieved by executing the code with an argument specifying the time (in hours) between executions. When running from the
terminal, it will look like this:

```
python retrieve_policydata.py 3
```

In this case, the data collection will be automatically repeated every 3 hours, and a new xlsx (Excel) export file will
be generated each time.

If you are not using the terminal, the timer argument can also be added in the run configuration of the IDE.

**Important**:
Depending on the size of the environment and the active services, the execution may take a while. Do not close the
terminal window or turn off your computer while the program is running. This is even more important when using the timer
functionality, do not interrupt the data collection. When no argument is passed, the data collection code will run once,
and then terminate. Once it is completed, a xlsx (Excel) file will be exported to the output directory of this project.  
