"use strict";

var local_uri_prefix = "";
if (typeof(KISMET_URI_PREFIX) !== 'undefined')
    local_uri_prefix = KISMET_URI_PREFIX;

// Add a generic pane, defaults to south tab pane
kismet_ui_tabpane.AddTab({
    id: 'atak-companion',
    tabTitle: 'ATAK Companion',
    expandable: false,
    createCallback: function(div) {
        $(document).ready(function () {
	$(div).append(`
<div>

<style>

:disabled {
  opacity: 0.5;
  pointer-events: none;
}

select {
  background-color: black;
  color: white;
  font-size: 12px;
  border-radius: 2px;
  border: 1px solid #ccc;
  padding: 10px;
  width: 200px;
  cursor: pointer;
}

input[type=file] input {
  opacity: 0;
  width: 0;
  height: 0;
}

input[type=file] {
  background-color: black;
  color: white;
  border: none;
  border-radius: 2px;
  position: relative;
  font-size: 12px;
  padding: 2px;
  width: 180px;
  text-align: center;
  transition-duration: 0.2s;
  text-decoration: none;
  overflow: hidden;
  cursor: pointer;
}

input[type=file]:after {
  content: "";
  background: #f1f1f1;
  display: block;
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%; 
  opacity: 0;
  transition: all 0.4s;
}

input[type=file]:active:after {
  padding: 0;
  margin: 0;
  opacity: 1;
  transition: 0s
}


.enableSwitch {
  position: relative;
  display: inline-block;
  width: 36px;
  height: 16px;
  margin: 4px
}

.enableSwitch input { 
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  -webkit-transition: .4s;
  transition: .4s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 10px;
  width: 10px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  -webkit-transition: .4s;
  transition: .4s;
}

input:checked + .slider {
  background-color: MediumSeaGreen;
}

input:focus + .slider {
  box-shadow: 0 0 1px MediumSeaGreen;
}

input:checked + .slider:before {
  -webkit-transform: translateX(20px);
  -ms-transform: translateX(20px);
  transform: translateX(20px);
}

button {
  background-color: white;
  color: black;
  border: 2px solid MediumSeaGreen;
  border-radius: 2px;
  position: relative;
  font-size: 12px;
  padding: 2px;
  width: 60px;
  text-align: center;
  transition-duration: 0.4s;
  text-decoration: none;
  overflow: hidden;
  cursor: pointer;
}

.submitButton {
  background-color: MediumSeaGreen;
  color: white;
  border: none;
  border-radius: 2px;
  position: relative;
  font-size: 12px;
  padding: 4px;
  width: 100px;
  text-align: center;
  transition-duration: 0.4s;
  text-decoration: none;
  overflow: hidden;
  cursor: pointer;
}

.submitButton:after, button:after {
  content: "";
  background: #f1f1f1;
  display: block;
  position: absolute;
  padding-top: 300%;
  padding-left: 350%;
  margin-left: -20px !important;
  margin-top: -120%;
  opacity: 0;
  transition: all 0.8s
}

.submitButton:active:after, button:active:after {
  padding: 0;
  margin: 0;
  opacity: 1;
  transition: 0s
}


.caretDown {
  fa fa-chevron-circle-right; 
}

.dropdown-btn {
  text-decoration: none;
  display: block;
  border: 1px solid white;
  cursor: pointer;
  outline: none;
}

.dropdown-container {
  display: none;
}

.show {display: block;}

</style>

<div style="border:1px solid white" id="all-fields">

<div style="padding:5px">
<fieldset>
<legend onclick="initializeDrop()" id="initialize-legend" class="dropdown-btn" style="border 1px solid red">Initialize: <i id="initializeIcon" class="fa fa-chevron-circle-right"></i></legend>
<div id="initializeDrop" class="dropdown-container">
<span style="padding:10px"><label for="current-ip">Kismet IP/Hostname:</label><input type="text" id="current-ip" placeholder="192.168.0.100"><i id="current-ip-status" style="color:MediumSeaGreen;"></i></span>
<br><br><span style="padding:10px"><label for="current-user">Kismet User:</label><input type="text" id="current-user"><i id="current-user-status" style="color:MediumSeaGreen;"></i></span>
<br><br><span style="padding:10px"><label for="current-password">Kismet Password:</label><input type="password" id="current-password"><i id="current-password-status" style="color:MediumSeaGreen;"></i></span>
<br><br><span style="padding:10px"><button class="submitButton" id="initialize-submit" type="button"><b>Submit</b></button></span>
<br><br><span id="initialize-config"></span>
</div>
</fieldset>
</div>

<div style="padding:5px">
<fieldset>
<legend onclick="takserverDrop()" id="takserver-legend" class="dropdown-btn">TAKServer Config: <i id="takserverIcon" class="fa fa-chevron-circle-right"></i></legend>
<div id="takserverDrop" class="dropdown-container">
<span style="padding:10px"><label for="takserver-enable">Enable:</label><label class="enableSwitch"><input id="takserver-enable" type="checkbox"><span class="slider"></span></label></span>
<br><br><span style="padding:10px"><label for="takserver">IP/Hostname:</label><input type="text" id="takserver" placeholder="192.168.1.69" disabled="true"></span>
<form id="uploadForm" enctype="multipart/form-data">
<br><br><span style="padding:10px"><label for="user-cert">User Pem:</label><input type="file" id="user-cert" accept=".pem" name="user_pem" disabled="true"></span>
<br><br><span style="padding:10px"><label for="user-key">User Key:</label><input type="file" id="user-key" accept=".key" name="user_key" disabled="true"></span>
<br><br><span style="padding:10px"><label for="takserver-password">User Key Password:</label><input type="password" id="takserver-password" placeholder="atakatak" disabled="true"></span>
<br><br><span style="padding:10px"><label for="root-cert">CA Pem:</label><input type="file" id="root-cert" accept=".pem" name="ca_pem" disabled="true"></span>
<br><br><span style="padding:10px"><button class="submitButton disabled" id="takserver-submit" type="button" disabled=true><b>Submit</b></button></span>
</form>
<br><br><span id="takserver-config"></span>
</div>
</fieldset>
</div>

<div style="padding:5px">
<fieldset>
<legend onclick="multicastDrop()" id="multicast-legend" class="dropdown-btn">Multicast Config: <i id="multicastIcon" class="fa fa-chevron-circle-right"></i></legend>
<div id="multicastDrop" class="dropdown-container">
<span style="padding:10px"><label for="multicast-enable">Enable:</label><label class="enableSwitch"><input id="multicast-enable" type="checkbox"><span class="slider"></span></label></span>
<br><br><span style="padding:10px"><label for="multicast-select">Multicast Address:</label><select name="multicast-select" id="multicast-select" disabled="true">
<option value="default" selected>239.2.3.1:6969 (Default)</option><option value="sensor">239.5.5.55:7171 (Sensor)</option></select></span>
<br><br><span style="padding:10px"><label for="multicast-nic">Multicast NIC:</label><select name="multicast-nic" id="multicast-nic" disabled="true"></select></span>
<br><br><span style="padding:10px"><button class="submitButton disabled" id="multicast-submit" type="button" disabled=true><b>Submit</b></button><span id="multicast-status"></span></span>
<br><br><span id="multicast-config"></span>
</div>
</fieldset>
</div>

<div style="padding:5px">
<fieldset>
<legend onclick="alertsDrop()" id="alert-legend" class="dropdown-btn">Alerts Config: <i id="alertsIcon" class="fa fa-chevron-circle-right"></i></legend>
<div id="alertsDrop" class="dropdown-container">
<span style="padding:10px"><label for="notification-chat">GeoChat Enable:</label><label class="enableSwitch"><input id="notification-chat" type="checkbox"><span class="slider"></span></label></span>
<br><br><span style="padding:10px"><label for="notification-cot">CoT Enable:</label><label class="enableSwitch"><input id="notification-cot" type="checkbox"><span class="slider"></span></label></span>
<br><br><span style="padding:10px"><label for="alert-chat-format">GeoChat Format:</label><select name="alert-chat-format" id="alert-chat-format" disabled="true">
<option value="standard" selected>Standard</option><option value="json">JSON</option></select></span>
<br><br><span style="padding:10px"><label for="alert-cot-type">CoT Type:</label><select name="alert-cot-type" id="alert-cot-type" disabled="true">
<option value="b-m-p-s-m" selected>Spot</option><option value="pushpin">Pushpin</option><option value="caution">Caution</option><option value="a-h-G">Hostile</option><option value="a-n-G">Neutral</option></select></span>
<br><br><span style="padding:10px"><label for="alert-cot-color">CoT Color:</label><select name="alert-cot-color" id="alert-cot-color" disabled="true">
<option value="-16711936">Green</option><option value="-65536" selected>Red</option><option value="-16776961">Blue</option><option value="-256">Yellow</option><option value="-65281">Purple</option></select></span>
<br><br><span style="padding:10px"><button class="submitButton disabled" id="notification-submit" type="button" disabled=true><b>Submit</b></button><span id="notification-status"></span></span>
<br><br><span id="alert-config"></span>
</div>
</fieldset>
</div>

<div style="padding:5px">
<fieldset>
<legend onclick="targetDrop()" id="target-legend" class="dropdown-btn">Target Config: <i id="targetIcon" class="fa fa-chevron-circle-right"></i></legend>
<div id="targetDrop" class="dropdown-container">
<span style="padding:10px"><label for="target-enable">Enable:</label><label class="enableSwitch"><input id="target-enable" type="checkbox"><span class="slider"></span></label></span>
<br><br><span style="padding:10px"><label for="target-add">Add Target:</label><input id="target-add" type="text" placeholder="XX:XX:XX:XX:XX:XX" disabled="true">
<button type="button" id="target-add-button" disabled="true">Add</button> *case sensitive</span>
<br><br><span style="padding:10px"><label for="file-target">Upload Targets:</label><input type="file" id="file-target" name="filename-target" accept=".txt" disabled=true></span>
<br><br><span style="padding:10px"><label for="target-list">Select:</label><select name="target-list" id="target-list" disabled="true"></select>
<button type="button" id="target-delete-button" disabled="true">Remove</button>
<button type="button" id="target-clear-button" disabled="true">Clear All</button></span>
<br><br><span style="padding:10px"><button class="submitButton disabled" id="target-submit" type="button" disabled=true><b>Submit</b></button><span id="target-status"></span></span>
<br><br><span id="target-config"></span>
</div>
</fieldset>
</div>

<div style="padding:5px">
<fieldset>
<legend onclick="trackerDrop()" id="tracker-legend" class="dropdown-btn">TAK Tracker Config: <i id="trackerIcon" class="fa fa-chevron-circle-right"></i></legend>
<div id="trackerDrop" class="dropdown-container">
<span style="padding:10px"><label for="tracker-enable">Enable:</label><label class="enableSwitch"><input id="tracker-enable" type="checkbox"><span class="slider"></span></label></span>
<br><br><span style="padding:10px"><label for="tracker-callsign">TAK Callsign:</label><input type="text" id="tracker-callsign" placeholder="Kismet-Tracker" disabled=true></span>
<br><br><span style="padding:10px"><label for="tracker-rate">Ping Rate (seconds):</label><input type="number" id="tracker-rate" value="60" placeholder="10" disabled=true></span>
<br><br><span style="padding:10px"><label for="kismet-cot-type">CoT Type:</label><select name="kismet-cot-type" id="kismet-cot-type" disabled="true">
<option value="a-f-G-U-C" selected>Team</option><option value="a-f-G">Friendly</option><option value="pushpin">Pushpin</option><option value="b-m-p-s-m">Spot</option><option value="a-n-G">Neutral</option><option value="a-h-G">Hostile</option></select></span>
<br><br><span style="padding:10px"><label for="kismet-cot-color">CoT Color:</label><select name="kismet-cot-color" id="kismet-cot-color" disabled="true">
<option value="-16711936">Green</option><option value="-16711681" selected>Cyan</option><option value="-65536">Red</option><option value="-16776961">Blue</option><option value="-256">Yellow</option><option value="-65281">Purple</option></select></span>
<br><br><span style="padding:10px"><button class="submitButton disabled" id="tracker-submit" type="button" disabled=true><b>Submit</b></button><span id="tracker-status"></span></span>
<br><br><span id="tracker-config"></span>
</div>
</fieldset>
</div>

<div style="padding:5px">
<fieldset>
<legend style="border:2px solid black;background-color:white;color:black" onclick="guideDrop()" id="guide-legend" class="dropdown-btn">User Guide: <i id="guideIcon" class="fa fa-chevron-circle-right"></i></legend>
<div id="guideDrop" class="dropdown-container">

<h3><u>Notes</u></h3>
<ul>
<li>Kismet should not run as root, this plugin will break kismet and explode. This means to NOT run "sudo" when starting kismet.</li>
<li>GPS data is pulled from Kismets API so any GPS you provide Kismet (GPSD, virtual, serial) in kismet.conf will be used for ATAK Companion.</li>
<li>Configurations for receiving CoT with kismet could be as follows: USB tether to ATAK, Cellular Modem/SixFab Cellular Hat, creating a WiFi AP over the RPi onboard WiFi interface, 
Etherneting the RPi to ATAK directly. Bluetooth has the potential to be an option for future updates. A lot of the network configuration portion 
 will likely need to be handled in the /etc/network/interfaces file for setting up USB tethering, Ethernet direct, and WiFi AP.</li>
<li>The assumption for the ATAK Companion Plugin is that kismet is NOT being run as root, the atakCompanion directory is added to the ~/.kismet/plugins folder after running "make install" 
 and that its on a Linux OS, only Raspbian has been tested.</li>
<li>iTAK has not been tested and often has issues receiving multicasted CoT that isnt a native TAK client, along with ChromeOS ATAK and Windows WinTAK (often firewall issues). 
 TAKX has also not been tested.</li>
</ul>

<h3><u>TAK Forwarder</u></h3>
<ul>
<li>TAK-FWD button will send CoT marker on your messaging protocol configured (multicast/TAKServer) along with the CoT marker and color you configured in the Alerts Config</li>
<li>When TAK-FWD button clicked it will either return "SENT!" or "NO-GPS!". If "NO-GPS!", this isnt because you dont have a valid GPS location data being pulled but because the device selected doesnt have GPS location attached to it in the device details. This is often an issue only with WiFi-Clients and WiFi-Bridge</li>
<li>MUST enable and configure TAKServer Config or Multicast Config AND enable and configure Alerts Config for TAK Forwarder to work</li>
</ul>

<h3><u>Initialize</u></h3>
<ul>
<li>If "Initialize:" isnt greyed out and bordered green, there was an issue fetching kismets login credentials from kismet_httpd file, or the ATAK Companion API isnt running yet. Try refreshing the web page.</li>
</ul>

<h3><u>TAKServer</u></h3>
<ul>
<li>Do NOT include the port number in the server IP/Hostname input, if all 3 certs are uploaded it will default to port 8089, if no certs are uploaded it will default to 8087.</li>
<li>TAKSserver user.pem, user.key, and ca.pem certs can be found in your TAKServers cert directory.</li>
<li>The default TAKServer key password is "atakatak" unless it has been changed by the TAKServer administrator.</li>
<li>It is recommended to have TAKServer create a new user cert for the ATAK Companion connection as to not conflict with multiple TAK devices using the same TAK user credentials.</li>
<li>If there is a need to handle TAKServer authentication other ways or for TAKServer ports to be a custom input field, I will add it on request.</li>
</ul>

<h3><u>Multicast</u></h3>
<ul>
<li>There should NOT be a need to change the multicast address to anything but default, even chat messages will multicast and ingest over the default address fine.</li>
<li>Multicast NIC is the network interface that will have CoT multicast out on. you can multicast out over OpenVPN or Zerotier for TAK devices on the network to be able to receive without the need for a TAKServer.</li>
<li>VPN interfaces are commonly tun0, Zerotier interfaces are commonly ztxxxx, USB tether interfaces are commonly usb0, WiFi APs are commonly wlan. Ensure you are not multicasting CoT on a WiFi interface that will end up in monitor mode for kismet!</li>
</ul>

<h3><u>Alerts/Notifications</u></h3>
<ul>
<li>Enabling GeoChat will have Kismet Alerts sent to TAK devices as a TAK chat message.</li>
<li>Enabling CoT will have Kismet Alerts sent to TAK devices to plot on TAK map. This is mostly for target MAC Addresses/SSIDs during wardriving that have location data attached to their Alert message.</li>
<li>Geochat Format currently does NOT do anything, it will be an added feature for future updates.</li>
<li>CoT type is the icon/marker used.</li>
<li>CoT/Chat enabled service will also be used for any targets added in the "Target Config:" tab.</li>
<li>Ensure a messaging protocol is setup to send CoT over, either multicast or TAKServer.</li>
</ul>

<h3><u>Targets</u></h3>
<ul>
<li>Targets now persist and are saved with the rest of config settings in atakCompanionConfig.ini file</li>
<li>Targets do NOT get added to kismets /etc/kismet/kismet_alerts.conf file, they are just filtered from the message bus of detected devices and are not actual kismet alerts.</li>
<li>If you want kismet targets to persist you should add them in /etc/kismet/kismet_alerts.conf file where they will be handled as a Kismet Alert.</li>
<li>Alert CoT/Chat service should be enabled if you want to receive CoT/Chat messages over TAK when these targets are detected!</li>
<li>Target List files uploaded should be .txt files with targets seperated by commas with NO spaces. ie: ssid1,ssid2,mac1,mac2</li>
<li>Make sure to click Submit after adding/uploading targets to persist saved changes across browser refreshes!</li>
</ul>

<h3><u>TAK Tracker</u></h3>
<ul>
<li>TAK Callsign is the name the device gets populated as on TAK map. TAK Callsign should not include spaces, or only have numbers!</li>
<li>Ping rate is in seconds of how often the tracker gets refreshed on the TAK map</li>
<li>CoT Type is the marker/icon used.</li>
<li>TAK Tracker service does NOT continue running when kismet service is stopped</li>
<li>Make sure a messaging protocol is enabled, either TAKServer or multicast for CoT to send out over</li>
</ul>

</div>
</fieldset>
</div>
<p id="test">Error: no javascript functions</p> 
</div>

<script type="text/javascript">

document.getElementById("test").innerHTML = "";

var takserverEnable = document.getElementById("takserver-enable");
var takserver = document.getElementById("takserver");
var takserverPassword = document.getElementById("takserver-password");
var userCert = document.getElementById("user-cert");
var userKey = document.getElementById("user-key");
var rootCert = document.getElementById("root-cert");
var takserverSubmit = document.getElementById("takserver-submit");

var multicastEnable = document.getElementById("multicast-enable");
var multicastSelect = document.getElementById("multicast-select");
var multicastNic = document.getElementById("multicast-nic");
var multicastSubmit = document.getElementById("multicast-submit");

var notificationChat = document.getElementById("notification-chat");
var notificationCot = document.getElementById("notification-cot");
var alertCotType = document.getElementById("alert-cot-type");
var alertCotColor = document.getElementById("alert-cot-color");
var alertChatFormat = document.getElementById("alert-chat-format");
var notificationSubmit = document.getElementById("notification-submit");

var trackerEnable = document.getElementById("tracker-enable");
var trackerCallsign = document.getElementById("tracker-callsign");
var trackerRate = document.getElementById("tracker-rate");
var kismetCotType = document.getElementById("kismet-cot-type");
var kismetCotColor = document.getElementById("kismet-cot-color");
var trackerSubmit = document.getElementById("tracker-submit");

var targetEnable = document.getElementById("target-enable");
var targetAdd = document.getElementById("target-add");
var targetFile = document.getElementById("file-target");
var targetAddButton = document.getElementById("target-add-button");
var targetList = document.getElementById("target-list");
var targetDeleteButton = document.getElementById("target-delete-button");
var targetClearButton = document.getElementById("target-clear-button");
var targetSubmit = document.getElementById("target-submit");

var targetListArray = [];
var targetListArrayFile = [];
var targetListStringFile;

var localInterfaces = [];

var takserverStatus;
var multicastStatus;
var notificationCotStatus;
var notificationChatStatus;
var targetStatus;
var trackerStatus;

var rawHttpdUser;
var rawHttpdPassword;

var rawTakserverService;
var rawTakserverAddress;
var rawTakserverPassword;

var rawMulticastService;
var rawMulticastSelect;
var rawMulticastInterface;

var rawNotificationChatService;
var rawNotificationChatFormat;
var rawNotificationCotService;
var rawNotificationCotType;
var rawNotificationCotColor;

var rawTrackerService;
var rawTrackerCot;
var rawTrackerColor;
var rawTrackerRate;
var rawTrackerCallsign;

var rawTargetService;
var rawTargetList = [];

var currentHostname = window.location.hostname;
var currentIp;
var currentUser;
var currentPassword;
var initializeSubmit = document.getElementById("initialize-submit");

function uploadFiles() {
    var userPemFile = document.getElementById('user-cert').files[0];
    var userKeyFile = document.getElementById('user-key').files[0];
    var caPemFile = document.getElementById('root-cert').files[0];
    var formData1 = new FormData();
    var formData2 = new FormData();
    var formData3 = new FormData();
    formData1.append('user_pem', userPemFile);
    formData2.append('user_key', userKeyFile);
    formData3.append('ca_pem', caPemFile);

    fetch('http://'+currentHostname+':8000/uploadUserPem', {
        method: 'POST',
        body: formData1
    })
    .then(response => {
        if (response.ok) {
            console.log('Files uploaded successfully');
        } else {
            console.error('Failed to upload files');
        }
    })
    .catch(error => {
        console.error('Error uploading files:', error);
    });
    fetch('http://'+currentHostname+':8000/uploadUserKey', {
        method: 'POST',
        body: formData2
    })
    .then(response => {
        if (response.ok) {
            console.log('Files uploaded successfully');
        } else {
            console.error('Failed to upload files');
        }
    })
    .catch(error => {
        console.error('Error uploading files:', error);
    });
    fetch('http://'+currentHostname+':8000/uploadCaPem', {
        method: 'POST',
        body: formData3
    })
    .then(response => {
        if (response.ok) {
            console.log('Files uploaded successfully');
        } else {
            console.error('Failed to upload files');
        }
    })
    .catch(error => {
        console.error('Error uploading files:', error);
    });
}


function matchValues() {
takserverStatus = rawTakserverService;
multicastStatus = rawMulticastService;
notificationCotStatus = rawNotificationCotService;
notificationChatStatus = rawNotificationChatService;
targetStatus = rawTargetService;
trackerStatus = rawTrackerService;
targetListArray = rawTargetList;
}

function checkDisabled() {
if (takserverEnable.checked === true) {
takserver.disabled = false;
takserverPassword.disabled = false;
userCert.disabled = false;
userKey.disabled = false;
rootCert.disabled = false;
takserverSubmit.disabled = false;
}
if (multicastEnable.checked === true) {
multicastSelect.disabled = false;
multicastNic.disabled = false;
multicastSubmit.disabled = false;
}
if (notificationChat.checked === true) {
alertChatFormat.disabled = false;
notificationSubmit.disabled = false;
}
if (notificationCot.checked === true) {
alertCotType.disabled = false;
if (alertCotType.value === "b-m-p-s-m" || alertCotType.value === "a-f-G-U-C" || alertCotType.value === "pushpin") {
alertCotColor.disabled = false;
notificationSubmit.disabled = false;
}}
if (trackerEnable.checked === true) {
trackerRate.disabled = false;
trackerCallsign.disabled = false;
kismetCotType.disabled = false;
if (kismetCotType.value === "b-m-p-s-m" || kismetCotType.value === "a-f-G-U-C" || kismetCotType.value === "pushpin") {
trackerSubmit.disabled = false;
kismetCotColor.disabled = false;
}}
if (targetEnable.checked === true) {
targetAdd.disabled = false;
targetAddButton.disabled = false;
targetFile.disabled = false;
targetList.disabled = false;
targetDeleteButton.disabled = false;
targetClearButton.disabled = false;
targetSubmit.disabled = false;
}
};

function checkActive() {
if (takserverStatus === true) {
document.getElementById("takserver-legend").setAttribute("style", "border:1px solid MediumSeaGreen")
} else {
document.getElementById("takserver-legend").setAttribute("style", "border:1px solid white")
}
if (multicastStatus === true) {
document.getElementById("multicast-legend").setAttribute("style", "border:1px solid MediumSeaGreen")
} else {
document.getElementById("multicast-legend").setAttribute("style", "border:1px solid white")
}
if (trackerStatus === true) {
document.getElementById("tracker-legend").setAttribute("style", "border:1px solid MediumSeaGreen")
} else {
document.getElementById("tracker-legend").setAttribute("style", "border:1px solid white")
}
if (targetStatus === true) {
document.getElementById("target-legend").setAttribute("style", "border:1px solid MediumSeaGreen")
} else {
document.getElementById("target-legend").setAttribute("style", "border:1px solid white")
}
if (notificationCotStatus === true || notificationChatStatus === true) {
document.getElementById("alert-legend").setAttribute("style", "border:1px solid MediumSeaGreen")
} else {
document.getElementById("alert-legend").setAttribute("style", "border:1px solid white")
}
};

function pushFileTargets() {
targetListArrayFile = targetListStringFile.split(",");
targetListArray.push(...targetListArrayFile);
if (targetListArray.includes("")){
targetListArray.splice(targetListArray.indexOf(""),1);
};
if (targetListArray.includes(" ")){
targetListArray.splice(targetListArray.indexOf(" "),1);
};
targetList.innerHTML = "";
targetListArray.forEach(updateTargetHtml);
};

function checkInitialize() {
if (currentHostname !== undefined) {
document.getElementById("current-ip-status").setAttribute("class", "fa fa-check");
document.getElementById("current-ip").disabled = true;
document.getElementById("current-ip").value = currentHostname.toString();
};
if (rawHttpdUser === true) {
document.getElementById("current-user-status").setAttribute("class", "fa fa-check");
document.getElementById("current-user").disabled = true;
};
if (rawHttpdPassword === true) {
document.getElementById("current-password-status").setAttribute("class", "fa fa-check");
document.getElementById("current-password").disabled = true;
};
if (rawHttpdPassword === true && rawHttpdPassword === true && currentHostname !== undefined) {
document.getElementById("initialize-legend").setAttribute("style", "color:grey; border:1px solid MediumSeaGreen");
document.getElementById("initialize-legend").setAttribute("onclick", "");
};
};


function initializeDrop() {
document.getElementById("initializeDrop").classList.toggle("show");
if (document.getElementById("initializeIcon").getAttribute("class") == "fa fa-chevron-circle-right") {
document.getElementById("initializeIcon").setAttribute("class", "fa fa-chevron-circle-down");
} else {
document.getElementById("initializeIcon").setAttribute("class", "fa fa-chevron-circle-right");
};
};

function takserverDrop() {
document.getElementById("takserverDrop").classList.toggle("show");
if (document.getElementById("takserverIcon").getAttribute("class") == "fa fa-chevron-circle-right") {
document.getElementById("takserverIcon").setAttribute("class", "fa fa-chevron-circle-down");
} else {
document.getElementById("takserverIcon").setAttribute("class", "fa fa-chevron-circle-right");
};
};

function multicastDrop() {
document.getElementById("multicastDrop").classList.toggle("show");
if (document.getElementById("multicastIcon").getAttribute("class") == "fa fa-chevron-circle-right") {
document.getElementById("multicastIcon").setAttribute("class", "fa fa-chevron-circle-down");
} else {
document.getElementById("multicastIcon").setAttribute("class", "fa fa-chevron-circle-right");
};
};

function alertsDrop() {document.getElementById("alertsDrop").classList.toggle("show");
if (document.getElementById("alertsIcon").getAttribute("class") == "fa fa-chevron-circle-right") {
document.getElementById("alertsIcon").setAttribute("class", "fa fa-chevron-circle-down");
} else {
document.getElementById("alertsIcon").setAttribute("class", "fa fa-chevron-circle-right");
};
};

function targetDrop() {document.getElementById("targetDrop").classList.toggle("show");
if (document.getElementById("targetIcon").getAttribute("class") == "fa fa-chevron-circle-right") {
document.getElementById("targetIcon").setAttribute("class", "fa fa-chevron-circle-down");
} else {
document.getElementById("targetIcon").setAttribute("class", "fa fa-chevron-circle-right");
};
};

function trackerDrop() {document.getElementById("trackerDrop").classList.toggle("show");
if (document.getElementById("trackerIcon").getAttribute("class") == "fa fa-chevron-circle-right") {
document.getElementById("trackerIcon").setAttribute("class", "fa fa-chevron-circle-down");
} else {
document.getElementById("trackerIcon").setAttribute("class", "fa fa-chevron-circle-right");
};
};

function guideDrop() {document.getElementById("guideDrop").classList.toggle("show");
if (document.getElementById("guideIcon").getAttribute("class") == "fa fa-chevron-circle-right") {
document.getElementById("guideIcon").setAttribute("class", "fa fa-chevron-circle-down");
} else {
document.getElementById("guideIcon").setAttribute("class", "fa fa-chevron-circle-right");
};
};

function updateInterfaceHtml(value) {
multicastNic.innerHTML += "<option value=" + value.ip[0] + " id=" + value.interface + ">" + value.ip[0] + " (" + value.interface + ")</option>";
};

function updateTargetHtml(value) {
console.log("updateTargetHtml value: " + value);
if (value !== "" || value !== " ") {
targetList.innerHTML += "<option value=" + value + " id=" + value + ">" + value + "</option>";
}
};

function persistData() {
if (rawTakserverService === true || rawTakserverAddress !== "") {
takserverEnable.checked = rawTakserverService;
takserver.value = rawTakserverAddress;
takserverPassword.value = rawTakserverPassword;
};
if (rawMulticastService === true || (rawMulticastSelect !== "" && rawMulticastInterface !== "")) {
multicastEnable.checked = rawMulticastService;
multicastSelect.value = rawMulticastSelect;
multicastNic.value = rawMulticastInterface;
};
if (rawNotificationChatService === true || rawNotificationChatFormat !== "") {
notificationChat.checked = rawNotificationChatService;
alertChatFormat.value = rawNotificationChatFormat;
};
if (rawNotificationCotService === true || (rawNotificationCotType !== "" && rawNotificationCotColor!== "")) {
notificationCot.checked = rawNotificationCotService;
alertCotType.value = rawNotificationCotType;
alertCotColor.value = rawNotificationCotColor;
};
if (rawTrackerService === true || (rawTrackerCallsign !== "" && rawTrackerRate !== 0 && rawTrackerCot !== "" && rawTrackerColor !== "")) {
trackerEnable.checked = rawTrackerService;
trackerCallsign.value = rawTrackerCallsign;
trackerRate.value = rawTrackerRate;
kismetCotType.value = rawTrackerCot;
kismetCotColor.value = rawTrackerColor;
};
if (true) {
targetEnable.checked = rawTargetService;
targetList.value = rawTargetList;
targetListArray = rawTargetList;
targetListArray.forEach(updateTargetHtml);
};
};

//forward user input to backend
function forwardJson(data) {
fetch('http://'+currentHostname+':8000/config', {
method: 'POST',
headers: {
'Content-Type': 'application/json'
},
body: JSON.stringify(data)
})
.then(response => {
if (!response.ok) {
throw new Error('Network response was not ok');
}
console.log('Data sent successfully');
})
.catch(error => {
console.error('Error sending data:', error);
});
};

function parametersInitialize(inputUser, inputPassword) {
const obj = {id: "initialize", user: inputUser, password: inputPassword};
forwardJson(obj)
};

function parametersTakserver(urlInput, passphrase, protocol, status) {
const obj = {id: "takserver", url: urlInput, key: passphrase, proto: protocol, service: status};
forwardJson(obj)
};

function parametersMulticast(address, iface, status) {
const obj = {id: "multicast", udp: address, net: iface, service: status}; 
forwardJson(obj)
};

function parametersNotificationCot(type, color, status) {
const obj = {id: "notification-cot", cot: type, rgb: color, service: status};
forwardJson(obj)
};

function parametersNotificationChat(format, status) {
const obj = {id: "notification-chat", type: format, service: status};
forwardJson(obj)
};

function parametersTracker(type, color, ping, callsign, status) {
const obj = {id: "tracker", cot: type, rgb: color, rate: ping, name:callsign, service: status};
forwardJson(obj);
};

function parametersTarget(list, status) {
const obj = {id: "target", targets: list, service: status};
forwardJson(obj);
};

//receive local interfaces
function receiveInterfacesJson() {
fetch('http://'+currentHostname+':8000/interfaces')
.then(response => {
if (!response.ok) {
throw new Error('Network response was not ok');
}
return response.json();
})
.then(data => {
console.log(data);
localInterfaces = data.interfaces;
//localInterfaces.forEach(updateInterfaceHtml);
})
.catch(error => {
console.error('Error fetching data:', error);
});
};

//receive persistent global variables from backend
function receivePersistJson() {
fetch('http://'+currentHostname+':8000/persist')
.then(response => {
if (!response.ok) {
throw new Error('Network response was not ok');
}
return response.json();
})
.then(data => {
console.log(data);
rawHttpdUser = data.initialize[0];
rawHttpdPassword = data.initialize[1];
rawTakserverService = data.takserver[0];
rawTakserverAddress = data.takserver[1];
rawMulticastService = data.multicast[0];
rawMulticastSelect = data.multicast[1];
rawMulticastInterface = data.multicast[2];
rawNotificationChatService = data.notificationChat[0];
rawNotificationChatFormat = data.notificationChat[1];
rawNotificationCotService = data.notificationCot[0];
rawNotificationCotType = data.notificationCot[1];
rawNotificationCotColor = data.notificationCot[2];
rawTrackerService = data.tracker[0];
rawTrackerCot = data.tracker[1];
rawTrackerColor = data.tracker[2];
rawTrackerRate = data.tracker[3];
rawTrackerCallsign = data.tracker[4];
rawTargetService = data.target[0];
rawTargetList = data.target[1];
if (rawTargetList.includes("")){
rawTargetList.splice(rawTargetList.indexOf(""),1);
};
if (rawTargetList.includes(" ")){
rawTargetList.splice(rawTargetList.indexOf(" "),1);
};
//receiveInterfacesJson();
multicastNic.innerHTML = "";
localInterfaces.forEach(updateInterfaceHtml);
persistData();
checkInitialize();
matchValues();
checkActive();
checkDisabled();
})
.catch(error => {
console.error('Error fetching data:', error);
});
};

//callback functions end

takserverEnable.onclick = function() {
if (takserverEnable.checked === true) {
takserver.disabled = false;
takserverPassword.disabled = false;
userCert.disabled = false;
userKey.disabled = false;
rootCert.disabled = false;
takserverSubmit.disabled = false;
} else {
takserver.disabled = true;
takserverPassword.disabled = true;
userCert.disabled = true;
userKey.disabled = true;
rootCert.disabled = true;
takserverSubmit.disabled = true;
parametersTakserver("","","",false);
document.getElementById("takserver-legend").setAttribute("style", "border:1px solid white")
}
};

multicastEnable.onclick = function() {
if (multicastEnable.checked === true) {
multicastSelect.disabled = false;
multicastNic.disabled = false;
multicastSubmit.disabled = false;
//receiveInterfacesJson();
//localInterfaces.forEach(updateInterfaceHtml);
} else {
multicastSelect.disabled = true;
multicastNic.disabled = true;
multicastSubmit.disabled = true;
parametersMulticast("","",false);
document.getElementById("multicast-legend").setAttribute("style", "border:1px solid white")
}
};

notificationChat.onclick = function() {
if (notificationChat.checked === true) {
alertChatFormat.disabled = false;
notificationSubmit.disabled = false;
} else if (notificationCot.checked === false && notificationChat.checked === false) {
notificationSubmit.disabled = true;
alertChatFormat.disabled = true;
parametersNotificationChat("",false);
document.getElementById("alert-legend").setAttribute("style", "border:1px solid white")
} else {
alertChatFormat.disabled = true;
parametersNotificationChat("",false);
}
};

notificationCot.onclick = function() {
if (notificationCot.checked === true) {
alertCotType.disabled = false;
notificationSubmit.disabled = false;
if (alertCotType.value === "b-m-p-s-m" || alertCotType.value === "a-f-G-U-C" || alertCotType.value === "pushpin") {
alertCotColor.disabled = false;
}} else if (notificationCot.checked === false && notificationChat.checked === false) {
notificationSubmit.disabled = true;
alertCotType.disabled = true;
alertCotColor.disabled = true;
parametersNotificationCot("","",false);
document.getElementById("alert-legend").setAttribute("style", "border:1px solid white")
} else {
alertCotType.disabled = true;
alertCotColor.disabled = true;
parametersNotificationCot("","",false);
}
};

alertCotType.onchange = function() {
if (alertCotType.value === "b-m-p-s-m" || alertCotType.value === "a-f-G-U-C" || alertCotType.value === "pushpin") {
alertCotColor.disabled = false;
} else {
alertCotColor.disabled = true;
}
};

trackerEnable.onclick = function () {
if (trackerEnable.checked === true) {
trackerSubmit.disabled = false;
trackerCallsign.disabled = false;
trackerRate.disabled = false;
kismetCotType.disabled = false;
if (kismetCotType.value === "b-m-p-s-m" || kismetCotType.value === "a-f-G-U-C" || kismetCotType.value === "pushpin") {
kismetCotColor.disabled = false;
}} else {
trackerRate.disabled = true;
trackerCallsign.disabled = true;
kismetCotType.disabled = true;
kismetCotColor.disabled = true;
trackerSubmit.disabled = true;
parametersTracker("","","","",false);
document.getElementById("tracker-legend").setAttribute("style", "border:1px solid white")
}
};

kismetCotType.onchange = function() {
if (kismetCotType.value === "b-m-p-s-m" || kismetCotType.value === "a-f-G-U-C" || kismetCotType.value === "pushpin") {
kismetCotColor.disabled = false;
} else {
kismetCotColor.disabled = true;
}
};

targetEnable.onclick = function() {
if (targetEnable.checked === true) {
targetAdd.disabled = false;
targetFile.disabled = false;
targetAddButton.disabled = false;
targetList.disabled = false;
targetDeleteButton.disabled = false;
targetClearButton.disabled = false;
targetSubmit.disabled = false;
} else {
targetAdd.disabled = true;
targetFile.disabled = true;
targetAddButton.disabled = true;
targetList.disabled = true;
targetDeleteButton.disabled = true;
targetClearButton.disabled = true;
targetSubmit.disabled = true;
parametersTarget(targetListArray,false);
document.getElementById("target-legend").setAttribute("style", "border:1px solid white")
}
};

targetAddButton.onclick = function() {
console.log("targetAdd.value " + targetAdd.value)
if (targetAdd.value !== "" || targetAdd.value.length > 1) {
targetListArray.push(targetAdd.value);
if (targetListArray.includes("")){
targetListArray.splice(targetListArray.indexOf(""),1);
};
if (targetListArray.includes(" ")){
targetListArray.splice(targetListArray.indexOf(" "),1);
};
targetList.innerHTML = "";
targetListArray.forEach(updateTargetHtml);
};
targetAdd.value = "";
};

targetDeleteButton.onclick = function() {
targetListArray.splice(targetListArray.indexOf(targetList.value), 1);
targetList.innerHTML = "";
targetListArray.forEach(updateTargetHtml);
targetAdd.value = "";
};

targetClearButton.onclick = function() {
targetListArray = [];
targetList.innerHTML = "";
targetListArray.forEach(updateTargetHtml);
targetAdd.value = "";
};

initializeSubmit.onclick = function() {
currentHostname = document.getElementById("current-ip").value;
currentUser = document.getElementById("current-user").value;
currentPassword = document.getElementById("current-password").value;
parametersInitialize(currentUser, currentPassword);
document.getElementById("initialize-submit").disabled = true;
document.getElementById("current-ip").value = "";
document.getElementById("current-user").value = "";
document.getElementById("current-password").value = "";
checkInitialize();
};

takserverSubmit.onclick = function() {
takserverStatus = true;
var protocol = "https";
if (userCert.value === "" && userKey.value === "" && rootCert.value === "") {
protocol = "http";
};
document.getElementById("takserver-legend").setAttribute("style", "border:1px solid MediumSeaGreen")
parametersTakserver(takserver.value, takserverPassword.value, protocol, takserverEnable.checked);
if (userCert.value !== "" && userKey.value !== "" && rootCert.value !== "" && takserverPassword.value !== "") {
uploadFiles()
};
};

multicastSubmit.onclick = function() {
multicastStatus = true;
document.getElementById("multicast-legend").setAttribute("style", "border:1px solid MediumSeaGreen")
parametersMulticast(multicastSelect.value, multicastNic.value, multicastEnable.checked)
};

notificationSubmit.onclick = function() {
if (notificationCot.checked) { notificationCotStatus = true;};
if (notificationChat.checked) { notificationChatStatus = true;};
document.getElementById("alert-legend").setAttribute("style", "border:1px solid MediumSeaGreen")
parametersNotificationCot(alertCotType.value, alertCotColor.value, notificationCot.checked)
parametersNotificationChat(alertChatFormat.value, notificationChat.checked)
};

trackerSubmit.onclick = function() {
document.getElementById("tracker-legend").setAttribute("style", "border:1px solid MediumSeaGreen")
trackerStatus = true;
parametersTracker(kismetCotType.value, kismetCotColor.value,
trackerRate.value, trackerCallsign.value, trackerEnable.checked)
};

targetSubmit.onclick = function() {
document.getElementById("target-legend").setAttribute("style", "border:1px solid MediumSeaGreen")
targetStatus = true;
parametersTarget(targetListArray, targetEnable.checked)
};

document.getElementById('file-target').addEventListener('change', function(event) {
//end of new function test
const file = event.target.files[0];
const reader = new FileReader();
reader.onload = function(e) {
targetListStringFile = e.target.result;
pushFileTargets();
}
reader.readAsText(file);
});

document.getElementById('file-target').addEventListener('click', function() {
document.getElementById('file-target').value = null;
});

checkInitialize();
receiveInterfacesJson();
//localInterfaces.forEach(updateInterfaceHtml);
receivePersistJson();
//persistData();
//matchValues();
//checkActive();
//checkDisabled();
</script>

</div>
	`);
	});
    },
});


