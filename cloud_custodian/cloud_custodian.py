import argformat
import argparse
import json
import numpy  as np
import pandas as pd
import warnings
import yaml

from sklearn.metrics import classification_report

def get_policies(data):
    """Extract policies from pandas DataFrame.

        Parameters
        ----------
        data : pd.DataFrame
            Data loaded from policy xlsx file.

        Returns
        -------
        policies : dict()
            All policies extracted from data, indexed by their name.
            Policies are given in the form of a JSON dictionary.
        """
    # Extract policies
    policies = dict()
    # Loop over all policies
    for name, policy in zip(data['PolicyName'], data['PolicyObject']):
        # Add policy name
        policies[name] = list()

        # Try to extract the policy as JSON format
        try:
            policy = json.loads(policy.replace("'", "\""))
        except:
            warnings.warn("Failed loading policy {}".format(name))
            continue

        # If policy is given as list, extract
        if not isinstance(policy, list):
            policy = [policy]

        # Append all policies
        for policy_ in policy:
            policies[name].append(policy_)

    # Return policies
    return policies


def preprocess_policies(policies, misconfigurations):
    """Transform policies into labelled training and testing data.

        Parameters
        ----------
        policies : dict()
            Policies as returned by get_policies(data).

        misconfigurations : iterable
            Iterable of policy names that are misconfigured.

        Returns
        -------
        X : np.array of shape=(n_subpolicies)
            Policies to check.

        y : np.array of shape=(n_subpolicies)
            Labels for each policy
        """
    # Cast misconfigurations to set
    misconfigurations = set(misconfigurations)

    # Initialise result
    X = list()
    y = list()

    # Loop over all policies
    for name, policy in policies.items():
        # Get label, 1 if misconfiguration, 0 otherwise
        label = int(name in misconfigurations)

        # Loop over all subpolicies
        for subpolicy in policy:
            # Add to data
            X.append(subpolicy)
            y.append(label)

    # Return results as numpy arrays
    return np.asarray(X), np.asarray(y)


def load_policies_cloud_custodian(paths):
    # Initialise rules
    rules = list()

    # Loop over all cloud custodian rules
    for rule_file in paths:
        with open(rule_file) as infile:
            data = infile.read()
            try:
                rules.append(yaml.safe_load(data))
            except:
                warnings.warn(
                    "Rule {} requires slight modification of c7n iam.py file. "
                    "Please see README.md on how to add this patch. "
                    "If the patch was added, you can ignore this message."
                    .format(rule_file)
                )
                # Load data correctly
                data = '\n'.join(data.split('\n')[:6])
                rules.append(yaml.safe_load(data))

    # Return rules
    return rules


