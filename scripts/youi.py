from jira import JIRA
import pandas as pd
from datetime import datetime
from scripts import youi_utils

#---------- FLOW METRICS ----------#

def get_pm_issues():
    results = youi_utils.jira_search('project in (PM)')
    file_name = 'pm_jira_' + datetime.now().strftime('%Y-%m-%d') + '.csv'
    results.to_csv(file_name, encoding='utf-8', index=False)
    return file_name

def pm_children_changelog(pm_csv):
    pm_jira = pd.read_csv(pm_csv)
    children = []
    pm_id_key = pd.DataFrame({'pm_id': pm_jira['id'], 'pm_key': pm_jira['key']})
    for index, row in pm_id_key.iterrows():
        issue_list = youi_utils.jira_auth().issue(row['pm_id'], expand='changelog').raw['fields']['issuelinks']
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
            youi_utils.get_single_changelog(row['pm_key'], row['pm_id'], rel)
    pm_changelog = pd.read_csv('pm_changelog.csv', names= ['remove', 'pm_key', 'pm_id', 'related_key', 'related_id', 'related_type', 'updated', 'status'])
    return pm_changelog

