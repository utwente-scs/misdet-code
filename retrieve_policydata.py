import subprocess
import os
import json
import sys

import pandas as pd
import time


# Run a CLI command to list all the IAM policies in the environment
def retrieve_iam_policies():
    policies = subprocess.check_output('aws iam list-policies', shell=True)

    json_policies = json.loads(policies)

    # Load the IAM policies into a pandas dataframe
    df_policies = pd.json_normalize(json_policies['Policies'])

    collected_policies = []

    # Loop through the list of collected policy names and retrieve the actual policy document
    for index, row in df_policies.iterrows():
        policy_object = subprocess.check_output(
            'aws iam get-policy-version --policy-arn ' + row.Arn + ' --version-id ' + row.DefaultVersionId,
            shell=True)
        json_policy_object = json.loads(policy_object)

        # Only take the statement part of the policy
        collected_policies.append(json_policy_object['PolicyVersion']['Document']['Statement'])

    # Append the retrieved policies as a new column to the dataframe
    df_policies['PolicyObject'] = collected_policies

    # In AWS policies need to be attached to an entity (users, groups and roles) before they can be used
    # Here we will retrieve entities to which the policy is attached and add it to the dataframe
    # (only applies for managed policies)

    # Create new columns in the dataframe for the attached entities and set default value to '-'
    df_policies['AttachedUsers'] = '-'
    df_policies['AttachedGroups'] = '-'
    df_policies['AttachedRoles'] = '-'

    for index, row in df_policies.iterrows():
        # If the policy is attached to entities, retrieve those entities and add it to the list
        if row.AttachmentCount > 0:
            attached_entities = json.loads(
                subprocess.check_output('aws iam list-entities-for-policy --policy-arn ' + row.Arn, shell=True))
            df_policies.at[index, 'AttachedUsers'] = attached_entities['PolicyGroups']
            df_policies.at[index, 'AttachedGroups'] = attached_entities['PolicyUsers']
            df_policies.at[index, 'AttachedRoles'] = attached_entities['PolicyRoles']

    return df_policies


# Retrieve all the users and the policies that are attached to them in the environment
def retrieve_users():
    # Run a CLI command to retrieve all the users in the environment and convert the output the JSON
    json_users = json.loads(subprocess.check_output('aws iam list-users', shell=True))

    # Create a new dataframe to hold the users and retrieve the attached policies
    df_users = pd.json_normalize(json_users['Users'])
    df_users['AttachedPolicies'] = '-'

    for index, row in df_users.iterrows():
        attached_user_policies = json.loads(
            subprocess.check_output('aws iam list-attached-user-policies --user-name ' + row.UserName, shell=True))
        df_users.at[index, 'AttachedPolicies'] = attached_user_policies['AttachedPolicies']

    return df_users


# Run a CLI command to retrieve all the groups in the environment and the attached policies
def retrieve_groups():
    json_groups = json.loads(subprocess.check_output('aws iam list-groups', shell=True))

    # Create a new dataframe to hold the group data, attached policies, and the users that are part of the group
    df_groups = pd.json_normalize(json_groups['Groups'])
    df_groups['AttachedPolicies'] = '-'
    df_groups['Users'] = '-'

    for index, row in df_groups.iterrows():
        attached_group_policies = json.loads(
            subprocess.check_output('aws iam list-attached-group-policies --group-name ' + row.GroupName,
                                    shell=True))
        df_groups.at[index, 'AttachedPolicies'] = attached_group_policies['AttachedPolicies']
        users_in_group = \
            json.loads(subprocess.check_output('aws iam get-group --group-name ' + row.GroupName, shell=True))[
                'Users']
        df_groups.at[index, 'Users'] = users_in_group

    return df_groups


# Run a CLI command to retrieve all the roles in the environment and the attached policies
def retrieve_roles():
    json_roles = json.loads(subprocess.check_output('aws iam list-roles', shell=True))

    df_roles = pd.json_normalize(json_roles['Roles'])
    df_roles['AttachedPolicies'] = '-'

    for index, row in df_roles.iterrows():
        attached_roles_policies = json.loads(
            subprocess.check_output('aws iam list-attached-role-policies --role-name ' + row.RoleName, shell=True))
        df_roles.at[index, 'AttachedPolicies'] = attached_roles_policies['AttachedPolicies']

    return df_roles


# Method to export the generated dataframes as a single xlsx file
def file_exporter(policies, users, groups, roles):
    # Check if the output directory exists, if not create it
    outdir = './output'
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    with pd.ExcelWriter(
            outdir + '/iam_policy_data_' + time.strftime("%Y-%m-%d") + '_' + time.strftime(
                "%H:%M") + '.xlsx') as writer:
        # policies.to_excel(writer, sheet_name="policies")
        policies.to_excel(writer, sheet_name="policies")
        users.to_excel(writer, sheet_name="users")
        groups.to_excel(writer, sheet_name="groups")
        roles.to_excel(writer, sheet_name="roles")


# Simple method to bundle the data collection methods and return the needed dataframes
def data_collector():
    policies = retrieve_iam_policies()
    users = retrieve_users()
    groups = retrieve_groups()
    roles = retrieve_roles()

    file_exporter(policies, users, groups, roles)


def timer(hours):
    while True:
        print('Data retrieval in progress....')
        data_collector()
        print('--------------------------------------------------')
        print('Data retrieval successful')
        print('CSV file saved in:')
        print(os.getcwd() + '/output')
        print('--------------------------------------------------')
        print('Next collection in ' + sys.argv[1] + ' hours')
        print('Do not terminate this program')
        print('--------------------------------------------------')

        # Convert hours to seconds and start sleep
        time.sleep(int(hours) * 3600)


if __name__ == '__main__':
    print('--------------------------------------------------')
    print('Starting data retrieval from the AWS environment')
    print('--------------------------------------------------')

    # If an argument is passed for the frequency start the timer, otherwise 'single shot collection
    if len(sys.argv) == 2:
        timer(sys.argv[1])

    else:
        print('Data retrieval in progress....')
        data_collector()
        print('--------------------------------------------------')
        print('Data retrieval successful')
        print('CSV file saved in:')
        print(os.getcwd() + '/output')

    print('--------------------------------------------------')
