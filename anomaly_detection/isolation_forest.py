# Imports
from neo4j            import GraphDatabase
from sklearn.ensemble import IsolationForest
from sklearn.metrics  import classification_report
from utils            import retrieve_embeddings, split_data

if __name__ == "__main__":
    # Load data
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    embedded_nodes = retrieve_embeddings(driver)

    # Split into train and test sets
    X_train, X_test, y_train, y_test = split_data(embedded_nodes)

    # Perform anomaly detection
    clf = IsolationForest(n_estimators=10, warm_start=True)
    clf.fit(X_train.embedding.tolist())
    clf.set_params(n_estimators=20)
    clf.fit(X_train.embedding.tolist())

    y_true, y_pred = y_test, clf.predict(X_test.embedding.tolist())

    # Print performance
    print(classification_report(
        y_true = y_true,
        y_pred = y_pred,
        digits = 4,
    ))
