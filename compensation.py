from CoolProp.CoolProp import PropsSI

# Kompensation für IdM Heatpipe
massenstrom_min = 23                    # kg/min
massenstrom = massenstrom_min / 60      # kg/sec
t_eingang = 273.15 + 14.2                # K
t_ausgang = 273.15 + 11.7               # K
druck = 200000                          # pa druck in wq leitung
verdampfer_leistung = 4158              # W

# berechnung
h1 = PropsSI("H", "P", druck, "T", t_eingang, "water")
h2 = PropsSI("H", "P", druck * 0.98, "T", t_ausgang, "water")
dh = h2 - h1            # Enthalpieverlust der Wärmequelle 
Q = massenstrom * dh    # von der Wärmequelle übertragene Wärme

Q_ges = -verdampfer_leistung    # gesamte Leistung der Wärmeaufnahme
dh_ges = Q_ges / massenstrom    # Enthalpieverlust der Wärmequelle wenn gesamte Leistung von Wärmequelle kommen würde
h1_virt = h2 - dh_ges
T1 = PropsSI("T", "P", druck, "H", h1_virt, "water" ) - 273.15 # theoretische Einganstemperatur der Wärmequelle
dt = T1 - t_eingang

print("Heat Flow from Heat source: " + str(round(Q,2)))
print("complete Heat Flow observed: " + str(Q_ges))
print("enthalpy difference: " + str(round(dh,2)))
print("compensated enthalpy difference: " + str(round(dh_ges,2 )))
print("Ursprüngliche Eingangstemperatur: " + str(round (t_eingang - 273.15, 2)) + "°C")
print("kompensierte Wärmequelleneingangstemperatur: " + str(round(T1,2)) + "°C")

print(" \n other testing stuff: -------------- \n")

t_cond = PropsSI("T", "Q", 1, "P", 2540000, "R410a")
print("tsat HP: " + str(round(t_cond-273.15)))
t_evap = PropsSI("T", "Q", 1, "P", 1040000, "R410a")
print("tsat LP: " + str(round(t_evap-273.15)))


