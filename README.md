# kismetAtakCompanion
Kismet Plugin that forwards Alerts and detection of targeted MAC Addresses and SSIDs to TAK Devices as GeoChat messages and CoT markers on TAK Map using Multicast or TAKServer.

Install ATAK Companion Plugin:

-go to your users home directory:

$ cd ~

-clone the ATAK Companion Plugin repo

$ git clone https://github.com/JaxProjex/kismetAtakCompanion.git

-change directories into the repo

$ cd kismetAtakCompanion

-run make to add files to necessary place, enable/start services for plugin to work

$ make install

-run kismet (not as root)

$ kismet

- go to kismets webserver at localhost:2501

- at the bottom next to "Messages" and "Channels" should be the Atak Companion Tab

Uninstall ATAK Companion Plugin:

$ cd ~/kismetAtakCompanion

$ make uninstall
