from jira import JIRA
import pandas as pd
from datetime import datetime
import ast
from scripts import youi_utils
import importlib

#---------- FLOW METRICS ----------#

def clean_labels():
    pm_cl_raw = pd.read_csv('pm_changelog.csv', names= ['remove', 'pm_key', 'pm_id', 'related_key', 'related_id', 'related_type', 'updated', 'status', 'labels'])
    pm_cl_raw.labels = pm_cl_raw.labels.apply(lambda s: list(ast.literal_eval(s))[0])
    pm_onehot = pd.get_dummies(pm_cl_raw.labels.apply(pd.Series).stack()).sum(level=0)
    pm_clean = pd.concat([pm_cl_raw, pm_onehot], axis=1)
    pm_clean.to_csv('pm_changelog_clean.csv', encoding='utf-8')
    print('clean df written to csv')
    return pm_clean

def get_pm_issues():
    results = youi_utils.jira_search('project in (PM)')
    file_name = 'pm_jira_' + datetime.now().strftime('%Y-%m-%d') + '.csv'
    results.to_csv(file_name, encoding='utf-8', index=False)
    return file_name

def pm_children_changelog(pm_csv):
    importlib.reload(youi_utils)
    pm_jira = pd.read_csv(pm_csv)
    children = []
    pm_id_key = pd.DataFrame({'pm_id': pm_jira['id'], 'pm_key': pm_jira['key']})
    for index, row in pm_id_key.iterrows():
        issue_list = youi_utils.jira_auth().issue(row['pm_id'], expand='changelog').raw['fields']['issuelinks']
        label_list = youi_utils.jira_auth().issue(row['pm_id'], expand='changelog').raw['fields']['labels']
        related_issues = []
        pm_labels = []
        for i in issue_list:
            try:
                related_entry = [i['outwardIssue']['id'], i['outwardIssue']['key']]
                print(related_entry)
                related_issues.append(related_entry)
                try:
                    print('labels: ' + str(label_list))
                    pm_labels.append(label_list)
                except:
                    print('no labels')
            except:
                print('No related issues')
        pm_related = [row['pm_key'], row['pm_id'], related_issues, pm_labels]
        children.append(pm_related)
    pm_all_related = pd.DataFrame.from_records(children, columns=['pm_key', 'pm_id', 'pm_related', 'pm_labels'])
    for index, row in pm_all_related.iterrows():
        for rel in row['pm_related']:
            youi_utils.get_single_changelog(row['pm_key'], row['pm_id'], rel, row['pm_labels'])
    pm_changelog = pd.read_csv('pm_changelog.csv', names= ['remove', 'pm_key', 'pm_id', 'related_key', 'related_id', 'related_type', 'updated', 'status', 'pm_labels'])
    return pm_changelog

