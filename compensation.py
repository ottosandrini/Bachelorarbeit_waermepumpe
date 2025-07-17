from CoolProp.CoolProp import PropsSI
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress



# Kompensation für IdM Heatpipe
massenstrom_min = 23                    # kg/min
massenstrom = massenstrom_min / 60      # kg/sec
t_eingang = 273.15 + 14.2                # K
t_ausgang = 273.15 + 11.7               # K
druck = 200000                          # pa druck in wq leitung
verdampfer_leistung = 4158              # W

# berechnung
h1 = PropsSI("H", "P", druck, "T", t_eingang, "water")
h2 = PropsSI("H", "P", druck, "T", t_ausgang, "water")
dh = h2 - h1            # Enthalpieverlust der Wärmequelle 
Q = massenstrom * dh    # von der Wärmequelle übertragene Wärme

Q_ges = -verdampfer_leistung    # gesamte Leistung der Wärmeaufnahme
dh_ges = Q_ges / massenstrom    # Enthalpieverlust der Wärmequelle wenn gesamte Leistung von Wärmequelle kommen würde
h1_virt = h2 - dh_ges
T1 = PropsSI("T", "P", druck, "H", h1_virt, "water" ) - 273.15 # theoretische Einganstemperatur der Wärmequelle
dt = T1 - t_eingang

"""
# TEST THINGS
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

"""

def lin(x, slope, intercept):
    return slope * x + intercept

def lin_reg(a, b): # do a linreg and plot the thing 
    var_labels = {
        'pressures': 'Druck Hochdruckseite / bar',
        'low_pressures': 'Druck Niederdruckseite / bar',
        'powers': 'Leistung Verdichter / W',
        'temps': 'Temperatur Verdichter-Austritt/Verflüssiger-Eingang / °C',
        'superheat': 'Überhitzung / °K',
        'con_pow': 'Leistung Verflüssiger / W',
        'eva_pow': 'Leistung Verdampfer / W',
        'ww_temp': 'Heizwasser Rücklauftemperatur / °C',
        'wq_in': 'Wärmequelle Rücklauftemperatur / °C',
        'wq_out': 'Wärmequelle Vorlauftemperatur / °C',
        'wq_mass': 'Wärmequelle Massenstrom / kg/min',
        'pressureratio': 'Druckverhältnis Verdichter - Aus-/Eingang',
        'dt': 'Temperaturdifferenz / °K',
        'hp_dt': 'Temperaturdifferenz / °K',
        'pr_deviation': 'Pressure Ratio Deviation',
        'hp_efficiency': 'Effizienz relativ zum Carnot COP',
        'carnot_con_pow': 'Carnot Leistung Verflüssiger / W'
    }
    a_name = [k for k,v in globals().items() if isinstance(v, list) and v is a][0]
    b_name = [k for k,v in globals().items() if isinstance(v, list) and v is b][0]

    x_label = var_labels.get(a_name, a_name)
    y_label = var_labels.get(b_name, b_name)
    #title = f'{y_label} vs {x_label}'
    slope, intercept, r_value, p_value, std_err = linregress(a, b)
    print(f"Regression for {y_label} against  {x_label}:")
    print(f"Slope: {slope}, Intercept: {intercept}, R-squared: {r_value**2}, P-value: {p_value}, Std Err: {std_err}")

    x = np.linspace(min(a), max(a), 100)
    y = lin(x, slope, intercept)

    print("slope: " + str(slope))
    print("intercept: " + str(intercept))
    plt.figure(figsize=(8, 5))
    plt.scatter(a, b, color='blue', label='Datenpunke')
    plt.plot(x, y, color='red', label=f'linear fit')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    #plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def compensate(wq_in, wq_out, eva_pow, wq_mf): # heatpipe compensation
    wq_t_in_compensated = []
    dt = []
    for i in range(len(wq_in)):
        # calculate the enthalpy at the inlet and outlet of the heat source
        #h1 = PropsSI("H", "P", w_pres, "T", wq_in[i] + 273.15, "water")
        h2 = PropsSI("H", "P", 200000, "T", wq_out[i] + 273.15, "ethanol")
        Q_ges = -eva_pow[i]
        dh_ges = Q_ges / (wq_mf[i] / 60)
        h1_virt = h2 - dh_ges
        T_comp = PropsSI("T", "P", 200000, "H", h1_virt, "ethanol") - 273.15
        wq_t_in_compensated.append(round(T_comp,1))
        dt.append(round(T_comp-wq_in[i],2))
    return (wq_t_in_compensated, dt)

