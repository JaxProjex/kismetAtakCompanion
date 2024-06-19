#!/usr/bin/env python3

import subprocess
import time
import requests

kismet_url = "http://localhost:2501"

def is_kismet_active():
    try:
        response = requests.get(kismet_url)
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def start_server():
    subprocess.run(["systemctl", "--user", "start", "run_atakCompanion.service"])

def stop_server():
    subprocess.run(["systemctl", "--user", "stop", "run_atakCompanion.service"])

def main():
    server_active = True

    while True:
        kismet_active = is_kismet_active()
        if kismet_active and not server_active:
            start_server()
            server_active = True
        elif not kismet_active and server_active:
            stop_server()
            server_active = False

        time.sleep(1)

if __name__ == "__main__":
    main()



