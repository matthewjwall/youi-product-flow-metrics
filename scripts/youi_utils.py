from jira import JIRA
import pandas as pd
from datetime import datetime

#---------- UTILITY FUNCTIONS ----------#

def get_single_changelog(pm_key, pm_id, single_issue, pm_labels):
    print('GSC, Labels: ' + str(pm_labels))
    cl_data = []
    issue = jira_auth().issue(single_issue[0], expand='changelog')
    print(issue)
    changelog = issue.changelog
    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                cl_item = [pm_key, pm_id, issue.key, issue.id, issue.raw['fields']['issuetype']['name'], history.created, item.toString, pm_labels]
                cl_item_df = pd.DataFrame([cl_item])
                print(cl_item)
                cl_item_df.to_csv('pm_changelog.csv', mode='a', header=False)
                #cl_data.append(cl_item)
    #cl = pd.DataFrame(cl_data, columns=['issue', 'date_changed', 'changed_to'])
    #cl_name = 'product_jira_changelog_' + datetime.now().strftime('%Y-%m-%d') + '.csv'
    #cl.to_csv(cl_name, encoding='utf-8', index=False)
    print('done')

def generic_changelog(single_issue, labels):
    cl_data = []
    issue = jira_auth().issue(single_issue, expand='changelog')
    print(issue)
    changelog = issue.changelog
    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                cl_item = [issue.key, issue.id, issue.raw['fields']['issuetype']['name'], history.created, item.toString, labels]
                cl_item_df = pd.DataFrame([cl_item])
                print(cl_item)
                cl_item_df.to_csv('eng_changelog.csv', mode='a', header=False)
                #cl_data.append(cl_item)
    #cl = pd.DataFrame(cl_data, columns=['issue', 'date_changed', 'changed_to'])
    #cl_name = 'product_jira_changelog_' + datetime.now().strftime('%Y-%m-%d') + '.csv'
    #cl.to_csv(cl_name, encoding='utf-8', index=False)
    print('done')

def flatten_dict(d):
    def items():
        for key, value in d.items():
            if isinstance(value, dict):
                for subkey, subvalue in flatten_dict(value).items():
                    yield key + "." + subkey, subvalue
            else:
                yield key, value
    return dict(items())

def jira_auth():
    user = 'matthew.wall@youi.tv'
    apikey = 'TlbsBflmaTz8YTJ2WGDzCD20'
    server = 'https://youilabs.atlassian.net'
    options = {
        'server': server
    }
    jira = JIRA(options, basic_auth=(user,apikey))
    return jira

def jira_search(query):
    #--- Set pandas column display
    pd.set_option('display.max_columns', 999)
    #--- Pagination Variables
    all_issues = []
    block_size = 100
    block_num = 0
    #--- Pagination Main
    while True:
        start_idx = block_num * block_size
        search_raw = jira_auth().search_issues(query, startAt=start_idx, maxResults=block_size)
        if len(search_raw) == 0:
            break
        block_num = block_num + 1
        all_issues.append(search_raw)
    all_issues_flat = [item for sublist in all_issues for item in sublist]
    search_list = []
    for item in all_issues_flat:
        flat_issue = flatten_dict(item.raw)
        search_list.append(flat_issue)
    search = pd.DataFrame.from_records(search_list)
    #search_final = search[jira_fields].copy()
    return search