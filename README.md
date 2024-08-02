# Kismet ATAK Companion Plugin

**Kismet Plugin to extend the Web UI and enable configuration to send Kismet device data to ATAK. Works only for "Release" version of kismet, NOT the "git" version. Configuring Kismet with GPS is Required.**

---

## Features:

* Stream all scanned devices by Kismet to ATAK Map as CoT via TAKServer or Multicast

* Connect to Network KML of active kismet log and display scanned devices 
  * can be imported into ATAK as Network Link, updates automatically every 60s

* Easily import past .Kismet files as KMLs 
  * .Kismet files with empty devices or devices without GPS coordinates will fail to be converted to KML)

* Forward all Kismet Alerts as CoT markers and/or GeoChat messages to ATAK via TAKServer or Multicast

* Forward all inputted Kismet Targets as CoT markers and/or GeoChat messages via TAKServer or Multicast 
  * Targets can be manually entered, imported as .txt file separated by commas or added from the Kismet Device Table via TGT+ button

* Run Kismet as a TAK Tracker 
  * Tracker service stops when Kismet service stops running

* Plot any scanned device in Kismet Device Tables to ATAK using TAK-FWD button (valid GPS coordinates attached to device required)

---

## Getting Started:
### Install
```bash
# go to user directory
$ cd ~

# clone kismetAtakCompanion Repo
$ git clone https://github.com/JaxProjex/kismetAtakCompanion.git

# change into working directory
$ cd kismetAtakCompanion

# run make install
$ make install

# run kismet in your preferred user directory
$ cd /home/pi/junk
$ kismet
```
### Uninstall
```bash
# to uninstall kismetAtakCompanion
$ cd kismetAtakCompanion
$ make uninstall
```

---

## Usage:

![kismetAtakCompanionPhoto](/photos/img6.png?raw=true)

![kismetAtakCompanionPhoto](/photos/img5.png?raw=true)

![kismetAtakCompanionPhoto](/photos/img4.png?raw=true)

![kismetAtakCompanionPhoto](/photos/img7.png?raw=true)

![kismetAtakCompanionPhoto](/photos/img8.png?raw=true)

![kismetAtakCompanionPhoto](/photos/img9.png?raw=true)

![kismetAtakCompanionPhoto](/photos/img10.png?raw=true)

![kismetAtakCompanionPhoto](/photos/img1.png?raw=true)

![kismetAtakCompanionPhoto](/photos/img2.png?raw=true)

![kismetAtakCompanionPhoto](/photos/img3.png?raw=true)

---

## To-Do:

* Bluetooth option
* Device DF feature
* device whitelist or device baseline feature
* other takserver auth options
* requests?
* bug fixes?
* ui adjustments?


---

## License:
[MIT](https://github.com/JaxProjex/kismetAtakCompanion/blob/main/LICENSE)
