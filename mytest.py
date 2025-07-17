from typing import Optional
from tespy.networks import Network
from tespy import components as com
from tespy.connections import Connection, Ref
from tespy.tools import logger, UserDefinedEquation
from CoolProp.CoolProp import PropsSI

design_heat_input = 4158
wq_massflow_data = 23                                   # kg/min
ww_massflow_data = 16.1                                 # kg/min        
wq_massflow = wq_massflow_data / 60                     # kg/s
ww_massflow = ww_massflow_data / 60                     # kg/s
ww_inflow_temp = 273.15 + 35.5    
water_pressure = 200000 # pa
# Heatpipe compensation
t_eingang = 273.15 + 14.2                # K
t_ausgang = 273.15 + 11.7                # K
h1 = PropsSI("H", "P", water_pressure, "T", t_eingang, "water")
h2 = PropsSI("H", "P", water_pressure, "T", t_ausgang, "water")
dh = h2 - h1            # Enthalpieverlust der Wärmequelle 
Q = wq_massflow * dh    # von der Wärmequelle übertragene Wärme

Q_ges = -design_heat_input    # gesamte Leistung der Wärmeaufnahme
dh_ges = Q_ges / wq_massflow    # Enthalpieverlust der Wärmequelle wenn gesamte Leistung von Wärmequelle kommen würde
h1_virt = h2 - dh_ges
t_compensated = PropsSI("T", "P", water_pressure, "H", h1_virt, "water" ) # theoretische Einganstemperatur der Wärmequelle
wq_inflow_temp = t_compensated

heatpump = Network()
heatpump.set_attr(T_unit='K', p_unit='bar', h_unit='kJ / kg', iterinfo=True)

cc = com.CycleCloser('cycle_closer')
evaporator = com.HeatExchanger('evaporator')
condenser = com.HeatExchanger('condenser')
expansionvalve = com.Valve('expansionValve')
compressor = com.Compressor('compressor')
superheater = com.HeatExchanger('superheater')
        # --- Sources ---
tank_in_ww = com.Sink('tank_in_ww')
tank_out_ww = com.Source('tank_out_ww')
tank_in_wq = com.Sink('tank_in_wq')
tank_out_wq = com.Source('tank_out_wq')
sink = com.Sink('Sink')
source = com.Source('Source')
        # Connections
        # --- Heatpump ---
c1 = Connection(source, 'out1', compressor, 'in1')
c2 = Connection(compressor, 'out1', condenser, 'in1')
c3 = Connection(condenser, 'out1', sink, 'in1')


conn0 = Connection(cc, 'out1', compressor, 'in1')
conn1 = Connection(compressor, 'out1', condenser, 'in1')
conn2 = Connection(condenser, 'out1', expansionvalve, 'in1')
conn3 = Connection(expansionvalve, 'out1', evaporator, 'in2')
conn4 = Connection(evaporator, 'out2', superheater, 'in2')
conn5 = Connection(superheater, 'out2', cc, 'in1')
        # --- Water system ---
ww1 = Connection(tank_out_ww, 'out1', condenser, 'in2')
ww2 = Connection(condenser, 'out2', tank_in_ww, 'in1')

wq1 = Connection(tank_out_wq, 'out1', superheater, 'in1')
wq2 = Connection(superheater, 'out1', evaporator, 'in1')
q3 = Connection(evaporator, 'out1', tank_in_wq, 'in1')
        # --- Add Connections and parametise ---

#heatpump.add_conns(self.conn0, self.conn1, self.conn2, self.conn3, self.conn4, self.conn5, self.ww1, self.ww2, self.wq1, self.wq2, self.wq3)
heatpump.add_conns(c1,c2,c3,ww1,ww2)


ww1.set_attr(T=ww_inflow_temp, p=2, m=ww_massflow, fluid={'ethanol': 1})
#wq1.set_attr(T=self.wq_inflow_temp, p=2, m=self.wq_massflow, fluid={'ethanol': 1})

compressor_power = 21.88877055400408 * (ww_inflow_temp-273.15) + 101.71412575912325
compressor.set_attr(P=compressor_power, eta_s=0.77)
high_pres = 0.6029903492677208 * (ww_inflow_temp - 273.15) + 4.036221627874944
c2.set_attr(p=high_pres, fluid={'R410a': 1})

heatpump.solve("design")
heatpump.print_results()