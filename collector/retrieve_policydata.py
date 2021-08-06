# Imports
from hashlib import sha256
import json
import os
import pandas as pd
import subprocess
import sys
import time

################################################################################
#                                Data retrieval                                #
################################################################################

def retrieve_iam_policies():
    """Retrieve IAM policies using aws iam command line tool."""

    # Run command to list all the IAM policies in the environment
    policies = subprocess.check_output('aws iam list-policies', shell=True)

    # Gather policies as json data
    json_policies = json.loads(policies)

    # Load the IAM policies into a pandas dataframe
    df_policies = pd.json_normalize(json_policies['Policies'])
    print('Found: ' + str(df_policies.shape[0]) + ' policies')
    print('Starting individual policy object retrieval (may take a while)')

    # Create new column in the dataframe for the policy object
    df_policies['PolicyObject'] = ''

    # Loop through the list of collected policy names and retrieve the actual policy document
    for index, row in df_policies.iterrows():
        policy_object = subprocess.check_output(
            'aws iam get-policy-version --policy-arn ' + row.Arn + ' --version-id ' + row.DefaultVersionId,
            shell=True)
        json_policy_object = json.loads(policy_object)
        policy_statement = json_policy_object['PolicyVersion']['Document']['Statement']

        # Check whether the policy object fits in an excel cell, if not split it.
        if len(str(policy_statement)) > 32767:
            df_policies.at[index, 'PolicyObject'] = str(policy_statement)[:32767]
            df_policies.at[index, 'ExtraPolicySpace'] = str(policy_statement)[32767:]

        # Only take the statement part of the policy and add to dataframe
        df_policies.at[index, 'PolicyObject'] = policy_statement

    # Return collected policies
    return df_policies


# Retrieve all the users and the policies that are attached to them in the environment
def retrieve_users():
    """Retrieve IAM users using aws iam command line tool."""
    # Run command to retrieve all the users in the environment
    users = subprocess.check_output('aws iam list-users', shell=True)

    # Gather users as json data
    json_users = json.loads(users)

    # Create a new dataframe to hold the users and retrieve the attached policies
    df_users = pd.json_normalize(json_users['Users'])
    df_users['AttachedPolicies'] = '-'

    for index, row in df_users.iterrows():
        attached_user_policies = json.loads(
            subprocess.check_output('aws iam list-attached-user-policies --user-name ' + row.UserName, shell=True))
        df_users.at[index, 'AttachedPolicies'] = attached_user_policies['AttachedPolicies']

        # Cryptographically hash identifiable data for some level of anonymization
        df_users.at[index, 'UserName'] = sha256(row.UserName.encode('utf-8')).hexdigest()
        df_users.at[index, 'UserId'] = sha256(row.UserId.encode('utf-8')).hexdigest()
        df_users.at[index, 'Arn'] = sha256(row.Arn.encode('utf-8')).hexdigest()

    # Return collected users
    return df_users


# Run a CLI command to retrieve all the groups in the environment and the attached policies
def retrieve_groups():
    json_groups = json.loads(subprocess.check_output('aws iam list-groups', shell=True))

    # Create a new dataframe to hold the group data, attached policies, and the users that are part of the group
    df_groups = pd.json_normalize(json_groups['Groups'])
    df_groups['AttachedPolicies'] = '-'
    df_groups['Users'] = '-'

    for index, row in df_groups.iterrows():

        # Retrieve the attached policies to the group
        attached_group_policies = json.loads(
            subprocess.check_output('aws iam list-attached-group-policies --group-name ' + row.GroupName,
                                    shell=True))

        # Retrieve the users that are part of the group
        df_groups.at[index, 'AttachedPolicies'] = attached_group_policies['AttachedPolicies']
        users_in_group = \
            json.loads(subprocess.check_output('aws iam get-group --group-name ' + row.GroupName, shell=True))[
                'Users']

        # Cryptographically hash the users in the group for anonymization
        anonymized_users = []
        for user in users_in_group:
            user_dict = {
                'UserName': sha256(user['UserName'].encode('utf-8')).hexdigest(),
                'UserId': sha256(user['UserId'].encode('utf-8')).hexdigest(),
                'Arn': sha256(user['Arn'].encode('utf-8')).hexdigest()
            }
            anonymized_users.append(user_dict)

        df_groups.at[index, 'Users'] = anonymized_users

        # Cryptographically hash identifiable data for some level of anonymization
        df_groups.at[index, 'GroupName'] = sha256(row.GroupName.encode('utf-8')).hexdigest()
        df_groups.at[index, 'GroupId'] = sha256(row.GroupId.encode('utf-8')).hexdigest()
        df_groups.at[index, 'Arn'] = sha256(row.Arn.encode('utf-8')).hexdigest()

    return df_groups


