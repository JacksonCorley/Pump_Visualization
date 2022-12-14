# -*- coding: utf-8 -*-
"""
Created on Thu Jan  6 19:56:06 2022

@author: JC056455
"""

import base64
import datetime
import io
import os
import math


from dash import dcc, html, Input, Output, State
import dash
import dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import shapely
from shapely.geometry import LineString, Point


######################################################################################################################################################################
################################ Dashbaord layout functions###########################################################################################################

FONT_AWESOME = (
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE], prevent_initial_callbacks=True)
server = app.server

## make a list for the number of pumps selected. Hard coded to 10 for now. Used to make labels for pump type selectors.
def generate_pump_inputs(numpumps):
    Total_Pumps = numpumps ## input for total number of pumps.
    Order = list(range(1,Total_Pumps+1))
    pumps = ["Pump {}".format(x) for x in Order]
    return pumps

## make a list for teh types of pumps in the nique identifier columns uploaded.
def generate_dropdown_options(pmp_sers):
    unique_options = [{'label':x,'value':x} for x in pmp_sers]
    return unique_options

## make inputs for pump selection dropdowns and speed ranges.
def make_pump_web_inputs(pumps):
    pump_u_inputs = []
    for s,v in enumerate(pumps):
        pump_u_inputs.append(
            html.Div([
                html.Label(f'{v}: ', style={'display':'inline', 'fontSize':15}),
                dcc.Dropdown(
                    id=f'pump_list_{s}',
                    options=[{'label': 'none', 'value':'none'}],##use generate pump types for outputs
                    style={'font-size':'85%'},
                    value='none',
                ),
                html.Label('speed (%)', style={'display':'inline', 'fontSize':15}),
                dcc.Slider(
                    id=f'spd_slider_{s}',
                    min= 50,
                    max= 100,
                    step = 1,
                    value = 100,
                    marks = {50:{'label': '50%', 'style':{'font-size':'70%'}},
                             60:{'label': '60%', 'style':{'font-size':'70%'}},
                             70:{'label': '70%', 'style':{'font-size':'70%'}},
                             80:{'label': '80%', 'style':{'font-size':'70%'}},
                             90:{'label': '90%', 'style':{'font-size':'70%'}},
                             100:{'label': '100%', 'style':{'font-size':'70%'}}},
                    tooltip = {'always_visible': True,'placement':'bottom'},
                ),
            ],)
        )
    return pump_u_inputs

data_upload_style = {
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        }

##make the layout of the application.
def update_app_layout(numpumps):
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Pump Performance Visualization Tool", style={'textAlign':'center'}), width=12),
            ]),
        dbc.Row([
            dbc.Col(dcc.Upload(id='pump_upload_data',
                               children=html.Div(['(Pump Curve Data Input) Drag and Drop or ',html.A('Select Files')]),
                               style = data_upload_style,multiple=True)),
            dbc.Col(dcc.Upload(id='system_upload_data',children=html.Div(['(System Curve Data Input) Drag and Drop or ',html.A('Select Files')]),
                               style = data_upload_style,multiple=True))
            ### update this to populate with all columns in the pump data table.
           ]),
        dbc.Row([
            dbc.Col([
                 html.Label('Pump Flow (gpm) Column', style={'display':'inline', 'fontSize':18}),
                 dcc.Dropdown(id='pump_flow_col',options=[{'label': 'none', 'value':'none'}],value='none',style={'font-size':'85%'},)]),
            dbc.Col([
                 html.Label('Pump TDH (ft) Column', style={'display':'inline', 'fontSize':18}),
                 dcc.Dropdown(id='pump_tdh_col',options=[{'label': 'none', 'value':'none'}],value='none',style={'font-size':'85%'},)]),
            dbc.Col([
                 html.Label('Pump Efficiency Column', style={'display':'inline', 'fontSize':18}),
                 dcc.Dropdown(id='pump_eff_col',options=[{'label': 'none', 'value':'none'}],value='none',style={'font-size':'85%'},)]),
            dbc.Col([
                 html.Label('Pump Unique Label Column', style={'display':'inline', 'fontSize':18}),
                 dcc.Dropdown(id='pump_label_col',options=[{'label': 'none', 'value':'none'}],value='none',style={'font-size':'85%'},)]),
            dbc.Col([
                 html.Label('System Flow (gpm) Column', style={'display':'inline', 'fontSize':18}),
                 dcc.Dropdown(id='sys_flow_col',options=[{'label': 'none', 'value':'none'}],value='none',style={'font-size':'85%'},)]),
            dbc.Col([
                 html.Label('System TDH (ft) Column', style={'display':'inline', 'fontSize':18}),
                 dcc.Dropdown(id='sys_tdh_col',options=[{'label': 'none', 'value':'none'}],value='none',style={'font-size':'85%'},)]),
            dbc.Col([
                 html.Label('System Label Column', style={'display':'inline', 'fontSize':18}),
                 dcc.Dropdown(id='sys_label_col',options=[{'label': 'none', 'value':'none'}],value='none',style={'font-size':'85%'},)]),
            dbc.Col([
                 html.Label('System Curve No. Column', style={'display':'inline', 'fontSize':18}),
                 dcc.Dropdown(id='sys_crv_n_col',options=[{'label': 'none', 'value':'none'}],value='none',style={'font-size':'85%'},)])
            ]),
        dbc.Row([
            dbc.Col([html.Label('Click to Update Dropdowns', style={'fontSize':18}),
                     html.Div([html.Button('Update Dropdowns', id='update-ids', n_clicks=0)])], xs=2, sm=2, md=2, lg=2, xl=2),
            dbc.Col([html.Label('Change All Speeds', style={'fontSize':18}),
                     html.Div([dcc.Slider(id='change_all_sld',min= 50,max= 100,step = 1, marks = {50:{'label': '50%', 'style':{'font-size':'70%'}},
                                                                                                 60:{'label': '60%', 'style':{'font-size':'70%'}},
                                                                                                 70:{'label': '70%', 'style':{'font-size':'70%'}},
                                                                                                 80:{'label': '80%', 'style':{'font-size':'70%'}},
                                                                                                 90:{'label': '90%', 'style':{'font-size':'70%'}},
                                                                                                 100:{'label': '100%', 'style':{'font-size':'70%'}}},
                                          value = 100,tooltip = {'always_visible': True, 'placement':'bottom'})])], xs=2, sm=2, md=2, lg=2, xl=2),
            dbc.Col([html.Label("Select System Curves",style={'fontSize':18}),
                     dcc.Dropdown(id='sys-dropdown', 
                                  multi=True,
                                  style={'font-size':'85%'})], xs=8, sm=8, md=8, lg=8, xl=8),
            ]),
        dbc.Row([
            ### update this to
            dbc.Col(make_pump_web_inputs(generate_pump_inputs(numpumps)), xs=2, sm=2, md=2, lg=2, xl=2),
            dbc.Col([
                dcc.Graph(id='my-performance-graph', figure={"layout": {"title": "Performance Curves","height": 600,}}),
                html.H6("For improvement suggestions or bugs contact Jackson Corley - jackson.corley@jacobs.com", style={'textAlign':'left'}),
                html.Div([dbc.Button(id='export-graph',
                                     children=[html.I(className="fa fa-download mr-1"), "Download Graph"],
                                     color="info",
                                     className="mt-1"),
                          dbc.Button(id='export-oprtng-pnts',
                                     children=[html.I(className="fa fa-download mr-1"), 'Download Operating Points'],
                                     color="info",
                                     className="mt-1", )]),
                html.Div([html.Div([html.Label('Upper Preferred Operating Range', style={'fontSize':18}),
                                    html.Div([dcc.Input(id="upr_por", type="number", value=1.2, step=0.01)])]),
                          html.Div([html.Label('Lower Preferred Operating Range', style={'fontSize':18}),
                                    html.Div([dcc.Input(id="lwr_por", type="number", value=0.7, step=0.01)])])]),
                dcc.Download(id="download-op-pnts"),
                dcc.Download(id="download-graph"),
                html.Div(id='operating-data-output')], xs=10, sm=10, md=10, lg=10, xl=10)
            ]),
        dbc.Row([
            dbc.Col([
                html.H4("Column Input Definitions:", style={'textAlign':'left'}),
                html.H6("- Pump Flow (gpm) Column: Used to define pump flow for each pump.", style={'textAlign':'left'}),
                html.H6("- Pump TDH (ft) Column: Used to define pump total dyanmic head for each pump.", style={'textAlign':'left'}),  
                html.H6("- Pump Efficiency Column: Used to define pump efficiency for each pump.", style={'textAlign':'left'}),
                html.H6("- Pump Unique Label Column: Used to define a unique identifier for each pump cuve. Dataset be in a long (or tidy) format.", style={'textAlign':'left'}),
                html.H6("- System Flow (gpm) Column: Used to define pump flow for each pump. ", style={'textAlign':'left'}),
                html.H6("- System TDH (ft) Column: Used to define system total dyanmic head for each pump.", style={'textAlign':'left'}),
                html.H6("- System Label Column: Used to define a unique identifier for each system cuve. Dataset be in a long (or tidy) format.", style={'textAlign':'left'}),
                html.H6("- System Curve No. Column: Used to define a unique identifier for each system cuve if there are multiple system curves per system label. This would be used to define multiple system curves for a range of static head conditions.", style={'textAlign':'left'}),
                     ]),
            ]),
        dbc.Row([
            dbc.Col(html.Div(id='pump-data-output')),
            dbc.Col(html.Div(id='system-data-output'))
            ])
        ])
    return app.layout

