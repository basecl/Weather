from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
import dask.dataframe as dd
import time
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from flask import Flask
from dash.exceptions import PreventUpdate

cluster = Cluster(['cassandra'])
session = cluster.connect('weather')

server = Flask(__name__)
app = dash.Dash(__name__, server=server, url_base_pathname='/dash-app/')

app.layout = html.Div([
    html.H1("Weather Data Visualization App"),

    html.Div([
        html.Label("Select City:"),
        dcc.Dropdown(
            id='city-dropdown',
            options=[],
            value=None
        ),

        html.Label("Select Date Range:"),
        dcc.RangeSlider(
            id='date-range-slider',
            min=0,
            step=1,
            value=[0, 1]
        )
    ], style={'width': '50%', 'margin': 'auto', 'textAlign': 'center'}),

    html.Div([
        dcc.Graph(id='temperature-line-plot'),
        dcc.Graph(id='humidity-bar-plot'),
        dcc.Graph(id='wind-speed-scatter-plot')
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-evenly'}),

    html.Div([
        html.Div(id='temperature-stats'),
        html.Div(id='humidity-stats'),
        html.Div(id='wind-speed-stats')
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-evenly'}),
])

@app.callback(
    [Output('temperature-line-plot', 'figure'),
     Output('humidity-bar-plot', 'figure'),
     Output('wind-speed-scatter-plot', 'figure'),
     Output('temperature-stats', 'children'),
     Output('humidity-stats', 'children'),
     Output('wind-speed-stats', 'children'),
     Output('date-range-slider', 'max'),
     Output('city-dropdown', 'options')],
    [Input('city-dropdown', 'value'),
     Input('date-range-slider', 'value')]
)
def update_plots(selected_city, selected_date_range):
    try:
        query = "SELECT DISTINCT city FROM r_city"
        cities_result = session.execute(query)
        cities = [city[0] for city in cities_result]

        if not selected_city and cities:
            selected_city = cities[0]

        query = f"SELECT * FROM r_city WHERE city = '{selected_city}'"
        result = session.execute(query)
        df_pandas = pd.DataFrame(result)
        df_dask = dd.from_pandas(df_pandas, npartitions=8)
        result_df = df_dask.compute()

        max_date = len(result_df) - 1

        selected_date_range = [max(0, selected_date_range[0]), min(max_date, selected_date_range[1])]

        filtered_df = result_df.iloc[selected_date_range[0]:selected_date_range[1] + 1].astype(str)

        temp_line_fig = px.line(
            filtered_df,
            x='date',
            y='avg_temp_c',
            title=f'Average Temperature Over Time - {selected_city}',
            labels={'avg_temp_c': 'Average Temperature (°C)', 'date': 'Date'}
        )

        humidity_bar_fig = px.bar(
            filtered_df,
            x='date',
            y='humidity',
            title=f'Humidity Over Time - {selected_city}',
            labels={'humidity': 'Humidity (%)', 'date': 'Date'}
        )

        wind_speed_scatter_fig = px.scatter(
            filtered_df,
            x='date',
            y='wind_kph',
            title=f'Wind Speed Over Time - {selected_city}',
            labels={'wind_kph': 'Wind Speed (kph)', 'date': 'Date'}
        )

        temp_stats = [
            f"Maximum Temperature: {filtered_df['max_temp_c'].max()}°C \t",
            f"Minimum Temperature: {filtered_df['min_temp_c'].min()}°C \t"
        ]

        humidity_stats = [
            f"Maximum Humidity: {filtered_df['humidity'].max()}% \t",
            f"Minimum Humidity: {filtered_df['humidity'].min()}% \t"
        ]

        wind_speed_stats = [
            f"Maximum Wind Speed: {filtered_df['wind_kph'].max()} kph \t",
            f"Minimum Wind Speed: {filtered_df['wind_kph'].min()} kph \t"
        ]

        max_date = len(result_df) - 1

        return temp_line_fig, humidity_bar_fig, wind_speed_scatter_fig, temp_stats, humidity_stats, wind_speed_stats, max_date, [{'label': city, 'value': city} for city in cities]
    except Exception as e:
        print(f"An error occurred: {e}")
        return (
            px.line(),
            px.bar(),
            px.scatter(),
            "No data available",
            "No data available",
            "No data available",
            0,
            []
        )

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=7954)
