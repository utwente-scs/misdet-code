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
The current implementation loads the data from the path `./output/iam_policy_data_2021-04-09_10:15.xlsx`, to change this to a custom file, please change the following line in the `__main__` function of the script.
```python
# Load data from stored files
df_policies, df_users, df_groups, df_roles = load_excel("./output/iam_policy_data_2021-04-09_10:15.xlsx")
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
The current implementation loads the original data from the path `./output/iam_policy_data_2021-04-02_12:19.xlsx`,
and the updated data from the path `./output/iam_policy_data_2021-04-02_13:12.xlsx`.
To change these inputs to custom files, please change the following lines in the `__main__` function of the script.
```python
df_policies, df_users, df_groups, df_roles = load_excel('./output/iam_policy_data_2021-04-02_12:19.xlsx')
new_df_policies, new_df_users, new_df_groups, new_df_roles = load_excel('./output/iam_policy_data_2021-04-02_13:12.xlsx')
```
