from tespy.networks import Network
from tespy import components as com
from tespy.connections import Connection, Ref
from tespy.tools import logger
import CoolProp.CoolProp as cp
import logging
from fluprodia import FluidPropertyDiagram
import matplotlib.pyplot as plt
import numpy as np

();logger.define_logging(
    logpath="myloggings", log_the_path=True, log_the_version=True,
    screen_level=logging.INFO, file_level=logging.DEBUG
);()  # +doctest: ELIPSIS

# ------- FLUID PROPERTY DIAGRAM -------

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

pressures = [7, 28, 28, 7, 7]  # in bar
enthalpies = [430, 445, 260, 260, 430] # in kJ/kg
# Plot on same axes as the diagram

diagram.draw_isolines(diagram_type='logph', fig=fig, ax=ax, x_min=0, x_max=750, y_min=1, y_max=800)
plt.plot(enthalpies, pressures, 'b-', color='red', label='Heat Pump Cycle')

plt.tight_layout()
#fig.savefig('logph_diagram_H2O.svg')
#fig.savefig('logph_diagram_H2O.png', dpi=300)
plt.show() 


# ----- TESPY SIMULATION -------

# Systemparameter
working_fluid = "R410a"
tanktemp = 288          # °K
tankvol = 200           # L
wq_pump_power = 50      # W
ww_pump_power = 50      # W
compressor_power = 1140 # W

# Network setup
heatpump = Network()
heatpump.set_attr(T_unit='K', p_unit='bar', h_unit='kJ / kg', iterinfo=True)


#inputs
r_in = com.Source('r_in')
r_out = com.Sink('r_out')

# consumer system
cc1 = com.CycleCloser('cc1')
p1 = com.Pump('p1')
condenser = com.Condenser('condenser')
consumer = com.SimpleHeatExchanger('consumer')

#connections
conn1 = Connection(r_in, 'out1', condenser, 'in1')
conn2 = Connection(condenser, 'out1', r_out, 'in1')

cons1 = Connection(consumer, 'out1', p1, 'in1')
cons2 = Connection(p1, 'out1', condenser, 'in2')
cons3 = Connection(condenser, 'out2', cc1, 'in1')
cons4 = Connection(cc1, 'out1', consumer, 'in1')


# parameters
heatpump.add_conns(conn1, conn2, cons1, cons2, cons3, cons4)
condenser.set_attr(pr1=0.99, pr2=0.99)
p1.set_attr(eta_s=0.75)
consumer.set_attr(pr=0.99)
p_cond = cp.PropsSI("P", "Q", 1, "T", 333, working_fluid) / 1e5
# t_psi = cp.PropsSI("", "")
#print("p_cond;  " + str(p_cond))
conn1.set_attr(T=333, p=p_cond, fluid={working_fluid: 1})
cons2.set_attr(T=278, p=2, fluid={"water": 1})
cons3.set_attr(T=310)
consumer.set_attr(Q=-4625)


# Final steps
#heatpump.add_conns()
heatpump.solve("design")
#heatpump.print_components()
print("------------         RESULTS           ---------------")
heatpump.print_results()
