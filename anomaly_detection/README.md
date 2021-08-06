# Anomaly Detection
This directory contains the code used for the four anomaly detection algorithms described and evaluated in our paper.
We provide a separate file for each anomaly detection algorithm:
 * `isolation_forest.py` contains the code for the Isolation Forest algorithm.
 * `local_outlier_factor.py` contains the code for the Local Outlier Factorization algorithm.
 * `one_class_svm.py` contains the code for the One-class Support Vector Machine algorithm.
 * `robust_covariance.py` contains the code for the Elliptic Envelope algorithm.

## Dependencies
The scripts used for anomaly detection require the following Python libraries to be installed:
 * [neo4j](https://pypi.org/project/neo4j/)
 * [pandas](https://pandas.pydata.org/)
 * [scikit-learn](https://scikit-learn.org/stable/index.html)

```
pip install neo4j pandas scikit-learn
```

## Setup
Each script is structured as follows:
 1. Load data from Neo4j database
 2. Split data into train and test sets
 3. Perform anomaly detection
 4. Print out performance

## Auxiliary methods
Functions for loading data and performing the train-test split are provided in the `utils.py` file.
