import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd


df = pd.read_csv('nyc_trees_sample.csv')
df = df.dropna(subset=['latitude', 'longitude', 'spc_common', 'health', 'borough', 'tree_dbh'])
df['spc_common'] = df['spc_common'].str.title()
df['steward']    = df['steward'].fillna('')


HEALTH_ORDER  = ['Good', 'Fair', 'Poor']
HEALTH_COLORS = {'Good': '#27AE60', 'Fair': '#F1C40F', 'Poor': '#E74C3C'}
STEWARD_MAP   = {'': 'None', '1or2': '1–2', '3or4': '3–4', '4orMore': '4+'}
STEWARD_ORDER = ['None', '1–2', '3–4', '4+']
DBH_MAX       = 60


_bh = (
    df[df['health'].isin(HEALTH_ORDER)]
    .groupby(['borough', 'health']).size().reset_index(name='count')
)
_bh['pct'] = (_bh['count'] / _bh.groupby('borough')['count'].transform('sum') * 100).round(1)
BOROUGH_HEALTH_DF = _bh

#Styles 
BG    = '#F4F7F6'
WHITE = '#FFFFFF'
TEXT  = '#2C3E50'
GREEN = '#27AE60'
BLUE  = '#2980B9'

_card = {
    'padding': '18px 16px', 'borderRadius': '10px',
    'textAlign': 'center', 'flex': '1', 'margin': '0 8px',
}
_panel = {
    'borderRadius': '10px', 'padding': '8px',
}
_filter_block = {
    'display': 'flex', 'flexDirection': 'column', 'gap': '6px',
    'padding': '0 16px 0 0',
}
_label = {'fontSize': '12px', 'fontWeight': 'bold', 'color': TEXT,
          'textTransform': 'uppercase', 'letterSpacing': '0.05em'}

app = dash.Dash(__name__)

app.layout = html.Div(
    style={'backgroundColor': BG, 'fontFamily': 'Segoe UI, sans-serif', 'padding': '2%'},
    children=[

        #Header
        html.H1("NYC Tree Census Visualization",
                style={'textAlign': 'center', 'color': TEXT, 'fontWeight': 'bold',
                       'marginBottom': '4px'}),
        html.P("Explore how community care, species, and geography shape NYC's urban forest.",
               style={'textAlign': 'center', 'color': '#7F8C8D', 'fontStyle': 'italic',
                      'marginBottom': '24px', 'maxWidth': '640px', 'margin': '0 auto 24px'}),

        #KPI Row
        html.Div([
            html.Div([html.H3(id='kpi-total',       style={'margin': '0', 'color': GREEN}),
                      html.P("Trees Analyzed",       style={'margin': '0', 'fontSize': '13px', 'color': '#7F8C8D'})], style=_card),
            html.Div([html.H3(id='kpi-pct-good',    style={'margin': '0', 'color': GREEN}),
                      html.P("In Good Health",       style={'margin': '0', 'fontSize': '13px', 'color': '#7F8C8D'})], style=_card),
            html.Div([html.H3(id='kpi-avg-dbh',     style={'margin': '0', 'color': BLUE}),
                      html.P("Avg Diameter (in)",    style={'margin': '0', 'fontSize': '13px', 'color': '#7F8C8D'})], style=_card),
            html.Div([html.H3(id='kpi-top-species', style={'margin': '0', 'color': '#8E44AD'}),
                      html.P("Dominant Species",     style={'margin': '0', 'fontSize': '13px', 'color': '#7F8C8D'})], style=_card),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '24px'}),

        #Filter Bar
        html.Div([
            html.Div([
                html.Label("Borough", style=_label),
                dcc.Dropdown(
                    id='borough-dropdown',
                    options=[{'label': b, 'value': b} for b in sorted(df['borough'].unique())],
                    value='Manhattan',
                    clearable=False,
                    style={'width': '200px'},
                ),
            ], style=_filter_block),

            #Health checklist
            html.Div([
                html.Label("Health Status", style=_label),
                dcc.Checklist(
                    id='health-checklist',
                    options=[{'label': h, 'value': h} for h in HEALTH_ORDER],
                    value=HEALTH_ORDER,
                    inline=True,
                    inputStyle={'marginRight': '4px', 'accentColor': GREEN},
                    labelStyle={'marginRight': '14px', 'fontSize': '14px', 'cursor': 'pointer'},
                ),
            ], style=_filter_block),

            # Range slider
            html.Div([
                html.Label("Trunk Diameter (inches)", style=_label),
                dcc.RangeSlider(
                    id='dbh-slider',
                    min=0, max=DBH_MAX, step=1,
                    value=[0, DBH_MAX],
                    marks={0: '0', 10: '10', 20: '20', 30: '30', 40: '40', 60: '60+'},
                    tooltip={'placement': 'bottom', 'always_visible': False},
                ),
            ], style={**_filter_block, 'flex': '1', 'minWidth': '240px', 'paddingRight': '0'}),

        ], style={
            'display': 'flex', 'alignItems': 'flex-start', 'gap': '32px',
            'flexWrap': 'wrap', 'borderRadius': '10px', 'padding': '16px 20px',
            'marginBottom': '24px',
        }),

        # Map + Species bar + Stewardship
        html.Div([
            html.Div([dcc.Graph(id='tree-map')],
                     style={**_panel, 'width': '57%', 'display': 'inline-block',
                            'verticalAlign': 'top', 'boxSizing': 'border-box'}),
            html.Div([dcc.Graph(id='species-bar',   style={'marginBottom': '8px'}),
                      dcc.Graph(id='stewardship-chart')],
                     style={**_panel, 'width': '40%', 'display': 'inline-block',
                            'marginLeft': '2%', 'verticalAlign': 'top',
                            'boxSizing': 'border-box'}),
        ], style={'marginBottom': '20px'}),

        #Borough comparison + Problems + Species scatter
        html.Div([
            html.Div([dcc.Graph(id='borough-health-chart')],
                     style={**_panel, 'width': '37%', 'display': 'inline-block',
                            'verticalAlign': 'top', 'boxSizing': 'border-box'}),
            html.Div([dcc.Graph(id='problems-chart')],
                     style={**_panel, 'width': '28%', 'display': 'inline-block',
                            'marginLeft': '2%', 'verticalAlign': 'top',
                            'boxSizing': 'border-box'}),
            html.Div([dcc.Graph(id='species-scatter')],
                     style={**_panel, 'width': '28%', 'display': 'inline-block',
                            'marginLeft': '2%', 'verticalAlign': 'top',
                            'boxSizing': 'border-box'}),
        ]),
    ],
)