# zusammenhang finden zwischen ww_massenstrom und spreizung
# zusammenhang für td_pinch finden -> wie groß der unterschied zwischen heiß und kalt ist (verdampfer)

# Daten        1     2     3     4     5     6     7     8     9     10    11    12
pressures=    [22.6, 24.5, 25.4, 19.1, 33.2, 34.3, 30.1, 22.6, 21.8, 32.4, 36.5, 19.7, 21.7, 32.8, 37,   21.8, 21.8 ]
low_pressures=[9.7,  10.3, 10.4, 9.6,  9.4,  9.28, 7.7,  8.93, 8.55, 9.09, 7.1,  11,   8.38, 8.76, 6.89, 9.88, 8.64 ] 
powers=       [780,  850,  880,  630,  1160, 1190, 1050, 790,  770,  1140, 1220, 620,  770,  1140, 1230, 620,  1400 ]
temps =       [50.6, 54.6, 56.3, 41,   76.3, 69.9, 76.4, 59,   58.6, 73.4, 65.2, 55.1, 59.7, 65.7, 82.4, 35.7, 59.1 ]
low_temps =   [11.4, 13.4, 13.7, 12.2, 11.2, 10.3, 1.06, 9.65, 9.34, 9.78, 0.654,24.6, 9.75, 9.24, -2.1, 9.13, 11.9 ]
superheat =   [5.1,  5.0,  4.8,  6.2,  5.8,  5.4,  2.3,  6.1,  7.2,  5.6,  4.5,  14,   8.3,  6.3,  2.7,  2.1,  9.4  ]
con_pow =     [5112, 4851, 5070, 5396, 4601, 3352, 4056, 5006, 4971, 4143, 1927, 6224, 4859, 3340, 2956, 3657, 8526 ]
eva_pow =     [4278, 3963, 4158, 4714, 3424, 2152, 2936, 4243, 4271, 3059, 819,  5500, 4066, 2234, 1740, 3013, 7154 ]
ww_temp =     [31.1, 34.1, 35.5, 24,   48.2, 49.2, 44.2, 31.4, 30,   48.4, 52.8, 24.8, 30.3, 46.4, 54,   32.2, 27.4 ]
wq_in =       [12.2, 13.7, 14.2, 11.8, 10.5, 9.97, 3.7,  9.23, 7.95, 7.98, 0.434,24.5, 8.13, 8.4, -0.318,10.1, 9.95 ]
wq_out =      [9.96, 11.1, 11.7, 10,   8.88, 8.47, 2.41, 7.52, 6.65, 7.05, 0.059,22.2, 7,    7.3, -0.833,9.44, 8.21 ] 
wq_mass =     [23.1, 23.2, 23,   28.4, 22.8, 22.5, 22.5, 22.9, 28.5, 28.6, 28,   26.4, 28.2, 28.5, 28.1, 28.4, 34.4 ]
pressureratio = []      # druckverhältnis am kompressor
dt = []                 # dt der Wärmequelle
hp_dt = []              # dt der wärmequellentemp und wärmesenkentemp
ref_dt = []             # dt (temps - low_temps)
dt_hc = []              # dt zwischen hot & cold in evap
pr_deviation = []       # abweichung des druckverhältnisses zum linear fit
hp_efficiency = []      # abweichung vom Carnot Wirkungsgrad
carnot_con_pow = []     # carnotsche wärmeleistung
t_cond = []             # verflüssigungstemps
t_evap = []             # verdampfungstemps
dt_evap_cond = []       # dt (t_cond-t_evap)
logdp = []              # log(pressures/low_pressures)
test = []               # test
test2 = []              # test2
cop = []                # COP

