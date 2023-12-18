import dash
from dash import html, dcc, ctx
from dash.dependencies import Output, Input
import dash_bootstrap_components as dbc

import pandas as pd
import plotly.express as px


def create_treemap(df, treemap_val):
    # treemap main graph
    treemap = px.treemap(df[df["Features"] == treemap_val],
                         path=['Region', 'Country'],
                         values="Value",
                         title="",
                         color_discrete_sequence=px.colors.qualitative.Bold)
    treemap.update_traces(hovertemplate='AVERAGE:<br>%{value:.2f} GW<extra></extra>')
    return treemap


def create_barchart(melted, country):
    global years_to_average
    filtered_df = melted[(melted['Country'] == country)
                         & melted['Features'].isin(['imports',
                                                    'exports'])
                         & melted_data['Year'].isin(years_to_average)].dropna(subset=['Value'])

    bar = px.bar(filtered_df,  # By selected country
                 x='Year',
                 y='Value',
                 color='Features',
                 labels={'Value': '[GW]', 'Year': 'Year'},
                 title='Comparision of imports and exports',
                 color_discrete_sequence=px.colors.qualitative.Prism)

    return bar


def create_dotplot(df, country):
    global years_to_average
    filtered_df = df[(df['Country'] == country)
                     & df['Features'].isin(['net generation', 'net consumption'])
                     & melted_data['Year'].isin(years_to_average)].dropna(subset=['Value'])
    fig = px.line(filtered_df,
                  x='Year',
                  y='Value',
                  color='Features',
                  labels={'Value': '[GW]', 'Year': 'Year'},
                  title='Comparison of net generation and net consumption',
                  color_discrete_sequence=px.colors.qualitative.Bold)

    return fig


def create_piechart(df, country):
    global years_to_average
    filtered_df_2 = df[
        (df['Country'] == country)
        & df['Features'].isin(['imports', 'net generation', 'distribution losses'])
        & melted_data['Year'].isin(years_to_average)].dropna(
        subset=['Value'])

    pie = px.pie(filtered_df_2,
                    names='Features',
                    values='Value',
                    title='Parts of net consumption',
                    color_discrete_sequence=px.colors.qualitative.Prism)

    pie.update_traces(texttemplate="%{percent:.2%}")

    return pie


########################################### DATA
treemap_value = "net consumption"

# Data
data = pd.read_csv("global_electricity_statistics.csv").sort_values(by=["Country"])

data = data.astype({'Country': 'string', 'Features': 'string', 'Region': 'string'})
data['Country'] = data['Country'].str.strip()
data['Features'] = data['Features'].str.strip()
data['Region'] = data['Region'].str.strip()

for column in data:
    if column not in ('Country', 'Features', 'Region'):
        data[column] = pd.to_numeric(data[column], errors='coerce')

# Melt the DataFrame to transform years into a single column 'Year'
melted_data = pd.melt(data, id_vars=['Country', 'Features', 'Region'], var_name='Year', value_name='Value')

# Convert 'Year' column to numeric (optional, if it's currently treated as an object)
melted_data['Year'] = pd.to_numeric(melted_data['Year'], errors='coerce')

years_to_average = melted_data['Year'].unique()  # Input timeframe
grouped_df = melted_data[melted_data['Year'].isin(years_to_average)].groupby(['Country', 'Region', 'Features'])[
    'Value'].mean().reset_index()

create_treemap(grouped_df, treemap_value)

######################################## Create the Dash app

external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    {
        'href': './assets/style.css',
        'rel': 'stylesheet',
    }
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                meta_tags=[{
                    'name': 'viewport',
                    'content': 'width=device-width, initial-scale=1.0'
                }])

app.css.config.serve_locally = True

server = app.server

