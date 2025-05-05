from tespy.networks import Network
from tespy import components as com
from tespy.connections import Connection, Ref
from tespy.tools import logger
import logging

();logger.define_logging(
    logpath="myloggings", log_the_path=True, log_the_version=True,
    screen_level=logging.INFO, file_level=logging.DEBUG
);()  # +doctest: ELIPSIS

# Systemparameter
#working_fluid = "propane"
working_fluid = "R410a"
tanktemp = 288          # °K
tankvol = 50            # L
wq_pump_power = 50      # W
ww_pump_power = 50      # W
compressor_power = 1140 # W


heatpump = Network()
heatpump.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg', iterinfo=True)

# Heatpump components
cc = com.CycleCloser('cycle closer')
evaporator = com.HeatExchanger('evaporator')
evaporator.set_attr(pr1=0.99, pr2=0.99)
condenser = com.HeatExchanger('condenser')
#condenser.set_attr(pr1=0.99, pr2=0.99, Q=-1e-5)
condenser.set_attr(Q=1)
expansionvalve = com.Valve('expansionValve')
expansionvalve.set_attr(pr=0.15)
compressor = com.Compressor('compressor')
compressor.set_attr(eta_s=0.85, P=compressor_power)
# connect the heatpump
conn0 = Connection(cc, 'out1', compressor, 'in1')
conn1 = Connection(compressor, 'out1', condenser, 'in1')
conn2 = Connection(condenser, 'out1', expansionvalve, 'in1')
conn3 = Connection(expansionvalve, 'out1', evaporator, 'in2')
conn4 = Connection(evaporator, 'out2', cc, 'in1')

conn4.set_attr(T=20, x=1, fluid={working_fluid:1})
conn2.set_attr(T=80, x=0)
#HEATING SYSTEM
#pufferspeicher
tank_in_h = com.Sink('tank_in_h')
tank_out_h = com.Source('tank_out_h')
tank_in_c = com.Sink('tank_in_c')
tank_out_c = com.Source('tank_out_c')

# waermequellenseite
reg_valve_1 = com.Valve('reg_valve_1')
reg_valve_1.set_attr(pr=0.85)
merge1 = com.Merge('merge1')
split1 = com.Splitter('split1')
p1 = com.Pump('p1')
p1.set_attr(eta_s=0.75, P=wq_pump_power)

# vor und ruecklauf
reg_valve_2 = com.Valve('reg_valve_2')
reg_valve_2.set_attr(pr=0.85)
merge2 = com.Merge('merge2')
split2 = com.Splitter('split2')
p2 = com.Pump('p2')
p2.set_attr(eta_s=0.75, P=ww_pump_power)

# connections wq-side ??? Does this work???
wq1 = Connection(tank_out_h, 'out1', merge1, 'in1')
wq2 = Connection(merge1, 'out1', p1, 'in1')
wq3 = Connection(p1, 'out1', evaporator, 'in1')
wq4 = Connection(evaporator, 'out1', split1, 'in1')
wq5 = Connection(split1, 'out1', reg_valve_1, 'in1')
wq6 = Connection(reg_valve_1, 'out1', merge1, 'in2')
wq7 = Connection(split1, 'out2', tank_in_h, 'in1')

#speichertemp
wq1.set_attr(T=tanktemp, p=1.2, fluid={'water': 1})
#wq7.set_attr(T=tanktemp-2)

# connections heating circuit
ww1 = Connection(tank_out_c, 'out1', merge2, 'in1')
ww2 = Connection(merge2, 'out1', p2, 'in1')
ww3 = Connection(p2, 'out1', condenser, 'in2')
ww4 = Connection(condenser, 'out2', split2, 'in1')
ww5 = Connection(split2, 'out1', reg_valve_2, 'in1')
ww6 = Connection(reg_valve_2, 'out1', merge2, 'in2')
ww7 = Connection(split2, 'out2', tank_in_c, 'in1')

#speichertemp
ww1.set_attr(T=tanktemp, p=1.2, fluid={'water': 1})
#ww7.set_attr(T=tanktemp+2, p=1)



heatpump.add_conns(conn0, conn1, conn2, conn3, conn4, ww1, ww2, ww3, ww4, ww5, ww6, ww7, wq1, wq2, wq3, wq4, wq5, wq6, wq7)
heatpump.solve("design")
#heatpump.print_components()
print("------------         RESULTS           ---------------")
heatpump.print_results()

