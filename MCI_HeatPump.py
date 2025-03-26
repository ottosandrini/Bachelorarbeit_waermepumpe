from tespy.networks import Network
from tespy import components as com
from tespy.connections import Connection, Ref
from tespy.tools import logger
import logging

();logger.define_logging(
    logpath="myloggings", log_the_path=True, log_the_version=True,
    screen_level=logging.INFO, file_level=logging.DEBUG
);()  # +doctest: ELIPSIS

tanktemp = 15
tankvol = 50

heatpump = Network()

heatpump.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg', iterinfo=True)

cc = com.CycleCloser('cycle closer')
# Heatpump components
evap = com.HeatExchanger('evaporator')
cond = com.HeatExchanger('condenser')
exva = com.Valve('expansionValve')
comp = com.Compressor('compressor')
comp.set_attr(pr=5)
# Heatpump pipes
pipe1 = com.Pipe('pipe1')
pipe2 = com.Pipe('pipe2')
pipe3 = com.Pipe('pipe3')
pipe4 = com.Pipe('pipe4')

# connect the heatpump
conn1 = Connection(comp, 'out1', pipe1, 'in1')
conn2 = Connection(pipe1, 'out1', cond, 'in1')
conn3 = Connection(cond, 'out1', pipe2, 'in1')
conn4 = Connection(pipe2, 'out1', exva, 'in1')
conn5 = Connection(exva, 'out1', pipe3, 'in1')
conn6 = Connection(pipe3, 'out1', evap, 'in1')
conn7 = Connection(evap, 'out1', pipe4, 'in1')
conn8 = Connection(pipe4, 'out1', comp, 'in1')

#rest of the heating system

tank_in = com.Sink('tank_in')
tank_out = com.Source('tank_out')




heatpump.add_conns(conn1, conn2, conn3, conn4, conn5, conn6, conn7, conn8)
heatpump.solve("design")
heatpump.print_components
print("------------         RESULTS           ---------------")
heatpump.print_results
# fluid is n-Propane
# hydraulic system components



# look at tespy docs more