# Define the layout of the app
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Electricity consumptions and generations based on countries",
                    style={'textAlign': 'center', 'margin': '40px'}),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.P("Choose treemap data:"),
            dcc.Dropdown(id='treemap-choice',
                         multi=False,
                         value='net consumption',
                         options=[{'label': 'Net consumption', 'value': 'net consumption'},
                                  {'label': 'Net generation', 'value': 'net generation'},
                                  {'label': 'Import', 'value': 'imports'},
                                  {'label': 'Export', 'value': 'exports'},
                                  {'label': 'Installed capacity', 'value': 'installed capacity'}
                                  ])
        ], width=6),
        dbc.Col([
            html.P("Show specific country on treemap:"),
            dcc.Dropdown(
                id='treemap-search',
                options=[{'label': category, 'value': category} for category in grouped_df['Country'].unique()],
                placeholder='Select a country'
            ),
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='main-treemap',
                figure={}
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.H4(id='year-text', style={'textAlign': 'end', 'margin-right': '20px'})
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.RangeSlider(
                id='year-slider',
                min=1980,
                max=2021,
                step=1,
                marks={year: str(year) for year in range(1980, 2021)},
                value=[1980, 2021]  # Initial selected range
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.H3(id='test-text', style={'margin': '50px'}),
            dcc.Location(id='jump', refresh=False),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='country-dotplot',
                figure={}
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='country-barchart',
                figure={}
            )
        ], width=8),
        dbc.Col([
            dcc.Graph(
                id='country-piechart',
                figure={}
            )
        ], width=4)
    ])
])


# Callback section: connecting the components
#########################################################################################
@app.callback(
    Output('main-treemap', 'figure'),
    Output('year-text', 'children'),
    Output("country-barchart", "style"),
    Output("country-dotplot", "style"),
    Output("country-piechart", "style"),
    Output("test-text", "children"),
    Input('treemap-search', 'value'),
    Input('treemap-choice', 'value'),
    Input('year-slider', 'value')
)
def update_treemap(searched, selected_value, selected_range):
    global grouped_df, treemap_value, grouped_df, years_to_average

    triggered_id = ctx.triggered_id
    if triggered_id == "treemap-search":
        if searched in melted_data['Country'].unique():
            tree = create_treemap(grouped_df[grouped_df["Country"] == searched.title()], treemap_value)
        else:
            tree = create_treemap(grouped_df, treemap_value)
    elif triggered_id == "treemap-choice":
        treemap_value = selected_value
        if searched in melted_data['Country'].unique():
            tree = create_treemap(grouped_df[grouped_df["Country"] == searched.title()], treemap_value)
        else:
            tree = create_treemap(grouped_df, treemap_value)
    else:
        years_to_average = list(range(selected_range[0], selected_range[1]+1))
        grouped_df = melted_data[melted_data['Year'].isin(years_to_average)].groupby(['Country', 'Region', 'Features'])[
            'Value'].mean().reset_index()
        if searched in melted_data['Country'].unique():
            tree = create_treemap(grouped_df[grouped_df["Country"] == searched.title()], treemap_value)
        else:
            tree = create_treemap(grouped_df, treemap_value)

    hide = {'display': 'none'}

    return tree, f'Selected Year Range: {selected_range[0]} - {selected_range[1]}', hide, hide, hide, ""


@app.callback(
    Output("test-text", "children", allow_duplicate=True),
    Output("country-barchart", "style", allow_duplicate=True),
    Output("country-barchart", "figure"),
    Output("country-dotplot", "style", allow_duplicate=True),
    Output("country-dotplot", "figure"),
    Output("country-piechart", "style", allow_duplicate=True),
    Output("country-piechart", "figure"),
    Input("main-treemap", "clickData"),
    prevent_initial_call=True
)
def update_country_graphs(selected_data):
    global melted_data
    country = ""
    if selected_data is not None:
        try:
            country = selected_data['points'][0]['label']
            if country in melted_data['Country'].unique():
                hide = {'display': 'block'}
                text = f'\u2193 Statistics for selected country: {country} \u2193'
            else:
                hide = {'display': 'none'}
                text = f'Selected Region: {country}'

        except:
            text = ""
            country = ""
            hide = {'display': 'none'}
    else:
        text = ""
        hide = {'display': 'none'}

    bar = create_barchart(melted_data, country)
    dot = create_dotplot(melted_data, country)
    pie = create_piechart(melted_data, country)

    return text, hide, bar, hide, dot, hide, pie


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
