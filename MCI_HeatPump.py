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

# Heatpipe compensation

# Wärmepumpe objekt das Sachen simulieren kann
class Heatpump():
    def __init__(self, **kwargs):
        # --- HEATPUMP PARAMETERS ---
        self.working_fluid = "R410A"
        self.isentropen_koeffizient = 0.7
        self.superheat = 5

        # --- HEATING SYSTEM PARAMETERS ---
        self.wq_massflow = 23 / 60
        self.wq_inflow_temp = 273.15 + 14.2
        self.ww_massflow = 16.1 / 60
        self.ww_inflow_temp = 273.15 + 35.5
        self.water_pressure = 200000

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
        # add connections to network
        self.heatpump.add_conns(self.conn0, self.conn1, self.conn2, self.conn3, self.conn4, self.conn5, self.ww1, self.ww2, self.wq1, self.wq2, self.wq3)


    def parametise(self):
        #print("\nParametising Heatpump... ")

        #print("ww_input: " + str(self.ww_inflow_temp))

        self.ww1.set_attr(T=self.ww_inflow_temp, p=2, m=self.ww_massflow, fluid={'ethanol': 1})
        self.wq1.set_attr(T=self.wq_inflow_temp, p=2, m=self.wq_massflow, fluid={'ethanol': 1})

        compressor_power = 21.88877055400408 * (self.ww_inflow_temp-273.15) + 101.71412575912325
        #print("Compressor Power: " + str(compressor_power) + " W")
        self.compressor.set_attr(eta_s=self.isentropen_koeffizient, P=compressor_power)

        pressure1 = 0.6029903492677208 * (self.ww_inflow_temp - 273.15) + 4.036221627874944
        #print("high pressure: " + str(pressure1) + " bar")
        self.conn1.set_attr(p=pressure1)

        #t_cond_guess = PropsSI('T', 'P', pressure1*100000, 'Q', 0, working_fluid)
        #self.conn2.set_attr(T0=t_cond_guess)

        self.condenser.set_attr(pr1=1, pr2=1) # , kA=7.39e+02
        self.superheater.set_attr(pr1=1, pr2=1) # , kA=1.36e+03
        self.evaporator.set_attr(pr1=1, pr2=1) # , kA=5.9e+01

        dt = 3 # in die 3 °K kann das heatpipe ding integriert werden (temp dt zwischen heiss und kalt im evap)
        t_evap = self.wq_inflow_temp - (dt+self.superheat)
        low_pres = PropsSI("P", "T", t_evap, "Q", 1, self.working_fluid) / 100000  # convert to bar
        #print("low_pres: " + str(low_pres) + ' bar ')
        #print("T5: " + str(self.wq_inflow_temp-dt))
        #h_test = PropsSI("H", 'T', self.wq_inflow_temp-dt, 'P', low_pres, self.working_fluid)
        #print('H5: ' + str(h_test))
        self.conn4.set_attr(x=1, fluid={self.working_fluid: 1})
        self.conn5.set_attr(T=self.wq_inflow_temp-dt)
        self.conn3.set_attr(p=low_pres)
        carnot = self.ww_inflow_temp / (self.ww_inflow_temp - self.wq_inflow_temp)
        cop = carnot * 0.368 # hardcoded efficiency
        #cop = (-9.5888331628315e-05) * (compressor_power * (self.ww_inflow_temp - self.wq_inflow_temp+ 1.5)) + 7.7508400878806025
        Q_cond = cop * compressor_power
        self.condenser.set_attr(Q=-Q_cond)
        #print("Parametisation done!\n")


    def solve(self):
        self.parametise()
        self.heatpump.solve("design")

    
    def solvejson(self):
        self.parametise()
        self.heatpump.solve(mode='design')
        self.heatpump.save('design_state.json')
        self.calc_superheat()
        self.heatpump.print_results()
        # self.show_cycle() only do this when plot button is pressed
        # get json of simulation results
        json_res = self.create_json()
        return json_res

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

        choice = 2 # always plot using mpld3
        if choice == 1: # WENN DIREKT GEPLOTTET WERDEN SOLL
            plt.plot(r_enthalpies, r_pressures, 'b-', label='Heat Pump Cycle')
            plt.show()
            #fig.savefig('logph_diagram_H2O.svg')
            #fig.savefig('logph_diagram_calculated.png', dpi=300)
        elif choice == 2: # WENN NUR FÜR GUI GEPLOTTET WERDEN SOLL
            ax.plot(r_enthalpies, r_pressures, 'b-', label='Heat Pump Cycle')
            ax.legend()
            mpld3.save_html(fig, "frontend/plots/thermocycle.html", figid="thermocycle")
        
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
        fig, axs = plt.subplots(1, 2, figsize=(18, 5))

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
@app.post("/simulation/{my_session_id}")
def run_offdesign(data: SimulationInput, my_session_id: str):
    if id_check(app.state.session_ids, my_session_id):
        #return data.model_dump_json()
        data_dict = data.model_dump()
        update_params(app.state.heatpumps[my_session_id], data_dict)
        result = app.state.heatpumps[my_session_id].solvejson()
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
                pump.wq_inflow_temp = value + 273.15
                logger.info(f"Attribute 1 (wq_in: T) was set to {value}")
            case 2:
                pump.ww_inflow_temp = value + 273.15
                logger.info(f"Attribute 2 (ww1_in: T) was set to {value}")
            case 3:
                pump.wq_massflow = value / 60
                logger.info(f"Attribute 3 (wq1_in: m) was set to {value}")
            case 4:
                pump.ww_massflow = value / 60
                logger.info(f"Attribute 4 (ww1_in: m) was set to {value}")
            case 5:
                pump.isentropen_koeffizient = value
                logger.info(f"Attribute 5 (compressor: eta_s) was set to {value}")
            case 6:
                pump.superheat = value
                logger.info(f"Attribute 6 (superheat_control_value) was set to {value}")
            case _:
                print(f"Warning: unknown parameter {param_num}")
    