# Digital Twin of a Heat Pump System - Bachelor's Thesis Project

![Heat Pump Visualization](frontend/plots/thermocycle.png)

## Table of Contents
- [Project Description](#project-description)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)


## Project Description
This project implements a digital twin of a heat pump system for a bachelor's thesis. It consists of:
- A thermodynamic simulation backend using TESPy (Thermal Engineering Systems in Python)
- A web-based frontend for visualization and interaction
- REST API for communication between frontend and backend

The system allows users to:
- Simulate different operating conditions of the heat pump
- Visualize the thermodynamic cycle
- Compare design and off-design performance
- Monitor key parameters (temperatures, pressures, power, etc.)

## Features
- **Thermodynamic Simulation**:
  - Complete heat pump cycle modeling (compressor, condenser, evaporator, expansion valve)
  - Design and off-design calculations
  - R410A refrigerant properties via CoolProp
- **Visualization**:
  - Interactive log(p)-h diagrams
  - Real-time parameter display
  - COP (Coefficient of Performance) gauge
- **Web Interface**:
  - Parameter adjustment
  - Session management
  - Comparison between simulated and real systems
- **API**:
  - FastAPI backend
  - Session-based operation
  - JSON data exchange

## Technologies Used
### Backend
- Python >= 3.12
- TESPy (Thermal Engineering Systems in Python) 0.9.0
- CoolProp for refrigerant properties
- FastAPI for web server
- Fluprodia for thermodynamic diagrams
- Matplotlib for plotting

### Frontend
- HTML5, CSS3, JavaScript
- Canvas API for heat pump visualization
- mpld3 for interactive plots
- RadialGauge.js for COP display

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/heatpump-digital-twin.git
    cd heatpump-digital-twin

2. Create virtual environment:
    ```bash 
    python -m venv venv
    source venv/bin/activate  
On Windows use `venv\Scripts\activate`
3. Install dependencies:
    ```bash
    pip install -r requirements.txt

4. Install additional frontend dependencies:
    ```bash
    npm install gauge.js

## Usage

1. Start developement server:
    ```bash
    fastapi dev MCI_HeatPump.py

3. Access GUI at:
    ```bash
    http://127.0.0.1:8000/frontend/


## Project Structure

heatpump-digital-twin/
├── frontend/                  # Web interface files
│   ├── index.html             # Main HTML file
│   ├── script.js              # Frontend logic
│   ├── stylesheet.css         # Styling
│   └── plots/                 # Generated diagrams
├── MCI_HeatPump.py            # Main Python application
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── design_state.json          # Saved design state


README generated using gen AI (deepseek.com model:R1)
