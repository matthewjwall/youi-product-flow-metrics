from jira import JIRA
import pandas as pd
from datetime import datetime
import plotly
import plotly.graph_objs as go
import numpy as np 
import ast
from sklearn.preprocessing import MultiLabelBinarizer

pd.set_option('display.max_columns', 999)
plotly.offline.init_notebook_mode()

data = pd.read_csv('pm_changelog_clean.csv').drop(['Unnamed: 0', 'remove'], axis=1)
eng_data = pd.read_csv('eng_changelog.csv', names=['remove', 'eng_key', 'eng_id', 'updated_time', 'updated_status', 'fix_version', 'labels'])

# REINDEX!

#names=['remove', 'eng_key', 'eng_id', 'updated_time', 'updated_status', 'fix_version', 'labels']
#eng_data.labels = eng_data.labels.apply(lambda s: list(ast.literal_eval(s)))
#eng_onehot = pd.get_dummies(eng_data.labels.apply(pd.Series).stack()).sum(level=0)
#eng_clean = pd.concat([eng_data, eng_onehot], axis=1)
#eng_clean.to_csv('eng_changelog_clean.csv', encoding='utf-8')

def milestone_investment():
    return eng_data

def pm_okrs():
    okrs_list = ["Cloud_JSX", "Enablement", "JSX", "Performance", "Platform", "RNCloud", "RN_Upgrade"]
    milestones = ["Milestone1", "Milestone2"]
    okrs = []
    for milestone in milestones:
        for okr in okrs_list:
            row = [milestone, okr, get_closed(data.loc[data[okr] == 1], milestone), get_total(data.loc[data[okr] == 1], milestone)]
            okrs.append(row)
    
    okrs_df = pd.DataFrame(okrs, columns=["milestone", "label", "closed", "total"])
    okrs_df["diff"] = okrs_df["total"].sub(okrs_df['closed'], axis=0)

    trace = [
        go.Bar(
            name="Closed",
            y=okrs_df.loc[okrs_df["milestone"] == "Milestone1"]["label"], 
            x=okrs_df.loc[okrs_df["milestone"] == "Milestone1"]["closed"],
            orientation='h',
            marker=go.bar.Marker(
                color='#374c80',
            )
        ),
        go.Bar(
            name="Remaining",
            y=okrs_df.loc[okrs_df["milestone"] == "Milestone1"]["label"], 
            x=okrs_df.loc[okrs_df["milestone"] == "Milestone1"]["diff"],
            orientation='h',
            marker=go.bar.Marker(
                color='#ff764a',
            )
        ),
    ]
    layout = go.Layout(
        barmode='stack',
        title='Product Objectives, Milestone 1',
        xaxis=dict(
            title='# of Issues',
            tickmode='linear',
            titlefont=dict(
                size=12,
            )
        ),
        yaxis=dict(
            #title='Objective',
            titlefont=dict(
                size=12,
            )
        )
    )
    fig = go.Figure(data=trace, layout=layout)
    plotly.offline.iplot(fig, filename='PM_OKRs_M1')
    trace = [
        go.Bar(
            name="Closed",
            y=okrs_df.loc[okrs_df["milestone"] == "Milestone2"]["label"], 
            x=okrs_df.loc[okrs_df["milestone"] == "Milestone2"]["closed"],
            orientation='h',
            marker=go.bar.Marker(
                color='#374c80',
            )
        ),
        go.Bar(
            name="Remaining",
            y=okrs_df.loc[okrs_df["milestone"] == "Milestone2"]["label"], 
            x=okrs_df.loc[okrs_df["milestone"] == "Milestone2"]["diff"],
            orientation='h',
            marker=go.bar.Marker(
                color='#ff764a',
            )
        ),
    ]
    layout = go.Layout(
        barmode='stack',
        title='Product Objectives, Milestone 2',
        xaxis=dict(
            title='# of Issues',
            tickmode='linear',
            titlefont=dict(
                size=12,
            )
        ),
        yaxis=dict(
            #title='Objective',
            titlefont=dict(
                size=12,
            )
        )
    )
    fig = go.Figure(data=trace, layout=layout)
    plotly.offline.iplot(fig, filename='PM_OKRs_M2')
    return okrs_df

def get_closed(df, label):
    return df.loc[(data["updated_status"] == "Closed") | (data["updated_status"] == "Done")].loc[data[label] == 1]["related_key"].unique().size

def get_total(df, label):
    return df.loc[data[label] == 1]["related_key"].unique().size