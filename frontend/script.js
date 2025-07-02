// --------------------------------------------------------------------------
// ----------------------- HEATPUMP CLASS -----------------------------------
// --------------------------------------------------------------------------

class HeatpumpVis {
    constructor(type) {
        this.canvas;
        // semi-random starting values
        this.Temperatures = {conn0:10, conn1:60, conn2:55, conn3:3, conn4:3, conn5:10, wq_in:11, wq_out:9, ww_in:11, ww_out:14};
        this.Pressures = {conn0:8, conn1:22, conn2:22, conn3:8, conn4:8, conn5:8};
        this.Enthalpies = {conn0:430, conn1:450, conn2:200, conn3:200, conn4:400, conn5:430};
        this.Powers = {evaporator:4000, condenser:5000, superheater:200, compressor:800, comp_eff:0.99};
        this.MassFlows = {conn0:4.02, conn1:4.02, conn2:4.02, conn03:4.02, conn4:4.02, conn5:4.02, wq:0.475*60, ww:0.265*60};
        // Select Simulation or Real Thing with 0 or 1
        this.type = type;
        this.overheat = 7;
    }

    reload_data(data) {
        if (data.Temperatures) {
            this.Temperatures = {
                conn0: data.Temperatures.conn0 || this.Temperatures.conn0,
                conn1: data.Temperatures.conn1 || this.Temperatures.conn1,
                conn2: data.Temperatures.conn2 || this.Temperatures.conn2,
                conn3: data.Temperatures.conn3 || this.Temperatures.conn3,
                conn4: data.Temperatures.conn4 || this.Temperatures.conn4,
                conn5: data.Temperatures.conn5 || this.Temperatures.conn5,
                wq_in: data.Temperatures.wq_in || this.Temperatures.wq_in,
                wq_out: data.Temperatures.wq_out || this.Temperatures.wq_out,
                ww_in: data.Temperatures.ww_in || this.Temperatures.ww_in,
                ww_out: data.Temperatures.ww_out || this.Temperatures.ww_out
            };
        }
        // Update pressures
        if (data.Pressures) {
            this.Pressures = {
                conn0: data.Pressures.conn0 || this.Pressures.conn0,
                conn1: data.Pressures.conn1 || this.Pressures.conn1,
                conn2: data.Pressures.conn2 || this.Pressures.conn2,
                conn3: data.Pressures.conn3 || this.Pressures.conn3,
                conn4: data.Pressures.conn4 || this.Pressures.conn4,
                conn5: data.Pressures.conn5 || this.Pressures.conn5
            };
        }
        // Update powers
        if (data.Powers) {
            this.Powers = {
                evaporator: data.Powers.evaporator || this.Powers.evaporator,
                condenser: data.Powers.condenser || this.Powers.condenser,
                superheater: data.Powers.superheater || this.Powers.superheater,
                compressor: data.Powers.compressor || this.Powers.compressor,
                comp_eff: data.Powers.comp_eff || this.Powers.comp_eff
            };
        }
        // Update mass flows
        if (data.MassFlows) {
            this.MassFlows = {
                conn0: data.MassFlows.conn0 || this.MassFlows.conn0,
                conn1: data.MassFlows.conn1 || this.MassFlows.conn1,
                conn2: data.MassFlows.conn2 || this.MassFlows.conn2,
                conn3: data.MassFlows.conn3 || this.MassFlows.conn3,
                conn4: data.MassFlows.conn4 || this.MassFlows.conn4,
                conn5: data.MassFlows.conn5 || this.MassFlows.conn5,
                wq: data.MassFlows.wq || this.MassFlows.wq,
                ww: data.MassFlows.ww || this.MassFlows.ww
            };
        }
        // Update overheat
        if (data.overheat !== undefined) {
            this.overheat = data.overheat;
        }
    }

    spec_canvas(canvas) {
        this.canvas = canvas;
    }

