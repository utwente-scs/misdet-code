from py2neo import Graph
from tqdm import tqdm
import json
import pandas as pd
import sys
import warnings

def load_excel(file_path):
    """Load pandas dataframes from stored Excel files.

        Parameters
        ----------
        file_path : string
            File path from which to load data.

        Returns
        -------
        policies : pd.DataFrame
            DataFrame listing all policies.

        users : pd.DataFrame
            DataFrame listing all users.

        groups : pd.DataFrame
            DataFrame listing all groups.

        roles : pd.DataFrame
            DataFrame listing all roles.

        """

    # Read from input file
    df_policies = pd.read_excel(file_path, sheet_name='policies', index_col=0)
    df_users    = pd.read_excel(file_path, sheet_name='users'   , index_col=0)
    df_groups   = pd.read_excel(file_path, sheet_name='groups'  , index_col=0)
    df_roles    = pd.read_excel(file_path, sheet_name='roles'   , index_col=0)

    # Fill NaN (Not a Number) field with an empty string
    df_policies.fillna('', inplace=True)
    df_roles.columns = df_roles.columns.str.replace('.', '', regex=False)

    # Check if extra space was needed for the policy object, if so merge it again
    if 'ExtraPolicySpace' in df_policies.columns:
        for index, row in df_policies.iterrows():
            if row.ExtraPolicySpace != '':
                df_policies.at[index, 'PolicyObject'] = row.PolicyObject + row.ExtraPolicySpace

    # Return result
    return df_policies, df_users, df_groups, df_roles


def create_policy_nodes(gr, policies):
    """Create policy nodes for given graph.

        Parameters
        ----------
        gr : Graph
            Graph for which to create nodes.

        policies : pd.DataFrame
            Policies for which to create nodes.
        """
    tx = gr.begin()

    for index, row in tqdm(policies.iterrows(), desc="Loading policies"):
        tx.evaluate('''
        CREATE (policy:Policy {name: $name, id: $id, arn: $arn, policyObject: $policyObject}) RETURN policy
        ''', parameters={
            'name'        : row.PolicyName,
            'id'          : row.PolicyId,
            'arn'         : row.Arn,
            'policyObject': row.PolicyObject,
        })
    gr.commit(tx)


def create_resource_nodes(gr, resources):
    """Create resource nodes for given graph.

        Parameters
        ----------
        gr : Graph
            Graph for which to create nodes.

        resources : pd.DataFrame
            Resources for which to create nodes.
        """
    tx = gr.begin()

    for index, row in tqdm(resources.iterrows(), desc="Loading resources"):
        policy_object = row.PolicyObject.replace("\'", "\"")
        policy_object = policy_object.replace("True", "true")
        policy_object = policy_object.replace("False", "false")

        try:
            policy_list = json.loads(policy_object)

            if not isinstance(policy_list, list):
                tmp = [policy_list]
                policy_list = tmp

            for policy in policy_list:

                # Check whether the policy actually contains resources
                if 'Resource' in policy:
                    resource_list = policy['Resource']

                    if not isinstance(resource_list, list):
                        tmp = [resource_list]
                        resource_list = tmp

                    for resource in resource_list:
                        tx.evaluate('''
                            MERGE (resource:Resource {name: $name, forPolicy: $policy})
                            ''', parameters={'name': resource, 'policy': row.PolicyName})

                elif 'NotResource' in policy:
                    not_resource_list = policy['NotResource']

                    if not isinstance(not_resource_list, list):
                        tmp = [not_resource_list]
                        not_resource_list = tmp

                    for not_resource in not_resource_list:
                        tx.evaluate('''
                            MERGE (notresource:NotResource {name: $name, forPolicy: $policy})
                            ''', parameters={'name': not_resource, 'policy': row.PolicyName})

        except json.decoder.JSONDecodeError as e:
            warnings.warn("Error in row '{}': '{}', skipping row...".format(row.PolicyName, e))

    gr.commit(tx)


