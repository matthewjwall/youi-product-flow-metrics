from jira import JIRA
import pandas as pd
from datetime import datetime
import plotly
import plotly.graph_objs as go
import numpy as np 
from ast import literal_eval
from IPython.display import display, HTML

pd.set_option('display.max_columns', 999)
plotly.offline.init_notebook_mode()

def product_closed_time(version):
    eng_data = pd.read_csv('eng_changelog_clean.csv', encoding='utf_8').drop(['Unnamed: 0'], axis=1)
    data = pd.read_csv('pm_changelog_clean.csv', encoding='utf_8').drop(['Unnamed: 0', 'remove'], axis=1)
    # Only include version string in pm_changelog_clean 'fix_version' column
    for index, row in data.iterrows():
        fix = row["fix_version"]
        try:
            fix = literal_eval(fix)[0]['name']
            data.at[index, "fix_version"] = fix
        except:
            data.at[index, "fix_version"] = "None"
    # Convert timestamps to utc, set index as 'updated_time' and sort index
    eng_data['updated_time'] = pd.to_datetime(eng_data['updated_time'], utc=True).dt.tz_convert('utc')
    eng_data = eng_data.set_index(pd.DatetimeIndex(eng_data['updated_time'])).sort_index()
    eng_data.index.names = ['index']
    eng_time_delta = []
    # Get time diff for non-PM issues
    for key in eng_data['eng_key'].unique():
        if key.startswith('PM') == False:
            issue = eng_data.loc[eng_data['eng_key'] == key]
            issue_diff = issue['updated_time'].diff()
            issue['time_diff'] = issue_diff
            # Get Sum of all status change time diffs 
            # *** TO DO: GET SUM OF ALL _RELEVANT_ STATUS CHANGE TIME DIFFS ***
            issue['time_sum'] = issue['time_diff'].sum()
            eng_time_delta.append(issue)
    
    eng_time = pd.concat(eng_time_delta)
    eng_time = eng_time.loc[eng_time['fix_version'] == version]
    
    #eng_time = eng_time.loc[(eng_time["updated_status"] == "Closed") | (eng_time["updated_status"] == "Done")]

    ddb = eng_time.loc[eng_time['DDB'] == 1]

    return ddb

def milestone_investment(version):
    eng_data = pd.read_csv('eng_changelog_clean.csv', encoding='utf_8').drop(['Unnamed: 0'], axis=1)
    data = pd.read_csv('pm_changelog_clean.csv', encoding='utf_8').drop(['Unnamed: 0', 'remove'], axis=1)
    for index, row in data.iterrows():
        fix = row["fix_version"]
        try:
            fix = literal_eval(fix)[0]['name']
            data.at[index, "fix_version"] = fix
        except:
            data.at[index, "fix_version"] = "None"

    eng = eng_data.loc[eng_data['fix_version'] == version]
    eng = eng.loc[(eng["updated_status"] == "Closed") | (eng["updated_status"] == "Done")]

    total = eng['eng_key'].unique().size

    ddb = eng.loc[eng['DDB'] == 1]["eng_key"].unique().size
    crt = eng.loc[(eng['Customer_Priority'] == 1) | (eng['Services_Priority'] == 1)]["eng_key"].unique().size
    qual = eng.loc[eng['issue_type'] == 'Bug']["eng_key"].unique().size
    pm = data.loc[data["fix_version"] == version].loc[(data["updated_status"] == "Closed") | (data["updated_status"] == "Done")]['related_key'].unique().size

    unlabelled = total - (ddb + crt + qual + pm)

    percentages = {
        'PM Backlog': str(format(calc_percent(pm, total), '.2f')) + '%',
        'Engineering': str(format(calc_percent(ddb, total), '.2f')) + '%',
        'Quality': str(format(calc_percent(qual, total), '.2f')) + '%',
        'CRT': str(format(calc_percent(crt, total), '.2f')) + '%',
        'Unlabelled': str(format(calc_percent(unlabelled, total), '.2f')) + '%',
    }

    issue_count = {
        'PM Backlog': pm,
        'Engineering': ddb,
        'Quality': qual,
        'CRT': crt,
        'Unlabelled': unlabelled,
    }

    inv_list = [
        [version, 'CRT', crt],
        [version, 'Quality', qual],
        [version, 'Engineering', ddb],
        [version, 'PM Backlog', pm]
    ]
    
    inv_df = pd.DataFrame(inv_list, columns=['release', 'category', 'closed'])
    trace = [
        go.Bar(
            name="Investment Breakdown for " + version,
            y=inv_df['category'], 
            x=inv_df['closed'],
            orientation='h',
            marker=go.bar.Marker(
                color='#374c80',
            )
        )
    ]
    layout = go.Layout(
        barmode='stack',
        title='Milestone Investment, ' + version,
        xaxis=dict(
            #title='# of Issues',
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
    plotly.offline.iplot(fig, filename='eng_' + version)

    display(HTML('''
        <i><h4>Nota Bene: Data Veracity</h4></i>
        <br>
        <div>For each release, a subset of issues do not include metadata (shown below as <i>Unlabelled</i>) that corresponds to Product Backlog, CRT, Quality or Engineering categories. Accordingly, the percentages listed for categories in each release do not have a sum total of 100%.</div>
    '''))
    display(pd.DataFrame.from_records([percentages]))
    display(pd.DataFrame.from_records([issue_count]))
    display(HTML('<i>Total Number of Issues: ' + str(total) + '</i>'))

def calc_percent(category, total):
    return (category / total) * 100

data = pd.read_csv('pm_changelog_clean.csv', encoding='utf_8').drop(['Unnamed: 0', 'remove'], axis=1)

def pm_okrs():
    okrs_list = ["Cloud_JSX", "Enablement", "JSX", "Product_Performance", "Platform", "RN_Upgrade"]
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

def get_closed(df, label):
    return df.loc[(data["updated_status"] == "Closed") | (data["updated_status"] == "Done")].loc[data[label] == 1]["related_key"].unique().size

def get_total(df, label):
    return df.loc[data[label] == 1]["related_key"].unique().size