    async update_data(json) {
        // this function updates Heat pump data by running a python script and reading new data
        // or getting new data from mqtt -> depending on this.type
        if (this.type == 0) { // Object is of type simulation
            // update by running python script
            // if jsonstring === 1 then no input specified -> run last simulation
            // if jsonstring === 20 then run design simulation
            if (json === 1) {
                // do nothing
                console.log("No parameters changed -> doing nothing")
                return 0
            }
            else if (json === 20) {
                // run design simulation
                var url = "http://127.0.0.1:8000/design_simulation/" + my_session_id;
                let response = await fetch(url, {method:"GET",headers:{"Content-type":"application/json; charset=UTF-8"}});
                if (!response.ok) {
                    throw_error("ID not ok. Something went wrong!");
                    return;
                }
                const json_resp  = await response.json();
                /*if (json_resp.my_session_id === 0 || json_resp.error) {
                    throw_error("Already too many people simulating. Please try again later");
                    my_session_id_get_in_progress = 0;
                    return;
                }*/
                //console.log(json_resp);
                this.reload_data(json_resp);
                this.update_buttons();
                var newcop = this.Powers.condenser / this.Powers.compressor;
                copgaugesim.value = newcop;
                document.getElementById("cop_value_sim").textContent = Math.round(newcop*100)/100;
            }

            else {
                // run simulation with json as inputs
                // send inputs and fetch result
                var url = "http://127.0.0.1:8000/offdesign_simulation/" + my_session_id;
                let resp = await fetch(url, {method:"POST", body:json, headers:{"Content-type": "application/json; charset=UTF-8"}});
                let json_resp = await resp.json();
                console.log("Server response; " + json_resp);
                // set new heatpump data and change buttons to match
                if (json_resp.message === undefined) {
                    this.reload_data(json_resp);
                    this.update_buttons();
                }
                else {
                    throw_error(json_resp.message)
                    console.log(`message from server: ${json_resp.message}`)
                }
            }
        }
        else if (this.type == 1) { // Heatpump is of type Real System
            // fetch mqtt data
            // response = await fetch();
            // json = await response.json();
            // console.log("Server Response; " + json);
            // this.reload_data(json);
            // this.update_viz_buttons();
            // update data from mqtt

            // testing things
            if (json === 1) {
                //console.log(Math.floor(Math.random() * 100) + ": update button pressed! Something might happen here eventually...")
                console.log("update button pressed! Something might happen here eventually...")
            }
        }
        else  {
            // give an error: Type not supported; choose Simulation (0) or Real System (1)
            throw_error("heat pump type not supported! Something went badly wrong here!");
        }
    }

    /*
    redrawParams(c, xoffset, yoffset){    // draw over old parameters
    c.font = "25px comic";
    // white out old things
    c.fillStyle = "green"; // green to check location
    //c.fillStyle = "white";
    c.fillRect(-25 + xoffset -2 , 388 + yoffset + 4 , 60, -30);
    c.fillRect(-25 + xoffset -2 , 308 + yoffset + 4 , 60, -30);
    c.fillRect(880 + xoffset -2 , 308 + yoffset + 4 , 60, -30);
    c.fillRect(880 + xoffset -2 , 388 + yoffset + 4 , 60, -30);
    c.fillRect(425 + xoffset -2 , 130 + yoffset + 4 , 60, -30);
    c.fillRect(425 + xoffset -2 , 710 + yoffset + 4 , 60, -30);
    // rewrite data fields
    c.fillStyle = "red";
    c.fillText(this.Temperatures.conn1 + "°C", -25 + xoffset, 388 + yoffset);
    c.fillText(this.Temperatures.conn1 + "°C", 880 + xoffset, 308 + yoffset);
    c.fillStyle = "blue";
    c.fillText(this.Temperatures.conn2 + "°C", -25 + xoffset, 308 + yoffset);
    c.fillText(this.Temperatures.conn2 + "°C", 880 + xoffset, 388 + yoffset);
    c.fillStyle = "black";
    c.fillText(this.Pressures.conn1 + " %", 425 + xoffset, 130 + yoffset);
    c.fillText(this.Pressures.conn2 + " %", 425 + xoffset, 710 + yoffset);
    }
    */

