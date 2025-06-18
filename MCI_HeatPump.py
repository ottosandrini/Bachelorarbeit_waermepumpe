from typing import Annotated
from tespy.networks import Network
from tespy import components as com
from tespy.connections import Connection, Ref
from tespy.tools import logger
from CoolProp.CoolProp import PropsSI
import logging
from fluprodia import FluidPropertyDiagram
import matplotlib.pyplot as plt, mpld3
import numpy as np
import json as jsonlib
from uuid import uuid4
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

"""
'Digitaler Zwilling' Versuchswärmepumpe MCI SBT

Übersicht MCI_HeatPump.py:

parametrisierung der WP

WP Klasse mit folgenden Methoden:
- solve             // löst das modell und gibt ergebnisse in der konsole aus
- solve_json        // löst das modell und generiert json
- reset             // setzt WP auf design parameter zurück
- show_design       // nutzt matplotlib um design parameter zu visualisieren
- show_cycle        // nutzt matplotlib um berechnete parameter zu visualisieren
- show_temps        // nutzt matplotlib um Temperaturen zu visualisieren
- show all          // alle plots in einem
- create_json       // erstellt json aus allen WP Parametern
- EVR               // ExpansionsVentilRegelung auf 7°K (für offdesign)

"""


# Enable logging
();logger.define_logging(
logpath="myloggings", log_the_path=True, log_the_version=True,
screen_level=logging.INFO, file_level=logging.DEBUG
);()

# PARAMETER LIST
working_fluid = "R410a"
compressor_power = 1050                                 # Leistungsaufnahme Verdichter [W]
isentropen_koeffizient = 0.95
design_heat_output = 4056
condensation_temp = 273.15 - 1.25                       # K  Niederdruckseitig!
low_pressure = PropsSI('P', 'T', condensation_temp, 'Q', 0, working_fluid) / 100000  # bar
condenser_pressure_ratio = 0.95
compressor_pressure_ratio = 3.9
high_pressure_side_temp = 273.15 + 76.4                # K
superheat = 2.3                                         # K
high_pressure = 30.1                                    # bar
# --- HEATING SYSTEM PARAMETERS ---
wq_massflow = 0.375                                     # kg/s
wq_inflow_temp = 273.15 + 3.7 + 1                       # K     +1°K wegen IDM "HEATPIPE" und schlechter isolierung
ww_massflow = 0.273                                     # kg/s
ww_inflow_temp = 273.15 + 44.2                          # K
condenser_wq_pressure_ratio = 0.98
superheater_wq_pressure_ratio = 0.85


