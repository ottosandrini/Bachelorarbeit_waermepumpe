from typing import Optional
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
from pydantic import BaseModel

"""
'Digitaler Zwilling' Versuchswärmepumpe MCI SBT Labor

Übersicht MCI_HeatPump.py:

parametrisierung der WP

WP Klasse mit folgenden Methoden:


"""


# Enable logging
();logger.define_logging(
logpath="myloggings", log_the_path=True, log_the_version=True,
screen_level=logging.INFO, file_level=logging.DEBUG
);()

# PARAMETER LIST
working_fluid = "R410A"  # Kaeltemittel
high_pressure = 2480000  # pa
low_pressure = 1040000   # pa
high_temp = 273.15 + 56.3
t_cond = PropsSI("T", "Q", 1, "P", high_pressure, working_fluid)    # verdampfungstemperatur Hochdurck
t_evap = PropsSI("T", "Q", 1, "P", low_pressure, working_fluid)    # verdampfungstemperatur Niederdurck
print("t_cond: " + str(t_cond))
print("t_evap: " + str(t_evap))
compressor_power = 880          # Leistungsaufnahme Verdichter [W]
isentropen_koeffizient = 0.7    # isentropische effizienz Verdichter                                
design_heat_output = 5070       # design Leistung der Wärmequelle
design_heat_input = 4158        # Leistung des Verdampfers (inkl superheater)
condenser_pressure_ratio = 0.98
evaporator_pressure_ratio = 0.98
superheater_pressure_ratio = 0.99
superheat = 4.8                                         # K
compressor_entry_enthalpy = PropsSI("H", "P", low_pressure, "T", t_evap + superheat, working_fluid)
compressor_output_enthalpy = PropsSI("H", "P", high_pressure, "T", high_temp, working_fluid)
print("compressor_entry_enthalpy: " + str(compressor_entry_enthalpy))
print("compressor_output_enthalpy: " + str(compressor_output_enthalpy))
# falls notwendig:
superheater_entry_enthalpy = PropsSI("H", "P", low_pressure / superheater_pressure_ratio, "T", t_evap, working_fluid)


# # --- HEATING SYSTEM PARAMETERS ---
wq_massflow_data = 23                                   # kg/min
ww_massflow_data = 16.1                                 # kg/min        
wq_massflow = wq_massflow_data / 60                     # kg/s
ww_massflow = ww_massflow_data / 60                     # kg/s
ww_inflow_temp = 273.15 + 35.5    
water_pressure = 200000 # pa
condenser_wq_pressure_ratio = 0.99
superheater_wq_pressure_ratio = 0.99
# Heatpipe compensation
t_eingang = 273.15 + 14.2                # K
t_ausgang = 273.15 + 11.7                # K
h1 = PropsSI("H", "P", water_pressure, "T", t_eingang, "water")
h2 = PropsSI("H", "P", water_pressure * superheater_wq_pressure_ratio, "T", t_ausgang, "water")
dh = h2 - h1            # Enthalpieverlust der Wärmequelle 
Q = wq_massflow * dh    # von der Wärmequelle übertragene Wärme

Q_ges = -design_heat_input    # gesamte Leistung der Wärmeaufnahme
dh_ges = Q_ges / wq_massflow    # Enthalpieverlust der Wärmequelle wenn gesamte Leistung von Wärmequelle kommen würde
h1_virt = h2 - dh_ges
t_compensated = PropsSI("T", "P", water_pressure, "H", h1_virt, "water" ) # theoretische Einganstemperatur der Wärmequelle
wq_inflow_temp = t_compensated