    drawHeatpump(){                            // draws the Heatpump at first start
        var xscale = 1.02;
        var yscale = 1;
        var c = this.canvas.getContext("2d");
        var xoffset = 50;
        var yoffset = 10;
        // draw compressor
        var compx = 400*xscale+xoffset;
        var compy = 85*yscale+yoffset;
        drawCompressor(c, compx, compy);
        // draw Evaporator
        var evax = 100*xscale+xoffset;
        var evay = 250*yscale+yoffset;
        drawHeatExchanger2(c, evax, evay);
        // draw condenser
        var cdx = 620*xscale+xoffset;
        var cdy = 250*yscale+yoffset;
        drawHeatExchanger1(c, cdx, cdy);
        // draw expansion valve
        var evx = 400*xscale+xoffset;
        var evy = 600*yscale+yoffset;
        drawValve(c, evx, evy);
        draw_thingy(c);
        drawNames(c);
        line1(c, evax+55,evay,compx-40,compy,0);
        line2(c, compx+40, compy, cdx+55, cdy, 0);
        line3(c, cdx+55, cdy+180, evx+30 ,evy,0);
        line4(c, evx-30, evy, evax+55, evay+180, 0);
        drawRoundedRect(c, 8, 8, 160, 90, 15);
        // enter data into buttons
        if (this.type === 0) {
            this.update_buttons();
        }
        else if (this.type === 1) {
            this.update_viz_buttons();
        }
    }

    update_buttons(){
        document.getElementById("p_button_1").textContent=this.Temperatures.wq_out+"°C";
        document.getElementById("p_button_2").textContent=this.Temperatures.ww_out+"°C";
        document.getElementById("p_button_3").textContent=this.Temperatures.conn1+"°C";
        document.getElementById("p_button_4").textContent=this.Temperatures.conn2+"°C";
        document.getElementById("p_button_5").textContent=this.Temperatures.conn3+"°C";
        document.getElementById("p_button_6").textContent=this.Temperatures.conn5+"°C";
        document.getElementById("p_button_7").textContent=this.Pressures.conn1+"bar";
        document.getElementById("p_button_8").textContent=this.Pressures.conn2+"bar";
        document.getElementById("p_button_9").textContent=this.Pressures.conn3+"bar";
        document.getElementById("p_button_10").textContent=this.Pressures.conn5+"bar";
        document.getElementById("p_button_11").textContent=this.Powers.condenser+" W";
        document.getElementById("p_button_12").textContent=this.Powers.evaporator+" W";
        document.getElementById("para_button_1").textContent=this.Temperatures.wq_in+"°C";
        document.getElementById("para_button_2").textContent=this.Temperatures.ww_in+"°C";
        document.getElementById("para_button_3").textContent=this.Powers.compressor+" W";
        document.getElementById("para_button_4").textContent=this.MassFlows.wq+" l/min";
        document.getElementById("para_button_5").textContent=this.MassFlows.ww+" l/min";
        document.getElementById("para_button_6").textContent=this.Powers.comp_eff;
        document.getElementById("para_button_7").textContent=this.overheat+"°K";
    }
    update_viz_buttons() {
        document.getElementById("viz_button_1").textContent = this.Temperatures.wq_out + "°C";
        document.getElementById("viz_button_2").textContent = this.Temperatures.ww_out + "°C";
        document.getElementById("viz_button_3").textContent = this.Temperatures.conn1 + "°C";
        document.getElementById("viz_button_4").textContent = this.Temperatures.conn2 + "°C";
        document.getElementById("viz_button_5").textContent = this.Temperatures.conn3 + "°C";
        document.getElementById("viz_button_6").textContent = this.Temperatures.conn5 + "°C";
        document.getElementById("viz_button_7").textContent = this.Pressures.conn1 + "bar";
        document.getElementById("viz_button_8").textContent = this.Pressures.conn2 + "bar";
        document.getElementById("viz_button_9").textContent = this.Pressures.conn3 + "bar";
        document.getElementById("viz_button_10").textContent = this.Pressures.conn5 + "bar";
        document.getElementById("viz_button_11").textContent = this.Powers.condenser + " W";
        document.getElementById("viz_button_12").textContent = this.Powers.evaporator + " W";
        document.getElementById("viz_button_13").textContent = this.Temperatures.wq_in + "°C";
        document.getElementById("viz_button_14").textContent = this.Temperatures.ww_in + "°C";
        document.getElementById("viz_button_15").textContent = this.Powers.compressor + " W";
        document.getElementById("viz_button_16").textContent = this.MassFlows.wq + " l/min";
        document.getElementById("viz_button_17").textContent = this.MassFlows.ww + " l/min";
        document.getElementById("viz_button_18").textContent = this.overheat + "°K";
        document.getElementById("viz_button_19").textContent = this.Powers.comp_eff;
    }
}

