# Our plugin directory name when we install
PLUGIN_NAME ?= atakCompanion

# Set sane values if we don't have the base config
INSTALL ?= /usr/bin/install

# As we have no live code, all we need is the manifest.conf to "compile"
all:	manifest.conf

# We have no requirements for install or userinstall, we just copy our data
install:
	mkdir -p ${HOME}/.kismet/plugins/$(PLUGIN_NAME)
	cp manifest.conf $(HOME)/.kismet/plugins/$(PLUGIN_NAME)
	cp atakCompanionServer.py $(HOME)/.kismet/plugins/$(PLUGIN_NAME)
	cp atakCompanionScript.py $(HOME)/.kismet/plugins/$(PLUGIN_NAME)
	cp -r httpd $(HOME)/.kismet/plugins/$(PLUGIN_NAME)
	cp -r persist $(HOME)/.kismet/plugins/$(PLUGIN_NAME)
	mkdir -p ${HOME}/.kismet/plugins/$(PLUGIN_NAME)/certs
	mkdir -p ${HOME}/.kismet/plugins/$(PLUGIN_NAME)/kml
	mkdir -p ${HOME}/.config/systemd/user
	chmod +x $(HOME)/.kismet/plugins/$(PLUGIN_NAME)/atakCompanionScript.py
	$(INSTALL) -m 644 monitor_atakCompanion.service ${HOME}/.config/systemd/user/monitor_atakCompanion.service
	$(INSTALL) -m 644 run_atakCompanion.service ${HOME}/.config/systemd/user/run_atakCompanion.service
	systemctl --user daemon-reload
	systemctl --user enable run_atakCompanion.service
	systemctl --user enable monitor_atakCompanion.service
	systemctl --user start monitor_atakCompanion.service

uninstall:
	rm -rf ${HOME}/.kismet/plugins/$(PLUGIN_NAME)
	systemctl --user disable monitor_atakCompanion.service || true
	systemctl --user stop monitor_atakCompanion.service || true
	rm -f ${HOME}/.config/systemd/user/monitor_atakCompanion.service
	systemctl --user disable run_atakCompanion.service || true
	systemctl --user stop run_atakCompanion.service || true
	rm -f ${HOME}/.config/systemd/user/run_atakCompanion.service
	systemctl --user daemon-reload
	systemctl --user reset-failed

clean:
	@echo "Nothing to clean"
