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
        this.Powers = {evaporator:4000, condenser:5000, superheater:200, compressor:800};
        this.MassFlows = {conn0:4.02, conn1:4.02, conn2:4.02, conn03:4.02, conn4:4.02, conn5:4.02, wq:0.475, ww:0.265};
        // Select Simulation or Real Thing with 0 or 1
        this.type = type;
        this.overheat = 7;
    }

    spec_canvas(canvas) {
        this.canvas = canvas;
    }

    update_data(json) {
        // this function updates Heat pump data by running a python script and reading new data
        
        if (this.type == 0) {
            // update by running python script
            // if jsonstring === 1 then no input specified -> run last simulation
            // if jsonstring === 20 then run design simulation
            if (jsonstring === 1) {
                // run simulation with last json string
            }
            else if (jsonstring === 20) {
                // run design simulation
            }
            else {
                // run simulation with json as inputs
            }
        }
        else if (this.type == 1) {
            // update data from mqtt
        }
        else  {
            // give an error: Type not supported; choose Simulation (0) or Real System (1)
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
        //this.redrawParams(c, xoffset, yoffset);
        // enter data into buttons;
        document.getElementById("para_button_1").textContent=this.Temperatures.wq_in+"°C";
        document.getElementById("para_button_2").textContent=this.Temperatures.wq_out+"°C";
        document.getElementById("para_button_3").textContent=this.Temperatures.ww_in+"°C";
        document.getElementById("para_button_4").textContent=this.Temperatures.ww_out+"°C";
        document.getElementById("para_button_5").textContent=this.Temperatures.conn1+"°C";
        document.getElementById("para_button_6").textContent=this.Temperatures.conn2+"°C";
        document.getElementById("para_button_7").textContent=this.Temperatures.conn3+"°C";
        document.getElementById("para_button_8").textContent=this.Temperatures.conn5+"°C";
        document.getElementById("para_button_9").textContent=this.Pressures.conn1+"bar";
        document.getElementById("para_button_10").textContent=this.Pressures.conn2+"bar";
        document.getElementById("para_button_11").textContent=this.Pressures.conn3+"bar";
        document.getElementById("para_button_12").textContent=this.Pressures.conn5+"bar";
        document.getElementById("para_button_13").textContent=this.Powers.compressor+" W";
        document.getElementById("para_button_14").textContent=this.Powers.condenser+" W";
        document.getElementById("para_button_15").textContent=this.Powers.evaporator+" W";
        document.getElementById("para_button_16").textContent=this.MassFlows.wq+"kg/s";
        document.getElementById("para_button_17").textContent=this.MassFlows.ww+"kg/s";
        document.getElementById("para_button_18").textContent=this.overheat+"°K";
    }
}

// global variable of both heatpumps
const realpump = new HeatpumpVis(1);
const simpump = new HeatpumpVis(0);
let copgaugereal;
let copgaugesim;


// --------------------------------------------------------------------------
// ----------------------- WEBSITE THINGS -----------------------------------
// --------------------------------------------------------------------------


// Website scaling maybe later (min width 1280px)
// function scale(window) {
    // var width = window.screen.width;
    // if (width =< 1300) {
// 
    // }
// }

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

function  close_inputs() {
    for (let i=1;i<=18;i++) {
        var newid = "para_in_" + i;
        document.getElementById(newid).value = "";
        replace_input(i);
    }
}

function run_simulation() {
    // function runs python sim and updates with new results
    reset_error();
    close_inputs();
    // check inputs and generate json string
    let jsonstring = "{";
    for (let i = 1; i <= 18; i++) {
        let id = "para_in_" + i;
        let element = document.getElementById(id);
        
        if (element) {
            let inputVal = Number(element.value); // Convert to number
    
            if (!isNaN(inputVal)) {
                jsonstring += `"${id}":${inputVal},`;
            }
            else {
                throw_error("One or more inputs are NaN! Aborting...");
                return;
            }
        }
    }
    if (jsonstring.endsWith(",")) {
        jsonstring = jsonstring.slice(0, -1);
    }
    jsonstring += "}";
    // check if json empty
    if (jsonstring === "{}") {
        jsonstring = "1"
    }
    // run simuilation with given parameters
    simpump.update_data(jsonstring);

    var cop = simpump.Powers.condenser/simpump.Powers.compressor;
    document.getElementById("cop_value_sim").textContent=cop;
    copgaugesim.value = cop;
}
  
window.addEventListener('load', () => {
    openTab(event, 'digital');
});



// --------------------------------------------------------------------------
// ------------------------- DOM THINGS -------------------------------------
// --------------------------------------------------------------------------


// Main Function ?!
document.addEventListener("DOMContentLoaded", function () {
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
    // ------ CANVAS GAUGES ------
    copgaugereal = new RadialGauge({
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
        highlights: [{"from": 3,"to": 12,"color": "rgba(10, 180, 50, .55)"}],
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
    copgaugesim = new RadialGauge({
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
        highlights: [{"from": 3,"to": 12,"color": "rgba(10, 180, 50, .55)"}],
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
});




// --------------------------------------------------------------------------
// ------------------ BUTTON FUNCTIONS -------------------------------------
// --------------------------------------------------------------------------

function buttonclick(element) {
    element.classList.add("button-clicked");
    setTimeout(() => {
        element.classList.remove("button-clicked");
    }, 50);
    if (element.id === "plot_button") {
        window.open("plots/thermocycle.html", "Thermocycle Plot", "width=1000, height=600")
    }
     else if (element.id === "calculate_button"){
        run_simulation();
    }
    else {
        // pass
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
    // Draw the circular path
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