// --------------------------------------------------------------------------
// ----------------------- WEBSITE THINGS -----------------------------------
// --------------------------------------------------------------------------

// ------ CANVAS GAUGES ------
let copgaugereal = new RadialGauge({
    renderTo: 'OTGaugeReal',
    width: 250,
    height: 200,
    units: "",
    minValue: 0,
    startAngle: 90,
    ticksAngle: 180,
    valueBox: false,
    maxValue: 12,
    majorTicks: ["0","2","4","6","8","10", "12"],
    minorTicks: 6,
    strokeTicks: true,
    // Highlights sind willkürlich gewählt
    highlights: [{"from": 4.5,"to": 12,"color": "rgba(10, 180, 50, .55)"}, {"from": 1.5,"to": 4.5,"color": "rgba(219, 191, 33, 0.59)"}, {"from": 0,"to": 1.5,"color": "rgba(180, 21, 10, 0.55)"}],
    colorPlate: "#fff",
    borderShadowWidth: 0,
    borders: false,
    needleType: "arrow",
    needleWidth: 2,
    needleCircleSize: 7,
    needleCircleOuter: true,
    needleCircleInner: false,
    animationDuration: 1500,
    animationRule: "linear"
}).draw();
let copgaugesim = new RadialGauge({
    renderTo: 'OTGaugeSim',
    width: 250,
    height: 200,
    units: "",
    minValue: 0,
    startAngle: 90,
    ticksAngle: 180,
    valueBox: false,
    maxValue: 12,
    majorTicks: ["0","2","4","6","8","10", "12"],
    minorTicks: 6,
    strokeTicks: true,
    // Highlights sind willkürlich gewählt
    highlights: [{"from": 4.5,"to": 12,"color": "rgba(10, 180, 50, .55)"}, {"from": 1.5,"to": 4.5,"color": "rgba(219, 191, 33, 0.59)"}, {"from": 0,"to": 1.5,"color": "rgba(180, 21, 10, 0.55)"}],
    colorPlate: "#fff",
    borderShadowWidth: 0,
    borders: false,
    needleType: "arrow",
    needleWidth: 2,
    needleCircleSize: 7,
    needleCircleOuter: true,
    needleCircleInner: false,
    animationDuration: 1500,
    animationRule: "linear"
}).draw();
// TEST ANIMATION:
// setInterval(() => {
//   gauge.value = Math.random() * -20 + 20;
// }, 100);
copgaugereal.value = 6.25;
copgaugesim.value = 6.25;

// global variables of both heatpumps and my_session_id
const NUMBER_OF_PARAMETERS = 7;
var superheat_control_value = 7;
var my_session_id = "test";
var my_session_id_get_in_progress = 0;
var attempted_to_get_my_session_id = 0;
// console.log(my_session_id);
const realpump = new HeatpumpVis(1);
const simpump = new HeatpumpVis(0);


// function runs when .js file is loaded by webpage
// function sets my_session_id if none is loaded
(async () => {
    for (var i=1;i<=NUMBER_OF_PARAMETERS;i++) {
        var el_id = "para_in_" + i;
        document.getElementById(el_id).value = -22;
    }
    try {
        var local = localStorage.getItem("my_session_id");
        if (local !== null && local !== "test") {
            if (await check_session_id(local)) {
                console.log("session id loaded from localStorage")
                my_session_id = local;
            }
            else  {
                await get_my_session_id();
            }
            document.getElementById("r_b").textContent = `Session ID: ${my_session_id}`;
        }
        else {
            await get_my_session_id();
            console.log("getting a new session id");
            document.getElementById("r_b").textContent = `Session ID: ${my_session_id}`;
        } 
    } catch (error) {
        console.error("Session init failed:", error);
    }
})();

