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

### Neo4j database
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

## Usage
To evaluate an anomaly detection algorithm, simply run the corresponding python script.
E.g.,
```
python3 isolation_forest.py
```

### Graph embedding
**Important**: To run any of the anomaly detection algorithms, we must create the graph embedding through the Neo4j database (see the README.md file in the `data_loader/` directory), otherwise we will miss some features.
To create the graph embedding for each policy node, we run the following command on the Neo4j database:
```
CALL gds.beta.node2vec.write({
  nodeProjection: "Policy",
  relationshipProjection: {
    contains: {
      type: "CONTAINS",
      orientation: "NATURAL"
    },
    works_on: {
      type: "WORKS_ON",
      orientation: "NATURAL"
    }
  },
  embeddingDimension: 128,
  iterations: 100,
  walkLength: 5000,
  writeProperty: "embeddingNode2vec"
})
```

This command will create a variable `embeddingNode2vec` for each `Policy` node, which we will use during anomaly detection.


### Connect to correct database instance
Note that the scripts will attempt to connect to a Neo4j database instance.
By default, we connect to the following instance, with the following credentials:
```python
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
```
Please modify this line in the ``__main__`` function of a script to connect to your database instance with the correct credentials.

### Perform train-test split with own data
The current implementation splits the data using the default `misconfigurations` parameter in the `split_data()` function from `utils.py`.
In case you use a different dataset, please specify the policy names of the misconfigurations as a list. E.g.,
```python
# Split into train and test sets
X_train, X_test, y_train, y_test = split_data(embedded_nodes, misconfigurations=[
    'policy name 1',
    'policy name 2',
    '...',
    'policy name n',
])
```

## Setup
Each script is structured as follows:
 1. Load data from Neo4j database
 2. Split data into train and test sets
 3. Perform anomaly detection
 4. Print out performance

## Auxiliary methods
Functions for loading data and performing the train-test split are provided in the `utils.py` file.