class CloudCustodianCustomEngine(object):
    """A custom engine for checking Cloud Custodian rules."""

    def predict(self, X, strict=False):
        """Validate whether given IAM management is in accordance with policies.

            Parameters
            ----------
            X : array-like of shape=(n_samples,)
                Samples for which to check if they match our rules.

            strict : boolean, default=False
                If True, use all policies, if False only use
                "generally applicable" policies, i.e. overly permissive policy
                detection.

            Returns
            -------
            result : np.array of shape=(n_samples,)
                Evaluation of acceptable (0) or misconfigured (1) policies.
            """
        # Initialise result
        result = list()

        # Loop over all policies
        for statement in X:
            # Check if statement is correct
            result.append(self.verify_statement(statement, strict=strict))

        # Return result
        return np.asarray(result)

    def verify_statement(self, statement, strict=False):
        """Verify whether a statement is acceptable for our rules.

            Note
            ----
            Rules are manually implemented version of policies from
            https://github.com/davidclin/cloudcustodian-policies.

            Parameters
            ----------
            statement : dict()
                Dictionary describing the statement.

            strict : boolean, default=False
                If True, use all policies, if False only use
                "generally applicable" policies, i.e. overly permissive policy
                detection.

            Returns
            -------
            result : int
                1 if statement is a mismatch, 0 otherwise.
            """
        # Extract values
        action   = statement.get('Action')
        resource = statement.get('Resource')
        effect   = statement.get('Effect')
        if action is None:
            actions = list()
        elif isinstance(action, list):
            actions = action
        else:
            actions = [action]

        # iam-ec2-policy-check
        # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-ec2-policy-check.yml
        if action == '*' and resource == '*' and effect == "Allow":
            return 1

        # Only do other policy checks if strict
        if strict:

            # Additional checks https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-ec2-policy-check.yml
            if 'Condition' not in statement and resource == "*" and effect == "Allow" and (
                    any("ec2:*"                       in a for a in actions) or
                    any("elasticloadbalancing:*"      in a for a in actions) or
                    any("cloudwatch:*"                in a for a in actions) or
                    any("autoscaling:*"               in a for a in actions) or
                    any("iam:CreateServiceLinkedRole" in a for a in actions) or
                    any("ec2:RunInstances"            in a for a in actions)
                ):
                return 1


            # iam-policy-CreatePolicy-audit
            # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-policy-CreatePolicy-audit.yml
            if self.filter_allow_all(statement) and any("CreatePolicy" in x for x in actions):
                return 1

            # iam-policy-CreatePolicyVersion-audit
            # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-policy-CreatePolicyVersion-audit.yml
            if self.filter_allow_all(statement) and any("CreatePolicyVersion" in x for x in actions):
                return 1

            # iam-policy-account-Summary-audit
            # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-policy-account-Summary-audit.yml

        # Otherwise return 0
        return 0

    def filter_allow_all(self, statement):
        """Returns if there is an 'allow all' statement."""
        return statement.get('Effect') == 'Allow' and (
            statement.get('Action')   == '*' or
            statement.get('Resource') == '*'
        )


if __name__ == "__main__":
    ########################################################################
    #                           Parse arguments                            #
    ########################################################################
    # Create parser
    parser = argparse.ArgumentParser(
        description     = "Cloud Custodian",
        formatter_class = argformat.StructuredFormatter,
    )

    # Add arguments
    parser.add_argument("statements", nargs='+', help="File(s) containing statements.")
    # parser.add_argument("rules"   , nargs='+', help="File(s) containing cloud custodian rules.")

    # Parse arguments
    args = parser.parse_args()

    ########################################################################
    #                              Load data                               #
    ########################################################################

    # Set misconfigurations
    misconfigurations = [
        'AmazonS3FullAccess',
        'AdministratorAccess',
        'PowerUserAccess',
        'DataScientist',
        'AWS_ConfigRole',
        'AWSCodeCommitPowerUser',
    ]

    X = list()
    y = list()

    # Load data for each input
    for policy in args.statements:
        data       = pd.read_excel(policy)
        statements = get_policies(data)
        X_, y_     = preprocess_policies(statements, misconfigurations)

        # Add partial results
        X.append(X_)
        y.append(y_)

    # Concatenate partial results
    X = np.concatenate(X)
    y = np.concatenate(y)

    ########################################################################
    #                      Load Cloud Custodian rules                      #
    ########################################################################

    engine = CloudCustodianCustomEngine()
    y_pred_loose  = engine.predict(X, strict=False)
    y_pred_strict = engine.predict(X, strict=True )

    ########################################################################
    #                          Print performance                           #
    ########################################################################

    # Print performance
    print()
    print("Performance - Only overly permissive detection")
    print("━"*60)
    print(classification_report(
        y_true        = y,
        y_pred        = y_pred_loose,
        target_names  = ["Correct", "Misconfiguration"],
        digits        = 4,
        zero_division = 0,
    ))

    print()
    print("Performance - Strict detection")
    print("━"*60)
    print(classification_report(
        y_true        = y,
        y_pred        = y_pred_strict,
        target_names  = ["Correct", "Misconfiguration"],
        digits        = 4,
        zero_division = 0,
    ))