# Wärmepumpe objekt das Sachen simulieren kann
class Heatpump():
    def __init__(self, **kwargs):
        # --- HEATPUMP PARAMETERS ---
        self.working_fluid = working_fluid
        self.compressor_power = compressor_power
        self.isentropen_koeffizient = isentropen_koeffizient
        self.design_heat_output = design_heat_output
        self.condensation_temp = t_cond
        self.evaporation_temp = t_evap
        self.low_pressure = low_pressure / 100000
        self.condenser_pressure_ratio = condenser_pressure_ratio
        self.superheat = superheat
        self.superheat_control_value = superheat
        self.compressor_out_enth = compressor_output_enthalpy / 1000

        self.high_pressure = high_pressure / 100000 # nur für design chart!
        # --- HEATING SYSTEM PARAMETERS ---
        self.wq_massflow = wq_massflow                       # Massenstrom Wärmequelle        (kg/s)
        self.wq_inflow_temp = t_compensated             # Wärmequelle Rücklauftemperatur (K)
        self.ww_massflow = ww_massflow                       # Massenstrom Warmwasser         (kg/s)
        self.ww_inflow_temp = ww_inflow_temp            # Warmwasser Rücklauftemperatur  (K)

        self.condenser_w_pressure_ratio = condenser_wq_pressure_ratio
        self.superheater_w_pressure_ratio = superheater_wq_pressure_ratio
        self.superheater_pressure_ratio = superheater_pressure_ratio
        self.evaporator_pressure_ratio = evaporator_pressure_ratio
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
        # set parameters
        self.parametise()
        # add connections to network
        self.heatpump.add_conns(self.conn0, self.conn1, self.conn2, self.conn3, self.conn4, self.conn5, self.ww1, self.ww2, self.wq1, self.wq2, self.wq3)


    def parametise(self):
        # --- PARAMETRISATION ---
        # COMPONENTS
        self.compressor.set_attr(eta_s=self.isentropen_koeffizient, P=self.compressor_power)
        self.compressor.set_attr(design=['P', 'eta_s'], offdesign=['P', 'eta_s'])

        self.condenser.set_attr(Q=-self.design_heat_output, pr1=self.condenser_pressure_ratio, pr2=self.condenser_w_pressure_ratio)
        self.condenser.set_attr(design=['Q', 'pr1', 'pr2'], offdesign=['kA', 'zeta1', 'zeta2'])
        
        self.superheater.set_attr(pr1=self.superheater_w_pressure_ratio, pr2=self.superheater_pressure_ratio)
        self.superheater.set_attr(design=['pr1', 'pr2'], offdesign=['kA', 'zeta1', 'zeta2'])
        self.evaporator.set_attr(pr1=self.superheater_w_pressure_ratio, pr2=self.evaporator_pressure_ratio)
        self.evaporator.set_attr(design=['pr1', 'pr2'], offdesign=['kA', 'zeta1', 'zeta2'])
        # CONNECTIONS

        self.conn1.set_attr(p=self.high_pressure)
        self.conn1.set_attr(design=['p'])

        self.conn3.set_attr(p=self.low_pressure)
        self.conn3.set_attr(design=['p'])

        self.conn4.set_attr(x=1, fluid={working_fluid: 1})

        self.conn5.set_attr(T=self.evaporation_temp + self.superheat)
        self.conn5.set_attr(design=['T'], offdesign=['T'])

        self.ww1.set_attr(T=self.ww_inflow_temp, p=2, m=self.ww_massflow, fluid={'ethanol': 1})      # Warmwasser Vorlauf
        self.ww1.set_attr(design=['T', 'p', 'm'], offdesign=['T', 'p', 'm'])
        self.wq1.set_attr(T=self.wq_inflow_temp, p=2, m=self.wq_massflow, fluid={'ethanol': 1})
        self.wq1.set_attr(design=['T', 'p', 'm'], offdesign=['T', 'p', 'm'])
        #self.wq2.set_attr(printout=False)
        #self.wq3.set_attr(printout=False)
        #self.ww2.set_attr(printout=False)

    def parametise_offdesign(self):
        self.conn1.set_attr(p=None)
        self.conn3.set_attr(p=None)
        self.conn1.set_attr(p0=self.high_pressure)
        self.compressor.set_attr(P=900, eta_s=0.77)
        self.conn5.set_attr(T=294)

    def solve(self, design):
        if design:
            self.reset()
            self.heatpump.solve(mode='design')
            self.heatpump.save('design_state.json')
            self.heatpump.print_results()
        else:
            self.heatpump.solve(mode="offdesign", design_path='design_state.json')
            self.heatpump.print_results()
        pres = 0
        for c in self.conn_list:
            if c.p.val > pres:
                pres = c.p.val
        print(f"high pressure side p = {round(pres,3)}")

    
    def solvejson(self, design: bool):
        if design:
            self.heatpump.solve(mode='design')
            self.heatpump.save('design_state.json')
            self.calc_superheat()
            # self.show_cycle() only do this when plot button is pressed
            # get json of simulation results
            json_res = self.create_json()
            return json_res
        else:
            # self.solve_offdesign()
            # EVR control loop
            self.heatpump.solve(mode="offdesign", design_path='design_state.json', max_iter=100)
            #self.heatpump.print_results()
            # check pump status:

            json_res = self.create_json()
            return json_res
            # self.show_cycle()
            # get json of simulation results
            # CODE BELOW ONLY FOR TESTING PURPOSES:
            test_res = 5
            results = {"test":test_res}
            return results
        
    def reset(self):
        # Change params that are changed in offdesign mode
        # --- PARAMETRISATION ---
        #self.conn1.set_attr(p=self.high_pressure)
        self.compressor.set_attr(eta_s=self.isentropen_koeffizient, P=self.compressor_power)
        self.conn1.set_attr(p=self.high_pressure)
        #self.conn1.set_attr(h=self.compressor_out_enth)
        self.condenser.set_attr(Q=-self.design_heat_output, pr1=self.condenser_pressure_ratio, pr2=self.condenser_w_pressure_ratio)
        
        self.conn5.set_attr(T=self.evaporation_temp + self.superheat)
        self.conn3.set_attr(p=self.low_pressure)
        self.conn4.set_attr(x=1, fluid={working_fluid: 1})

        self.superheater.set_attr(pr1=self.superheater_w_pressure_ratio, pr2=self.superheater_pressure_ratio)
        self.evaporator.set_attr(pr1=self.superheater_w_pressure_ratio, pr2=self.evaporator_pressure_ratio)


        self.ww1.set_attr(T=self.ww_inflow_temp, p=2, m=self.ww_massflow, fluid={'ethanol': 1})      # Warmwasser Vorlauf
        self.wq1.set_attr(T=self.wq_inflow_temp, p=2, m=self.wq_massflow, fluid={'ethanol': 1})

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
                "compressor": round(self.compressor.P.val, 1),
                "comp_eff": round(self.isentropen_koeffizient, 2)
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
    
    def calc_superheat(self):
        pressure = self.conn5.p.val * 1e5
        temp_inlet = self.conn5.T.val  # Temperature at compressor inlet [K]
        fluid = self.working_fluid
        T_sat = PropsSI('T', 'P', pressure, 'Q', 1, fluid)  # Q=1 for saturated vapor
        self.superheat = temp_inlet - T_sat
    
    def check_superheat(self, boundary):
        self.calc_superheat()
        if self.superheat < self.superheat_control_value + boundary and self.superheat > self.superheat_control_value - boundary:
            return True
        else:
            return False

