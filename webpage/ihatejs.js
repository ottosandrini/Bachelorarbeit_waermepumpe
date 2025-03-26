// copied from the w3schools example and only slightly modified
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
  
  window.addEventListener('load', () => {
    openTab(event, 'real');   
  });

document.addEventListener("DOMContentLoaded", function () {
  var gauge = new RadialGauge({
    renderTo: 'OTGaugeReal',
    width: 250,
    height: 250,
    units: "°C",
    minValue: 0,
    startAngle: 90,
    ticksAngle: 180,
    valueBox: false,
    maxValue: 20,
    majorTicks: [
        "0",
        "5",
        "10",
        "15",
        "20"
    ],
    minorTicks: 4,
    strokeTicks: true,
    highlights: [
        {
            "from": 0,
            "to": 8,
            "color": "rgba(200, 50, 50, .75)"
        }
    ],
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
  }
).draw();

  var gauge = new RadialGauge({
    renderTo: 'OTGaugeSim',
    width: 250,
    height: 250,
    units: "°C",
    minValue: 0,
    startAngle: 90,
    ticksAngle: 180,
    valueBox: false,
    maxValue: 20,
    majorTicks: [
        "0",
        "5",
        "10",
        "15",
        "20"
    ],
    minorTicks: 4,
    strokeTicks: true,
    highlights: [
        {
            "from": 0,
            "to": 8,
            "color": "rgba(200, 50, 50, .75)"
        }
    ],
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
  }
  ).draw();
// TEST ANIMATION:
// setInterval(() => {
//   gauge.value = Math.random() * -20 + 20;
// }, 100);

});