async function check_session_id(current_id) {
    var url = "http://127.0.0.1:8000/checkID/" + current_id;
    let response = await fetch(url, {method:"GET", headers:{"Content-type": "application/json; charset=UTF-8"}});
    if (!response.ok) {
        throw_error("ID not ok. Something went wrong!");
        my_session_id_get_in_progress = 0;
        return;
    }
    const json_resp = await response.json();
    if (json_resp.message === "OK") {
        return true;
    }
    else if (json_resp.message === "NOT_OK") {
        return false;
    }
    else {
        console.log("session id verification error");
        return false;
    }
}

// get session id to communicate with FastAPI
async function get_my_session_id(){
    if (my_session_id_get_in_progress === 1) {return;}
    my_session_id_get_in_progress = 1;
    // console.log("session: ", my_session_id);
    
    if (my_session_id === "test" || my_session_id === null) {    // if my_session_id = test get new my_session_id, check and set it
        let response = await fetch("http://127.0.0.1:8000/session_start", {method:"GET",headers:{"Content-type":"application/json; charset=UTF-8"}});
        if (!response.ok) {
            throw_error("ID not ok. Something went wrong!");
            my_session_id_get_in_progress = 0;
            return;
        }
        const json_resp  = await response.json();
        if (json_resp.my_session_id === 0 || json_resp.error) {
            throw_error("Already too many people simulating. Please try again later");
            my_session_id_get_in_progress = 0;
            return;
        }
        localStorage.setItem("my_session_id", json_resp.my_session_id);
        my_session_id = json_resp.my_session_id;
        document.getElementsByClassName("refreshbt")[0].textContent="Session ID: " + my_session_id;
        console.log("Successfully initialized session:", my_session_id);
    }
    else {
        console.log("session already started, with id: " + my_session_id);
    }
    my_session_id_get_in_progress = 0;
}

async function plot_request() {
    var url = "http://127.0.0.1:8000/build_plot/" + my_session_id;
    let response = await fetch(url, {method:"GET", headers:{"Content-type": "application/json; charset=UTF-8"}});
    let json_resp = await response.json();
    console.log(json_resp);
    window.open("plots/thermocycle.html", "Thermocycle Plot", "width=1000, height=600");
}

// Website scaling maybe later (min width 1280px)
// function scale(window) {
    // var width = window.screen.width;
    // if (width =< 1300) {
// 
    // }
// }

function session_refresh(event) {
    if (event) event.preventDefault();
    var url = "http://127.0.0.1:8000/session_end/" + my_session_id;
    fetch(url, {method:"GET", headers:{"Content-type": "application/json; charset=UTF-8"}});
    console.log("ended session with id:" + my_session_id);
    my_session_id = "test";
    // get new my_session_id from api
    get_my_session_id();
}

// function debug_python(){
//     var url = "http://127.0.0.1:8000/print_list";
//     fetch(url, {method:"GET", headers:{"Content-type": "application/json; charset=UTF-8"}});
// }

/*window.onbeforeunload = function () {
    var url = "http://127.0.0.1:8000/session_end/" + my_session_id;
    fetch(url, {method:"GET", headers:{"Content-type": "application/json; charset=UTF-8"}});
    console.log("ended session on unload with id: " + my_session_id);
    localStorage.removeItem("my_session_id");
}*/

function throw_error(msg) {
    document.getElementsByClassName("errorfield")[0].textContent=msg;
    document.getElementsByClassName("errorfield")[0].style="background-color: rgb(255, 185, 185); color: rgb(110, 20, 20);";
}   

function reset_error() {
    document.getElementsByClassName("errorfield")[0].textContent="No errors";
    document.getElementsByClassName("errorfield")[0].style="background-color: #cbffbb; color: #79c475;";
}   
 
