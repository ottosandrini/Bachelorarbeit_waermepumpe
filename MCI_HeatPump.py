from tespy.networks import Network
from tespy import components as com
from tespy.connections import Connection, Ref
from tespy.tools import logger
from CoolProp.CoolProp import PropsSI
import logging
from fluprodia import FluidPropertyDiagram
import matplotlib.pyplot as plt
import numpy as np
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

# Enable logging
();logger.define_logging(
logpath="myloggings", log_the_path=True, log_the_version=True,
screen_level=logging.INFO, file_level=logging.DEBUG
);()

"""
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Free Heatpump advice")
        button = QPushButton("Press Me!")

        # Set the central widget of the Window.
        self.setCentralWidget(button)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
"""

# Wärmepumpe objekt das Sachen simulieren kann
class Heatpump():
    def __init__(self, **kwargs):
        self.working_fluid = "R410a"
        if 'fluid' in kwargs:
            print('fluio in kwargs')
            self.working_fluid = kwargs.get('fluid') # needs better automatic pressure calculation for fluids other than R410a
        self.compressor_power = 1140
        self.ww_pump_power = 50
        self.wq_pump_power = 50
        self.condensation_temp = 273
        self.high_pressure = 28
        self.low_pressure = PropsSI('P', 'T',  self.condensation_temp, 'Q', 0, self.working_fluid) / 100000
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
        self.ww1 = Connection(self.tank_out_wq, 'out1', self.condenser, 'in2')
        self.ww2 = Connection(self.condenser, 'out2', self.tank_in_wq, 'in1')
        self.wq1 = Connection(self.tank_out_ww, 'out1', self.superheater, 'in1')
        self.wq2 = Connection(self.superheater, 'out1', self.evaporator, 'in1')
        self.wq3 = Connection(self.evaporator, 'out1', self.tank_in_ww, 'in1')
        self.conn_list = [self.conn0, self.conn1, self.conn2, self.conn3, self.conn4, self.conn5]
        # --- PARAMETRISATION ---
        self.conn1.set_attr(p=self.high_pressure)
        self.conn1.set_attr(design=['p'], offdesign=['p'])       # offdesign??
        self.conn3.set_attr(p=self.low_pressure+0.2)
        self.conn3.set_attr(design=['p'])                        # offdesign no value, pressure determined by expansionvalve zeta
        self.conn4.set_attr(T=self.condensation_temp, x=1, fluid={self.working_fluid: 1})
        self.conn4.set_attr(design=['T', 'x', 'fluid'], offdesign=['T', 'x', 'fluid'])   # offdesign??
        self.conn5.set_attr(p=self.low_pressure, h=430)
        self.ww1.set_attr(T=278, p=2, m=0.6, fluid={'ethanol': 1})                       # Warmwasser Vorlauf
        self.wq1.set_attr(T=self.condensation_temp+10, p=2, m=0.6, fluid={'ethanol': 1})      # Wärmequelle Vorlauf
        #self.wq3.set_attr(T=self.condensation_temp+10, p=2, m=0.6, fluid={'ethanol': 1})      # Superheater seperater zulauf
        #self.wq2.set_attr()
        self.compressor.set_attr(P=self.compressor_power, eta_s=0.85)
        self.compressor.set_attr(design=['P', 'eta_s'], offdesign=['P', 'eta_s'])
        self.condenser.set_attr(Q=-4725, pr1=0.98, pr2=0.98)
        self.condenser.set_attr(design=['Q', 'pr1', 'pr2'], offdesign=['zeta1', 'zeta2', 'kA'])
        #expansionvalve.set_attr(pr=4)
        self.evaporator.set_attr(pr1=0.98)
        self.evaporator.set_attr(design=['pr1'], offdesign=['zeta1'])
        self.superheater.set_attr(pr1=0.98)
        self.superheater.set_attr(design=['pr1'], offdesign=['zeta1'])
        self.expansionvalve.set_attr(offdesign=['zeta'])
        # add connections to network
        self.heatpump.add_conns(self.conn0, self.conn1, self.conn2, self.conn3, self.conn4, self.conn5, self.ww1, self.ww2, self.wq1, self.wq2, self.wq3)

    def solve(self):
        self.heatpump.solve(mode='design')
        self.heatpump.print_results()

    def show_design(self): # fluid property diagram pre calc
        pressures = [self.low_pressure, self.high_pressure, self.high_pressure, self.low_pressure, self.low_pressure]  # in bar
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
            r_pressures.append(Conn.p.val)   # get pressure at connection for -- // --

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
        plt.plot(r_enthalpies, r_pressures, 'b-', label='Heat Pump Cycle')
        #fig.savefig('logph_diagram_H2O.svg')
        #fig.savefig('logph_diagram_H2O.png', dpi=300)
        plt.show()
                    
pump = Heatpump()
pump.solve()
pump.show_cycle()


