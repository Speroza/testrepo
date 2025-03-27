#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# Load the data using pandas
data = pd.read_csv('https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMDeveloperSkillsNetwork-DV0101EN-SkillsNetwork/Data%20Files/historical_automobile_sales.csv')

# Initialize the Dash app
app = dash.Dash(__name__)

# Set the title of the dashboard
app.title = "Automobile Statistics Dashboard"

# Create the dropdown menu options
dropdown_options = [
    {'label': 'Yearly Statistics', 'value': 'Yearly Statistics'},
    {'label': 'Recession Period Statistics', 'value': 'Recession Period Statistics'}
]

# List of years
year_list = sorted(data["Year"].unique())

# Create the layout of the app
app.layout = html.Div([
    # Title
    html.H1("Automobile Sales Statistics Dashboard",
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 24}),
    
    # Dropdowns
    html.Div([
        html.Label("Select Statistics:"),
        dcc.Dropdown(
            id='dropdown-statistics',
            options=dropdown_options,
            value='Yearly Statistics',
            placeholder='Select a report type'
        )
    ]),

    html.Div([
        html.Label("Select Year:"),
        dcc.Dropdown(
            id='select-year',
            options=[{'label': i, 'value': i} for i in year_list],
            value=year_list[0],
            placeholder='Select a year'
        )
    ]),

    html.Div(id='output-container', className='chart-grid', style={'display': 'flex'})
])

# Callback to enable/disable year selection based on statistics type
@app.callback(
    Output('select-year', 'disabled'),
    Input('dropdown-statistics', 'value')
)
def update_input_container(selected_statistics):
    return selected_statistics != 'Yearly Statistics'

# Callback for updating the output container
@app.callback(
    Output('output-container', 'children'),
    [Input('dropdown-statistics', 'value'), Input('select-year', 'value')]
)
def update_output_container(selected_statistics, selected_year):
    if selected_statistics == 'Recession Period Statistics':
        recession_data = data[data['Recession'] == 1]
        
        # Plot 1: Automobile sales fluctuate over Recession Period
        yearly_rec = recession_data.groupby('Year')['Automobile_Sales'].mean().reset_index()
        R_chart1 = dcc.Graph(figure=px.line(yearly_rec, x='Year', y='Automobile_Sales', title="Average Automobile Sales Over Recession Period"))

        # Plot 2: Average Vehicle Sales by Type During Recession
        avg_sales = recession_data.groupby('Vehicle_Type')['Automobile_Sales'].mean().reset_index()
        R_chart2 = dcc.Graph(figure=px.bar(avg_sales, x='Vehicle_Type', y='Automobile_Sales', title="Average Vehicles Sold by Type During Recession"))

        # Plot 3: Total Advertisement Expenditure per Vehicle Type
        exp_data = recession_data.groupby('Vehicle_Type')['Advertising_Expenditure'].sum().reset_index()
        R_chart3 = dcc.Graph(figure=px.pie(exp_data, values='Advertising_Expenditure', names='Vehicle_Type', title="Total Advertising Expenditure per Vehicle Type"))

        # Plot 4: Effect of Unemployment Rate on Vehicle Sales
        unemp_data = recession_data.groupby(['Unemployment_Rate', 'Vehicle_Type'])['Automobile_Sales'].mean().reset_index()
        R_chart4 = dcc.Graph(figure=px.bar(unemp_data, x='Unemployment_Rate', y='Automobile_Sales', color='Vehicle_Type',
                                           labels={'Unemployment_Rate': 'Unemployment Rate', 'Automobile_Sales': 'Average Automobile Sales'},
                                           title='Effect of Unemployment Rate on Vehicle Type and Sales'))

        return [
            html.Div([R_chart1, R_chart2], style={'display': 'flex'}),
            html.Div([R_chart3, R_chart4], style={'display': 'flex'})
        ]
    
    elif selected_statistics == 'Yearly Statistics':
        yearly_data = data[data['Year'] == selected_year]
        
        # Plot 1: Yearly Automobile Sales Trend
        yas = data.groupby('Year')['Automobile_Sales'].mean().reset_index()
        Y_chart1 = dcc.Graph(figure=px.line(yas, x='Year', y='Automobile_Sales', title="Yearly Automobile Sales Trend"))

        # Plot 2: Total Monthly Automobile Sales
        mas = yearly_data.groupby('Month')['Automobile_Sales'].sum().reset_index()
        Y_chart2 = dcc.Graph(figure=px.line(mas, x='Month', y='Automobile_Sales', title="Total Monthly Automobile Sales"))

        # Plot 3: Average Vehicle Sales per Type
        avg_vdata = yearly_data.groupby('Vehicle_Type')['Automobile_Sales'].mean().reset_index()
        Y_chart3 = dcc.Graph(figure=px.bar(avg_vdata, x='Vehicle_Type', y='Automobile_Sales',
                                           title=f'Average Vehicles Sold by Type in {selected_year}'))

        # Plot 4: Total Advertisement Expenditure per Vehicle Type
        exp_data = yearly_data.groupby('Vehicle_Type')['Advertising_Expenditure'].sum().reset_index()
        Y_chart4 = dcc.Graph(figure=px.pie(exp_data, values='Advertising_Expenditure', names='Vehicle_Type',
                                           title=f"Total Advertising Expenditure per Vehicle Type in {selected_year}"))

        return [
            html.Div([Y_chart1, Y_chart2], style={'display': 'flex'}),
            html.Div([Y_chart3, Y_chart4], style={'display': 'flex'})
        ]

    return None

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
