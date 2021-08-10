from load_data import *

################################################################################
#                          Auxiliary graph functions                           #
################################################################################
def delete_roles(gr):
    """Delete all the roles and the attached relationships in the graph."""
    tx = gr.begin()
    tx.evaluate('''
        MATCH (r:Role)
        DETACH DELETE r
    ''')
    gr.commit(tx)


def delete_users(gr):
    """Delete all the users and the attached relationships in the graph."""
    tx = gr.begin()
    tx.evaluate('''
        MATCH (u:User)
        DETACH DELETE u
    ''')
    gr.commit(tx)


def delete_groups(gr):
    """Delete all the groups and the attached relationships in the graph."""
    tx = gr.begin()
    tx.evaluate('''
        MATCH (g:Group)
        DETACH DELETE g
    ''')
    gr.commit(tx)


def delete_policy_nodes(gr, policies):
    """Delete all the policies and the attached relationships in the graph."""
    tx = gr.begin()

    for index, row in policies.iterrows():
        tx.evaluate('''
            MATCH (p:Policy)-[r]->(a)-[re]->(res)
            WHERE p.name = $policyName and p.id = $policyId
            DETACH DELETE res, a, p
        ''', parameters={'policyName': row.PolicyName, 'policyId': row.PolicyId})

    gr.commit(tx)


def update_entities(gr, users, groups, roles):
    """Update the entities (users, groups and roles) in the graph."""
    # First delete all the entities in the graph
    delete_users (gr)
    delete_groups(gr)
    delete_roles (gr)

    # Now recreate the updated entities
    create_user_nodes (gr, users)
    create_group_nodes(gr, groups)
    create_role_nodes (gr, roles)


def create_updated_policy_nodes(gr, policies):
    """Update the policy nodes in the graph."""
    create_policy_nodes  (gr, policies)
    create_resource_nodes(gr, policies)
    create_action_nodes  (gr, policies)


def update_policy_node(gr, policies, new_policies):
    tx = gr.begin()

    for index, row in policies.iterrows():
        for i, r in row.iteritems():
            # If the policy change is not to the policyDocumen, simple update the property of the node
            if (not pd.isnull(r)) & (i[0] != 'PolicyDocument') & (i[1] == 'other'):
                # Set the property name and lower the first letter
                property_name = i[0][0].lower() + i[0][1:]
                tx.evaluate('''
                    MATCH (p:Policy)
                    WHERE p.name = $policyName AND p.id = $policyId
                    SET p.''' + property_name + ''' = $propertyValue
                    RETURN p.name
                ''', parameters={'policyName': new_policies.iloc[index].PolicyName,
                                 'policyId': new_policies.iloc[index].PolicyId, 'propertyValue': r})

            # If a change has been made to the policyDocument:
            # Delete the node and all the attached entities
            # Recreate the whole subgraph based on the new data
            if (not pd.isnull(r)) & (i[0] == 'PolicyDocument') & (i[1] == 'other'):
                updated_row = (new_policies.iloc[index]).to_frame().T
                delete_policy_nodes(gr, updated_row)
                create_updated_policy_nodes(gr, updated_row)

    gr.commit(tx)


# Compare the policies and return a new dataframe with updated policies that need to be changed in the graph
def compare_policies(old_policies, new_policies):
    old_policies.fillna('', inplace=True)
    new_policies.fillna('', inplace=True)

    cols = ['PolicyName', 'PolicyId']

    df_merge = old_policies.merge(new_policies, on=cols,
                                  how='outer', indicator=True)

    df_to_delete = df_merge[df_merge['_merge'] == 'left_only']

    df_to_add = df_merge[df_merge['_merge'] == 'right_only']

    temp_add_df = pd.DataFrame(columns=list(new_policies.columns))
    for index, row in df_to_add.iterrows():
        temp_add_df = temp_add_df.append(new_policies.loc[
                                     (new_policies.PolicyName == row.PolicyName) & (
                                                 new_policies.PolicyId == row.PolicyId)])

    # Concat the to be deleted and to added policies (to perform the compare later)
    df_to_do = pd.concat([df_to_delete, df_to_add])

    for index, row in df_to_do.iterrows():
        old_policies.drop(
            old_policies.loc[
                (old_policies.PolicyName == row.PolicyName) & (old_policies.PolicyId == row.PolicyId)].index,
            inplace=True)
        new_policies.drop(
            new_policies.loc[
                (new_policies.PolicyName == row.PolicyName) & (new_policies.PolicyId == row.PolicyId)].index,
            inplace=True)

    # Sort the policies and reset the pandas index
    old_policies.sort_values(by=['PolicyName'], inplace=True)
    new_policies.sort_values(by=['PolicyName'], inplace=True)
    old_policies.reset_index(drop=True, inplace=True)
    new_policies.reset_index(drop=True, inplace=True)

    # Concat the extra policy space to the policyDocument
    # and remove the ExtraPolicySpace column from both old and new dataframe
    if 'ExtraPolicySpace' in old_policies.columns:
        for index, row in old_policies.iterrows():
            if row.ExtraPolicySpace != '':
                old_policies.at[index, 'PolicyObject'] = row.PolicyObject + row.ExtraPolicySpace
        old_policies.drop('ExtraPolicySpace', 1, inplace=True)

    if 'ExtraPolicySpace' in new_policies.columns:
        for index, row in new_policies.iterrows():
            if row.ExtraPolicySpace != '':
                new_policies.at[index, 'PolicyObject'] = row.PolicyObject + row.ExtraPolicySpace
        new_df_policies.drop('ExtraPolicySpace', 1, inplace=True)

    # Use pd.compare to look for differences between the old and new policies
    diff = old_policies.compare(new_policies)

    return df_to_delete, temp_add_df, diff


if __name__ == "__main__":
    graph = Graph("bolt://localhost:7687", user="neo4j", password="password")

    df_policies, df_users, df_groups, df_roles = load_excel('./output/iam_policy_data_2021-04-02_12:19.xlsx')
    new_df_policies, new_df_users, new_df_groups, new_df_roles = load_excel('./output/iam_policy_data_2021-04-02_13:12.xlsx')

    delete, add, difference = compare_policies(df_policies, new_df_policies)

    print('Updating policies...')
    delete_policy_nodes(graph, delete)
    create_policy_nodes(graph, add)

    update_policy_node(graph, difference, new_df_policies)

    print('Updating entities...')
    update_entities(graph, new_df_users, new_df_groups, new_df_roles)
    print('Entities successfully updated')