// copied from the w3schools example for tabs and only slightly modified
function openTab(evt, tabName) {
    // Declare all variables
    var i, tabcontent, tablinks;
  
    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
  
    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
  
    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

function  close_inputs() { // closes all input fields open on the simulation canvas
    for (let i=1;i<=NUMBER_OF_PARAMETERS;i++) {
        var newid = "para_in_" + i;
        document.getElementById(newid).value = -22;
        replace_input(i);
    }
}

function run_simulation() {
    // function runs python sim and updates with new results
    // function runs only after calculate_button is pressed
    var isempty = true;
    reset_error();
    // check inputs and generate json string
    let jsonstring = "{";
    for (let i=1; i <= NUMBER_OF_PARAMETERS; i++) {
        let id = "para_in_" + i;
        let element = document.getElementById(id);
        if (element.value !== -22) {
            isempty = false;
        }
        if (element) {
            let inputVal = Number(element.value); // Convert to number
    
            if (!isNaN(inputVal)) {
                if (id === 'para_in_7') {
                    if (inputVal !== -22) {
                        superheat_control_value = inputVal;
                    }
                    jsonstring += `"para_in_7":${superheat_control_value},`;
                    continue;
                }
                jsonstring += `"${id}":${inputVal},`;
                
            }
            else {
                throw_error("One or more inputs are NaN! Aborting...");
                return;
            }
        }
    }
    if (isempty) {
        jsonstring = 1;
    }
    if (jsonstring.endsWith(",")) {
        jsonstring = jsonstring.slice(0, -1);
    }
    jsonstring += "}";
    // run simuilation with given parameters
    console.log("run_simulation json; "+jsonstring);
    simpump.update_data(jsonstring);
    close_inputs();
    var cop = simpump.Powers.condenser/simpump.Powers.compressor;
    cop = Math.round(cop*100) / 100
    document.getElementById("cop_value_sim").textContent=cop;
    copgaugesim.value = cop;
}


// --------------------------------------------------------------------------
// ------------------ BUTTON FUNCTIONS -------------------------------------
// --------------------------------------------------------------------------

function buttonclick(element) {
    element.classList.add("button-clicked");
    setTimeout(() => {
        element.classList.remove("button-clicked");
    }, 50);
    if (element.id === "plot_button") {
        plot_request();
    }
     else if (element.id === "calculate_button"){
        run_simulation();
    }
    else if (element.id === "debug_button"){
        simpump.update_data(20);
    }
    else if (element.id === "update_button"){
        realpump.update_data(1);
    }
    else {
        //pass0
    }
    // if (element.id === "something_else") {
        // do something else
    // }
}

let tooltip;
function showtool(element, text) {
    tooltip = document.createElement("div");
    tooltip.className = "tooltip";
    tooltip.innerText = text;
    document.body.appendChild(tooltip);

    const rect = element.getBoundingClientRect();
    tooltip.style.top = (window.scrollY + rect.top - tooltip.offsetHeight - 8) + "px";
    tooltip.style.left = (window.scrollX + rect.right + 8) + "px";
}

function replace_button(number) {
    // switch button and entry field visibility
    var i_id = "para_in_" + number;
    var b_id = "para_button_" + number;
    document.getElementById(b_id).style="display:none;"
    document.getElementById(i_id).style="display:block;"
}

function replace_input(number) {
    // switch entry field and button visibility
    var i_id = "para_in_" + number;
    var b_id = "para_button_" + number;
    document.getElementById(i_id).style="display:none;"
    document.getElementById(b_id).style="display:block;"
}

function hidetool() {
    if (tooltip) {
    tooltip.remove();
    tooltip = null;
    }
}

function brighten(element) {
    element.style.filter = "brightness(1.2)";
}

function unbrighten(element) {
    element.style.filter = "brightness(1)";
}

// --------------------------------------------------------------------------
// ------------------------- DOM THINGS -------------------------------------
// --------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {             // draw the heatpumps and gauges
    var HPR = document.getElementById("HeatPumpReal");
    if (HPR) {  
        realpump.spec_canvas(HPR);
        realpump.drawHeatpump();
    }
    var HPS = document.getElementById("HeatPumpSim");
    if (HPS) {
        simpump.spec_canvas(HPS);
        simpump.drawHeatpump();
    }
 
});  

