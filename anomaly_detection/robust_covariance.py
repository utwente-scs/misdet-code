
from neo4j import GraphDatabase

from sklearn.covariance import EllipticEnvelope
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

import pandas as pd


def retrieve_embeddings(driver):
    # Retrieve the policy nodes and their embedding from the graph database
    with driver.session(database="neo4j") as session:
        result = session.run("""
        MATCH (p:Policy)
        RETURN p.name AS policy, p.embeddingNode2vec AS embedding
        """, )
        X = pd.DataFrame([dict(record) for record in result])
    return X


def split_data(X):
    X['target'] = 1

    df_misconfs = pd.DataFrame(columns=['policy', 'embedding', 'target'])

    # These are specific misconfigurations in this dataset, need to be changed for new datasets.
    misconfs = ['tf-secmon-iam-policy', 'tf-splunk-ingestion-aws-addon-policy-master20200917101618881200000005',
                'tf-customconfig-policy-master', 'tf-ds-tscm-lambda-policy', 'tf-aws-team-cf-cr', 'awt-role-boundary',
                'awt-user-boundary', 'CloudabilityPolicy', 'PowerUserAccess', 'AdministratorAccess',
                'AWSOpsWorksRegisterCLI', 'AWSCodeStarServiceRole', 'AWSApplicationMigrationReplicationServerPolicy']

    for name in misconfs:
        for index, policy in X.iterrows():
            if policy.policy == name:
                df_misconfs = df_misconfs.append(policy, ignore_index=True)
                X.drop(index, inplace=True)

    df_misconfs['target'] = -1
    y = X.pop('target')

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)
    y_misconfs = df_misconfs.pop('target')

    X_test = X_test.append(df_misconfs)
    y_test = y_test.append(y_misconfs)

    return X_train, X_test, y_train, y_test


if __name__ == "__main__":
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    embedded_nodes = retrieve_embeddings(driver)

    X_train, X_test, y_train, y_test = split_data(embedded_nodes)

    clf = EllipticEnvelope(random_state=1, contamination=0.1)
    clf.fit(X_train.embedding.tolist())
    y_true, y_pred = y_test, clf.predict(X_test.embedding.tolist())

    print(classification_report(y_true, y_pred))
