import tespy as tp

heatpump = tp.networks.network.Network()

heatpump.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg')

cc = tp.components.CycleCloser('cycle closer')

# look at tespy docs more