# remove outlier
list_of_lists = [pressures, low_pressures, powers, temps, low_temps, superheat, con_pow, eva_pow, ww_temp, wq_in, wq_out, wq_mass,
                 pressureratio, dt, hp_dt, ref_dt, dt_hc, pr_deviation, hp_efficiency, carnot_con_pow, t_cond, t_evap, dt_evap_cond,
                 logdp, test, test2, cop]

for i in range(len(list_of_lists)-15):
    del list_of_lists[i][-1]

list_dict = {
    "pressures": pressures,"low_pressures": low_pressures,"powers": powers,"temps": temps,"low_temps": low_temps,
    "superheat": superheat,"con_pow": con_pow,"eva_pow": eva_pow,"ww_temp": ww_temp, "wq_in": wq_in, "wq_out": wq_out,
    "wq_mass": wq_mass, "pressureratio": pressureratio, "dt": dt,"ref_dt": ref_dt,"dt_hc": dt_hc, "pr_deviation": pr_deviation,
    "hp_efficiency": hp_efficiency, "carnot_con_pow": carnot_con_pow, "t_cond": t_cond, "t_evap": t_evap,"dt_evap_cond": dt_evap_cond,
    "logdp": logdp, "test": test, "test2": test2,"cop": cop,
}


lists = compensate(wq_in, wq_out, eva_pow, wq_mass)     # compensation der IDM Heatpipe und Umgebungswärme
wq_in_comp = lists[0]                                   
dt_comp = lists[1]

wq_pow = [a + b for a, b in zip(wq_in, powers)]  # Wärmequelle Einlass Temp * Leistung


# iterate over data
for i in range(len(wq_in)):
    dt.append(wq_in_comp[i] - wq_out[i])
    carnot_con_pow.append(((ww_temp[i]+273.15) / (ww_temp[i]-wq_in_comp[i])) * powers[i])
    hp_dt.append(ww_temp[i]-wq_in_comp[i])
    t1 = PropsSI('T', 'P', pressures[i] * 100000, 'Q', 0, 'R410a')
    t2 = PropsSI('T', 'P', low_pressures[i] * 100000, 'Q', 1, 'R410a')
    t_cond.append(t1)
    t_evap.append(t2)
    logdp.append(pressures[i]/low_pressures[i])
    cop.append(con_pow[i]/powers[i])
    ref_dt.append((temps[i]-low_temps[i]))
    dt_hc.append(wq_in_comp[i]-low_temps[i])
    #print("wq_in_comp: " + str(wq_in_comp[i]) + " - low_temps: " + str(low_temps[i]) + " = " + str(dt_hc[i]))

#print("dt: " + str(dt))

# calculate average superheat and deviation
average_superheat = sum(superheat) / len(superheat)
superheat_deviation = [sh - average_superheat for sh in superheat]

# iterate over data again
for i in range(len(wq_in)):
    pressureratio.append(pressures[i] / low_pressures[i])
    hp_efficiency.append(con_pow[i]/carnot_con_pow[i])
    dt_evap_cond.append(temps[i]-wq_in_comp[i]-2)
    test.append(powers[i]*hp_dt[i])
    test2.append((wq_in[i]+273)*wq_mass[i])

norm_lift = [lift/max(dt_evap_cond) for lift in dt_evap_cond]
load_param = [(p_ratio * lift)/mf for p_ratio,lift,mf in zip(pressureratio, dt_evap_cond, wq_mass)]
#print('carnot: ' + str(carnot_con_pow) + '\ncarnon: ' + str(con_pow))