# Run a CLI command to retrieve all the roles in the environment and the attached policies
def retrieve_roles():
    json_roles = json.loads(subprocess.check_output('aws iam list-roles', shell=True))

    df_roles = pd.json_normalize(json_roles['Roles'])
    df_roles['AttachedPolicies'] = '-'

    for index, row in df_roles.iterrows():
        # Retrieve the attached role policies
        attached_roles_policies = json.loads(
            subprocess.check_output('aws iam list-attached-role-policies --role-name ' + row.RoleName, shell=True))
        df_roles.at[index, 'AttachedPolicies'] = attached_roles_policies['AttachedPolicies']

        # Cryptographically hash identifiable data for some level of anonymization
        df_roles.at[index, 'RoleName'] = sha256(row.RoleName.encode('utf-8')).hexdigest()
        df_roles.at[index, 'RoleId'] = sha256(row.RoleId.encode('utf-8')).hexdigest()
        df_roles.at[index, 'Arn'] = sha256(row.Arn.encode('utf-8')).hexdigest()

    return df_roles


# Method to export the generated dataframes as a single xlsx file
def file_exporter(policies, users, groups, roles):
    # Check if the output directory exists, if not create it
    outdir = '/output'
    absolute_dir_path = os.path.abspath(os.path.dirname(__file__))
    if not os.path.exists(absolute_dir_path + outdir):
        os.mkdir(absolute_dir_path + outdir)

    # Write data to excel file.
    with pd.ExcelWriter(
            absolute_dir_path +
            outdir +
            '/iam_policy_data_' +
            time.strftime("%Y-%m-%d") +
            '_' +
            time.strftime("%H:%M")
            + '.xlsx'
        ) as writer:
        policies.to_excel(writer, sheet_name="policies")
        users   .to_excel(writer, sheet_name="users")
        groups  .to_excel(writer, sheet_name="groups")
        roles   .to_excel(writer, sheet_name="roles")


# Simple method to bundle the data collection methods and return the needed dataframes
def collect_data():
    # Collect policy data
    print('Collecting policy data...')
    policies = retrieve_iam_policies()
    print('Finished policy retrieval')
    print('-------------------------')

    # Collect user data
    print('Collecting user data...')
    users = retrieve_users()
    print('Finished user retrieval')
    print('-------------------------')

    # Collect group data
    print('Collecting group data...')
    groups = retrieve_groups()
    print('Finished group retrieval')
    print('-------------------------')

    # Collect role data
    print('Collecting role data...')
    roles = retrieve_roles()
    print('Finished role retrieval')

    # Export retrieved data to output file
    file_exporter(policies, users, groups, roles)


def timer(hours):
    """Perform a multiple rounds of data collection every given hours.

        Parameters
        ----------
        hours : int
            Interval in hours, each interval will collect data via the
            collect_single() method.
        """
    while True:
        collect_single()
        print('--------------------------------------------------')
        print('Next collection in ' + hours + ' hours')
        print('Do not terminate this program')
        print('--------------------------------------------------')

        # Convert hours to seconds and start sleep
        time.sleep(int(hours) * 3600)


def collect_single():
    """Perform a single round of data collection.

        Output will be saved in the ./output directory.
        """
    print('Data retrieval in progress....')
    collect_data()
    print('--------------------------------------------------')
    print('Data retrieval successful')
    print('CSV file saved in:')
    print(os.getcwd() + '/output')


if __name__ == '__main__':
    print('--------------------------------------------------')
    print(' Starting data retrieval from the AWS environment ')
    print('--------------------------------------------------')

    # If an argument is passed for the frequency start the timer, otherwise 'single shot collection
    if len(sys.argv) == 2:
        timer(sys.argv[1])

    else:
        collect_single()

    print('--------------------------------------------------')
