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
            subpolicy['PolicyName'] = name

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
            violations = self.verify_statement(statement)

            if violations and (strict or "allow-all" in violations):
                result.append(1)
            else:
                result.append(0)

        # Return result
        return np.asarray(result)


    def verify_statement(self, statement):
        """Verify whether a statement is acceptable for our rules.

            Note
            ----
            Rules are manually implemented version of policies from
            https://github.com/davidclin/cloudcustodian-policies.

            Parameters
            ----------
            statement : dict()
                Dictionary describing the statement.

            Returns
            -------
            result : set()
                Set of matching policies.
            """
        # Initialise result
        result = set()

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
            result.add('allow-all')

        # Other policy checks
        if 'Condition' not in statement and resource == "*" and effect == "Allow":

            # Specify mismatches
            mismatches = [
                # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-ec2-policy-check.yml
                "ec2:*",
                "elasticloadbalancing:*",
                "cloudwatch:*",
                "autoscaling:*",
                "iam:CreateServiceLinkedRole",
                "ec2:RunInstances",

                # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-policy-CreatePolicy-audit.yml
                # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-policy-CreatePolicyVersion-audit.yml
                # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-policy-account-Summary-audit.yml
                # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-policy-account-audit.yml
                # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-user-DeleteLoginProfile-offboarding.yml
                # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-user-UpdateAccessKey-offboarding.yml
                # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/c7n-org/CustomAccount/iam-user-CreateLoginProfile.yml
                # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/c7n-org/CustomAccount/iam-user-UpdateAccessKey-audit.yml
                "account:*",
                "account:EnableRegion",
            ]

            # Check against mismatches
            for mismatch in mismatches:
                if mismatch in actions:
                    result.add(mismatch)

            # https://github.com/davidclin/cloudcustodian-policies/blob/master/policies/iam-role-with-managed-policy-audit.yml
            if statement.get('PolicyName') in {"AmazonEC2FullAccess", "AutoScalingFullAccess", "ElasitcLoadBalancingFullAccess", "AutoScalingConsoleFullAccess"}:
                result.add("policyname-violation")


        # Return result
        return result


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
