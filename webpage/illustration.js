const Temperatures = {conn0:10, conn1:60, conn2:55, conn03:3, conn4:3, conn5:10}
const Pressures = {conn0:8, conn1:22, conn2:22, conn03:8, conn4:8, conn5:8}
const Enthalpies = {conn0:430, conn1:450, conn2:200, conn03:200, conn4:400, conn5:430}
const Powers = {evaporator:4000, condenser:5000, superheater:200, compressor:800}
const MassFlows = {conn0:4.02, conn1:4.02, conn2:4.02, conn03:4.02, conn4:4.02, conn5:4.02}

const HPData = {temp:Temperatures, pressure:Pressures, enthalpy:Enthalpies, power:Powers, massflow:MassFlows}

class HeatpumpVis {
    constructor(data, type, canvas) {
        this.canvas = canvas;
        this.Temperatures = data.temp;
        this.Pressures = data.pressure;
        this.Enthalpies = data.enthalpy;
        this.Powers = data.power;
        this.MassFlows = data.massflow;
        this.type = type;                   // Select Simulation or Real Thing with 0 or 1
    }

    update_data() {
        // update Heat pump data here by running python script and reading new data
        if (this.type == 0) {
            // update by running python script
        }
        else if (this.type == 1) {
            // update data from mqtt
        }
        else  {
            // give an error: Type not supported; choose Simulation (0) or Real System (1)
        }
    }

    redrawParams(c, xoffset, yoffset){    // draw over old parameters, might need to white out old ones
    c.font = "25px comic";
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

    drawHeatpump(){                            // draws the Heatpump at first start
    var c = this.canvas.getContext("2d");
    var xoffset = 50;
    var yoffset = 10;
    // draw compressor
    var compx = 450+xoffset;
    var compy = 45+yoffset;
    drawCompressor(c, compx, compy);
    // draw Evaporator
    var evax = 100+xoffset;
    var evay = 250+yoffset;
    drawHeatExchanger2(c, evax, evay);
    // draw condenser
    var cdx = 700+xoffset;
    var cdy = 250+yoffset;
    drawHeatExchanger1(c, cdx, cdy);
    // draw expansion valve
    var evx = 450+xoffset;
    var evy = 650+yoffset;
    drawValve(c, evx, evy);
    line1(c, evax+55,evay,compx-40,compy,0);
    line2(c, compx+40, compy, cdx+55, cdy, 0);
    line3(c, cdx+55, cdy+180, evx+30 ,evy,0);
    line4(c, evx-30, evy, evax+55, evay+180, 0);
    this.redrawParams(c, xoffset, yoffset);
    }

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
    c.strokeStyle = "black";
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
    c.strokeStyle = "black";
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
    c.moveTo(x+150, y+50);
    drawPoint(c, "lr",x+150, y+50);
    c.lineTo(x+30, y+50);
    c.lineTo(x+90, y+90);
    c.lineTo(x+30, y+130);
    c.lineTo(x+150, y+130);
    drawPoint(c, "ll", x+150, y+130);
    c.stroke();
}

function drawHeatExchanger2(c, x, y){
    c.strokeStyle = "black";
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
    c.moveTo(x-40, y+50);
    drawPoint(c, "rl", x-40, y+50);
    c.lineTo(x+80, y+50);
    c.lineTo(x+20, y+90);
    c.lineTo(x+80, y+130);
    c.lineTo(x-40, y+130);
    drawPoint(c, "rr", x-40, y+130);
    c.stroke();
}


function drawValve(c, x, y) {
    c.strokeStyle = "black";
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
    c.strokeStyle = "black";
    c.lineWidth = 4;
    c.beginPath();
    c.moveTo(x1,y1);
    c.bezierCurveTo(x1, y2+r, x1+r, y2, x2, y2);
    c.stroke();
}

function line2(c, x1, y1, x2, y2, r) {
    c.strokeStyle = "black";
    c.lineWidth = 4;
    c.beginPath();
    c.moveTo(x1,y1);
    c.bezierCurveTo(x2-r, y1, x2, y1+r, x2, y2);
    c.stroke();
}

function line3(c, x1, y1, x2, y2, r) {
    c.strokeStyle = "black";
    c.lineWidth = 4;
    c.beginPath();
    c.moveTo(x1,y1);
    c.bezierCurveTo(x1, y2-r, x1-r, y2, x2, y2);
    c.stroke();
}

function line4(c, x1, y1, x2, y2, r) {
    c.strokeStyle = "black";
    c.lineWidth = 4;
    c.beginPath();
    c.moveTo(x1,y1);
    c.bezierCurveTo(x2+r, y1, x2, y1-r, x2, y2);
    c.stroke();
}

// Main Function ?!
document.addEventListener("DOMContentLoaded", function () {
    var HPR = document.getElementById("HeatPumpReal");
    if (HPR) {  
        const realpump = new HeatpumpVis(HPData, 1, HPR);
        realpump.drawHeatpump();
    }
    var HPS = document.getElementById("HeatPumpSim");
    if (HPS) {
        const simpump = new HeatpumpVis(HPData, 0, HPS);
        simpump.drawHeatpump();
    }
});