# Wärmepumpe objekt das Sachen simulieren kann
class Heatpump():
    def __init__(self, **kwargs):
        # --- HEATPUMP PARAMETERS ---
        self.working_fluid = working_fluid
        self.compressor_power = compressor_power
        self.isentropen_koeffizient = isentropen_koeffizient
        self.design_heat_output = design_heat_output
        self.condensation_temp = condensation_temp
        self.low_pressure = low_pressure
        self.condenser_pressure_ratio = condenser_pressure_ratio
        self.compressor_pressure_ratio = compressor_pressure_ratio
        self.high_pressure_side_temp = high_pressure_side_temp
        self.superheat = superheat
        self.superheat_control_value = superheat

        self.high_pressure = high_pressure # nur für design chart!
        # --- HEATING SYSTEM PARAMETERS ---
        self.wq_massflow = wq_massflow                       # Massenstrom Wärmequelle        (kg/s)
        self.wq_inflow_temp = wq_inflow_temp             # Wärmequelle Rücklauftemperatur (K)
        self.ww_massflow = ww_massflow                       # Massenstrom Warmwasser         (kg/s)
        self.ww_inflow_temp = ww_inflow_temp            # Warmwasser Rücklauftemperatur  (K)

        self.condenser_wq_pressure_ratio = condenser_wq_pressure_ratio
        self.superheater_wq_pressure_ratio = superheater_wq_pressure_ratio
        # --- Network ---
        self.heatpump = Network()
        self.heatpump.set_attr(T_unit='K', p_unit='bar', h_unit='kJ / kg', iterinfo=True)
        # Components
        # --- Heatpump ---
        self.cc = com.CycleCloser('cycle_closer')
        self.evaporator = com.HeatExchanger('evaporator')
        self.condenser = com.HeatExchanger('condenser')
        self.expansionvalve = com.Valve('expansionValve')
        self.compressor = com.Compressor('compressor')
        self.superheater = com.HeatExchanger('superheater')
        # --- Water system ---
        self.ww_merge = com.Merge('ww_merge')
        self.wq_merge = com.Merge('wq_merge')
        self.ww_split = com.Splitter('ww_split')
        self.wq_split = com.Splitter('wq_split')
        self.ww_valve = com.Valve('ww_valve')
        self.wq_valve = com.Valve('wq_valve')
        self.ww_pump = com.Pump('ww_pump')
        self.wq_pump = com.Pump('wq_pump')
        # --- Sources ---
        self.tank_in_ww = com.Sink('tank_in_ww')
        self.tank_out_ww = com.Source('tank_out_ww')
        self.tank_in_wq = com.Sink('tank_in_wq')
        self.tank_out_wq = com.Source('tank_out_wq')
        # Connections
        # --- Heatpump ---
        self.conn0 = Connection(self.cc, 'out1', self.compressor, 'in1')
        self.conn1 = Connection(self.compressor, 'out1', self.condenser, 'in1')
        self.conn2 = Connection(self.condenser, 'out1', self.expansionvalve, 'in1')
        self.conn3 = Connection(self.expansionvalve, 'out1', self.evaporator, 'in2')
        self.conn4 = Connection(self.evaporator, 'out2', self.superheater, 'in2')
        self.conn5 = Connection(self.superheater, 'out2', self.cc, 'in1')
        # --- Water system ---
        self.ww1 = Connection(self.tank_out_ww, 'out1', self.condenser, 'in2')
        self.ww2 = Connection(self.condenser, 'out2', self.tank_in_ww, 'in1')
        self.wq1 = Connection(self.tank_out_wq, 'out1', self.superheater, 'in1')
        self.wq2 = Connection(self.superheater, 'out1', self.evaporator, 'in1')
        self.wq3 = Connection(self.evaporator, 'out1', self.tank_in_wq, 'in1')
        self.conn_list = [self.conn0, self.conn1, self.conn2, self.conn3, self.conn4, self.conn5]
        # --- PARAMETRISATION ---
        #self.conn1.set_attr(p=self.high_pressure)
        self.conn1.set_attr(T=self.high_pressure_side_temp)
        self.conn1.set_attr(design=['p'], offdesign=['p'])       # offdesign??
        self.conn3.set_attr(p=self.low_pressure+0.2)
        self.conn3.set_attr(design=['p'])                        # offdesign no value, pressure determined by expansionvalve zeta
        self.conn4.set_attr(T=self.condensation_temp, x=1, fluid={self.working_fluid: 1})
        self.conn4.set_attr(design=['T', 'x', 'fluid'], offdesign=['T', 'x', 'fluid'])   # offdesign??
        #self.conn5.set_attr(p=self.low_pressure, h=self.starting_enthalpy)
        self.conn5.set_attr(p=self.low_pressure, T=self.condensation_temp+self.superheat) 
        self.ww1.set_attr(T=self.ww_inflow_temp, p=2, m=self.ww_massflow, fluid={'ethanol': 1})      # Warmwasser Vorlauf
        self.wq1.set_attr(T=self.wq_inflow_temp, p=2, m=self.wq_massflow, fluid={'ethanol': 1})      # Wärmequelle Vorlauf
        #self.wq3.set_attr(T=self.condensation_temp+10, p=2, m=0.6, fluid={'ethanol': 1})      # Superheater seperater zulauf
        #self.wq2.set_attr()
        #self.compressor.set_attr(P=self.compressor_power, eta_s=self.isentropen_koeffizient)
        self.compressor.set_attr(P=self.compressor_power, pr=self.compressor_pressure_ratio)
        self.compressor.set_attr(design=['P', 'eta_s'], offdesign=['P', 'eta_s'])
        self.condenser.set_attr(Q=-self.design_heat_output, pr1=self.condenser_pressure_ratio, pr2=self.condenser_wq_pressure_ratio)
        self.condenser.set_attr(design=['Q', 'pr1', 'pr2'], offdesign=['zeta1', 'zeta2', 'kA'])
        #expansionvalve.set_attr(pr=4)
        self.evaporator.set_attr(pr1=self.superheater_wq_pressure_ratio)
        self.evaporator.set_attr(design=['pr1'], offdesign=['zeta1'])
        self.superheater.set_attr(pr1=self.superheater_wq_pressure_ratio)
        self.superheater.set_attr(design=['pr1'], offdesign=['zeta1'])
        self.expansionvalve.set_attr(offdesign=['zeta'])
        # add connections to network
        self.heatpump.add_conns(self.conn0, self.conn1, self.conn2, self.conn3, self.conn4, self.conn5, self.ww1, self.ww2, self.wq1, self.wq2, self.wq3)

    def solve(self, design):
        if design:
            self.heatpump.solve(mode='design')
            self.heatpump.save('designstate/design_state.json')
            self.heatpump.print_results()
        else:
            self.heatpump.solve(mode="offdesign", design_path='designstate/design_state.json')
            self.heatpump.print_results()
        pres = 0
        for c in self.conn_list:
            if c.p.val > pres:
                pres = c.p.val
        print(f"high pressure side p = {round(pres,3)}")

    
    def solvejson(self, design: bool):
        if design:
            self.heatpump.solve(mode='design')
            self.heatpump.save('designstate/design_state.json')
            self.show_cycle()
            # get json of simulation results
            json_res = self.create_json()
            return json_res
        else:
            self.heatpump.solve(mode="offdesign", design_path='designstate/design_state.json')
            self.show_cycle()
            # get json of simulation results
            sim_res = 5
            results = {"test":sim_res}
            return results
    
    def reset(self):
        # --- HEATPUMP PARAMETERS ---
        self.working_fluid = working_fluid
        self.compressor_power = compressor_power
        self.isentropen_koeffizient = isentropen_koeffizient
        self.design_heat_output = design_heat_output
        self.condensation_temp = condensation_temp
        self.low_pressure = low_pressure
        self.condenser_pressure_ratio = condenser_pressure_ratio
        self.compressor_pressure_ratio = compressor_pressure_ratio
        self.high_pressure_side_temp = high_pressure_side_temp
        self.superheat = superheat

        self.high_pressure = high_pressure # nur für design chart!
        # --- HEATING SYSTEM PARAMETERS ---
        self.wq_massflow = wq_massflow                       # Massenstrom Wärmequelle        (kg/s)
        self.wq_inflow_temp = wq_inflow_temp             # Wärmequelle Rücklauftemperatur (K)
        self.ww_massflow = ww_massflow                       # Massenstrom Warmwasser         (kg/s)
        self.ww_inflow_temp = ww_inflow_temp            # Warmwasser Rücklauftemperatur  (K)

        self.condenser_wq_pressure_ratio = condenser_wq_pressure_ratio
        self.superheater_wq_pressure_ratio = superheater_wq_pressure_ratio

    def show_design(self): # fluid property diagram pre calc
        pressures = [self.low_pressure, 28, self.high_pressure, self.low_pressure, self.low_pressure]  # in bar
        enthalpies = [430, 470, 260, 260, 430] # in kJ/kg
        diagram = FluidPropertyDiagram(fluid=self.working_fluid)
        diagram.set_unit_system(T='°C', h='kJ/kg', p='bar')
        Q = np.linspace(0, 1, 11)
        T = np.arange(-25, 150, 5)
        p = np.geomspace(0.01, 1000, 6)
        v = np.geomspace(0.001, 10, 5)
        s = np.linspace(1000, 10000, 10)
        h = np.linspace(0, 1000, 19)
        #diagram.set_isolines( T=T, p=p, v=v, s=s, h=h)
        diagram.set_isolines(Q=Q, T=T, p=p, h=h)
        diagram.calc_isolines()
        fig, ax = plt.subplots(1, figsize=(8, 5))
        diagram.draw_isolines(diagram_type='logph', fig=fig, ax=ax, x_min=0, x_max=750, y_min=1, y_max=800)
        plt.plot(enthalpies, pressures, 'b-', label='Heat Pump Cycle')
        #fig.savefig('logph_diagram.svg')
        #fig.savefig('logph_diagram.png', dpi=300)
        #plt.show() 

    def show_cycle(self):
        r_enthalpies = []
        r_pressures = []
        for Conn in self.conn_list:
            r_enthalpies.append(Conn.h.val)  # get enthalpy at connection and add it to list for fluprodia diagram
            r_pressures.append(Conn.p.val)   # get pressure -- // --

        diagram2 = FluidPropertyDiagram(fluid='R410a')
        diagram2.set_unit_system(T='°C', h='kJ/kg', p='bar')
        Q = np.linspace(0, 1, 11)
        T = np.arange(-25, 150, 5)
        p = np.geomspace(0.01, 1000, 6)
        v = np.geomspace(0.001, 10, 5)
        s = np.linspace(1000, 10000, 10)
        h = np.linspace(0, 1000, 19)
        #diagram.set_isolines( T=T, p=p, v=v, s=s, h=h)
        diagram2.set_isolines(Q=Q, T=T, p=p, h=h)
        diagram2.calc_isolines()
        fig, ax = plt.subplots(1, figsize=(8, 5))
        
        diagram2.draw_isolines(diagram_type='logph', fig=fig, ax=ax, x_min=0, x_max=750, y_min=1, y_max=800)
        # WENN DIREKT GEPLOTTET WERDEN SOLL
        #plt.plot(r_enthalpies, r_pressures, 'b-', label='Heat Pump Cycle')
        #fig.savefig('logph_diagram_H2O.svg')
        #fig.savefig('logph_diagram_calculated.png', dpi=300)
        # WENN NUR FÜR GUI GEPLOTTET WERDEN SOLL
        mpld3.save_html(fig, "frontend/plots/thermocycle.html", figid="thermocycle")
        #mpld3.save_json(fig, "thermocycle.json")
        
    def show_temps(self):
        # Funktion nicht notwendig für GUI
        r_enthalpies = []
        r_pressures = []
        r_temperatures = []
        for Conn in self.conn_list:
            r_enthalpies.append(Conn.h.val)  # get enthalpy at connection and add it to list for fluprodia diagram
            r_pressures.append(Conn.p.val)   # get pressure -- // --
            r_temperatures.append(Conn.T.val)# get temperature -- // --
        
        fig, ax = plt.subplots()
        plt.plot(r_pressures, r_temperatures, 'r-', label='Temperatures')
        #ax.plot(r_enthalpies, r_temperatures, 'r-', label='Temperatures')
        count = 0
        for xy in zip(r_pressures, r_temperatures):                                       # <--
            ax.annotate(f'conn{count}', xy=xy, textcoords='data')
            count += 1

        ax.grid()
        plt.show()

    def show_all(self):
        fig, axs = plt.subplots(1, 3, figsize=(18, 5))

        # --- Plot 1: Design Diagram ---
        pressures = [self.low_pressure, self.high_pressure, self.high_pressure, self.low_pressure, self.low_pressure]
        enthalpies = [430, 470, 260, 260, 430]

        diagram = FluidPropertyDiagram(fluid=self.working_fluid)
        diagram.set_unit_system(T='°C', h='kJ/kg', p='bar')
        Q = np.linspace(0, 1, 11)
        T = np.arange(-25, 150, 5)
        p = np.geomspace(0.01, 1000, 6)
        h = np.linspace(0, 1000, 19)
        diagram.set_isolines(Q=Q, T=T, p=p, h=h)
        diagram.calc_isolines()
        diagram.draw_isolines(diagram_type='logph', fig=fig, ax=axs[0], x_min=0, x_max=750, y_min=1, y_max=800)
        axs[0].plot(enthalpies, pressures, 'b-', label='Design Cycle')
        axs[0].set_title('Design Log(p)-h Diagram')

        # --- Plot 2: Real Cycle Diagram ---
        r_enthalpies = [c.h.val for c in self.conn_list]
        r_pressures = [c.p.val for c in self.conn_list]

        diagram2 = FluidPropertyDiagram(fluid='R410a')
        diagram2.set_unit_system(T='°C', h='kJ/kg', p='bar')
        diagram2.set_isolines(Q=Q, T=T, p=p, h=h)
        diagram2.calc_isolines()
        diagram2.draw_isolines(diagram_type='logph', fig=fig, ax=axs[1], x_min=0, x_max=750, y_min=1, y_max=800)
        axs[1].plot(r_enthalpies, r_pressures, 'g-', label='Real Cycle')
        axs[1].set_title('Calculated log p-h Diagram')

        '''
        # --- Plot 3: Temperatures vs Pressure ---
        r_temperatures = [c.T.val for c in self.conn_list]
        axs[2].plot(r_pressures, r_temperatures, 'r-', label='Temperature Profile')

        for i, (p_val, t_val) in enumerate(zip(r_pressures, r_temperatures)):
            axs[2].annotate(f'conn{i}', xy=(p_val, t_val), textcoords='data')

        axs[2].set_title('Temperature vs Pressure')
        axs[2].set_xlabel('Pressure (bar)')
        axs[2].set_ylabel('Temperature (°K)')
        axs[2].grid()
        '''
        # --- Plot 3: Temperature by Connection Index ---
        r_temperatures = [c.T.val for c in self.conn_list]
        conn_indices = list(range(len(r_temperatures)))  # [0, 1, 2, 3, 4, 5]

        axs[2].plot(conn_indices, r_temperatures, 'ro-', label='Temperature Profile')  # red line with circle markers
        axs[2].set_title('Temperature Across Connections')
        axs[2].set_xlabel('Connection Index')
        axs[2].set_ylabel('Temperature (°C)')

        for i, temp in enumerate(r_temperatures):
            axs[2].annotate(f'{temp:.1f}°C', xy=(i, temp), textcoords='offset points', xytext=(0, 8), ha='center')

        axs[2].set_xticks(conn_indices)
        axs[2].grid()

        # General cleanup
        for ax in axs:
            ax.legend()
            ax.grid(True)

        plt.tight_layout()
        plt.show()

    # superheat needs to be calculated by coolprop for offdesign calculations
    def create_json(self):
        data = {
            "Temperatures": {
                "conn0": round(self.conn0.T.val-273.15, 1),
                "conn1": round(self.conn1.T.val-273.15, 1),
                "conn2": round(self.conn2.T.val-273.15, 1),
                "conn3": round(self.conn3.T.val-273.15, 1),
                "conn4": round(self.conn4.T.val-273.15, 1),
                "conn5": round(self.conn5.T.val-273.15, 1),
                "wq_in":  round(self.wq1.T.val-273.15, 1),
                "wq_out": round(self.wq3.T.val-273.15, 1),
                "ww_in":  round(self.ww1.T.val-273.15, 1),
                "ww_out": round(self.ww2.T.val-273.15, 1)
            },
            "Pressures": {
                "conn0": round(self.conn0.p.val, 1),
                "conn1": round(self.conn1.p.val, 1),
                "conn2": round(self.conn2.p.val, 1),
                "conn3": round(self.conn3.p.val, 1),
                "conn4": round(self.conn4.p.val, 1),
                "conn5": round(self.conn5.p.val, 1)
            },
            "Powers": {
                "evaporator": round(-self.evaporator.Q.val, 1),
                "condenser": round(-self.condenser.Q.val, 1),
                "superheater": round(-self.superheater.Q.val, 1),
                "compressor": round(self.compressor.P.val, 1)
            },
            "MassFlows": {
                "conn0": round(self.conn0.m.val*60, 1),
                "conn1": round(self.conn1.m.val*60, 1),
                "conn2": round(self.conn2.m.val*60, 1),
                "conn3": round(self.conn3.m.val*60, 1),
                "conn4": round(self.conn4.m.val*60, 1),
                "conn5": round(self.conn5.m.val*60, 1),
                "wq": round(self.wq1.m.val*60, 1),
                "ww": round(self.ww1.m.val*60, 1)
            },
            "overheat": round(self.superheat, 1)
        }
        # store json as file
        #with open("calculated_data.json", 'w') as f:
        #    jsonlib.dump(data, f, indent=4)

        # print("Simulation data saved to 'calculated_data.json'!")
        return data