"""

# Systemparameter
working_fluid = "R410a"
condensation_temp = 273
tanktemp = 288          # °K
tankvol = 200           # L
wq_pump_power = 50      # W
ww_pump_power = 50      # W
compressor_power = 1140 # W
high_pressure = 28
low_pressure = PropsSI('P', 'T',  condensation_temp, 'Q', 0, working_fluid) / 100000
pressures = [low_pressure, high_pressure, high_pressure, low_pressure, low_pressure]  # in bar
enthalpies = [430, 470, 260, 260, 430] # in kJ/kg

# --- --- --- --- --- --- --- --- --- --- 
# ------- FLUID PROPERTY DIAGRAM --------
# --- --- --- --- --- --- --- --- --- --- 

diagram = FluidPropertyDiagram(fluid='R410a')
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

# Plot on same axes as the diagram
diagram.draw_isolines(diagram_type='logph', fig=fig, ax=ax, x_min=0, x_max=750, y_min=1, y_max=800)
plt.plot(enthalpies, pressures, 'b-', label='Heat Pump Cycle')
# plt.tight_layout()
#fig.savefig('logph_diagram_H2O.svg')
#fig.savefig('logph_diagram_H2O.png', dpi=300)
# plt.show()
# --- --- --- --- --- --- --- ---
# ------ TESPY SIMULATION -------
# --- --- --- --- --- --- --- ---

# --- Network ---
heatpump = Network()
heatpump.set_attr(T_unit='K', p_unit='bar', h_unit='kJ / kg', iterinfo=True)

# --- --- COMPONENTS --- ---
# --- Heatpump ---
cc = com.CycleCloser('cycle_closer')
evaporator = com.HeatExchanger('evaporator')
condenser = com.HeatExchanger('condenser')
expansionvalve = com.Valve('expansionValve')
compressor = com.Compressor('compressor')
superheater = com.HeatExchanger('superheater')
# --- Water system ---
ww_merge = com.Merge('ww_merge')
wq_merge = com.Merge('wq_merge')
ww_split = com.Splitter('ww_split')
wq_split = com.Splitter('wq_split')
ww_valve = com.Valve('ww_valve')
wq_valve = com.Valve('wq_valve')
ww_pump = com.Pump('ww_pump')
wq_pump = com.Pump('wq_pump')
# --- Sources ---
tank_in_ww = com.Sink('tank_in_ww')
tank_out_ww = com.Source('tank_out_ww')
tank_in_wq = com.Sink('tank_in_wq')
tank_out_wq = com.Source('tank_out_wq')
#sink = com.Sink('sink')
#source = com.Source('source')

# --- --- CONNECTIONS --- ---
# --- Heatpump ---
conn0 = Connection(cc, 'out1', compressor, 'in1')
conn1 = Connection(compressor, 'out1', condenser, 'in1')
conn2 = Connection(condenser, 'out1', expansionvalve, 'in1')
conn3 = Connection(expansionvalve, 'out1', evaporator, 'in2')
conn4 = Connection(evaporator, 'out2', superheater, 'in2')
conn5 = Connection(superheater, 'out2', cc, 'in1')
# --- Water system ---
ww1 = Connection(tank_out_wq, 'out1', condenser, 'in2')
ww2 = Connection(condenser, 'out2', tank_in_wq, 'in1')
wq1 = Connection(tank_out_ww, 'out1', superheater, 'in1')
wq2 = Connection(superheater, 'out1', evaporator, 'in1')
wq3 = Connection(evaporator, 'out1', tank_in_ww, 'in1')
conn_list = [conn0, conn1, conn2, conn3, conn4, conn5]

# --- PARAMETRISATION ---
conn1.set_attr(p=high_pressure)
conn1.set_attr(design=['p'], offdesign=['p'])       # offdesign??
conn3.set_attr(p=low_pressure+0.2)
conn3.set_attr(design=['p'])                        # offdesign no value, pressure determined by expansionvalve zeta
conn4.set_attr(T=condensation_temp, x=1, fluid={working_fluid: 1})
conn4.set_attr(design=['T', 'x', 'fluid'], offdesign=['T', 'x', 'fluid'])   # offdesign??
conn5.set_attr(p=low_pressure, h=430)

ww1.set_attr(T=278, p=2, m=0.6, fluid={'ethanol': 1})                       # Warmwasser Vorlauf
wq1.set_attr(T=condensation_temp+10, p=2, m=0.6, fluid={'ethanol': 1})      # Wärmequelle Vorlauf
#wq3.set_attr(T=condensation_temp+10, p=2, m=0.6, fluid={'ethanol': 1})      # Superheater seperater zulauf
#wq2.set_attr()

compressor.set_attr(P=compressor_power, eta_s=0.85)
compressor.set_attr(design=['P', 'eta_s'], offdesign=['P', 'eta_s'])
condenser.set_attr(Q=-4725, pr1=0.98, pr2=0.98)
condenser.set_attr(design=['Q', 'pr1', 'pr2'], offdesign=['zeta1', 'zeta2', 'kA'])
#expansionvalve.set_attr(pr=4)
evaporator.set_attr(pr1=0.98)
evaporator.set_attr(design=['pr1'], offdesign=['zeta1'])
superheater.set_attr(pr1=0.98)
superheater.set_attr(design=['pr1'], offdesign=['zeta1'])
expansionvalve.set_attr(offdesign=['zeta'])
# FINISH SETUP AND SOLVE
heatpump.add_conns(conn0, conn1, conn2, conn3, conn4, conn5, ww1, ww2, wq1, wq2, wq3)
heatpump.solve(mode='design')
heatpump.save('designstate/design_state.json')
#heatpump.solve(mode="offdesign", design_path='designstate/design_state.json')

#
# print("------------------------------------------------------")
# print("------------         RESULTS           ---------------")
# print("------------------------------------------------------")
#
# heatpump.print_results()
superheat = conn5.T.val - condensation_temp
print(f"Superheat = {superheat}")

# --- CALCULATED HEAT CYCLE DIAGRAM ---
r_enthalpies = []
r_pressures = []
for Conn in conn_list:
    r_enthalpies.append(Conn.h.val)  # get enthalpy at connection and add it to list for fluprodia diagram
    r_pressures.append(Conn.p.val)   # get pressure at connection for -- // --

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
plt.plot(r_enthalpies, r_pressures, 'b-', label='Heat Pump Cycle')

plt.tight_layout()
#fig.savefig('logph_diagram_H2O.svg')
#fig.savefig('logph_diagram_H2O.png', dpi=300)
plt.show()
"""