window.addEventListener('load', () => {
    openTab(event, 'digital');
});

// --------------------------------------------------------------------------
// ------------------ DRAWING FUNCTIONS -------------------------------------
// --------------------------------------------------------------------------

var basecolor = "rgb(32, 32, 32)";
var textcolor = "rgb(75, 75, 75)";

function drawNames(c) {
    c.fillStyle = textcolor;
    c.strokeStyle = textcolor;
    c.font = "25px ubuntu";
    c.fillText("Verdichter", 400, 40);
    c.fillText("Expansionsventil", 360, 580);
    c.fillText("Verflüssiger", 760, 230);
    c.fillText("Verdampfer", 40, 230);
    c.fillText("Überhitzung", 20, 40);
    /*
    var [r,x,y,width,height] = [5,385,210,165,80];
    c.lineWidth = 2;
    c.beginPath();
    c.moveTo(x + r, y);
    c.lineTo(x + width - r, y);
    c.quadraticCurveTo(x + width, y, x + width, y + r);
    c.lineTo(x + width, y + height - r);
    c.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
    c.lineTo(x + r, y + height);
    c.quadraticCurveTo(x, y + height, x, y + height - r);
    c.lineTo(x, y + r);
    c.quadraticCurveTo(x, y, x + r, y);
    c.stroke();
    */
}

function draw_thingy(c) {
    // Draw the circular arrow in the middle
    var dia = 60;
    c.strokeStyle = "rgb(94, 94, 94)";
    c.beginPath();
    var cx = 470;
    var cy = 345;
    c.arc(cx, cy, dia, 0.5, 0 * Math.PI); // radius = 50 for 100px diameter
    //c.stroke();
    // draw the center thingy
    //c.beginPath();
    //c.moveTo(ax+50, ay);
    c.lineTo(cx+dia+7, cy-15   );
    //c.moveTo(ax+50, ay);
    //c.lineTo(ax+50+5, ay-5);
    c.stroke();
}

function drawPoint(c, d, cX, cY) {
    if (d=="rr"){
        c.lineTo(cX-12, cY-6);
        c.lineTo(cX-12, cY+6);
        c.lineTo(cX, cY);
    }
    if (d=="rl"){
        c.lineTo(cX, cY-6);
        c.lineTo(cX-12, cY);
        c.lineTo(cX, cY+6);
        c.lineTo(cX, cY);
    }
    if (d=="ll"){
        c.lineTo(cX+12, cY-6);
        c.lineTo(cX+12, cY+6);
        c.lineTo(cX, cY);
    }
    if (d=="lr"){
        c.lineTo(cX, cY-6);
        c.lineTo(cX+12, cY);
        c.lineTo(cX, cY+6)
        c.lineTo(cX, cY);
    }
    if (d=="uu"){
        c.lineTo(cX-6, cY-12);
        c.lineTo(cX+6, cY-12);
        c.lineTo(cX, cY);
    }
    if (d=="ud"){
        c.lineTo(cX-6, cY);
        c.lineTo(cX, cY-12);
        c.lineTo(cX+6, cY);
        c.lineTo(cX, cY);
    }
    if (d=="dd"){
        c.lineTo(cX-6, cY+12);
        c.lineTo(cX+6, cY+12);
        c.lineTo(cX, cY);
    }
    if (d=="du"){
        c.lineTo(cX-6, cY);
        c.lineTo(cX, cY+12);
        c.lineTo(cX+6, cY);
        c.lineTo(cX, cY);
    }
}

function drawCompressor(c, x, y) {
    c.strokeStyle = basecolor;
    c.lineWidth = 4;
    c.beginPath();
    c.arc(x, y, 40, 0, 2 * Math.PI);
    c.stroke();
    c.beginPath();
    c.moveTo(x-30, y-25);
    c.lineTo(x+35, y-17);
    c.stroke();
    c.beginPath();
    c.moveTo(x-30, y+25);
    c.lineTo(x+35, y+17);
    c.stroke();
}