def create_action_nodes(gr, actions):
    """Create action nodes for given graph.

        Parameters
        ----------
        gr : Graph
            Graph for which to create nodes.

        actions : pd.DataFrame
            Actions for which to create nodes.
        """
    tx = gr.begin()

    for index, row in tqdm(actions.iterrows(), desc="Loading actions"):
        # Replace single quote with double quote for json parsing
        policy_object = row.PolicyObject.replace("\'", "\"")
        policy_object = policy_object.replace("True", "true")
        policy_object = policy_object.replace("False", "false")

        try:
            policy_list = json.loads(policy_object)

            if not isinstance(policy_list, list):
                tmp = [policy_list]
                policy_list = tmp

            for policy in policy_list:
                resource_list = []
                not_resource_list = []
                action_list = []
                not_action_list = []

                if 'Resource' in policy:
                    resource_list = policy['Resource']
                elif 'NotResource' in policy:
                    resource_list = policy['NotResource']

                if not isinstance(resource_list, list):
                    tmp = [resource_list]
                    resource_list = tmp

                if not isinstance(not_resource_list, list):
                    tmp = [not_resource_list]
                    not_resource_list = tmp

                if 'Action' in policy:
                    action_list = policy['Action']
                elif 'NotAction' in policy:
                    not_action_list = policy['NotAction']

                if not isinstance(action_list, list):
                    tmp = [action_list]
                    action_list = tmp

                if not isinstance(not_action_list, list):
                    tmp = [not_action_list]
                    not_action_list = tmp

                if resource_list and action_list:
                    for resource in resource_list:
                        for action in action_list:
                            tx.evaluate('''
                                MATCH (p:Policy), (res:Resource)
                                WHERE p.name = $policyName AND res.name = $resourceName AND res.forPolicy = $policy
                                CREATE (p)-[:CONTAINS]->(action:Action {name: $name})-[:WORKS_ON]->(res)
                                RETURN action
                               ''', parameters={'policyName': row.PolicyName, 'resourceName': resource, 'name': action,
                                                'policy': row.PolicyName})

                if not_resource_list and action_list:
                    for resource in not_resource_list:
                        for action in action_list:
                            tx.evaluate('''
                                MATCH (p:Policy), (res:NotResource)
                                WHERE p.name = $policyName AND res.name = $resourceName AND res.forPolicy = $policy
                                CREATE (p)-[:CONTAINS]->(action:NotAction {name: $name})-[:WORKS_NOT_ON]->(res)
                                RETURN action
                               ''', parameters={'policyName': row.PolicyName, 'resourceName': resource, 'name': action,
                                                'policy': row.PolicyName})

                if not_resource_list and not_action_list:
                    for resource in not_resource_list:
                        for action in not_action_list:
                            tx.evaluate('''
                                MATCH (p:Policy), (res:NotResource)
                                WHERE p.name = $policyName AND res.name = $resourceName AND res.forPolicy = $policy
                                CREATE (p)-[:CONTAINS]->(action:notAction {name: $name})-[:WORKS_NOT_ON]->(res)
                                RETURN action
                               ''', parameters={'policyName': row.PolicyName, 'resourceName': resource, 'name': action,
                                                'policy': row.PolicyName})

                if resource_list and not_action_list:
                    for resource in resource_list:
                        for action in not_action_list:
                            tx.evaluate('''
                                MATCH (p:Policy), (res:Resource)
                                WHERE p.name = $policyName AND res.name = $resourceName AND res.forPolicy = $policy
                                CREATE (p)-[:CONTAINS]->(action:NotAction {name: $name})-[:WORKS_NOT_ON]->(res)
                                RETURN action
                               ''', parameters={'policyName': row.PolicyName, 'resourceName': resource, 'name': action,
                                                'policy': row.PolicyName})

        except json.decoder.JSONDecodeError as e:
            warnings.warn("Error in row '{}': '{}', skipping row...".format(row.PolicyName, e))

    gr.commit(tx)


def create_user_nodes(gr, users):
    """Create user nodes for given graph.

        Parameters
        ----------
        gr : Graph
            Graph for which to create nodes.

        users : pd.DataFrame
            Users for which to create nodes.
        """
    tx = gr.begin()

    for index, row in tqdm(users.iterrows(), desc="Loading users"):
        tx.evaluate('''
            CREATE (user:User {name: $name, id: $id, arn: $arn, attachedPolicies: $attachedPolicies}) RETURN user
            ''', parameters={'name': row.UserName, 'id': row.UserId, 'arn': row.Arn,
                             'attachedPolicies': row.AttachedPolicies})
    gr.commit(tx)

    tx = gr.begin()
    for index, row in tqdm(users.iterrows(), desc="Attaching user policies"):
        attached_policies = row.AttachedPolicies.replace("\'", "\"")
        attached_policies_list = json.loads(attached_policies)
        for policy in attached_policies_list:
            tx.evaluate('''
                MATCH (u:User), (p:Policy)
                WHERE u.name = $userName AND p.name = $policyName
                CREATE (p)-[:IS_ATTACHED_TO]->(u)
                ''', parameters={'userName': row.UserName, 'policyName': policy['PolicyName']})
    gr.commit(tx)