# FastAPI backend for webpage
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

origins = [
    "http://localhost:5500",    # VS Code Live Server
    "http://127.0.0.1:5500",   # Alternative localhost
    "http://localhost:8000",    # For testing
    "http://127.0.0.1:8000",    # Alternative testing
    "http://localhost:8001",    # For testing
    "http://127.0.0.1:8001",    # Alternative testing
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Your live-server address
    allow_credentials=True,
    #allow_methods=["*"],
    #allow_headers=["*"],
)
maximum_amount_of_sessions = 20
app.state.session_ids = {}
app.state.heatpumps = {}

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/checkID/{my_session_id}")
def check_if_valid(my_session_id: str):
    if id_check(app.state.session_ids, my_session_id):
        return {"message":"OK"}
    else:
        return {"message":"NOT_OK"}

@app.get("/session_start")
def session_start():
    if len(app.state.session_ids) >= maximum_amount_of_sessions:
        return {"error":"0"}
    
    new_id = str(uuid4())
    app.state.session_ids[new_id] = new_id
    app.state.heatpumps[new_id] = Heatpump()
    return {"my_session_id":new_id}

@app.get("/session_end/{my_session_id}")
def session_end(my_session_id: str):
    if id_check(app.state.session_ids, my_session_id):
        app.state.session_ids.pop(my_session_id)
        app.state.heatpumps.pop(my_session_id)
        return {"message":"Session ended"}
    else:
        return {"message":"Session ID old or incorrect"}

