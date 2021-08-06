from neo4j           import GraphDatabase
from sklearn.svm     import OneClassSVM
from sklearn.metrics import classification_report
from utils           import retrieve_embeddings, split_data

if __name__ == "__main__":
    # Load data
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    embedded_nodes = retrieve_embeddings(driver)

    # Split into train and test sets
    X_train, X_test, y_train, y_test = split_data(embedded_nodes)

    # Perform anomaly detection
    clf = OneClassSVM(gamma=0.001, nu=0.5).fit(X_train.embedding.tolist())
    y_true, y_pred = y_test, clf.predict(X_test.embedding.tolist())

    # Print performance
    print(classification_report(
        y_true = y_true,
        y_pred = y_pred,
        digits = 4,
    ))