kismet_ui.AddDeviceColumn('column_foo_channel', {
    sTitle: 'TAK Forwarder',
    field: 'kismet.device.base.macaddr',
    sanitize: true,
    renderfunc: function(data, type, row, meta) {
return `

<button style="background:black; border:2px solid darkgray; color:white; width:80px" id="tak-fwd-${data}"><b>TAK-FWD</b></button>
<p id ="test${data}"></p>
<script>

var currentHostname = window.location.hostname;
var cot;
//var status;
var test;

function post_data(send) {
fetch('http://'+currentHostname+':8000/device', {
method: 'POST',
body: JSON.stringify(send)
})
.then(response => {
if (response.ok) {
console.log('cot sent to backend');
} else {
console.error('cot failed to send');
}
})
.catch(error => {
console.error('cot error: ', error);
});
};


async function get_data(mac) {
try {
const response = await fetch('http://'+currentHostname+':2501//devices/by-mac/'+mac+'/devices.json');
if (!response.ok) {
throw new Error('Network response was not ok');
}
const getData = await response.json();
console.log(getData);
var lat1 = getData[0]['kismet.device.base.signal']['field.unknown.not.registered']['kismet.common.location.geopoint'][1];
var lon1 = getData[0]['kismet.device.base.signal']['field.unknown.not.registered']['kismet.common.location.geopoint'][0];
//var lat2 = getData[0]['kismet.device.base.location']['kismet.common.location.avg_loc']['kismet.common.location.geopoint'][1];
//var lon2 = getData[0]['kismet.device.base.location']['kismet.common.location.avg_loc']['kismet.common.location.geopoint'][0];
var currentDevice = getData[0]['kismet.device.base.commonname'];
cot = {lat:lat1, lon:lon1, device:currentDevice};
} catch (error) {
console.error('Error fetching data:', error);
}
};

//onclick function starts
document.getElementById("tak-fwd-${data}").onclick = async function(event) {
event.stopPropagation();
await get_data('${data}');
//document.getElementById("test${data}").innerHTML = JSON.stringify(cot);
var status;
if (cot === undefined || cot.device === undefined) {
status = false;
} else {
status = true;
}

if (status === true) {
post_data(cot);
document.getElementById("tak-fwd-${data}").innerHTML = "SENT!";
document.getElementById("tak-fwd-${data}").setAttribute("style", "background:black; border:2px solid green; color:white; width:80px");
} else {
document.getElementById("tak-fwd-${data}").innerHTML = "NO-GPS!";
document.getElementById("tak-fwd-${data}").setAttribute("style", "background:black; border:2px solid red; color:white; width:80px");
}

cot = undefined;
status = undefined;
}; //end of onclick function()

</script>
`
    },
});
