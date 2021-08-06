# Code for experiments with Cloud Custodian
This directory contains the code used to compare our approach with Cloud Custodian.

## Dependencies
The scripts used for anomaly detection require the following Python libraries to be installed:
* [argformat](https://pypi.org/project/argformat/)
* [numpy](https://numpy.org/)
* [pandas](https://pandas.pydata.org/)
* [scikit-learn](https://scikit-learn.org/stable/index.html)

```
pip install argformat numpy pandas scikit-learn
```

## Usage
To check a file against the Cloud Custodian rules, we simply run `cloud_custodian.py` with a path to the given excel file:
```
python3 cloud_custodian.py ../collector/example/iam_policy_data_2021-03-26_14:11.xlsx
```

## Cloud Custodian patch

### Note
```
This patch is only required when using the c7n package.
The cloud_custodian script provides an engine for applying the specific rules from https://github.com/davidclin/cloudcustodian-policies without requiring the c7n package.
```

The open-source rules from cloudcustodian-policies require a minor patch to the cloudcustodian source code.
To be able to perform the `has-allow-all` filter, we must add the code below to the `/cloud-custodian/c7n/resources/iam.py` module.
When installed using `pip` as a local user on Ubuntu 20.04, this file can be found at `~/.local/lib/python3.8/site-packages/c7n/resources/iam.py`

```
##############################################################################################      
Note: By default, `has-allow-all` matches IAM policies that have the following JSON code block
##############################################################################################   
{
 'Version': '2012-10-17',
 'Statement': [{
     'Action': '*',
     'Resource': '*',
     'Effect': 'Allow'
 }]
}


##############################################################################################      
Since I needed to have the Action match on specific values, the following lines were manually
added to the def has_allow_all_policy(self, client, resource) method in the
/cloud-custodian/c7n/resources/iam.py module:
##############################################################################################   
def has_allow_all_policy(self, client, resource):

    # START - THIS CODE ALREADY EXISTS - START#
    statements = client.get_policy_version(
        PolicyArn=resource['Arn'],
        VersionId=resource['DefaultVersionId']
    )['PolicyVersion']['Document']['Statement']
    if isinstance(statements, dict):
        statements = [statements]
    # END - THIS CODE ALREADY EXISTS - END #

    # START - THIS CODE SHOULD BE ADDED BELOW THE CODE ABOVE - START #
    # has ec2:*
    for s in statements:
        if ('Condition' not in s and
                'Action' in s and
                isinstance(s['Action'], six.string_types) and
                s['Action'] == "ec2:*" and    
                'Resource' in s and
                isinstance(s['Resource'], six.string_types) and
                s['Resource'] == "*" and
                s['Effect'] == "Allow"):
            return True

    # has elasticloadbalancing:*
    for s in statements:
        if ('Condition' not in s and
                'Action' in s and
                isinstance(s['Action'], six.string_types) and
                s['Action'] == "elasticloadbalancing:*" and
                'Resource' in s and
                isinstance(s['Resource'], six.string_types) and
                s['Resource'] == "*" and
                s['Effect'] == "Allow"):
            return True

    # has cloudwatch:*
    for s in statements:
        if ('Condition' not in s and
                'Action' in s and
                isinstance(s['Action'], six.string_types) and
                s['Action'] == "cloudwatch:*" and
                'Resource' in s and
                isinstance(s['Resource'], six.string_types) and
                s['Resource'] == "*" and
                s['Effect'] == "Allow"):
            return True

    # has autoscaling:*
    for s in statements:
        if ('Condition' not in s and
                'Action' in s and
                isinstance(s['Action'], six.string_types) and
                s['Action'] == "autoscaling:*" and
                'Resource' in s and
                isinstance(s['Resource'], six.string_types) and
                s['Resource'] == "*" and
                s['Effect'] == "Allow"):
            return True

    # has iam:CreateServiceLinkedRole
    for s in statements:
        if ('Condition' not in s and
                'Action' in s and
                isinstance(s['Action'], six.string_types) and
                s['Action'] == "iam:CreateServiceLinkedRole" and
                'Resource' in s and
                isinstance(s['Resource'], six.string_types) and
                s['Resource'] == "*" and
                s['Effect'] == "Allow"):
            return True

    # has ec2:RunInstances
    for s in statements:
        if ('Condition' not in s and
                'Action' in s and
                isinstance(s['Action'], six.string_types) and
                s['Action'] == "ec2:RunInstances" and
                'Resource' in s and
                isinstance(s['Resource'], six.string_types) and
                s['Resource'] == "*" and
                s['Effect'] == "Allow"):
            return True
    return False
    # END - THIS CODE SHOULD BE ADDED BELOW THE CODE ABOVE - END #

# START - THE CODE BELOW ALREADY EXISTS AND SHOULD FOLLOW THE ADDED CODE #
def process(self, resources, event=None):
    c = local_session(self.manager.session_factory).client('iam')
    results = [r for r in resources if self.has_allow_all_policy(c, r)]
    self.log.info(
        "%d of %d iam policies have allow all.",
        len(results), len(resources))
    return results

##############################################################################################   
Note: For the changes to the iam.py module to take effect, remember to issue:
##############################################################################################   

    $ cd ~/cloud-custodian
    $ python install setup.up install
```
