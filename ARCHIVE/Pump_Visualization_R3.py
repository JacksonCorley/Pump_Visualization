# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 18:06:09 2020

@author: JC056455
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
pio.renderers.default='svg'
from plotly.offline import download_plotlyjs, init_notebook_mode,  plot
from plotly.graph_objs import *
init_notebook_mode()
import plotly.graph_objects as go
import shapely
from shapely.geometry import LineString, Point

Total_Pumps = 6 ## input for total number of pumps.
Order = list(range(1,Total_Pumps+1))
Pumps = [1,1,1,1,2,2] ## input for pump orders.
speeds = [1,1,1,1,0.85,0.85] ## input for pump speeds.
Upper_POR_rat = 1.2 ## user input for POR range
Lower_POR_rat = 0.7 ## user input for POR range
pump_data = pd.read_csv("C:/Users/jc056455/OneDrive - Jacobs/Personal/Programming/Pump_Visualization/Pump_Curves.csv") ## import pump curves
system_curve_data = pd.read_csv("C:/Users/jc056455/OneDrive - Jacobs/Personal/Programming/Pump_Visualization/System_Curves.csv") ## import system curves

##Pump_Order = pd.DataFrame({"Pump": Pumps,"Order": Order}) ## NOT USED!!!
##Combined_Pumps = [{"Flow (gpm)":[], "TDH (ft)":[],"Efficiency (%)":[], "Pump":[], "identifier":[],}] ## NOT USED!!! 
##cPump = Pump_Order["Pump"][0] ## NOT USED!!! 
##cum_pump_curve = pump_data.loc[pump_data.Pump == cPump] ## NOT USED!!! 
##iPump = Pump_Order["Pump"][1] ## NOT USED!!! 
##i_pump_curve = pump_data.loc[pump_data.Pump == iPump] ## NOT USED!!! 



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
        
def cal_op_points(system_curve_data, pump_curve_data):
    #get list of 
    return 0

def getopranges(comb_PORs,prevdata,i):
    ## makes a dataset of preferred Operating Ranges.
    prevdata.sort_values(by = "Flow (gpm)", ascending = True, inplace = True)
    operating_Ranges = pd.DataFrame(data = {"Flow (gpm)":[], "TDH (ft)":[],"EFFICIENCY":[], "Pump":[], "identifier":[],})
    BEP_Flow = prevdata.loc[prevdata.EFFICIENCY == max(prevdata.EFFICIENCY),"Flow (gpm)"].values
    BEP_TDH = prevdata.loc[prevdata.EFFICIENCY == max(prevdata.EFFICIENCY),"TDH (ft)"].values
    Upper_Flow = BEP_Flow[0] * Upper_POR_rat ##could make this a user input in the future.
    Upper_TDH = interpolate(list(prevdata["Flow (gpm)"]), list(prevdata["TDH (ft)"]),Upper_Flow)
    Upper_Efficiency = interpolate(list(prevdata["Flow (gpm)"]), list(prevdata["EFFICIENCY"]),Upper_Flow)
    Lower_Flow = BEP_Flow[0] * Lower_POR_rat ##could make this a user input in the future.
    Lower_TDH = interpolate(list(prevdata["Flow (gpm)"]), list(prevdata["TDH (ft)"]),Lower_Flow)
    Lower_Efficiency = interpolate(list(prevdata["Flow (gpm)"]), list(prevdata["EFFICIENCY"]),Lower_Flow)
    BEP_OP_PNT = pd.DataFrame(data = {"Flow (gpm)":BEP_Flow[0], "TDH (ft)":BEP_TDH[0],"EFFICIENCY":[max(prevdata['EFFICIENCY'])], "Pump":[0], "identifier":['Pump Curve ' + str(i)+ ' BEP']})
    Lower_OP_PNT = pd.DataFrame(data = {"Flow (gpm)":[Lower_Flow], "TDH (ft)":[Lower_TDH],"EFFICIENCY":[Lower_Efficiency], "Pump":[0], "identifier":['Pump Curve ' + str(i)+ ' Lower POR']})
    Upper_OP_PNT = pd.DataFrame(data = {"Flow (gpm)":[Upper_Flow], "TDH (ft)":[Upper_TDH],"EFFICIENCY":[Upper_Efficiency], "Pump":[0], "identifier":['Pump Curve ' + str(i)+ ' Upper POR']})
    operating_Ranges = BEP_OP_PNT
    operating_Ranges = operating_Ranges.append([Lower_OP_PNT,Upper_OP_PNT], ignore_index=True)
    comb_PORs = comb_PORs.append(operating_Ranges, ignore_index = True)
    print('comb_PORs = ', comb_PORs)
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
                            flow_ops.append(pmp_line.intersection(sys_line).x)
                            tdh_ops.append(pmp_line.intersection(sys_line).y)
                            pmp_crvs.append(pump)
                            sys_crvs.append(sys_crv)
                            break
                        
    return pd.DataFrame({'Flow (gpm)':flow_ops, 'TDH (ft)': tdh_ops, "Pump Curve": pmp_crvs, "System Curve": sys_crvs})


##speeds input, Pumps input, pump_data_table, system_curve_data
def generate_figure(Pumps, speeds, pump_data, system_curve_data):
    comb_POR_data = pd.DataFrame(data = {"Flow (gpm)":[], "TDH (ft)":[],"EFFICIENCY":[], "Pump":[], "identifier":[],}) ##make empty dataframe for PORs

    ## make mater dataset. This should probably be made a function.
    for i, o_pump in enumerate(Pumps):
        print("i  = ", i, "opump = ", o_pump)
        if i == 0:
            masterpumps = pump_data[pump_data['Pump'] == o_pump].copy()
            masterpumps["identifier"] = 'Pump Curve ' + str(i+1) + " @ " + str(speeds[i]*100) + '%'
            masterpumps["Flow (gpm)"] = masterpumps["Flow (gpm)"] * speeds[i]
            masterpumps["TDH (ft)"] = masterpumps["TDH (ft)"] * speeds[i]**2
            comb_POR_data = getopranges(comb_POR_data, masterpumps, i)
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
            comb_POR_data = getopranges(comb_POR_data, comb_idataset, i+1)
            masterpumps = masterpumps.append(comb_idataset, ignore_index=True)
    masterpumps = masterpumps.rename(columns = {"EFFICIENCY": "Efficiency (%)"})
    print('masterpumps = ', masterpumps) 
    oprtng_pts = calc_intrsctns(masterpumps, system_curve_data)
    print("Operating Points = ", oprtng_pts)
    ## add labels to the comb_POR_data dataset
    comb_POR_data = find_PO_Labels(comb_POR_data,'identifier')
    
    ## Create plotly figure with pump curves from masterpumps.
    fig = px.line(masterpumps, x='Flow (gpm)', y = "TDH (ft)", line_group  = 'identifier', color = 'Pump', color_discrete_sequence=px.colors.qualitative.Plotly, template='seaborn', hover_data={'Flow (gpm)':':.0f', # remove species from hover data
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
    fig.update_layout(legend = dict(orientation='h'))
    
    fig.add_scatter(x= oprtng_pts['Flow (gpm)'],y=oprtng_pts["TDH (ft)"], mode="markers", marker=dict(size=7, color='red', line=dict(width=2, color='DarkSlateGrey')),name="Operating Point", 
                    hovertemplate = 'Flow (gpm): %{x:.0f}'+
                    '<br>TDH (ft): %{y:.2f} ')
    
    return fig

fig = generate_figure(Pumps,speeds,pump_data,system_curve_data)
plot(fig)