# remove outliers if desired
if 1:
    indices = []
    for i in range(len(hp_efficiency)):
        if hp_efficiency[i] < 0.12:
            print("YES: " + str(i))
            indices.append(i)
    for i in range(len(indices)):
        hp_efficiency.pop(indices[i])

    # effizienz statistik dinge
    mean_eff = np.mean(hp_efficiency)
    std_eff = np.std(hp_efficiency)
    min_eff = np.min(hp_efficiency)
    max_eff = np.max(hp_efficiency)
    print(f"Mean: {mean_eff:.4f}")
    print(f"Std Dev: {std_eff:.4f}")
    print(f"Min: {min_eff:.4f}")
    print(f"Max: {max_eff:.4f}")
    print("efficiency:")
    print(hp_efficiency)


# Plotten von relevanten Daten
choice = 7
if choice == 1:
    lin_reg(hp_dt,cop)
elif choice == 2:
    lin_reg(test2, dt_comp)
elif choice == 3:
    lin_reg(cop, dt_comp)
elif choice == 4:
    lin_reg(ref_dt, cop)
elif choice == 5:
    lin_reg(dt_hc, hp_efficiency)
elif choice == 6:
    lin_reg(ww_temp, pressures)
elif choice == 7:
    lin_reg(ww_temp, powers)
elif choice == 8:
    lin_reg(wq_in, con_pow)
elif choice == 9:
    lin_reg(hp_dt, hp_efficiency)
elif choice == 10: # requires the efficiency statistics above
    plt.hist(hp_efficiency, bins=20, edgecolor='black', alpha=0.7)
    plt.axvline(mean_eff, color='red', linestyle='dashed', linewidth=1.5, label=f"Mean = {mean_eff:.3f}")
    #plt.title('Histogram of hp_efficiency')
    plt.xlabel('Effizienz')
    plt.ylabel('Frequenz')
    plt.legend()
    plt.grid(True)
    plt.show()
else:
    print("Nothing chosen")

# Finden von Zusammnehängen:
def find_correlated_lists(list_of_lists, target_index, r_threshold=0.7, p_threshold=0.05):
    target = list_of_lists[target_index]
    correlated = []

    for i, candidate in enumerate(list_of_lists):
        if i == target_index:
            continue  # Skip comparing target with itself

        if len(candidate) != len(target):
            #print(f"Skipping index {i} due to length mismatch.")
            continue

        result = linregress(target, candidate)

        if abs(result.rvalue) > r_threshold and result.pvalue < p_threshold:
            correlated.append((i, result.rvalue, result.pvalue, candidate))

    if not correlated:
        print("No lists found with correlation above threshold.")
    else:
        print(f"Lists correlated with list at index {target_index}:")
        for idx, r, p, values in correlated:
            print(f" - Index {idx}: R={r:.3f}, p={p:.3g}, List={values}")

    return correlated  # Optional: return for further use

def analyze_correlations(named_dict, r_thresh=0.7, p_thresh=0.05):
    results = []
    keys = list(named_dict.keys())

    for i in range(len(keys)):
        for j in range(len(keys)):
            if i == j:
                continue  # Skip self-correlation
            x_name, y_name = keys[i], keys[j]
            x, y = named_dict[x_name], named_dict[y_name]

            if len(x) != len(y):
                continue  # Skip if lengths don't match

            try:
                slope, intercept, r_value, p_value, std_err = linregress(x, y)
                if abs(r_value) >= r_thresh and p_value < p_thresh:
                    results.append({
                        'x': x_name,
                        'y': y_name,
                        'r': r_value,
                        'r²': r_value**2,
                        'p': p_value,
                        'slope': slope,
                        'intercept': intercept
                    })
            except Exception as e:
                print(f"Failed regression for {x_name} vs {y_name}: {e}")

    # Sort by descending R²
    results.sort(key=lambda d: abs(d['r²']), reverse=True)

    # Print results
    print("\nSignificant correlations (R > {:.2f}, p < {:.2f}):\n".format(r_thresh, p_thresh))
    for res in results:
        print(f"{res['y']} vs {res['x']}: R = {res['r']:.3f}, R² = {res['r²']:.3f}, p = {res['p']:.3e}")


#analyze_correlations(list_dict)
#find_correlated_lists(list_of_lists, 18)
