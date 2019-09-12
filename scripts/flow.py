from jira import JIRA
import pandas as pd
from datetime import datetime
import plotly
import plotly.graph_objs as go
import numpy as np 

plotly.offline.init_notebook_mode()

pm_data = pd.read_csv('pm_changelog_clean.csv')

pm_data['updated'] = pd.to_datetime(pm_data['updated'], utc=True).dt.tz_convert('utc')#.dt.date
pm_data = pm_data.set_index(pd.DatetimeIndex(pm_data['updated'])).sort_index()
pm_data = pm_data['2019-01-01':]

def throughput():
    pm_data_tp = pm_data
    pm_data_tp.index = pm_data_tp.index.month #_name()
    closed = pm_data_tp.loc[pm_data['status'] == 'Closed']
    closed_count = closed.index.value_counts().to_frame().sort_index()
    trace = [go.Scatter(
        x = closed_count.index,
        y = closed_count['updated'],
        mode='lines+markers',
        name='Children of PM Issues Closed by Month'
    )]
    layout = go.Layout(
        title='Children of PM Issues Closed by Month',
        xaxis=dict(
            title='Month',
            titlefont=dict(
                size=12,
            )
        ),
        yaxis=dict(
            title='# of Closed Issues',
            titlefont=dict(
                size=12,
            )
        )
    )
    fig = go.Figure(data=trace, layout=layout)
    plotly.offline.iplot(fig, filename='flow-throughput')
    # return closed_count

def time():
    pm_data.index.names = ['index']
    pm_issue_time_delta = []

    for key in pm_data['related_key'].unique():
        if key.startswith('PM') == False:
            rn = pm_data.loc[pm_data['related_key'] == key]
            rn_diff = rn['updated'].diff()
            rn['time_diff'] = rn_diff
            pm_issue_time_delta.append(rn)
    #pd.concat(pm_issue_time_delta)
    pm_time_delta_concat = pd.concat(pm_issue_time_delta)
    pm_time_delta_concat = pm_time_delta_concat.loc[pm_time_delta_concat['status'] == 'Test']
    pm_time_delta_concat['time_diff'] = pm_time_delta_concat['time_diff'].dt.components['days']
    pm_time_delta_concat = pm_time_delta_concat.sort_values(by=['time_diff'], ascending=False)
    #   TICK LABELS GETTING MIXED UP WHEN THERE ARE TWO INSTANCES OF ONE RELATED_KEY
    #   EXAMPLE:
    #   print(pm_time_delta_concat.loc[pm_time_delta_concat['related_key'] == 'RN-1665'])
    trace = [
        go.Bar(
            x=pm_time_delta_concat['related_key'], 
            y=pm_time_delta_concat['time_diff']
        )
    ]
    layout = go.Layout(
        title='Doing Duration of PM Child Issues',
        width=1280, 
        xaxis=dict(
            title='Issue Key',
            tickmode='linear',
            tickvals=pm_time_delta_concat['time_diff'],
            titlefont=dict(
                size=12,
            )
        ),
        yaxis=dict(
            title='Time Delta',
            titlefont=dict(
                size=12,
            )
        )
    )
    fig = go.Figure(data=trace, layout=layout)
    plotly.offline.iplot(fig, filename='flow-throughput')
    #return pm_time_delta_concat
    #return pm_time_delta_concat['time_diff'].mean()
    #pm_data.index.names = ['index']
    #return pm_data
        
def distribution():
    pm_data_tp = pm_data
    pm_data_tp.index = pm_data_tp.index.month #_name()
    closed = pm_data_tp.loc[pm_data['status'] == 'Closed']
    closed_type_count = closed.groupby(closed.index)['related_type'].value_counts().to_frame().unstack(level=-1)
    idx_int = [1,2,3,4,5,6,7,8,9]
    idx_month = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sept']
    closed_type_count = closed_type_count.rename(index=dict(zip(idx_int,idx_month)))
    # Bug	Epic	Feature	// New Feature	// Spike	Story	Technical Story
    trace = [
        go.Bar(
            name="Bug",
            x=closed_type_count.index, 
            y=closed_type_count['related_type']['Bug'],
            marker=go.bar.Marker(
                color='#003f5c',
            )
        ),
        go.Bar(
            name="Epic",
            x=closed_type_count.index, 
            y=closed_type_count['related_type']['Epic'],
            marker=go.bar.Marker(
                color='#374c80',
            )
        ),
        go.Bar(
            name="Feature",
            x=closed_type_count.index, 
            y=closed_type_count['related_type']['Feature'],
            marker=go.bar.Marker(
                color='#7a5195',
            )
        ),
        go.Bar(
            name="New Feature",
            x=closed_type_count.index, 
            y=closed_type_count['related_type']['New Feature'],
            marker=go.bar.Marker(
                color='#bc5090',
            )
        ),
        go.Bar(
            name="Spike",
            x=closed_type_count.index, 
            y=closed_type_count['related_type']['Spike'],
            marker=go.bar.Marker(
                color='#ef5675',
            )
        ),
        go.Bar(
            name="Story",
            x=closed_type_count.index, 
            y=closed_type_count['related_type']['Story'],
            marker=go.bar.Marker(
                color='#ff764a',
            )
        ),
        go.Bar(
            name="Technical Story",
            x=closed_type_count.index, 
            y=closed_type_count['related_type']['Technical Story'],
            marker=go.bar.Marker(
                color='#ffa600',
            )
        ),
    ]
    layout = go.Layout(
        title='Distribution of Closed Issues by Month',
        barmode='stack',
        width=1280,
        height=720,
        xaxis=dict(
            title='Month',
            tickmode='linear',
            #tickvals=['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sept'],
            titlefont=dict(
                size=12,
            )
        ),
        yaxis=dict(
            title='# of Issues',
            titlefont=dict(
                size=12,
            )
        )
    )
    fig = go.Figure(data=trace, layout=layout)
    plotly.offline.iplot(fig, filename='flow-distribution')


def load():
    return pm_data

# pm_doing_closed = pm_data.loc[pm_data['status'] == 'Doing'].append(pm_data.loc[pm_data['status'] == 'Closed'])I'm