app.layout = update_app_layout(10)

## parse contents of uploaded files and output in a table.
def parse_contents(contents, filename, date, tableid):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    print("decoded = ", decoded)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(id = tableid,
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            editable=True
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

## parse contents of uploaded files and output in a df.
def return_df(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            print("excel = ", io.BytesIO(decoded))
            df = pd.read_excel(io.BytesIO(decoded))
            print("excel_df = ",df)
    except Exception as e:
        print(e)
    return df

#### update this to predict cols.
def find_col_sys_name(cols):
    #print("sys cols = ", cols)
    for col in cols:
        if ("flow" in col.lower()) or ('gpm' in col.lower()):
            #print('sys_q = ', col)
            q = col
            break
        else:
            q = cols[0]
    for col in cols:
        if ("tdh" in col.lower()) or ("head" in col.lower()) or ("dynamic" in col.lower()) or ("ft" in col.lower()):
            #print('sys_tdh = ', col)
            tdh = col
            break
        else:
            tdh = cols[0]
    for col in cols: ##pump id
        if ("id" in col.lower()) or ("identifier" in col.lower()) or ("name" in col.lower()) or ("scenario" in col.lower()):
            sys_id = col
            #print("pump_id = ", sys_id)
            break
        else:
            sys_id = cols[0]
    for col in cols: #sys_curve_no
        #print("sys_crv_i = ", col)
        if ("curve" in col.lower()) or ("number" in col.lower()) or ("no." in col.lower()):
            sys_crv_no = col
            #print("sys_crv_no = ", sys_crv_no)
            break
        else:
            sys_crv_no = cols[0]
    return q, tdh, sys_id, sys_crv_no
 
    
def find_col_pump_name(cols):
    for col in cols:
        if ("flow" in col.lower()) or ('gpm' in col.lower()):
            q = col
            #print("q = ", q)
            break
        else:
            q = cols[0]
    for col in cols:
        if ("tdh" in col.lower()) or ("head" in col.lower()) or ("dynamic" in col.lower()) or ("ft" in col.lower()):
            tdh = col
            #print("tdh = ", tdh)
            break
        else:
            tdh = cols[0]
    for col in cols: ##effieincy
        if ("efficiency" in col.lower()) or ("%" in col.lower()) or ("eff" in col.lower()):
            eff = col
            #print("eff = ", eff)
            break
        else:
            eff = cols[0]
    for col in cols: ##pump id
        if ("id" in col.lower()) or ("pump" in col.lower()) or ("identifier" in col.lower()) or ("name" in col.lower()) or ("model" in col.lower()):
            pump_id = col
            #print("pump_id = ", pump_id)
            break
        else:
            pump_id = cols[0]
        ##make col lower case and do searches based on lower case.
        ##return not lower case col.
    return q, tdh, eff, pump_id
######################################################################################################################################################################
################################ END Dashbaord layout functions#######################################################################################################

######################################################################################################################################################################
################################ Graph Update Functions###############################################################################################################
def interpolate(xrange, yrange, x):
    ## interpolates values. Used to interpolate between values.
    for i in range(0,len(xrange)):
        nextrow = min(i+1,len(xrange)-1)
        int_val = yrange[nextrow] - (xrange[nextrow]-x)*((yrange[nextrow]-yrange[i])/(xrange[nextrow]-xrange[i]))
        if (x >= xrange[i]) and (x <= xrange[nextrow]) or (x <= xrange[i]) and (x >= xrange[nextrow]):
            return int_val
            break
        elif x > max(xrange) or x < min(xrange):
            int_val = 0
            return int_val
            break

def getopranges(comb_PORs,prevdata,i, upr_por, lwr_por):
    ## makes a dataset of preferred Operating Ranges.
    prevdata.sort_values(by = "Flow (gpm)", ascending = True, inplace = True)
    operating_Ranges = pd.DataFrame(data = {"Flow (gpm)":[], "TDH (ft)":[],"EFFICIENCY":[], "Pump":[], "identifier":[],})
    BEP_Flow = prevdata.loc[prevdata.EFFICIENCY == max(prevdata.EFFICIENCY),"Flow (gpm)"].values
    BEP_TDH = prevdata.loc[prevdata.EFFICIENCY == max(prevdata.EFFICIENCY),"TDH (ft)"].values
    Upper_Flow = BEP_Flow[0] * upr_por ##could make this a user input in the future.
    Upper_TDH = interpolate(list(prevdata["Flow (gpm)"]), list(prevdata["TDH (ft)"]),Upper_Flow)
    Upper_Efficiency = interpolate(list(prevdata["Flow (gpm)"]), list(prevdata["EFFICIENCY"]),Upper_Flow)
    Lower_Flow = BEP_Flow[0] * lwr_por ##could make this a user input in the future.
    Lower_TDH = interpolate(list(prevdata["Flow (gpm)"]), list(prevdata["TDH (ft)"]),Lower_Flow)
    Lower_Efficiency = interpolate(list(prevdata["Flow (gpm)"]), list(prevdata["EFFICIENCY"]),Lower_Flow)
    BEP_OP_PNT = pd.DataFrame(data = {"Flow (gpm)":BEP_Flow[0], "TDH (ft)":BEP_TDH[0],"EFFICIENCY":[max(prevdata['EFFICIENCY'])], "Pump":[0], "identifier":['Pump Curve ' + str(i)+ ' BEP']})
    Lower_OP_PNT = pd.DataFrame(data = {"Flow (gpm)":[Lower_Flow], "TDH (ft)":[Lower_TDH],"EFFICIENCY":[Lower_Efficiency], "Pump":[0], "identifier":['Pump Curve ' + str(i)+ ' Lower POR']})
    Upper_OP_PNT = pd.DataFrame(data = {"Flow (gpm)":[Upper_Flow], "TDH (ft)":[Upper_TDH],"EFFICIENCY":[Upper_Efficiency], "Pump":[0], "identifier":['Pump Curve ' + str(i)+ ' Upper POR']})
    operating_Ranges = BEP_OP_PNT
    operating_Ranges = operating_Ranges.append([Lower_OP_PNT,Upper_OP_PNT], ignore_index=True)
    comb_PORs = comb_PORs.append(operating_Ranges, ignore_index = True)
    return comb_PORs

def int_paralell_flows(prevdata,currentdata):
    ## return data = current pump curve data
    ## prevdata = cummulative pump curve data
    last_data = prevdata.copy().reset_index(drop=True)
    #print("last_data = ", last_data)
    returndata = currentdata.copy().reset_index(drop=True)   
    returndata.sort_values(by = ["TDH (ft)"], ascending = False, inplace = True)
    int_q_list = []
    #print("returndata = ", returndata,'\n\n')
    for r in returndata["TDH (ft)"]:
        New_Flow = interpolate(list(last_data["TDH (ft)"]), list(last_data["Flow (gpm)"]),r)
        int_q_list.append(New_Flow)
    currentflows = returndata['Flow (gpm)']
    cumflows = pd.DataFrame(data = {"Flow (gpm) OLD": int_q_list})
    #print("cumflows = ", cumflows)
    flows = pd.concat([currentflows, cumflows], axis=1).fillna(0)
    flows['Flow_total (gpm)'] = flows["Flow (gpm) OLD"]+ flows['Flow (gpm)']
    #print("flows = ", flows)
    returndata["Flow (gpm)"] = flows['Flow_total (gpm)']
    return returndata

    #set the first pump here in cumulative dataset
    
def find_PO_Labels(inp_dataframe, label):
    ## sets POR labels based on finding BEP, and POR 
    dataframe = inp_dataframe.copy()
    string_series = dataframe[label]
    labellst = []
    for string in string_series:
        if string.find('BEP') > -1:
            rtrn_strng = "Best Efficiency Point"
            labellst.append(rtrn_strng)
        elif string.find('Upper POR') > -1 or string.find('Lower POR') > -1:
            rtrn_strng = "Preffered Operating Range"
            labellst.append(rtrn_strng)
    dataframe['label'] = labellst
    return dataframe


def calc_intrsctns(pump_data, sys_data):
    pump_data_2 = pump_data.copy()
    sys_data_2 = sys_data.copy()
    flow_ops = []
    tdh_ops = []
    eff_ops = []
    pmp_crvs = []
    sys_crvs = []
    for pump in list(set(pump_data_2['identifier'])):
        ipump_data = pump_data_2[pump_data_2['identifier'] == pump].reset_index()
        #print("ipump_data = ", ipump_data)
        for sys_crv in list(set(sys_data_2['identifier'])):
            isys_data = sys_data_2[sys_data_2['identifier'] == sys_crv].reset_index()
            #print("isys_data = ", isys_data)
            for isys_num_crv in list(set(isys_data['Number'])):
                isys_num_data = isys_data[isys_data['Number'] == isys_num_crv].reset_index()
                for i_p in range(len(ipump_data['Flow (gpm)'])-1):
                    pq1 = ipump_data['Flow (gpm)'].iloc[i_p]
                    pq2 = ipump_data['Flow (gpm)'].iloc[i_p+1]
                    ptdh1 = ipump_data['TDH (ft)'].iloc[i_p]
                    ptdh2 = ipump_data['TDH (ft)'].iloc[i_p+1]
                    #print("pq1 = ", pq1, "pq2 = ", pq2)
                    for i_sys in range(len(isys_num_data['Flow (gpm)'])-1):
                        sq1 = isys_num_data['Flow (gpm)'].iloc[i_sys]
                        sq2 = isys_num_data['Flow (gpm)'].iloc[i_sys+1]
                        stdh1 = isys_num_data['TDH (ft)'].iloc[i_sys]
                        stdh2 = isys_num_data['TDH (ft)'].iloc[i_sys+1]
                        #print("sq1 = ", sq1, "sq2 = ", sq2)
                        pmp_line = LineString([(pq1,ptdh1),(pq2,ptdh2)])
                        #print("pmp_line = ", pmp_line)
                        sys_line = LineString([(sq1,stdh1),(sq2,stdh2)])
                        #print("sys_line = ", sys_line)
                        intrsctn_log = pmp_line.intersects(sys_line)
                        #print("intersection = ", intrsctn_log)
                        if intrsctn_log != False:
                            q = pmp_line.intersection(sys_line).x
                            eff_ops.append(interpolate(list(ipump_data["Flow (gpm)"]), list(ipump_data["EFFICIENCY"]),q))
                            flow_ops.append(q)
                            tdh_ops.append(pmp_line.intersection(sys_line).y)
                            pmp_crvs.append(pump)
                            sys_crvs.append(sys_crv)
                            break
                        
    return pd.DataFrame({'Flow (gpm)':flow_ops, 'TDH (ft)': tdh_ops,"Efficiency (%)": eff_ops, "Pump Curve": pmp_crvs, "System Curve": sys_crvs})


##speeds input, Pumps input, pump_data_table, system_curve_data
def generate_figure(Pumps, speeds, pump_data, system_curve_data, upr_por, lwr_por):
    comb_POR_data = pd.DataFrame(data = {"Flow (gpm)":[], "TDH (ft)":[],"EFFICIENCY":[], "Pump":[], "identifier":[],}) ##make empty dataframe for PORs

    ## make mater dataset. This should probably be made a function.
    for i, o_pump in enumerate(Pumps):
        print("i  = ", i, "opump = ", o_pump)
        if i == 0:
            masterpumps = pump_data[pump_data['Pump'] == o_pump].copy()
            masterpumps["identifier"] = 'Pump Curve ' + str(i+1) + " @ " + str(speeds[i]*100) + '%'
            masterpumps["Flow (gpm)"] = masterpumps["Flow (gpm)"] * speeds[i]
            masterpumps["TDH (ft)"] = masterpumps["TDH (ft)"] * speeds[i]**2
            comb_POR_data = getopranges(comb_POR_data, masterpumps, i, upr_por, lwr_por)
        else:
            idataset = pump_data[pump_data['Pump'] == o_pump].copy()
            idataset["Flow (gpm)"] = idataset["Flow (gpm)"] * speeds[i]
            idataset["TDH (ft)"] = idataset["TDH (ft)"] * speeds[i]**2
            ident = 'Pump Curve ' + str(i) + " @ " + str(speeds[i-1]*100) + '%'
            lastdataset = masterpumps[masterpumps['identifier'] == ident]
            idataset["identifier"] = 'Pump Curve ' + str(i+1) + " @ " + str(speeds[i]*100) + '%'
            #print("currentdata = \n", idataset, '\n\n')
            #print("prevdata = \n", lastdataset, '\n\n')
            comb_idataset = int_paralell_flows(lastdataset,idataset)
            #print("comb_idataset = \n", comb_idataset, '\n\n')
            comb_POR_data = getopranges(comb_POR_data, comb_idataset, i+1, upr_por, lwr_por)
            masterpumps = masterpumps.append(comb_idataset, ignore_index=True)
    
    #####UNCOMMENT
    oprtng_pts = calc_intrsctns(masterpumps, system_curve_data)
    #print("Operating Points = ", oprtng_pts)
    masterpumps = masterpumps.rename(columns = {"EFFICIENCY": "Efficiency (%)"})
    #print('masterpumps = ', masterpumps)
    
    ## add labels to the comb_POR_data dataset
    comb_POR_data = find_PO_Labels(comb_POR_data,'identifier')
    
    ## Create plotly figure with pump curves from masterpumps.
    fig = px.line(masterpumps, x='Flow (gpm)', y = "TDH (ft)", line_group  = 'identifier', title="Pump Performance Graph", color = 'Pump', color_discrete_sequence=px.colors.qualitative.Plotly, template='seaborn', hover_data={'Flow (gpm)':':.0f', # remove species from hover data
                            'TDH (ft)':':.1f', # customize hover for column of y attribute
                            'Efficiency (%)':':.1f',
                             'identifier':True,
                             'Pump': True# add other column, default formatting
                            })
               
            
    ## add POR points to plot with data from comb_POR_data
    for label in list(set(list(comb_POR_data['label']))):
        i_POR_data =  comb_POR_data[comb_POR_data['label'] == label]
        if label == "Best Efficiency Point":
            color = 'chartreuse'
        else:
            color = 'gold'
        fig.add_scatter(x= i_POR_data['Flow (gpm)'],y=i_POR_data["TDH (ft)"], mode="markers", marker=dict(size=9, color=color, line=dict(width=2, color='DarkSlateGrey')),name=label, 
                        hovertemplate = 'Flow (gpm): %{x:.0f}'+
                        '<br>TDH (ft): %{y:.2f} ')
    
    ## add system curves to plot based on system curve sceanrios.
    scanerios = list(set(system_curve_data['identifier'])) 
    colors = ['steelblue', 'olive', 'darkturquoise', 'yellow', 'red', 'orange', 'black', 'gray'] ## colors for system curve scenarios. This could potentially be a user input.
    for i, scen in enumerate(scanerios):
        #scen_data = system_curve_data[system_curve_data['identifier'] == scen]
        duplicates = list(set(list(system_curve_data[system_curve_data['identifier'] == scen]['Number'])))
        for dup in duplicates:
            ##print('dup = ', dup)
            scen_dup_data = system_curve_data[(system_curve_data['identifier'] == scen) & (system_curve_data['Number'] == dup)]
            fig.add_trace(go.Scatter(x=scen_dup_data['Flow (gpm)'],y=scen_dup_data["TDH (ft)"],mode="lines", name = scen, hovertemplate = 'Flow (gpm): %{x:.0f}'+ 
                                     '<br>TDH (ft): %{y:.2f} ', line=go.scatter.Line(color=colors[i])))
    #fig.update_layout(legend = dict(orientation='h'))
    
    fig.add_scatter(x= oprtng_pts['Flow (gpm)'],y=oprtng_pts["TDH (ft)"], mode="markers", marker=dict(size=7, color='red', line=dict(width=2, color='DarkSlateGrey')),name="Operating Point", 
                    hovertemplate = 'Flow (gpm): %{x:.0f}'+
                    '<br>TDH (ft): %{y:.2f} ')
    
    fig.update_xaxes(range=[0, int(math.ceil(max(masterpumps['Flow (gpm)'] / 25.0))) * 25])
    fig.update_yaxes(range=[0, int(math.ceil(max(masterpumps['TDH (ft)'] / 25.0))) * 25])
    
    
    #print("#test".split("#")[1])
        
    ##added
    
    logical = [x < 1 for x in speeds]
    #print(logical)
    #print("true in logical:",True in logical)
    if True in logical:
        ## make mater dataset. This should probably be made a function.
        for i, o_pump in enumerate(Pumps):
            #print("i  = ", i, "opump = ", o_pump)
            if i == 0:
                masterpumps_100 = pump_data[pump_data['Pump'] == o_pump].copy()
                masterpumps_100["identifier"] = 'Pump Curve ' + str(i+1) + " @ 100%"
                comb_POR_data_100 = getopranges(comb_POR_data, masterpumps_100, i, upr_por, lwr_por)
            else:
                idataset_100 = pump_data[pump_data['Pump'] == o_pump].copy()
                ident_100 = 'Pump Curve ' + str(i) + " @ 100%"
                lastdataset_100 = masterpumps_100[masterpumps_100['identifier'] == ident_100]
                idataset_100["identifier"] = 'Pump Curve ' + str(i+1) + " @ 100%"
                #print("currentdata 100 = \n", idataset, '\n\n')
                #print("prevdata 100 = \n", lastdataset, '\n\n')
                comb_idataset_100 = int_paralell_flows(lastdataset_100,idataset_100)
                #print("comb_idataset  100 = \n", comb_idataset, '\n\n')
                comb_POR_data_100 = getopranges(comb_POR_data_100, comb_idataset_100, i+1, upr_por, lwr_por)
                masterpumps_100 = masterpumps_100.append(comb_idataset_100, ignore_index=True)
        
        
        colors = px.colors.qualitative.Plotly
        
        
        ## add labels to the comb_POR_data dataset
        comb_POR_data_100 = find_PO_Labels(comb_POR_data_100,'identifier')
        
        
        #####uncomment!!!!
        oprtng_pts_100 = calc_intrsctns(masterpumps_100, system_curve_data)
        #print("Operating Points 100% = ", oprtng_pts_100)
        masterpumps_100 = masterpumps_100.rename(columns = {"EFFICIENCY": "Efficiency (%)"})
        #print('masterpumps 100% = ', masterpumps_100)  
        
        ##added
        clrs= {}
        i=-1
        for pmp in masterpumps['Pump']:
            if pmp not in clrs.keys():
                i=i+1
                clrs[pmp] = colors[i]
        #print("colors dict = ", clrs)
        
        
        clrs_tmpt = {}
        for idnt in sorted(list(set(list(masterpumps_100['identifier'])))):
            i_pmp_data = masterpumps_100[masterpumps_100['identifier'] == idnt]
            pmp =list(set(i_pmp_data["Pump"]))[0]
            clrs_tmpt[idnt] = clrs[pmp]
        #print("colors template = ", clrs_tmpt)
        
        ##added
        
        for pmp_id in sorted(list(set(list(masterpumps_100['identifier'])))):
            #print(pmp_id)
            i_pmp_data_100 = masterpumps_100[masterpumps_100['identifier'] == pmp_id]
            ##pick up here
            #print("i_pmp_data_100 = ", i_pmp_data_100)
            #print("clrs_tmpt[pmp_id] = ", clrs_tmpt[pmp_id])
            #print(list(set(i_pmp_data_100['identifier']))[0])
            fig.add_trace(go.Scatter(x=i_pmp_data_100['Flow (gpm)'],y=i_pmp_data_100["TDH (ft)"],mode="lines", name = list(set(i_pmp_data_100['identifier']))[0], opacity=0.5, hovertemplate = 'Flow (gpm): %{x:.0f}'+ 
                                     '<br>TDH (ft): %{y:.2f} ', line=go.scatter.Line(color=clrs_tmpt[pmp_id])))
            
        ## add POR points to plot with data from comb_POR_data
        for label in list(set(list(comb_POR_data_100['label']))):
            i_POR_data100 =  comb_POR_data_100[comb_POR_data_100['label'] == label]
            if label == "Best Efficiency Point":
                color = 'chartreuse'
            else:
                color = 'gold'
            #print("in POR 100")
            fig.add_scatter(x= i_POR_data100['Flow (gpm)'],y=i_POR_data100["TDH (ft)"], mode="markers", opacity=0.5, marker=dict(size=7, color=color, line=dict(width=2, color='DarkSlateGrey')),name=label, 
                            hovertemplate = 'Flow (gpm): %{x:.0f}'+
                            '<br>TDH (ft): %{y:.2f} ')
            
        fig.add_scatter(x= oprtng_pts_100['Flow (gpm)'],y=oprtng_pts_100["TDH (ft)"], mode="markers", opacity=0.5, marker=dict(size=5, color='red', line=dict(width=1, color='DarkSlateGrey')),name="Operating Point", 
                        hovertemplate = 'Flow (gpm): %{x:.0f}'+
                        '<br>TDH (ft): %{y:.2f} ')
        
        fig.update_xaxes(range=[0, int(math.ceil(max(masterpumps_100['Flow (gpm)'] / 25.0))) * 25])
        fig.update_yaxes(range=[0, int(math.ceil(max(masterpumps_100['TDH (ft)'] / 25.0))) * 25])
        
        
        oprtng_pts = oprtng_pts.append(oprtng_pts_100)
    
    return fig, oprtng_pts

######################################################################################################################################################################
################################END Graph Update Functions############################################################################################################


######################################################################################################################################################################
################################Inputs and Outputs for callbacks######################################################################################################

##make output list for first callback for pump curves upload.
pump_outputs = [Output('pump-data-output', 'children'),
                Output('pump_flow_col', 'options'),
                Output('pump_tdh_col', 'options'),
                Output('pump_eff_col', 'options'),
                Output('pump_label_col', 'options'),
                Output('pump_flow_col', 'value'),
                Output('pump_tdh_col', 'value'),
                Output('pump_eff_col', 'value'),
                Output('pump_label_col', 'value')]

##make output list for second callback for system curves upload.
system_outputs = [Output('system-data-output', 'children'),
                  Output('sys_flow_col', 'options'),
                  Output('sys_tdh_col', 'options'),
                  Output('sys_label_col', 'options'),
                  Output('sys_crv_n_col', 'options'),
                  Output('sys_flow_col', 'value'),
                  Output('sys_tdh_col', 'value'),
                  Output('sys_label_col', 'value'),
                  Output('sys_crv_n_col', 'value')]

##make output list for third callback for updating pump selection dropdowns.
pump_type_output = [Output('sys-dropdown', 'options'),
                    Output('pump_list_0', 'options'),
                    Output('pump_list_1', 'options'),
                    Output('pump_list_2', 'options'),
                    Output('pump_list_3', 'options'),
                    Output('pump_list_4', 'options'),
                    Output('pump_list_5', 'options'),
                    Output('pump_list_6', 'options'),
                    Output('pump_list_7', 'options'),
                    Output('pump_list_8', 'options'),
                    Output('pump_list_9', 'options')]

slider_outputs = [Output('spd_slider_0', 'value'),
                  Output('spd_slider_1', 'value'),
                  Output('spd_slider_2', 'value'),
                  Output('spd_slider_3', 'value'),
                  Output('spd_slider_4', 'value'),
                  Output('spd_slider_5', 'value'),
                  Output('spd_slider_6', 'value'),
                  Output('spd_slider_7', 'value'),
                  Output('spd_slider_8', 'value'),
                  Output('spd_slider_9', 'value')]

pump_graph_inputs = [Input('pump_flow_col', 'value'),
                     Input('pump_tdh_col', 'value'),
                     Input('pump_eff_col', 'value'),
                     Input('pump_label_col', 'value'),
                     Input('sys-dropdown', 'value'),
                     Input('sys_flow_col', 'value'),
                     Input('sys_tdh_col', 'value'),
                     Input('sys_label_col', 'value'),
                     Input('sys_crv_n_col', 'value'),
                     Input('pump_list_0', 'value'),
                     Input('pump_list_1', 'value'),
                     Input('pump_list_2', 'value'),
                     Input('pump_list_3', 'value'),
                     Input('pump_list_4', 'value'),
                     Input('pump_list_5', 'value'),
                     Input('pump_list_6', 'value'),
                     Input('pump_list_7', 'value'),
                     Input('pump_list_8', 'value'),
                     Input('pump_list_9', 'value'),
                     Input('spd_slider_0', 'value'),
                     Input('spd_slider_1', 'value'),
                     Input('spd_slider_2', 'value'),
                     Input('spd_slider_3', 'value'),
                     Input('spd_slider_4', 'value'),
                     Input('spd_slider_5', 'value'),
                     Input('spd_slider_6', 'value'),
                     Input('spd_slider_7', 'value'),
                     Input('spd_slider_8', 'value'),
                     Input('spd_slider_9', 'value'),
                     Input("upr_por", "value"),
                     Input("lwr_por", "value")]
pump_graph_states = [State('pump_curves_dtbl', 'columns'),
                     State('pump_curves_dtbl', 'data'),
                     State('system_curves_dtbl', 'columns'),
                     State('system_curves_dtbl', 'data')]


######################################################################################################################################################################
################################END Inputs and Outputs for callbacks##################################################################################################

function_inps = " pump_q_c, pump_tdh_c, pump_eff_c, pump_lab_c,  sys_q_c, sys_tdh_c, sys_lab_c, sys_crv_n,  pmp_nm_0, pmp_nm_1, pmp_nm_2, pmp_nm_3, pmp_nm_4, pmp_nm_5, pmp_nm_6, pmp_nm_7, pmp_nm_8, pmp_nm_9,  pmp_sld_0, pmp_sld_1, pmp_sld_2, pmp_sld_3, pmp_sld_4, pmp_sld_5, pmp_sld_6, pmp_sld_7, pmp_sld_8, pmp_sld_9, pmp_crv_cols, pmp_crv_rows, sys_crv_cols, sys_crv_rows"


######################################################################################################################################################################
################################ Callbacks ###########################################################################################################################

@app.callback(pump_outputs,
              [Input('pump_upload_data', 'contents')],
              [State('pump_upload_data', 'filename'),
              State('pump_upload_data', 'last_modified')])
def update_pump_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        #print("list_of_contents = ", list_of_contents)
        #print("list_of_names = ", list_of_names)
        #print("list_of_dates = ", list_of_dates)
        children = [
            parse_contents(c, n, d, "pump_curves_dtbl") for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        combined_df = pd.DataFrame()
        for x,v in zip(list_of_contents, list_of_names):
            combined_df = combined_df.append(return_df(x,v))
        #print("combined_df = ", combined_df)
        columns = list(combined_df.columns)
        q_pred, tdh_pred, eff_pred, pump_id_pred = find_col_pump_name(columns)
        #print(columns)
        options=[{'label':opt, 'value':opt} for opt in columns]
        #print(options)
        #print("children = ", children)
        return children, options, options, options, options, q_pred, tdh_pred, eff_pred, pump_id_pred
    
@app.callback(system_outputs,
              Input('system_upload_data', 'contents'),
              [State('system_upload_data', 'filename'),
              State('system_upload_data', 'last_modified')])
def update_system_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d, "system_curves_dtbl") for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        combined_df = pd.DataFrame()
        for x,v in zip(list_of_contents, list_of_names):
            combined_df= combined_df.append(return_df(x,v))
        #print("combined_df = ", combined_df)
        columns = list(combined_df.columns)
        q_pred, tdh_pred, sys_id_pred, sys_curve_n_pred = find_col_sys_name(columns)
        options=[{'label':opt, 'value':opt} for opt in columns]
        #print("columns = ", columns)
        return children, options, options, options, options, q_pred, tdh_pred, sys_id_pred, sys_curve_n_pred
    

@app.callback(pump_type_output,
              [Input('update-ids','n_clicks'),
              State('pump_label_col','value'),
              State('pump_tdh_col','value'),
              State('pump_curves_dtbl','data'),
              State('pump_curves_dtbl','columns'),
              State('sys_label_col','value'),
              State('system_curves_dtbl','data'),
              State('system_curves_dtbl','columns')])
def make_pump_options_drop(n_clicks, pmp_column_nm, tdhclm_nm, pmp_rows, pmp_cols, sys_col_nm, sys_rows, sys_cols):
    #print("column_nm = ", column_nm)
    #print('rows = ', rows)
    #print('columns = ', cols)
    pump_data=pd.DataFrame(pmp_rows,columns=[c['name'] for c in pmp_cols])
    system_data = pd.DataFrame(sys_rows,columns=[c['name'] for c in sys_cols])
    #print("pump data = ",pump_data)
    order_by_lbl = pump_data[[pmp_column_nm,tdhclm_nm]].groupby(by=[pmp_column_nm]).max().sort_values(by=[tdhclm_nm], ascending=True).reset_index()
    #print("pump_data = ", pump_data)
    pump_options = generate_dropdown_options(order_by_lbl[pmp_column_nm])
    system_options = generate_dropdown_options(list(set(system_data[sys_col_nm])))
    #print(pump_options)
    return system_options, pump_options, pump_options, pump_options, pump_options, pump_options, pump_options, pump_options, pump_options, pump_options, pump_options

## add final call back to update the figure when a button is clicked. Add functaionlity to grpah to show operating points by finding the intersection between lines.
## automatically select columns in 1st and second callback.

@app.callback(slider_outputs,
              Input('change_all_sld','value'))
def update_all_speeds(all_spds):
    return all_spds, all_spds, all_spds, all_spds, all_spds, all_spds, all_spds, all_spds, all_spds, all_spds

##update this
@app.callback([Output(component_id='my-performance-graph', component_property='figure'),
               Output('operating-data-output','children')],
              pump_graph_inputs,
              pump_graph_states)
def update_perf_graph(pump_q_c, pump_tdh_c, pump_eff_c, pump_lab_c, sys_crvs_drpdwn, sys_q_c, sys_tdh_c, sys_lab_c, sys_crv_n, pmp_nm_0, pmp_nm_1, pmp_nm_2, pmp_nm_3, pmp_nm_4, pmp_nm_5, pmp_nm_6, pmp_nm_7, pmp_nm_8, pmp_nm_9,  pmp_sld_0, pmp_sld_1, pmp_sld_2, pmp_sld_3, pmp_sld_4, pmp_sld_5, pmp_sld_6, pmp_sld_7, pmp_sld_8, pmp_sld_9, up_por, lw_por, pmp_crv_cols, pmp_crv_rows, sys_crv_cols, sys_crv_rows):
    #pump_q_c, pump_tdh_c, pump_eff_c, pump_lab_c,  sys_q_c, sys_tdh_c, sys_lab_c,  pmp_nm_0, pmp_nm_1, pmp_nm_2, pmp_nm_3, pmp_nm_4, pmp_nm_5, pmp_nm_6, pmp_nm_7, pmp_nm_8, pmp_nm_9,  pmp_sld_0, pmp_sld_1, pmp_sld_2, pmp_sld_3, pmp_sld_4, pmp_sld_5, pmp_sld_6, pmp_sld_7, pmp_sld_8, pmp_sld_9, pmp_crv_cols, pmp_crv_rows, sys_crv_cols, sys_crv_rows
    count = 0
    inlcuded_pumps = []
    included_curves = [] ## input for graph function.
    included_speeds = [] ##input for graph function
    if (pmp_nm_0 != 'none') and (pmp_nm_0 is not None):
        count = count +1
        inlcuded_pumps.append("pmp_nm_0")
        included_curves.append(pmp_nm_0)
        included_speeds.append(pmp_sld_0/100)
    if (pmp_nm_1 != 'none') and (pmp_nm_1 is not None):
        count = count +1 
        inlcuded_pumps.append("pmp_nm_1")
        included_curves.append(pmp_nm_1)
        included_speeds.append(pmp_sld_1/100)
    if (pmp_nm_2 != 'none') and (pmp_nm_2 is not None):
        count = count +1
        inlcuded_pumps.append("pmp_nm_2")
        included_curves.append(pmp_nm_2)
        included_speeds.append(pmp_sld_2/100)
    if (pmp_nm_3 != 'none') and (pmp_nm_3 is not None):
        count = count +1   
        inlcuded_pumps.append("pmp_nm_3")
        included_curves.append(pmp_nm_3)
        included_speeds.append(pmp_sld_3/100)
    if (pmp_nm_4 != 'none') and (pmp_nm_4 is not None):
        count = count +1
        inlcuded_pumps.append("pmp_nm_4")
        included_curves.append(pmp_nm_4)
        included_speeds.append(pmp_sld_4/100)
    if (pmp_nm_5 != 'none') and (pmp_nm_5 is not None):
        count = count +1 
        inlcuded_pumps.append("pmp_nm_5")
        included_curves.append(pmp_nm_5)
        included_speeds.append(pmp_sld_5/100)
    if (pmp_nm_6 != 'none') and (pmp_nm_6 is not None):
        count = count +1
        inlcuded_pumps.append("pmp_nm_6")
        included_curves.append(pmp_nm_6)
        included_speeds.append(pmp_sld_6/100)
    if (pmp_nm_7 != 'none') and (pmp_nm_7 is not None):
        count = count +1  
        inlcuded_pumps.append("pmp_nm_7")
        included_curves.append(pmp_nm_7)
        included_speeds.append(pmp_sld_7/100)
    if (pmp_nm_8 != 'none') and (pmp_nm_8 is not None):
        count = count +1  
        inlcuded_pumps.append("pmp_nm_8")
        included_curves.append(pmp_nm_8)
        included_speeds.append(pmp_sld_8/100)
    if (pmp_nm_9 != 'none') and (pmp_nm_9 is not None):
        count = count +1  
        inlcuded_pumps.append("pmp_nm_9")
        included_curves.append(pmp_nm_9)
        included_speeds.append(pmp_sld_9/100)
    pump_data=pd.DataFrame(pmp_crv_rows,columns=[c['name'] for c in pmp_crv_cols])
    pump_data = pump_data[[pump_q_c, pump_tdh_c, pump_eff_c, pump_lab_c]]
    pump_data = pump_data.rename(columns = {pump_q_c: "Flow (gpm)" ,pump_tdh_c: "TDH (ft)" ,pump_eff_c: "EFFICIENCY",pump_lab_c: 'Pump'})
    #print('pump_data = ',pump_data)
    system_curve_data=pd.DataFrame(sys_crv_rows,columns=[c['name'] for c in sys_crv_cols])
    if (sys_crv_n is None) or (sys_crv_n == "none") or (sys_crv_n == "Flow (gpm)"):
        system_curve_data["Number"]=1
        sys_crv_n = "Number"
    system_curve_data=system_curve_data[[sys_q_c, sys_tdh_c, sys_lab_c, sys_crv_n]]
    system_curve_data = system_curve_data[system_curve_data[sys_lab_c].isin(sys_crvs_drpdwn)]
    system_curve_data = system_curve_data.rename(columns = {sys_q_c: "Flow (gpm)" ,sys_tdh_c: "TDH (ft)" ,sys_lab_c: 'identifier',sys_crv_n: 'Number'})
    #print('system_curve_data = ',system_curve_data)
    #print("included_pump = ", inlcuded_pumps)
    #print("included_curves = ", included_curves)
    #print("included_speeds = ", included_speeds)
    #print("count = ", count)
    #print("pump_q_c = ", pump_q_c)
    #print("pump_tdh_c = ", pump_tdh_c)
    #print("pump_eff_c = ", pump_eff_c)
    #print("pump_lab_c = ", pump_lab_c)
    #print("sys_q_c = ", sys_q_c)
    #print("sys_tdh_c = ", sys_tdh_c)
    #print("sys_lab_c = ", sys_lab_c)
    #print("sys_crv_n = ", sys_crv_n)
    #print("pmp_nm_0 = ", pmp_nm_0)
    #print("pmp_nm_1 = ", pmp_nm_1)   
    #print("pmp_nm_2 = ", pmp_nm_2)
    #print("pmp_nm_3 = ", pmp_nm_3)
    #print("pmp_nm_4 = ", pmp_nm_4)
    #print("pmp_nm_5 = ", pmp_nm_5)
    #print("pmp_nm_6 = ", pmp_nm_6)
    #print("pmp_nm_7 = ", pmp_nm_7)
    #print("pmp_nm_8 = ", pmp_nm_8)
    #print("pmp_nm_9 = ", pmp_nm_9)
    #print("pmp_sld_0 = ", pmp_sld_0)
    #print("pmp_sld_1 = ", pmp_sld_1)
    #print("pmp_sld_2 = ", pmp_sld_2)
    #print("pmp_sld_3 = ", pmp_sld_3)
    #print("pmp_sld_4 = ", pmp_sld_4)
    #print("pmp_sld_5 = ", pmp_sld_5)
    #print("pmp_sld_6 = ", pmp_sld_6)
    #print("pmp_sld_7 = ", pmp_sld_7)
    #print("pmp_sld_8 = ", pmp_sld_8)
    #print("pmp_sld_9 = ", pmp_sld_9)
    #print("pmp_crv_cols = ", pmp_crv_cols)
    #print("pmp_crv_rows = ", pmp_crv_rows)
    #print("sys_crv_cols = ", sys_crv_cols)
    #print("sys_crv_rows = ", sys_crv_rows)
    fig, operating_pnts_data = generate_figure(included_curves, included_speeds, pump_data, system_curve_data, up_por, lw_por)
    children = [html.Div([
        dash_table.DataTable(id = "operatingpoints",
            data=operating_pnts_data.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in operating_pnts_data.columns],
            editable=True)])]
    #fig.write_html("C:/Users/Public/Downloads/Pump_Graph.html")
    #operating_pnts_data.to_csv("C:/Users/Public/Downloads/Operating_Points.csv", index=False)
    return fig, children

@app.callback(Output("download-op-pnts", "data"),
              [Input('export-oprtng-pnts','n_clicks'),
              State('operatingpoints','data'),
              State('operatingpoints','columns')],
              prevent_initial_call=True)
def export_ops(n_clicks, rows, cols):
    #print("column_nm = ", column_nm)
    #print('rows = ', rows)
    #print('columns = ', cols)
    ops_data=pd.DataFrame(rows,columns=[c['name'] for c in cols])
    return dcc.send_data_frame(ops_data.to_csv, "ops_data.csv")

@app.callback(Output("download-graph", "data"),
              [Input('export-graph','n_clicks'),
              State(component_id='my-performance-graph', component_property='figure')],
              prevent_initial_call=True)
def export_fig(n_clicks, fig):

    #print("pump data = ",pump_data)
    #print(fig)
    fig=go.Figure(fig)
    wrkdir = os.getcwd()
    file = wrkdir + "/Pump_Graph.html"
    print(file)
    fig.write_html(file)
    return dcc.send_file(file)

if __name__ == '__main__':
    app.run_server(host='0.0.0.0',debug=False, port=8050)
    
 ######################################################################################################################################################################
 ################################ END Callbacks #######################################################################################################################   
    
## imporevements
## add options to specify preffered operating range.
## fix the number column or just remove it all together.
## adjust flow (gpm) on the bottom legend.
## output another column for system curve scenario number if it is not present.



    
    
    
