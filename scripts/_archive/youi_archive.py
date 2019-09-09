from jira import JIRA
import pandas as pd
from datetime import datetime

jira_fields = ['key', 'fields.issuetype.name', 'fields.priority.name', 'fields.project.key', 'fields.assignee.name',
               'fields.created', 'fields.creator.name', 'fields.customfield_10004',
               'fields.reporter.name', 'fields.resolution.name', 'fields.resolutiondate', 'fields.summary', 
              ] #fields.customfield_10004: Story Points

pm_fields = ['key', 'fields.issuetype.name', 'fields.labels', 'fields.summary']

#----- GET ALL PRODUCT ISSUES TO CSV -----#
#     data = youi.get_closed_in_period()
#     jira_data = pd.read_csv('product_jira_2019-08-09.csv')
#     changelog = pd.read_csv('product_jira_changelog_2019-08-10.csv')
#     youi.get_changelog(jira_data)
#----- GET ALL PRODUCT ISSUES TO CSV  -----#

#---------- UTILITY FUNCTIONS ----------#

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

def get_closed_in_period(period = '-12w'):
    results = jira_search('project in (US, BS, CS, RN, PT, PA) AND status changed to closed AFTER ' + period)
    file_name = 'product_jira_' + datetime.now().strftime('%Y-%m-%d') + '.csv'
    results.to_csv(file_name, encoding='utf-8', index=False)
    return file_name

def get_pm_issues():
    results = jira_search('project in (PM)')
    file_name = 'pm_jira_' + datetime.now().strftime('%Y-%m-%d') + '.csv'
    results.to_csv(file_name, encoding='utf-8', index=False)
    return file_name

#---------- FLOW METRICS ----------#

# Throughput: The number of JIRA issues completed within a given time period (e.g. 1 week)
def throughput(tp_data):
    issuetype_dict = {k: v for k, v in tp_data.groupby('fields.project.key')}
    for key, df in issuetype_dict.items():
        print(key)
        print(df['fields.issuetype.name'].value_counts())


# Flow Time: The time it takes for JIRA issues to go from start to finish. 
def flow_time(ft_data):
    created = pd.to_datetime(ft_data['fields.created'], utc=True).dt.tz_convert('utc')
    resolved = pd.to_datetime(ft_data['fields.resolutiondate'], utc=True).dt.tz_convert('utc')
    flow_time_delta = pd.DataFrame((resolved - created), columns=['flow.timedelta'])#, name='Flow Time Delta')
    flow_time_full = pd.concat([ft_data, flow_time_delta], axis=1)
    return flow_time_full

def get_changelog(issues):
    cl_data = []
    issues_list = list(issues['key'])
    for i in issues_list:
        print(i)
        issue = jira_auth().issue(i, expand='changelog')
        changelog = issue.changelog
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'status':
                    cl_item = [issue, history.created, item.toString]
                    cl_data.append(cl_item)
    cl = pd.DataFrame(cl_data, columns=['issue', 'date_changed', 'changed_to'])
    cl_name = 'product_jira_changelog_' + datetime.now().strftime('%Y-%m-%d') + '.csv'
    cl.to_csv(cl_name, encoding='utf-8', index=False)
    return 'done writing ' + cl_name

def get_single_changelog(pm_key, pm_id, single_issue):
    cl_data = []
    issue = jira_auth().issue(single_issue[0], expand='changelog')
    changelog = issue.changelog
    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                cl_item = [pm_key, pm_id, issue.key, issue.id, issue.raw['fields']['issuetype']['name'], history.created, item.toString]
                cl_item_df = pd.DataFrame([cl_item])
                print(cl_item)
                cl_item_df.to_csv('pm_changelog.csv', mode='a', header=False)
                #cl_data.append(cl_item)
    #cl = pd.DataFrame(cl_data, columns=['issue', 'date_changed', 'changed_to'])
    #cl_name = 'product_jira_changelog_' + datetime.now().strftime('%Y-%m-%d') + '.csv'
    #cl.to_csv(cl_name, encoding='utf-8', index=False)
    print('done')

def tester(pm_key, pm_id, single_issue):
    cl_data = []
    issue = jira_auth().issue(single_issue[0], expand='changelog')
    changelog = issue.changelog
    for history in changelog.histories:
        for item in history.items:
            if item.field == 'status':
                print(issue.raw['fields']['issuetype']['name'])

def get_children(issue_id):
    children = [] 
    for i in issue_id:
        print(i)
        issue_list = jira_auth().issue(i, expand='changelog').raw['fields']['issuelinks']
        for item in issue_list:
            flat_issue_list = flatten_dict(item)
            children.append(flat_issue_list)
    file_name = 'pm_jira_children' + datetime.now().strftime('%Y-%m-%d') + '.csv'
    pd.DataFrame.from_records(children).to_csv(file_name, encoding='utf-8', index=False)
    print('Finished writing: ' + file_name)

def main_calc():
    pm_jira = pd.read_csv('pm_jira_2019-08-19.csv')
    children = []
    pm_id_key = pd.DataFrame({'pm_id': pm_jira['id'], 'pm_key': pm_jira['key']})
    for index, row in pm_id_key.iterrows():
        issue_list = jira_auth().issue(row['pm_id'], expand='changelog').raw['fields']['issuelinks']
        related_issues = []
        for i in issue_list:
            try:
                related_entry = [i['outwardIssue']['id'], i['outwardIssue']['key']]
                print(related_entry)
                related_issues.append(related_entry)
            except:
                print('No related issues')
        pm_related = [row['pm_key'], row['pm_id'], related_issues]
        children.append(pm_related)
    pm_all_related = pd.DataFrame.from_records(children, columns=['pm_key', 'pm_id', 'pm_related'])
    for index, row in pm_all_related.iterrows():
        for rel in row['pm_related']:
            get_single_changelog(row['pm_key'], row['pm_id'], rel)
    pm_changelog = pd.read_csv('pm_changelog.csv', names= ['remove', 'pm_key', 'pm_id', 'related_key', 'related_id', 'related_type', 'updated', 'status'])
    return pm_changelog

    #return jira_auth().issue('76939', expand='changelog').raw['changelog']

    #cl_pivot #.groupby([cl_pivot.index, 'from_to'])['changed'].first().unstack()

    #return pd.pivot(cl_pivot, values=cl_pivot['changed'], columns=cl_pivot['from_to'])