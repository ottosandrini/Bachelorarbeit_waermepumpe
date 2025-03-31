# Wärmepumpenprojekt - Parameterliste

## Im Wärmekreis

### Druck & Temperatur
- `p_high` - Druck nach Kompressor
- `p_low` - Druck vor Kompressor
- `t_point_1` - Temperatur Punkt 1 im Wärmekreis
- `t_point_2` - Temperatur Punkt 2 im Wärmekreis
- `t_point_3` - Temperatur Punkt 3 im Wärmekreis
- `t_point_4` - Temperatur Punkt 4 im Wärmekreis

### Mechanisch & Energetisch
- `exp_valve_pos_ist` - Ventilposition Expansionsventil Ist-Wert
- `exp_valve_pos_soll` - Ventilposition Expansionsventil Soll-Wert
- `compressor_power` - Leistung Kompressor
- `superheat` - Überhitzung
- `cop` - Coefficient of Performance

## Im Wasserkreis

### Druck & Temperatur
- `t_vorlauf` - Temperatur Vorlauf
- `t_ruecklauf` - Temperatur Rücklauf
- `t_wq_in` - Temperatur Wärmequelle hin
- `t_wq_out` - Temperatur Wärmequelle weg
- `t_tank` - Temperatur Wärmespeicher
- `t_cooling_in` - Temperatur Frischwasserkühlung Einlass
- `t_cooling_out` - Temperatur Frischwasserkühlung Auslass

### Mechanisch & Energetisch
- `flow_source` - Durchfluss Wärmequelle
- `flow_sink` - Durchfluss Wärmesenke

## Schalter
- `wp_on_off` - An/Aus Schalter gesamtes System
- `cooling_on_off` - An/Aus Frischwasserkühlung
- `exp_valve_mode` - Auto/Manuell Regelung Expansionsventil
- `compressor_mode` - Auto/Manuell Verdichter

