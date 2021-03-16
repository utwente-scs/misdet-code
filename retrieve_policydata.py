import subprocess
import os
import json
import sys

import pandas as pd
import time


def retrieve_iam_policies():
    # Run a CLI command to list all the IAM policies in the environment and convert the output to JSON
    policies = subprocess.check_output('awslocal iam list-policies', shell=True)

    json_policies = json.loads(policies)

    # Load the IAM policies into a pandas dataframe
    df = pd.json_normalize(json_policies['Policies'])

    # Check if the output directory exists, if not create it
    outdir = './output'
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    collected_policies = []

    # Loop through the list of collected policy names and retrieve the actual policy document
    for index, row in df.iterrows():
        policy_object = subprocess.check_output(
            'awslocal iam get-policy-version --policy-arn ' + row.Arn + ' --version-id ' + row.DefaultVersionId,
            shell=True)
        json_policy_object = json.loads(policy_object)

        # Only take the statement part of the policy
        collected_policies.append(json_policy_object['PolicyVersion']['Document']['Statement'])

    # Append the retrieved policies as a new collumn to the dataframe
    df['PolicyObject'] = collected_policies

    # In AWS policies need to be attached to an entity (users, groups and roles) before they can be used
    # Here we will retrieve entities to which the policy is attached and add it to the dataframe

    # Create new columns in the dataframe for the attached entities and set default value to '-'
    df['AttachedUsers'] = '-'
    df['AttachedGroups'] = '-'
    df['AttachedRoles'] = '-'

    for index, row in df.iterrows():
        # If the policy is attached to entities, retrieve those entities and add it to the list
        if row.AttachmentCount > 0:
            attached_entities = json.loads(
                subprocess.check_output('awslocal iam list-entities-for-policy --policy-arn ' + row.Arn, shell=True))
            df.at[index, 'AttachedUsers'] = attached_entities['PolicyGroups']
            df.at[index, 'AttachedGroups'] = attached_entities['PolicyUsers']
            df.at[index, 'AttachedRoles'] = attached_entities['PolicyRoles']

    # Transform the dataframe to a csv file and save it
    df.to_csv(outdir + '/iam_policy_data_' + time.strftime("%Y-%m-%d") + '_' + time.strftime("%H:%M") + '.csv',
              index=False)


def timer(hours):
    while True:
        print('Data retrieval in progress....')
        retrieve_iam_policies()
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

    # If an argument is passed for the frequency start the timer, otherwise single shot collection
    if len(sys.argv) == 2:
        timer(sys.argv[1])

    else:
        retrieve_iam_policies()
        print('Data retrieval in progress....')
        print('--------------------------------------------------')
        print('Data retrieval successful')
        print('CSV file saved in:')
        print(os.getcwd() + '/output')

    print('--------------------------------------------------')