# FastAPI backend for webpage
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

class SimulationInput(BaseModel):
    para_in_1: Optional[float] = None
    para_in_2: Optional[float] = None
    para_in_3: Optional[float] = None
    para_in_4: Optional[float] = None
    para_in_5: Optional[float] = None
    para_in_6: Optional[float] = None
    para_in_7: Optional[float] = None


logger = logging.getLogger("uvicorn.error")
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
    
@app.get("/build_plot/{my_session_id}")
def build_plot(my_session_id: str):
    if id_check(app.state.session_ids, my_session_id):
        app.state.heatpumps[my_session_id].show_cycle()
        return {"message": "successfully built plot"}
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
def run_offdesign(data: SimulationInput, my_session_id: str):
    if id_check(app.state.session_ids, my_session_id):
        #return data.model_dump_json()
        data_dict = data.model_dump()
        update_params(app.state.heatpumps[my_session_id], data_dict)
        result = app.state.heatpumps[my_session_id].solvejson(False)
        return result
    else:
        return {"error": "Invalid session ID"}, 423

    # change parameters of pump to get it ready for an offdesign calc
    # pass 
     
def id_check(list, id):
    if id in list:
        return True
    return False

def update_params(pump: Heatpump, data: dict):
    for param_name, value in data.items():
        if value == -22:
            continue
        
        param_num = int(param_name.split("_")[-1])

        match param_num:
            case 1:
                pump.wq1.set_attr(T=value)
                logger.info(f"Attribute 1 (wq_in: T) was set to {value}")
            case 2:
                pump.ww1.set_attr(T=value)
                logger.info(f"Attribute 2 (ww1_in: T) was set to {value}")
            case 3:
                pump.compressor.set_attr(P=value)
                logger.info(f"Attribute 3 (compressor: P) was set to {value}")
            case 4:
                pump.wq1.set_attr(m=value)
                logger.info(f"Attribute 4 (wq1_in: m) was set to {value}")
            case 5:
                pump.ww1.set_attr(m=value)
                logger.info(f"Attribute 5 (ww1_in: m) was set to {value}")
            case 6:
                pump.compressor.set_attr(eta_s=value)
                logger.info(f"Attribute 6 (compressor: eta_s) was set to {value}")
            case 7:
                pump.superheat_control_value = value
                logger.info(f"Attribute 7 (superheat_control_value) was set to {value}")
            case _:
                print(f"Warning: unknown parameter {param_num}")
        





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