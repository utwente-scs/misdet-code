## Load IAM policies and the attached entities
We provide code for loading Microsoft Excel data and turning it into a Neo4j graph as well as for updating an existing graph with new data.
We provide the following scripts:
 * `load_data.py` which loads data from a given file and creates a Neo4j graph out of this data.
 * `update_data.py` which loads data from a given file and updates an existing Neo4j graph from this data.

## Dependencies
The scripts used for anomaly detection require the following Python libraries to be installed:
 * [pandas](https://pandas.pydata.org/)
 * [py2neo](https://py2neo.org/2021.1/)

```
pip install pandas py2neo
```

## Usage
