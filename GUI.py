import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# funktionen um reale betriebsdaten zu bekommen
def getT1():
    return 5

def getT2():
    return 17

def getP1():
    return 100000

def getP2():
    return 200000

# Streamlit layout
st.set_page_config(page_title="Heat Pump Digital Twin", layout="wide")
tab1, tab2, tab3 = st.tabs(["Real System", "Virtual System", "Comparison"])

# Real System Tab
with tab1:
    st.header("Real Heat Pump Data")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.header("Relevant data")
        #st.image("https://static.streamlit.io/examples/cat.jpg")

    with col2:
        st.header("condenser")
        #st.image("https://static.streamlit.io/examples/dog.jpg")

    with col3:
        st.header("Heatpump System")
        #st.image("https://static.streamlit.io/examples/owl.jpg")
        c3c = st.container()
        c3c.write("compressor")
        c3c.image("https://static.streamlit.io/examples/cat.jpg")
        c3c.empty()
        c3c.write("expansion valve")
        c3c.image("https://static.streamlit.io/examples/owl.jpg")

    with col4:
        st.header("evaporator")


    # Placeholder for live updates
    placeholder = st.empty()
    for _ in range(5):  # Simulate live updates
        #real_data = get_real_data()
        with placeholder.container():
            st.write("Updated Data: 98237958 ")
        time.sleep(1)

# Virtual System Tab
with tab2:
    st.header("Simulated Heat Pump Data")
    #virtual_data = get_virtual_data()
    st.metric("Temperature Inlet", "{virtual_data['Temperature Inlet']:.2f} °C")
    st.metric("Temperature Outlet", "{virtual_data['Temperature Outlet']:.2f} °C")
    st.metric("Pressure", "{virtual_data['Pressure']:.2f} bar")
    st.metric("Energy Consumption", "{virtual_data['Energy Consumption']:.2f} kWh")

# Comparison Tab
with tab3:
    st.header("Comparison: Real vs Virtual System")

    # Schematic (simplified representation)
    #fig, ax = plt.subplots()
    #ax.text(0.5, 0.9, "Compressor", fontsize=12, ha='center')
    #ax.text(0.5, 0.6, "Condenser", fontsize=12, ha='center')
    #ax.text(0.5, 0.4, "Expansion Valve", fontsize=12, ha='center')
    #ax.text(0.5, 0.2, "Evaporator", fontsize=12, ha='center')
    #ax.plot([0.5, 0.5], [0.1, 0.9], 'ro-', markersize=10)
    #ax.set_xlim(0, 1)
    #ax.set_ylim(0, 1)
    #ax.axis('off')
    #st.pyplot(fig)

st.sidebar.header("Something")

