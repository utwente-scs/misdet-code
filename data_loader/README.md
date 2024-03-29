## Load IAM policies and the attached entities
We provide code for loading Microsoft Excel data and turning it into a Neo4j graph as well as for updating an existing graph with new data.
We provide the following scripts:
 * `load_data.py` which loads data from a given file and creates a Neo4j graph out of this data.
 * `update_data.py` which loads data from a given file and updates an existing Neo4j graph from this data.

## Dependencies
The scripts used for anomaly detection require the following Python libraries to be installed:
 * [pandas](https://pandas.pydata.org/)
 * [py2neo](https://py2neo.org/2021.1/)
 * [tqdm](https://tqdm.github.io/)

```
pip install pandas py2neo tqdm
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

### Loading data
To load data into a graph, please run `load_data.py`.

#### Connect to correct database instance
Note that the script will attempt to connect to a Neo4j database instance.
By default, we connect to the following instance, with the following credentials:
```python
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
```
Please modify this line in the `__main__` function of the script to connect to your database instance with the correct credentials.

#### Different dataset
The current implementation loads the data from the path `../collector/example/iam_policy_data_2021-03-26_14:11.xlsx`, to change this to a custom file, please change the following line in the `__main__` function of the script.
```python
# Load data from stored files
df_policies, df_users, df_groups, df_roles = load_excel("../collector/example/iam_policy_data_2021-03-26_14:11.xlsx")
```

### Updating a graph
To update an existing graph with new data, please run `update_data.py`.

#### Connect to correct database instance
Note that the script will attempt to connect to a Neo4j database instance.
By default, we connect to the following instance, with the following credentials:
```python
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
```
Please modify this line in the `__main__` function of the script to connect to your database instance with the correct credentials.

#### Different dataset
The current implementation loads the original data from the path `../collector/example/iam_policy_data_2021-03-26_14:11.xlsx`,
and the updated data from the path `../collector/example/iam_policy_data_2021-03-26_14:11.xlsx`.
To change these inputs to custom files, please change the following lines in the `__main__` function of the script.
```python
df_policies, df_users, df_groups, df_roles = load_excel('../collector/example/iam_policy_data_2021-03-26_14:11.xlsx')
new_df_policies, new_df_users, new_df_groups, new_df_roles = load_excel('../collector/example/iam_policy_data_2021-03-26_14:11.xlsx')
```

### Graph embedding
**Important**: To run any of the anomaly detection algorithms, we must create the graph embedding through the Neo4j database, otherwise we will miss some features.
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