@app.callback(
    [Output('tree-map',             'figure'),
     Output('species-bar',          'figure'),
     Output('stewardship-chart',    'figure'),
     Output('borough-health-chart', 'figure'),
     Output('problems-chart',       'figure'),
     Output('species-scatter',      'figure'),
     Output('kpi-total',            'children'),
     Output('kpi-pct-good',         'children'),
     Output('kpi-avg-dbh',          'children'),
     Output('kpi-top-species',      'children')],
    [Input('borough-dropdown', 'value'),
     Input('health-checklist',  'value'),
     Input('dbh-slider',        'value')],
)
def update_dashboard(selected_borough, selected_health, dbh_range):
    if not selected_health:
        selected_health = HEALTH_ORDER

    dbh_lo, dbh_hi = dbh_range
    dbh_hi_actual = df['tree_dbh'].max() if dbh_hi >= DBH_MAX else dbh_hi

    fdf = df[
        (df['borough'] == selected_borough) &
        (df['tree_dbh'] >= dbh_lo) &
        (df['tree_dbh'] <= dbh_hi_actual)
    ]

    hdf = fdf[fdf['health'].isin(selected_health)]

    total    = f"{len(fdf):,}"
    pct_good = f"{(fdf['health'] == 'Good').mean() * 100:.0f}%" if len(fdf) else "—"
    avg_dbh  = f"{fdf['tree_dbh'].mean():.1f}\"" if len(fdf) else "—"
    top_spec = fdf['spc_common'].mode()[0] if len(fdf) else "N/A"

    #Map
    fig_map = px.scatter_mapbox(
        hdf, lat='latitude', lon='longitude',
        color='health',
        color_discrete_map=HEALTH_COLORS,
        category_orders={'health': HEALTH_ORDER},
        hover_name='spc_common',
        hover_data={'tree_dbh': True, 'steward': True,
                    'latitude': False, 'longitude': False},
        zoom=11, height=680,
        title=f"Tree Health Map — {selected_borough}",
    )
    fig_map.update_layout(mapbox_style='carto-positron',
                          margin={'r': 0, 't': 40, 'l': 0, 'b': 0},
                          legend_title_text='Health')

    # Stacked species bar
    top10     = hdf['spc_common'].value_counts().nlargest(10).index
    sp_health = (
        hdf[hdf['spc_common'].isin(top10)]
        .groupby(['spc_common', 'health']).size().reset_index(name='count')
    )
    fig_species = px.bar(
        sp_health, x='count', y='spc_common', color='health', orientation='h',
        color_discrete_map=HEALTH_COLORS,
        category_orders={'health': HEALTH_ORDER},
        barmode='stack',
        title='Top 10 Species',
        labels={'count': 'Trees', 'spc_common': ''},
        height=330,
    )
    fig_species.update_layout(yaxis={'categoryorder': 'total ascending'},
                               plot_bgcolor='white',
                               margin={'t': 40, 'b': 10, 'l': 10, 'r': 10},
                               legend_title_text='Health')

    #Stewardship vs Health
    stew_df = fdf.copy()
    stew_df['steward_label'] = stew_df['steward'].map(STEWARD_MAP)
    sw = (
        stew_df[stew_df['health'].isin(selected_health)]
        .groupby(['steward_label', 'health']).size().reset_index(name='count')
    )
    sw['pct'] = (sw['count'] / sw.groupby('steward_label')['count'].transform('sum') * 100).round(1)

    fig_stew = px.bar(
        sw, x='steward_label', y='pct', color='health',
        color_discrete_map=HEALTH_COLORS,
        category_orders={'health': HEALTH_ORDER, 'steward_label': STEWARD_ORDER},
        barmode='stack',
        title='Does Stewardship Improve Health?',
        labels={'steward_label': 'Stewards per Tree', 'pct': '% of Trees'},
        height=310,
    )
    fig_stew.update_layout(plot_bgcolor='white',
                            margin={'t': 40, 'b': 20, 'l': 10, 'r': 10},
                            legend_title_text='Health',
                            yaxis=dict(ticksuffix='%', range=[0, 101]))
    fig_stew.update_traces(texttemplate='%{y:.0f}%', textposition='inside', textfont_size=10)

    #Borough comparison
    fig_bh = px.bar(
        BOROUGH_HEALTH_DF, x='borough', y='pct', color='health',
        color_discrete_map=HEALTH_COLORS,
        category_orders={'health': HEALTH_ORDER},
        barmode='stack',
        title='Health Distribution',
        labels={'pct': '% of Trees', 'borough': ''},
        height=370, text='pct',
    )
    fig_bh.update_traces(texttemplate='%{text:.0f}%', textposition='inside', textfont_size=10)
    fig_bh.update_layout(plot_bgcolor='white',
                          margin={'t': 40, 'b': 20, 'l': 10, 'r': 10},
                          legend_title_text='Health',
                          yaxis=dict(ticksuffix='%', range=[0, 101]),
                          uniformtext_minsize=8, uniformtext_mode='hide')
    boroughs_sorted = sorted(df['borough'].unique())
    for trace in fig_bh.data:
        trace.marker.opacity = [1.0 if b == selected_borough else 0.35 for b in boroughs_sorted]

    #Problems breakdown
    raw_problems = (
        fdf['problems'].dropna().str.split(',').explode()
        .str.strip().replace('', pd.NA).dropna()
    )
    prob_counts = raw_problems.value_counts().nlargest(8).reset_index()
    prob_counts.columns = ['problem', 'count']

    fig_prob = px.bar(
        prob_counts, x='count', y='problem', orientation='h',
        title='Top Tree Problems',
        color_discrete_sequence=['#E67E22'],
        labels={'count': 'Trees', 'problem': ''},
        height=370,
    )
    fig_prob.update_layout(yaxis={'categoryorder': 'total ascending'},
                            plot_bgcolor='white',
                            margin={'t': 40, 'b': 20, 'l': 10, 'r': 10})

    #Species scatter
    top20 = fdf['spc_common'].value_counts().nlargest(20).index
    sp_agg = (
        fdf[fdf['spc_common'].isin(top20)]
        .groupby('spc_common')
        .agg(
            count=('tree_dbh', 'count'),
            avg_dbh=('tree_dbh', 'mean'),
            pct_good=('health', lambda x: (x == 'Good').mean() * 100)
        )
        .reset_index()
    )
    sp_agg['avg_dbh']  = sp_agg['avg_dbh'].round(1)
    sp_agg['pct_good'] = sp_agg['pct_good'].round(1)

    fig_scatter = px.scatter(
        sp_agg, x='avg_dbh', y='pct_good', size='count',
        hover_name='spc_common',
        hover_data={'avg_dbh': True, 'pct_good': True, 'count': True},
        title='Tree Size vs. Health by Species',
        labels={'avg_dbh': 'Avg Diameter (in)', 'pct_good': '% in Good Health',
                'count': 'Tree Count'},
        color_discrete_sequence=[GREEN],
        size_max=30,
        height=370,
    )
    fig_scatter.update_layout(plot_bgcolor='white',
                               margin={'t': 40, 'b': 20, 'l': 10, 'r': 10})
    fig_scatter.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='white')))

    return (fig_map, fig_species, fig_stew, fig_bh, fig_prob, fig_scatter,
            total, pct_good, avg_dbh, top_spec)


if __name__ == '__main__':
    app.run(debug=True)