# run a design simulation to "wipe the slate clean"
@app.get("/design_simulation/{my_session_id}")
def run_simulation(my_session_id: str):
    if id_check(app.state.session_ids, my_session_id):
        app.state.heatpumps[my_session_id].reset()
        results = app.state.heatpumps[my_session_id].solvejson(True)
        return results
    else:
        return  {"error":"Session ID Error"}

# DELETE THIS METHOD BEFORE PRODUCTION!
@app.get("/clear_sessions")
def clear_sessions():
    app.state.session_ids = {}
    app.state.heatpumps = {}
# DELETE THIS METHOD BEFORE PRODUCTION!


# receive data as input for new simulation
@app.post("/offdesign_simulation/{my_session_id}")
def run_offdesign(jsonstring, my_session_id:str):
    if id_check():
        json = jsonlib.loads(jsonstring)
        for el in json:
            if el == -1:
                pass #run offdesign simulation
    else:
        return {"error": "Invalid session ID"}, 422

    # change parameters of pump to get it ready for an offdesign calc
    # pass 
     
def id_check(list, id):
    if id in list:
        return True
    return False

"""
# not needed when run as web server backend
# only needed when script should only be run once with python           
pump = Heatpump()
pump.solve(1)
pump.save_json()
#pump.show_design()
pump.show_cycle()
#pump.show_temps()
#pump.show_all()
"""