def create_group_nodes(gr, groups):
    """Create group nodes for given graph.

        Parameters
        ----------
        gr : Graph
            Graph for which to create nodes.

        groups : pd.DataFrame
            Groups for which to create nodes.
        """
    tx = gr.begin()

    for index, row in tqdm(groups.iterrows(), desc="Loading groups"):
        tx.evaluate('''
            CREATE (group:Group {name: $name, id: $id, arn: $arn, attachedPolicies: $attachedPolicies, user: $users}) RETURN group
            ''', parameters={'name': row.GroupName, 'id': row.GroupId, 'arn': row.Arn,
                             'attachedPolicies': row.AttachedPolicies, 'users': row.Users})
    gr.commit(tx)

    tx = gr.begin()
    for index, row in tqdm(groups.iterrows(), desc="Attaching group policies"):
        attached_policies = row.AttachedPolicies.replace("\'", "\"")
        attached_policies_list = json.loads(attached_policies)
        for policy in attached_policies_list:
            tx.evaluate('''
                MATCH (g:Group), (p:Policy)
                WHERE g.name = $groupName AND p.name = $policyName
                CREATE (p)-[:IS_ATTACHED_TO]->(g)
                ''', parameters={'groupName': row.GroupName, 'policyName': policy['PolicyName']})
        gr.commit(tx)
        tx = gr.begin()
        users = row.Users.replace("\'", "\"")
        users_list = json.loads(users)
        for user in users_list:
            tx.evaluate('''
                MATCH (u:User), (g:Group)
                WHERE u.name = $userName AND g.name = $groupName
                CREATE (u)-[:PART_OF]->(g)
                ''', parameters={'userName': user['UserName'], 'groupName': row.GroupName})
        gr.commit(tx)


def create_role_nodes(gr, roles):
    """Create role nodes for given graph.

        Parameters
        ----------
        gr : Graph
            Graph for which to create nodes.

        roles : pd.DataFrame
            Roles for which to create nodes.
        """
    tx = gr.begin()

    for index, row in tqdm(roles.iterrows(), desc="Loading roles"):
        try:
            tx.evaluate('''
                CREATE (role:Role {name: $name, id: $id, arn: $arn, attachedPolicies: $attachedPolicies, assumeRolePolicyDocumentVersion: $assumeRolePolicyDocumentVersion ,assumeRolePolicyDocumentStatement: $assumeRolePolicyDocumentStatement}) RETURN role
                ''', parameters={'name': row.RoleName, 'id': row.RoleId, 'arn': row.Arn,
                                 'attachedPolicies': row.AttachedPolicies,
                                 'assumeRolePolicyDocumentVersion': row.AssumeRolePolicyDocumentStatement,
                                 'assumeRolePolicyDocumentStatement': row.AssumeRolePolicyDocumentStatement})
        except AttributeError as e:
            # Print warning
            warnings.warn("Error in row '{}': '{}', trying to load as json...".format(row.RoleName, e))

            policy_document = json.loads(row.AssumeRolePolicyDocument)

            tx.evaluate('''
                CREATE (role:Role {name: $name, id: $id, arn: $arn, attachedPolicies: $attachedPolicies, assumeRolePolicyDocumentVersion: $assumeRolePolicyDocumentVersion ,assumeRolePolicyDocumentStatement: $assumeRolePolicyDocumentStatement}) RETURN role
                ''', parameters={'name': row.RoleName, 'id': row.RoleId, 'arn': row.Arn,
                                 'attachedPolicies': row.AttachedPolicies,
                                 'assumeRolePolicyDocumentVersion': policy_document.get('Version', 'N/A'),
                                 'assumeRolePolicyDocumentStatement': str(policy_document.get('Statement', 'N/A'))})

    gr.commit(tx)

    tx = gr.begin()

    for index, row in tqdm(roles.iterrows(), desc="Attaching role policies"):
        attached_policies = row.AttachedPolicies.replace("\'", "\"")
        attached_policies_list = json.loads(attached_policies)
        for policy in attached_policies_list:
            tx.evaluate('''
                MATCH (r:Role), (p:Policy)
                WHERE r.name = $roleName AND p.name = $policyName
                CREATE (p)-[:IS_ATTACHED_TO]->(r)
                ''', parameters={'roleName': row.RoleName, 'policyName': policy['PolicyName']})
    gr.commit(tx)


if __name__ == "__main__":
    # Create connection with Graph
    graph = Graph("bolt://localhost:7687", user="neo4j", password="password")

    # Load data from stored files
    # df_policies, df_users, df_groups, df_roles = load_excel("./output/iam_policy_data_2021-04-09_10:15.xlsx")
    df_policies, df_users, df_groups, df_roles = load_excel("../data/iam_policy_data_2021-05-12_11:03.xlsx")

    # Create relevant nodes
    create_policy_nodes  (graph, df_policies)
    create_resource_nodes(graph, df_policies)
    create_action_nodes  (graph, df_policies)
    create_role_nodes    (graph, df_roles)
