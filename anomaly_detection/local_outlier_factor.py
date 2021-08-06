from neo4j             import GraphDatabase
from sklearn.manifold  import TSNE
from sklearn.metrics   import classification_report
from sklearn.neighbors import LocalOutlierFactor
from utils             import retrieve_embeddings, split_data

if __name__ == "__main__":
    # Load data
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    embedded_nodes = retrieve_embeddings(driver)

    # Split into train and test sets
    X_train, X_test, y_train, y_test = split_data(embedded_nodes)

    # Perform anomaly detection
    X_train_embedded = TSNE(n_components=2, random_state=6).fit_transform(list(X_train.embedding))
    X_test_embedded  = TSNE(n_components=2, random_state=6).fit_transform(list(X_test .embedding))

    clf = LocalOutlierFactor(n_neighbors=5, novelty=True)
    clf.fit(X_train_embedded.tolist())
    y_true, y_pred = y_test, clf.predict(X_test_embedded.tolist())

    # Print performance
    print(classification_report(
        y_true = y_true,
        y_pred = y_pred,
        digits = 4,
    ))