function drawHeatExchanger1(c, x, y){
    c.strokeStyle = basecolor;
    c.lineWidth = 4;
    c.beginPath();
    c.rect(x,y, 110, 180);
    c.stroke();
    c.beginPath();
    var grad = c.createLinearGradient(x , y + 40, x , y + 140);
    grad.addColorStop(1,"blue");
    grad.addColorStop(0,"red");
    c.strokeStyle = grad;
    c.lineWidth = 4;
    c.moveTo(x+150, y+30);
    drawPoint(c, "lr",x+150, y+30);
    c.lineTo(x+30, y+30);
    c.lineTo(x+90, y+90);
    c.lineTo(x+30, y+150);
    c.lineTo(x+150, y+150);
    drawPoint(c, "ll", x+150, y+150);
    c.stroke();
}

function drawHeatExchanger2(c, x, y){
    c.fillStyle= basecolor;
    c.lineWidth = 4;
    c.beginPath();
    c.rect(x,y, 110, 180);
    c.stroke();
    c.beginPath();
    var grad = c.createLinearGradient(x , y + 10, x , y + 160);
    grad.addColorStop(0,"blue");
    grad.addColorStop(1,"red");
    c.strokeStyle = grad;
    c.lineWidth = 4;
    c.moveTo(x-40, y+30);
    drawPoint(c, "rl", x-40, y+30);
    c.lineTo(x+80, y+30);
    c.lineTo(x+20, y+90);
    c.lineTo(x+80, y+150);
    c.lineTo(x-40, y+150);
    drawPoint(c, "rr", x-40, y+150);
    c.stroke();
}


function drawValve(c, x, y) {
    c.strokeStyle= basecolor;
    c.lineWidth = 4;
    c.beginPath();
    c.moveTo(x-30, y-15);
    c.lineTo(x+30, y+15);
    c.lineTo(x+30, y-15);
    c.lineTo(x-30, y+15);
    c.lineTo(x-30, y-15);
    c.lineTo(x+30, y+15);
    c.stroke();
}

function line1(c, x1, y1, x2, y2, r) {
    c.strokeStyle= basecolor;
    c.lineWidth = 4;
    c.beginPath();
    c.moveTo(x1,y1);
    c.bezierCurveTo(x1, y2+r, x1+r, y2, x2, y2);
    c.stroke();
}

function line2(c, x1, y1, x2, y2, r) {
    c.strokeStyle= basecolor;
    c.lineWidth = 4;
    c.beginPath();
    c.moveTo(x1,y1);
    c.bezierCurveTo(x2-r, y1, x2, y1+r, x2, y2);
    c.stroke();
}

function line3(c, x1, y1, x2, y2, r) {
    c.strokeStyle= basecolor;
    c.lineWidth = 4;
    c.beginPath();
    c.moveTo(x1,y1);
    c.bezierCurveTo(x1, y2-r, x1-r, y2, x2, y2);
    c.stroke();
}

function line4(c, x1, y1, x2, y2, r) {
    c.strokeStyle= basecolor;
    c.lineWidth = 4;
    c.beginPath();
    c.moveTo(x1,y1);
    c.bezierCurveTo(x2+r, y1, x2, y1-r, x2, y2);
    c.stroke();
}

function drawRoundedRect(c, x, y, width, height, radius) {
    radius = Math.min(radius, width/2, height/2);
    c.strokeStyle = "rgb(155,155,155)";
    c.beginPath();
    c.moveTo(x + radius, y);
    c.lineTo(x + width - radius, y);
    c.arcTo(x + width, y, x + width, y + radius, radius);
    c.lineTo(x + width, y + height - radius);
    c.arcTo(x + width, y + height, x + width - radius, y + height, radius);
    c.lineTo(x + radius, y + height);
    c.arcTo(x, y + height, x, y + height - radius, radius);
    c.lineTo(x, y + radius);
    c.arcTo(x, y, x + radius, y, radius);
    c.stroke();
}
