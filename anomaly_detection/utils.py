from sklearn.model_selection import train_test_split
import pandas as pd

def retrieve_embeddings(driver):
    """Retrieve the policy nodes and their embedding from the graph database.

        Parameters
        ----------
        driver : neo4j.GraphDatabase.driver
            Driver for database connection.

        Returns
        -------
        result : pd.DataFrame
            Pandas dataframe containing retrieved records.
        """
    # Create a graph database session
    with driver.session(database="neo4j") as session:
        # Collect all policies
        result = session.run(
            """
            MATCH (p:Policy)
            RETURN p.name AS policy, p.embeddingNode2vec AS embedding
            """,
        )

        # Transform retrieved data to a pandas dataframe and return
        return pd.DataFrame([dict(record) for record in result])


def split_data(X, misconfigurations = [
        'tf-secmon-iam-policy',
        'tf-splunk-ingestion-aws-addon-policy-master20200917101618881200000005',
        'tf-customconfig-policy-master',
        'tf-ds-tscm-lambda-policy',
        'tf-aws-team-cf-cr',
        'awt-role-boundary',
        'awt-user-boundary',
        'CloudabilityPolicy',
        'PowerUserAccess',
        'AdministratorAccess',
        'AWSOpsWorksRegisterCLI',
        'AWSCodeStarServiceRole',
        'AWSApplicationMigrationReplicationServerPolicy',
    ]):
    """Split data such that the train data contains only correct configurations
        and the test data contains a mix of correct and misconfigured policies.

        Parameters
        ----------
        X : pd.DataFrame
            Dataframe to split into train and test data.

        misconfigurations : list, default=list used for own database.
            List of misconfigured policynames.

            Important: The misconfigurations must be specified if using
            different evaluation data.

        Returns
        -------
        X_train : list
            Train data.

        X_test : list
            Test data.

        y_train : list
            Train labels.

        y_test : list
            Test labels.
        """
    # Set all target values to 1, i.e. benign
    X['target'] = 1

    ############################################################################
    #                        Extract misconfigurations                         #
    ############################################################################

    # Create dataframe for misconfigurations
    df_misconfs = pd.DataFrame(columns=['policy', 'embedding', 'target'])

    # Loop over all policies
    for name in misconfigurations:
        for index, policy in X.iterrows():
            # Check if policy is misconfigured
            if policy.policy == name:

                # Add policy to misconfigurations
                df_misconfs = df_misconfs.append(policy, ignore_index=True)
                # Remove policy from correct configurations
                X.drop(index, inplace=True)

    # Set misconfiguration target to malicious
    df_misconfs['target'] = -1
    y = X.pop('target')

    # Split benign data into train-test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

    # Add misconfigurations to test set
    y_misconfs = df_misconfs.pop('target')
    X_test = X_test.append(df_misconfs)
    y_test = y_test.append( y_misconfs)

    # Return result
    return X_train, X_test, y_train, y_test
