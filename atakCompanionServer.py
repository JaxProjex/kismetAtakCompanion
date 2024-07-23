from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, HTTPServer #python api server
import xml.etree.ElementTree as ET #readable cot template
import socketserver #for network kml
import websockets #for websocket client
import subprocess #to run ifconfig and ssl decrypt
import re #extract ip addresses
import asyncio #for websocket client
import socket #for getting network interfaces, multicasting out
import json #for get/post/ws api data
import time #tak tracker ping rate
from datetime import datetime, timedelta #for cot time / stale
import threading #for websocket, tak tracker, http server
import random #to generate random uids for tak chat messages
import os #to get local system files (~/.kismet/kismet_httpd.conf
import requests #to get local files (takserver certs)
import ssl #for takserver cot sending
import configparser #for reading/writing atakCompanionConfig.conf file
#import cv2 #for opencv video recording

config = configparser.ConfigParser()

current_time = datetime.now() #system time
date = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
stale = (current_time + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
current_timestamp = 0 #kismet time seconds
device_seen = 0

current_ip = ""
current_user = ""
current_password = ""
kml_network_link = "http://"+current_ip+":8000/networklink.kml"

#kismet api gps
current_lat = "0.0"
current_lon = "0.0"

# TAKServer details
takserver_user = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs/user_pem.pem")
takserver_key = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs/user_key.key")
takserver_key_dec = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs/user_key_dec.key")
takserver_ca = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs/ca_pem.pem")
takserver_password = ""
takserver_cert_error = False
#takserver_cert_service = False
takserver_service = False
takserver_address = ""
takserver_port = 0
takserver_protocol = ""

# multicast details
multicast_service = False
multicast_select = ""
multicast_address = ""
multicast_port = 0
multicast_interface = ""
udp_service = False
udp_list = []
udp_list_filter = []
[udp_list_filter.append(x) for x in udp_list if x not in udp_list_filter]
# alert/notification chat details
notification_chat_service = False
notification_chat_format = ""

# alert/notification cot details
notification_cot_service = False
notification_cot_type = ""
notification_cot_color = ""

# video/image details
#video_service = True
#video_url = "http://motioneye.local:9081"
#video_active = False

# TAK tracker details
tracker_service = False
tracker_callsign = ""
tracker_rate = 0
tracker_cot = ""
tracker_color = ""

# target details
target_service = False
target_list = []
target_list_filter = []
[target_list_filter.append(x) for x in target_list if x not in target_list_filter]

# target chat details
target_chat_service = False
target_chat_format = ""

# target cot details
target_cot_service = False
target_cot_type = ""
target_cot_color = ""

# stream cot details
stream_cot_service = False
stream_cot_type = ""
stream_cot_color = ""

# device from monitor ws
device_array = []

# certs filepath
file_path_prekey = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs/user_key.key")
file_path_postkey = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs/user_key_dec.key")

check_file1 = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs/user_key.key")
check_file2 = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs/user_key_dec.key")
check_file3 = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs/user_pem.pem")
check_file4 = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs/ca_pem.pem")
takserver_cert_service = os.path.isfile(check_file1) and os.path.isfile(check_file2) and os.path.isfile(check_file3) and os.path.isfile(check_file4)

# kml file
kml_file = ""
kml_files = []
kml_service = False
kml_filepath = ""
kml_error = False

def get_kismet_files():
    global kml_error, kml_filepath, kml_files, kml_file
    kml_files = []
    if kml_filepath == "":
        kml_error = True
        #set_kml_config()
        return
    directory = os.path.abspath(kml_filepath)
    if not os.path.exists(directory):
        kml_error = True
        #set_kml_config()
        return
    if os.path.exists(directory):
        kml_error = False
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path) and filename.endswith('.kismet'):
                kml_files.append(filename)
    #kml_error = False

# kismet user/pass login details
httpd_username_status = False
httpd_password_status = False
file_path = os.path.expanduser("~/.kismet/kismet_httpd.conf")
httpd_username = None
httpd_password = None
with open(file_path, 'r') as file:
    for line in file:
        key, value = line.strip().split('=')
        if key == 'httpd_username':
            httpd_username = value
        elif key == 'httpd_password':
            httpd_password = value

if (httpd_username != None):
    httpd_username_status = True
if (httpd_password != None):
    httpd_password_status = True

uri = f""
uri_monitor = f""

if (httpd_username is not None and httpd_password is not None):
    uri = f"ws://127.0.0.1:2501/eventbus/events.ws?user="+httpd_username+"&password="+httpd_password+""
    uri_monitor = f"ws://127.0.0.1:2501/devices/monitor.ws?user="+httpd_username+"&password="+httpd_password+""

def get_interface_addresses(): #get network interface names matched with ips
    interface_addresses = []
    command = ['ifconfig']
    output = subprocess.check_output(command).decode('utf-8')
    interface_regex = re.compile(r'^([a-zA-Z0-9]+).*?inet (\d+\.\d+\.\d+\.\d+)', re.MULTILINE | re.DOTALL)
    matches = interface_regex.findall(output)
    for match in matches:
        interface_name, ipv4_address = match
        interface_addresses.append({'interface': interface_name, 'ip': [ipv4_address]})
    return interface_addresses

def key_decrypt(password):
    global file_path_prekey, file_path_postkey
    try:
        command = ["openssl", "rsa", "-passin", "pass:"+password, "-in", file_path_prekey, "-out", file_path_postkey]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        if result.returncode == 0:
            print("Command executed successfully.")
            print("Output:", result.stdout)
        else:
            print("Command failed with error code:", result.returncode)
            print("Error output:", result.stderr)
    except subprocess.CalledProcessError as e:
        print("Command failed with exception:", e)

class RequestHandler(BaseHTTPRequestHandler):

    api_token = "thecakeisalie"

    def _set_response(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def _check_auth(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {self.api_token}": #change kml name
            self.send_response(401)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'message':'Unauthorized'}).encode('utf-8'))
            return False
        return True

    def do_OPTIONS(self):
        print("do_options")
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*') #find a fix for local addresses
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.end_headers()

    def do_POST(self):
        if not self._check_auth():
            return
        global video_url, video_service, video_active, takserver_password, takserver_service, takserver_address, takserver_port, takserver_cert_service, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        if self.path == '/config':
            data = post_data.decode('utf-8')
            json_data = json.loads(data)
            message_id = json_data.get('id')
            if message_id == 'initialize':
                handle_initialize(json_data)
            elif message_id == 'takserver':
                handle_takserver(json_data)
                #set_takserver_config()
            elif message_id == 'multicast':
                handle_multicast(json_data)
                #set_multicast_config()
            elif message_id == 'notification-cot':
                handle_notification_cot(json_data)
                #set_alert_cot_config()
            elif message_id == 'notification-chat':
                handle_notification_chat(json_data)
                #set_alert_chat_config()
            elif message_id == 'tracker':
                handle_tracker(json_data)
                #set_tracker_config()
            elif message_id == 'target':
                handle_target(json_data)
            elif message_id == 'target-cot':
                handle_target_cot(json_data)
            elif message_id == 'target-chat':
                handle_target_chat(json_data)
            elif message_id == 'kismet-file':
                handle_kml(json_data)
            elif message_id == 'stream-cot':
                handle_stream_cot(json_data)
                #set_target_config()
#            elif message_id == 'video':
#                handle_video(json_data)
            else:
                self.handle_default(json_data)
        elif self.path == '/uploadUserPem':
            print("/upload called...")
            content_type = self.headers['Content-Type']
            print("Content-Type:", content_type)
            upload_directory = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs")
            file_name = 'user_pem.pem'
            absolute_file_path = os.path.join(upload_directory, file_name)
            with open(absolute_file_path, 'wb') as f:
                f.write(post_data)
        elif self.path == '/uploadUserKey':
            print("/upload called...")
            content_type = self.headers['Content-Type']
            print("Content-Type:", content_type)
            upload_directory = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs")
            file_name = 'user_key.key'
            absolute_file_path = os.path.join(upload_directory, file_name)
            with open(absolute_file_path, 'wb') as f:
                f.write(post_data)
        elif self.path == '/uploadCaPem':
            print("/upload called...")
            content_type = self.headers['Content-Type']
            print("Content-Type:", content_type)
            upload_directory = os.path.expanduser("~/.kismet/plugins/atakCompanion/certs")
            file_name = 'ca_pem.pem'
            absolute_file_path = os.path.join(upload_directory, file_name)
            with open(absolute_file_path, 'wb') as f:
                f.write(post_data)
        elif self.path == '/device':
            data = post_data.decode('utf-8')
            json_data = json.loads(data)
            handle_device(json_data)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'Data received')

    def do_GET(self):
        #if not self._check_auth() and (self.path != '/kismetdb.kml' or self.path != '/networklink.kml' self.path != '/stream.kml':
        #if False:
        #    return
        #print(self.headers['Host'])
        if self.path != '/networklink.kml' and self.path != '/kismetdb.kml' and self.path != '/stream.kml':
            if not self._check_auth():
                print(self.path)
                print("didnt pass do_get, exiting...")
                return
        global kml_error, kml_service, kml_filepath, kml_file, httpd_username_status, httpd_password_status, target_chat_service, target_chat_format, target_cot_service, target_cot_type, target_cot_color, takserver_service, takserver_address, takserver_port, takserver_protocol, takserver_cert_error, takserver_cert_service, multicast_service, multicast_address, multicast_select, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_callsign, tracker_rate, tracker_cot, tracker_color, target_service, target_list, stream_cot_service, stream_cot_color, stream_cot_type
        if self.path == '/interfaces':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = {"interfaces": get_interface_addresses()}
            json_data = json.dumps(data)
            print(json_data)
            self.wfile.write(json_data.encode('utf-8'))
        elif self.path == '/persist':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = {"initialize": [httpd_username_status, httpd_password_status], "takserver": [takserver_service, takserver_address, takserver_protocol, takserver_cert_error, takserver_cert_service], "multicast": [multicast_service, multicast_select, multicast_interface, udp_service, udp_list], "notificationCot": [notification_cot_service, notification_cot_type, notification_cot_color], "notificationChat": [notification_chat_service, notification_chat_format], "tracker": [tracker_service, tracker_cot, tracker_color, tracker_rate, tracker_callsign], "target": [target_service, target_list], "targetCot": [target_cot_service, target_cot_type, target_cot_color], "targetChat": [target_chat_service, target_chat_format], "kismetFiles": [kml_files, kml_service, kml_file, kml_filepath, kml_error], "stream": [stream_cot_service, stream_cot_type, stream_cot_color]}
            json_data = json.dumps(data)
            print(json_data)
            self.wfile.write(json_data.encode('utf-8'))
        elif self.path == '/kismetdb.kml':
            if kml_filepath == "":
                return
            kml_path = os.path.expanduser("~/.kismet/plugins/atakCompanion/kml/kismetdb.kml")
            print(kml_path)
            if os.path.exists(kml_filepath):
                self.send_response(200)
                self.send_header('Content-type', 'application/vnd.google-earth.kml+xml')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(kml_path, 'rb') as file:
                    self.wfile.write(file.read())
        elif self.path == '/stream.kml':
            kml_path = os.path.expanduser("~/.kismet/plugins/atakCompanion/kml/stream.kml")
            print(kml_path)
            if os.path.exists(kml_path):
                self.send_response(200)
                self.send_header('Content-type', 'application/vnd.google-earth.kml+xml')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(kml_path, 'rb') as file:
                    self.wfile.write(file.read())
        elif self.path == '/networklink.kml':
            print('/networklink.kml...')
            create_kml_network_link("http://"+self.headers['Host']+"/stream.kml")
            kml_path = os.path.expanduser("~/.kismet/plugins/atakCompanion/kml/networklink.kml")
            print(kml_path)
            if os.path.exists(kml_path):
                self.send_response(200)
                self.send_header('Content-type', 'application/vnd.google-earth.kml+xml')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(kml_path, 'rb') as file:
                    self.wfile.write(file.read())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found in python Do_Get')

def cot_template(marker, cot_type, cot_color, cot_callsign, cot_uid, cot_message, uid_message, cot_lat, cot_lon):
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, tracker_callsign, target_service, target_list
    print("cot_template...")
    if (marker == 'spot'):
        cot_xml = ET.Element('event', version="2.0", uid=cot_uid)
        cot_xml.set('type', cot_type)
        cot_xml.set('how', 'm-g')
        cot_xml.set('time', date)
        cot_xml.set('start', date)
        cot_xml.set('stale', stale)
        point = ET.SubElement(cot_xml, 'point')
        point.set('lat', cot_lat)
        point.set('lon', cot_lon)
        point.set('hae', '0.0')
        point.set('ce', '9999999.0')
        point.set('le', '9999999.0')
        detail = ET.SubElement(cot_xml, 'detail')
        remarks = ET.SubElement(detail, 'remarks')
        remarks.text = cot_message
        usericon = remarks = ET.SubElement(detail, 'usericon')
        usericon.set('iconsetpath', 'COT_MAPPING_SPOTMAP/b-m-p-s-m/'+cot_color) #will this work?
        contact = ET.SubElement(detail, 'contact')
        contact.set('callsign', cot_callsign)
        color = ET.SubElement(detail, 'color')
        color.set('argb', cot_color)
        cot_xml_str = ET.tostring(cot_xml, encoding='utf-8', method='xml')
        print("TAK CoT Message: ")
        print(cot_xml_str.decode('utf-8'))
        return cot_xml_str

    elif (marker == 'cot'):
        iconsetpath_marker = 'COT_MAPPING_2525C/a-h/a-h-G'
        if cot_type == 'a-h-G':
            iconsetpath_marker = 'COT_MAPPING_2525C/a-h/a-h-G'
        elif cot_type == 'a-n-G':
            iconsetpath_marker = 'COT_MAPPING_2525C/a-n/a-n-G'
        elif cot_type == 'a-f-G':
            iconsetpath_marker = 'COT_MAPPING_2525C/a-f/a-f-G'

        cot_xml = ET.Element('event', version="2.0", uid=cot_uid)
        cot_xml.set('type', cot_type)
        cot_xml.set('how', 'm-g')
        cot_xml.set('time', date)
        cot_xml.set('start', date)
        cot_xml.set('stale', stale)
        point = ET.SubElement(cot_xml, 'point')
        point.set('lat', cot_lat)
        point.set('lon', cot_lon)
        point.set('hae', '0.0')
        point.set('ce', '9999999.0')
        point.set('le', '9999999.0')
        detail = ET.SubElement(cot_xml, 'detail')
        remarks = ET.SubElement(detail, 'remarks')
        remarks.text = cot_message
        usericon = remarks = ET.SubElement(detail, 'usericon')
        usericon.set('iconsetpath', iconsetpath_marker)
        contact = ET.SubElement(detail, 'contact')
        contact.set('callsign', cot_callsign)
        cot_xml_str = ET.tostring(cot_xml, encoding='utf-8', method='xml')
        print("TAK CoT Message: ")
        print(cot_xml_str.decode('utf-8'))
        return cot_xml_str

    elif (marker == 'caution'):
        cot_xml = ET.Element('event', version="2.0", uid=cot_uid)
        cot_xml.set('type', 'a-u-G')
        cot_xml.set('how', 'm-g')
        cot_xml.set('time', date)
        cot_xml.set('start', date)
        cot_xml.set('stale', stale)
        point = ET.SubElement(cot_xml, 'point')
        point.set('lat', cot_lat)
        point.set('lon', cot_lon)
        point.set('hae', '0.0')
        point.set('ce', '9999999.0')
        point.set('le', '9999999.0')
        detail = ET.SubElement(cot_xml, 'detail')
        remarks = ET.SubElement(detail, 'remarks')
        remarks.text = cot_message
        contact = ET.SubElement(detail, 'contact')
        contact.set('callsign', cot_callsign)
        usericon = ET.SubElement(detail, 'usericon')
        usericon.set('iconsetpath', 'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/caution.png')
        cot_xml_str = ET.tostring(cot_xml, encoding='utf-8', method='xml')
        print("TAK CoT Message: ")
        print(cot_xml_str.decode('utf-8'))
        return cot_xml_str

    elif (marker == 'pushpin'):
        iconsetpath_marker = 'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/wht-pushpin.png'
        if (cot_color == "-65281"):
            iconsetpath_marker = 'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/purple-pushpin.png'
        elif (cot_color == "-65536"):
            iconsetpath_marker = 'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/red-pushpin.png'
        elif (cot_color == "-256"):
            iconsetpath_marker = 'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/ylw-pushpin.png'
        elif (cot_color == "-16711936"):
            iconsetpath_marker = 'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/grn-pushpin.png'
        elif (cot_color == "-16776961"):
            iconsetpath_marker = 'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/blue-pushpin.png'
        elif (cot_color == "-16711681"):
            iconsetpath_marker = 'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/ltblu-pushpin.png'

        cot_xml = ET.Element('event', version="2.0", uid=cot_uid)
        cot_xml.set('type', 'a-u-G')
        cot_xml.set('how', 'm-g')
        cot_xml.set('time', date)
        cot_xml.set('start', date)
        cot_xml.set('stale', stale)
        point = ET.SubElement(cot_xml, 'point')
        point.set('lat', cot_lat)
        point.set('lon', cot_lon)
        point.set('hae', '0.0')
        point.set('ce', '9999999.0')
        point.set('le', '9999999.0')
        detail = ET.SubElement(cot_xml, 'detail')
        remarks = ET.SubElement(detail, 'remarks')
        remarks.text = cot_message
        color = ET.SubElement(detail, 'color')
        color.set('argb', '-1')
        contact = ET.SubElement(detail, 'contact')
        contact.set('callsign', cot_callsign)
        usericon = ET.SubElement(detail, 'usericon')
        usericon.set('iconsetpath', iconsetpath_marker)
        cot_xml_str = ET.tostring(cot_xml, encoding='utf-8', method='xml')
        print("TAK CoT Message: ")
        print(cot_xml_str.decode('utf-8'))
        return cot_xml_str

    elif (marker == 'chat'):
        cot_xml = ET.Element('event', version="2.0", uid=cot_uid)
        cot_xml.set('type', 'b-t-f')
        cot_xml.set('how', 'm-g')
        cot_xml.set('time', date)
        cot_xml.set('start', date)
        cot_xml.set('stale', stale)
        point = ET.SubElement(cot_xml, 'point')
        point.set('lat', '0.0')
        point.set('lon', '0.0')
        point.set('hae', '0.0')
        point.set('ce', '9999999.0')
        point.set('le', '9999999.0')
        detail = ET.SubElement(cot_xml, 'detail')
        chat = ET.SubElement(detail, '__chat')
        chat.set('parent', 'RootContactGroup')
        chat.set('groupOwner', 'false')
        chat.set('messageId', str(uid_message))
        chat.set('chatroom', 'All Chat Rooms')
        chat.set('id', 'All Chat Rooms')
        chat.set('senderCallsign', cot_callsign)
        chatgrp = ET.SubElement(detail, 'chatgrp')
        chatgrp.set('uid0', 'kismet')
        chatgrp.set('uid1', 'All Chat Rooms')
        chatgrp.set('id', 'All Chat Rooms')
        remarks = ET.SubElement(detail, 'remarks')
        remarks.set('source', 'kismet-chat')
        remarks.set('to', 'All Chat Rooms')
        remarks.set('time', date)
        remarks.text = cot_message
        cot_xml_str = ET.tostring(cot_xml, encoding='utf-8', method='xml')
        print("TAK CoT Message: ")
        print(cot_xml_str.decode('utf-8'))
        return cot_xml_str

    elif (marker == 'teammate'):
        cot_color_teammate = 'Cyan'
        if (cot_color == "-65281"):
            cot_color_teammate = "Purple"
        elif (cot_color == "-65536"):
            cot_color_teammate = "Red"
        elif (cot_color == "-256"):
            cot_color_teammate = "Yellow"
        elif (cot_color == "-16711936"):
            cot_color_teammate = "Green"
        elif (cot_color == "-16776961"):
            cot_color_teammate = "Blue"
        elif (cot_color == "-16711681"):
            cot_color_teammate = "Cyan"
        cot_xml = ET.Element('event', version="2.0", uid=cot_uid)
        cot_xml.set('type', cot_type)
        cot_xml.set('how', 'm-g')
        cot_xml.set('time', date)
        cot_xml.set('start', date)
        cot_xml.set('stale', stale)
        point = ET.SubElement(cot_xml, 'point')
        point.set('lat', cot_lat)
        point.set('lon', cot_lon)
        point.set('hae', '0.0')
        point.set('ce', '9999999.0')
        point.set('le', '9999999.0')
        detail = ET.SubElement(cot_xml, 'detail')
        takv = ET.SubElement(detail, 'takv')
        takv.set('os', 'linux')
        takv.set('device', 'kismet')
        takv.set('platform', 'ATAK')
        contact = ET.SubElement(detail, 'contact')
        contact.set('callsign', cot_callsign)
        uid = ET.SubElement(detail, cot_uid)
        uid.set('alertable', 'true')
        uid.set('Droid', cot_callsign)
        group = ET.SubElement(detail, '__group')
        group.set('role', 'Team Member')
        group.set('name', cot_color_teammate)
        cot_xml_str = ET.tostring(cot_xml, encoding='utf-8', method='xml')
        print("TAK CoT Message: ")
        print(cot_xml_str.decode('utf-8'))
        return cot_xml_str

def cot_send_multicast(cot, address, port, interface): #send cot over multicast
    global takserver_service, takserver_address, takserver_port, udp_service, udp_list, udp_list_filter, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("cot_send_multicast...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(interface))
    sock.sendto(cot, (address, port))
    sock.close()

def cot_send_takserver(cot): #send cot over takserver
    global takserver_cert_error, takserver_user, takserver_key, takserver_key_dec, takserver_ca, takserver_password, takserver_service, takserver_address, takserver_port, takserver_protocol
    print("cot_send_takserver...")
    if (takserver_protocol == "https"):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=takserver_user, keyfile=takserver_key_dec, password=takserver_password)
            context.load_verify_locations(cafile=takserver_ca)
            with context.wrap_socket(sock, server_side=False, server_hostname=takserver_address) as ssock:
                ssock.connect((takserver_address, 8089)) #port 8089 https
                ssock.sendall(cot)
                response = ssock.recv(4096).decode()
            takserver_cert_error = False
            set_takserver_config()
        except Exception as e:
            print(f"error connecting to takserver over https: {e}")
            takserver_cert_error = True
            set_takserver_config()
    else:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((takserver_address, 8087)) #port 8087 http
            sock.sendall(cot)
            sock.close()
            takserver_cert_error = False
            set_takserver_config()
        except Exception as e:
            print(f"error connecting to takserver over http: {e}")
            takserver_cert_error = True
            set_takserver_config()

def test_send_takserver(): #send test over takserver
    global takserver_cert_error, takserver_user, takserver_key, takserver_key_dec, takserver_ca, takserver_password, takserver_service, takserver_address, takserver_port, takserver_protocol
    print("cot_send_takserver...")
    if (takserver_protocol == "https"):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=takserver_user, keyfile=takserver_key_dec, password=takserver_password)
            context.load_verify_locations(cafile=takserver_ca)
            with context.wrap_socket(sock, server_side=False, server_hostname=takserver_address) as ssock:
                ssock.connect((takserver_address, 8089)) #port 8089 https
                #ssock.sendall("test")
                #response = ssock.recv(4096).decode()
            takserver_cert_error = False
            set_takserver_config()
        except Exception as e:
            print(f"error connecting to takserver over https: {e}")
            takserver_cert_error = True
            set_takserver_config()
    else:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((takserver_address, 8087)) #port 8087 http
            #sock.sendall("test")
            sock.close()
            takserver_cert_error = False
            set_takserver_config()
        except Exception as e:
            print(f"error connecting to takserver over http: {e}")
            takserver_cert_error = True
            set_takserver_config()

def handle_initialize(data): #ws login config
    global current_user, current_password, current_ip, uri, kml_network_link
    print("handle initialize...")
    current_ip = data.get('ip')
    #create_kml_network_link("http://"+current_ip+":8000/stream.kml")
    current_user = data.get('user')
    current_password = data.get('password')
    uri = f"ws://127.0.0.1:2501/eventbus/events.ws?user="+current_user+"&password="+current_password+""
    print(current_ip)
    print(uri)

def handle_takserver(data): #takserver config
    global takserver_service, takserver_password, takserver_address, takserver_protocol, takserver_port, takserver_cert_service, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_takserver...")
    if data.get('service') == True:
        takserver_service = True
        if data.get('key') != "":
            takserver_password = data.get('key')
        takserver_address = data.get('url')
        takserver_protocol = data.get('proto')
        if takserver_protocol == 'https':
            key_decrypt(takserver_password)
    elif data.get('service') == False:
        takserver_service = False
    takserver_cert_service = os.path.isfile(check_file1) and os.path.isfile(check_file2) and os.path.isfile(check_file3) and os.path.isfile(check_file4)
    set_takserver_config()
    test_send_takserver()
    set_takserver_config()

def handle_multicast(data): #multicast config
    global takserver_service, takserver_address, takserver_port, udp_service, udp_list, udp_list_filter, multicast_service, multicast_select, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_multicast...")
    if data.get('service') == True:
        multicast_interface = data.get('net')
        multicast_select = data.get('udp')
        multicast_service = True
        if data.get('udp') == 'default':
            multicast_address = '239.2.3.1'
            multicast_port = 6969
        elif data.get('udp') == 'sensor':
            multicast_address = '239.5.5.55'
            multicast_port = 7171
    elif data.get('service') == False:
        multicast_service = False
    if data.get('multicast') == True:
        udp_service = True
        udp_temp = data.get('clients')
        udp_list = list(filter(None, udp_temp))
        print(str(udp_list))
    elif data.get('multicast') == False:
        udp_service = False
    set_multicast_config()


def handle_notification_cot(data): #alert/notification config
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_notification_cot...")
    if data.get('service') == True:
        notification_cot_service = True
        notification_cot_type = data.get('cot')
        notification_cot_color = data.get('rgb')
    elif data.get('service') == False:
        notification_cot_service = False
    set_alert_cot_config()

def handle_notification_chat(data): #chat config
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_notification_chat...")
    if data.get('service') == True:
        notification_chat_service = True
        notification_chat_format = data.get('type')
    elif data.get('service') == False:
        notification_chat_service = False
    set_alert_chat_config()

def handle_tracker(data): #tracker config, start background tracker service (threading)
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, tracker_callsign, target_list
    print("handle_tracker...")
    if data.get('service') == True:
        tracker_cot = data.get('cot')
        tracker_color = data.get('rgb')
        tracker_rate = data.get('rate')
        tracker_callsign = data.get('name') #filter to replace spaces with underscores...
        tracker_service = True
        if tracker_callsign == "":
            tracker_callsign = "kismet-tracker"
        start_tracker_service()
    elif data.get('service') == False:
        tracker_service = False
    set_tracker_config()

def handle_target(data): #store target list submitted
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_target...")
    if data.get('service') == True:
        target_service = True
        target_temp = data.get('targets')
        target_list = list(filter(None, target_temp))
        print(str(target_list))
    elif data.get('service') == False:
        target_service = False
    set_target_config()

def handle_target_cot(data): #target cot config
    global target_chat_service, target_chat_format, target_cot_service, target_cot_type, target_cot_color, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format
    print("handle_target_cot...")
    if data.get('service') == True:
        target_cot_service = True
        target_cot_type = data.get('cot')
        target_cot_color = data.get('rgb')
    elif data.get('service') == False:
        target_cot_service = False
    set_target_cot_config()

def handle_target_chat(data): #target chat config
    global target_chat_service, target_chat_format, target_cot_service, target_cot_type, target_cot_color, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format
    print("handle_target_chat...")
    if data.get('service') == True:
        target_chat_service = True
        target_chat_format = data.get('type')
    elif data.get('service') == False:
        target_chat_service = False
    set_target_chat_config()

def handle_kml(data):
    global kml_file, kml_service, kml_filepath, kml_error
    print("handle_kml...")
    if True:
        kml_service = True
        kml_file = data.get('file')
        kml_filepath = data.get('directory')
        if len(kml_filepath) > 2 and kml_filepath[0] != "/":
            kml_filepath = "/" + kml_filepath
        get_kismet_files();
        kml_path = os.path.expanduser("~/.kismet/plugins/atakCompanion/kml/kismetdb.kml")
        if kml_file != "" and kml_filepath != "":
            try:
                if os.path.exists(kml_path):
                    command1 = ["rm", kml_path]
                    result1 = subprocess.run(command1, capture_output=True, text=True, check=True)
                    if result1.returncode == 0:
                        print("Command executed successfully.")
                        print("Output:", result1.stdout)
                    else:
                        kml_error = True
                        print("Command failed with error code:", result1.returncode)
                        print("Error output:", result1.stderr)
                command = ["kismetdb_to_kml", "--in", os.path.join(kml_filepath, kml_file), "--out", kml_path]
                print(command)
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                if result.returncode == 0:
                    kml_error = False
                    print("Command executed successfully.")
                    print("Output:", result.stdout)
                else:
                    kml_error = True
                    print("Command failed with error code:", result.returncode)
                    print("Error output:", result.stderr)
            except subprocess.CalledProcessError as e:
                kml_error = True
                print("Command failed with exception:", e)
    #elif False:
    #    kml_service = False
    #set_kml_config()

def handle_stream_cot(data): #alert/notification config
    global stream_cot_service, stream_cot_type, stream_cot_color, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface
    print("handle_stream_cot...")
    if data.get('service') == True:
        stream_cot_service = True
        stream_cot_type = data.get('cot')
        stream_cot_color = data.get('rgb')
    elif data.get('service') == False:
        stream_cot_service = False
    set_stream_cot_config()


#def handle_video(data): #video submitted
#    global video_url, video_service, video_active
#    print("handle_video...")
#    if data.get('service') == True:
#        video_service = True
#        video_url = data.get('url')
#    elif data.get('service') == False:
#        video_service = False

#def start_recording(device, start_timestamp):
#    global video_url, video_active, video_service, current_timestamp, device_seen, httpd_username, httpd_password
#    device_timestamp = 0
#    print("start_recording")
#    cap = cv2.VideoCapture(video_url)
#    if not cap.isOpened():
#        print("error: could not open video")
#    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#    fourcc = cv2.VideoWriter_fourcc(*'XVID')
#    out = cv2.VideoWriter('/home/pi/junk/'+device+'_'+str(start_timestamp)+'.avi', fourcc, 1.0, (frame_width, frame_height))
#    response = requests.get("http://localhost:2501/devices/by-mac/"+device+"/devices.json?user="+httpd_username+"&password="+httpd_password+"")
#    if response.status_code == 200:
#        data = response.json()
#        device_timestamp = data[0]['kismet.device.base.last_time']
#    print(current_timestamp)
#    print(device_timestamp)
#    print("recording STARTED...")
#    if video_service == True:
#        while current_timestamp - device_timestamp < 30 and current_timestamp - start_timestamp < 300:
#            response = requests.get("http://localhost:2501/devices/by-mac/"+device+"/devices.json?user="+httpd_username+"&password="+httpd_password+"")
#            if response.status_code == 200:
#                data = response.json()
#                device_timestamp = data[0]['kismet.device.base.last_time']
           # video_active = True
#            ret, frame = cap.read()
#            if ret:
#                out.write(frame)
#            else:
#                break
#        cap.release()
#        out.release()
#        cv2.destroyAllWindows()
       # video_active = False
#        print("recording STOPPED...")

def handle_device(data): #tak-fwd cot, hard coded hostile marker
    print("handle_device...")
    device_lat = str(data.get('lat'))
    device_lon = str(data.get('lon'))
    device = str(data.get('device'))
    #marker = "cot" #saved for tak-forwarder config maybe?
    #if (notification_cot_type == "a-f-G-U-C"):
    #    marker = "teammate"
    #elif (notification_cot_type == "b-m-p-s-m"):
    #    marker = "spot"
    #elif (notification_cot_type == "pushpin"):
    #    marker = "pushpin"
    #elif (notification_cot_type == "caution"):
    #    marker = "caution"
    if (multicast_service):
        print("send tak-fwd cot over multicast")
        cot = cot_template('cot', 'a-h-G', 'red', device, device, "", device, device_lat, device_lon)
        cot_send_multicast(cot, multicast_address, multicast_port, multicast_interface)
    if (udp_service):
        for clients in udp_list:
            print("send tak-fwd cot over udp")
            cot = cot_template('cot', 'a-h-G', 'red', device, device, "", device, device_lat, device_lon)
            cot_send_multicast(cot, clients, 4242, multicast_interface)
    if (takserver_service):
        print("send tak-fwd cot over takserver")
        cot = cot_template('cot', 'a-h-G', 'red', device, device, "", device, device_lat, device_lon)
        cot_send_takserver(cot)

def handle_default(data):
    print("handle_default...")

def get_config():
    print("get_config...")
    global stream_cot_service, stream_cot_type, stream_cot_color, kml_error, kml_service, kml_file, kml_filepath, target_chat_service, target_chat_format, target_cot_service, target_cot_type, target_cot_color, udp_service, udp_list, udp_list_filter, takserver_cert_error, takserver_service, takserver_address, takserver_port, takserver_protocol, takserver_cert_service, takserver_password, multicast_service, multicast_address, multicast_select, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_callsign, tracker_cot, tracker_color, target_service, target_list, target_list_filter
    config.read(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'))

    # takserver details
    takserver_password = config['TAKSERVER']['password']
    takserver_cert_error = eval(config['TAKSERVER']['cert_error'])
    takserver_service = eval(config['TAKSERVER']['service'])
    takserver_address = config['TAKSERVER']['hostname']
    takserver_port = int(config['TAKSERVER']['port'])
    takserver_protocol = config['TAKSERVER']['protocol']

    # multicast details
    multicast_service = eval(config['MULTICAST']['service'])
    multicast_select = config['MULTICAST']['select']
    multicast_address = config['MULTICAST']['address']
    multicast_port = int(config['MULTICAST']['port'])
    multicast_interface = config['MULTICAST']['interface']
    udp_service = eval(config['UDP']['service'])
    udp_list = config['UDP']['clients'].split(',')
    udp_list_filter = config['UDP']['clients_filter'].split(',')

    # alert/notification chat details
    notification_chat_service = eval(config['ALERTS']['chat_service'])
    notification_chat_format = config['ALERTS']['chat_format']

    # alert/notification cot details
    notification_cot_service = eval(config['ALERTS']['cot_service'])
    notification_cot_type = config['ALERTS']['cot_type']
    notification_cot_color = config['ALERTS']['cot_color']

    # TAK tracker details
    tracker_service = eval(config['TRACKER']['service'])
    tracker_callsign = config['TRACKER']['callsign']
    tracker_rate = int(config['TRACKER']['rate'])
    tracker_cot = config['TRACKER']['cot_type']
    tracker_color = config['TRACKER']['cot_color']

    # target details
    target_service = eval(config['TARGET']['service'])
    target_list = config['TARGET']['targets'].split(',')
    target_list_filter = config['TARGET']['targets_filter'].split(',')

    # target chat details
    target_chat_service = eval(config['TARGET']['chat_service'])
    target_chat_format = config['TARGET']['chat_format']

    # target cot details
    target_cot_service = eval(config['TARGET']['cot_service'])
    target_cot_type = config['TARGET']['cot_type']
    target_cot_color = config['TARGET']['cot_color']

    # kml details
    #kml_file = config['KML']['file']
    #kml_service = eval(config['KML']['service'])
    #kml_filepath = config['KML']['filepath']
    #kml_error = eval(config['KML']['error'])

    # stream cot details
    stream_cot_service = eval(config['STREAM']['cot_service'])
    stream_cot_type = config['STREAM']['cot_type']
    stream_cot_color = config['STREAM']['cot_color']


def set_takserver_config():
    global config, takserver_service, takserver_address, takserver_port, takserver_cert_error, takserver_cert_service, takserver_password, takserver_protocol, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    # takserver details
    config['TAKSERVER']['password'] = str(takserver_password)
    config['TAKSERVER']['cert_error'] = str(takserver_cert_error)
    config['TAKSERVER']['service'] = str(takserver_service)
    config['TAKSERVER']['hostname'] = takserver_address
    config['TAKSERVER']['port'] = str(takserver_port)
    config['TAKSERVER']['protocol'] = takserver_protocol
    with open(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'), 'w') as configfile:
        config.write(configfile)
    print("updated changes to atakCompanionConfig.ini file")

def set_multicast_config():
    global config, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_select, multicast_port, multicast_interface, udp_service, udp_list, udp_list_filter, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    # multicast details
    config['MULTICAST']['service'] = str(multicast_service)
    config['MULTICAST']['select'] = multicast_select
    config['MULTICAST']['address'] = multicast_address
    config['MULTICAST']['port'] = str(multicast_port)
    config['MULTICAST']['interface'] = multicast_interface
    config['UDP']['service'] = str(udp_service)
    config['UDP']['clients'] = (',').join(udp_list)
    config['UDP']['clients_filter'] = (',').join(udp_list_filter)
    with open(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'), 'w') as configfile:
        config.write(configfile)
    print("updated changes to atakCompanionConfig.ini file")

def set_alert_chat_config():
    global config, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    # alert/notification chat details
    config['ALERTS']['chat_service'] = str(notification_chat_service)
    config['ALERTS']['chat_format'] = notification_chat_format
    with open(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'), 'w') as configfile:
        config.write(configfile)
    print("updated changes to atakCompanionConfig.ini file")

def set_alert_cot_config():
    global config, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    # alert/notification cot details
    config['ALERTS']['cot_service'] = str(notification_cot_service)
    config['ALERTS']['cot_type'] = notification_cot_type
    config['ALERTS']['cot_color'] = notification_cot_color
    with open(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'), 'w') as configfile:
        config.write(configfile)
    print("updated changes to atakCompanionConfig.ini file")

def set_tracker_config():
    global config, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_callsign, tracker_color, target_service, target_list
    # TAK tracker details
    config['TRACKER']['service'] = str(tracker_service)
    config['TRACKER']['callsign'] = tracker_callsign
    config['TRACKER']['rate'] = str(tracker_rate)
    config['TRACKER']['cot_type'] = tracker_cot
    config['TRACKER']['cot_color'] = tracker_color
    with open(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'), 'w') as configfile:
        config.write(configfile)
    print("updated changes to atakCompanionConfig.ini file")

def set_target_config():
    global config, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    # target details
    config['TARGET']['service'] = str(target_service)
    config['TARGET']['targets'] = (',').join(target_list)
    config['TARGET']['targets_filter'] = (',').join(target_list_filter)
    with open(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'), 'w') as configfile:
        config.write(configfile)
    print("updated changes to atakCompanionConfig.ini file")

def set_target_chat_config():
    global config, target_chat_service, target_chat_format, target_cot_service, target_cot_type, target_cot_color
    # target chat details
    config['TARGET']['chat_service'] = str(target_chat_service)
    config['TARGET']['chat_format'] = target_chat_format
    with open(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'), 'w') as configfile:
        config.write(configfile)
    print("updated changes to atakCompanionConfig.ini file")

def set_target_cot_config():
    global config, target_chat_service, target_chat_format, target_cot_service, target_cot_type, target_cot_color
    # target cot details
    config['TARGET']['cot_service'] = str(target_cot_service)
    config['TARGET']['cot_type'] = target_cot_type
    config['TARGET']['cot_color'] = target_cot_color
    with open(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'), 'w') as configfile:
        config.write(configfile)
    print("updated changes to atakCompanionConfig.ini file")

def set_kml_config():
    global kml_service, kml_file, kml_filepath, kml_error
    config['KML']['service'] = str(kml_service)
    if kml_file != "":
        config['KML']['file'] = kml_file
    if kml_filepath != "":
        config['KML']['filepath'] = str(kml_filepath)
    config['KML']['error'] = str(kml_error)
    with open(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'), 'w') as configfile:
        config.write(configfile)
    print("updated changes to atakCompanionConfig.ini file")

def set_stream_cot_config():
    global config, stream_cot_service, stream_cot_type, stream_cot_color, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface
    # stream cot details
    config['STREAM']['cot_service'] = str(stream_cot_service)
    config['STREAM']['cot_type'] = stream_cot_type
    config['STREAM']['cot_color'] = stream_cot_color
    with open(os.path.expanduser('~/.kismet/plugins/atakCompanion/persist/atakCompanionConfig.ini'), 'w') as configfile:
        config.write(configfile)
    print("updated changes to atakCompanionConfig.ini file")



def handle_gps(data): #ws eventbus gps_location
    global current_lat, current_lon, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    current_lat = str(data.get('kismet.common.location.geopoint')[1])
    current_lon = str(data.get('kismet.common.location.geopoint')[0])
    #print("handle_gps...")

def handle_alert(data): #ws eventbus alerts
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_alert...")
    print(data)
    alert_severity = data.get('kismet.alert.severity')
    alert_header = data.get('kismet.alert.header')
    alert_class = data.get('kismet.alert.class')
    alert_text = data.get('kismet.alert.text')
    alert_timestamp = data.get('kismet.alert.timestamp')
    alert_dest = data.get('kismet.alert.dest_mac')
    alert_src = data.get('kismet.alert.source_mac')
    alert_tx = data.get('kismet.alert.transmitter_mac')
    name = "Alert"
    if (alert_severity == 20):
        name = "Alert: Critical"
    elif (alert_severity == 15):
        name = "Alert: High"
    elif (alert_severity == 10):
        name = "Alert: Medium"
    elif (alert_severity == 5):
        name = "Alert: Low"
    elif (alert_severity == 0):
        name = "Alert: Info"
    alert_remark = alert_header + ", " + str(alert_class) + ", " + str(name) + ", " + str(alert_text) + ", Destination MAC: " + str(alert_dest) + ", Source MAC: " + str(alert_src) + ", Transmitter MAC: " + str(alert_tx)
    #alert_remark = name + ", " + alert_text
    trigger_target(alert_remark, alert_src)

def handle_message(data): #ws eventbus messages
    global current_lat, current_lon, target_list_found, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    #print("handle_message...")
    if target_service == True:
        device = data.get('kismet.messagebus.message_string')
        for target in target_list:
            if target in device:
                print("target match from handle_message")
                print(target)
                trigger_target_geo(device, target, current_lat, current_lon)
                #start_recording_service(target)

def handle_monitor(name, mac, lat, lon): #ws monitor device/target matched
    global target_list, target_service, stream_cot_service, device_array
    #print("handle_monitor...")
    if target_service == True:
        for target in target_list:
            if target in mac:
                print("target match of device_mac from handle_monitor...")
                remark = "Found: " + mac
                trigger_target_geo(remark, target, lat, lon)
            if target in name:
                print("target match of device_name from handle_monitor...")
                remark = "Found: " + name
                trigger_target_geo(remark, target, lat, lon)
    elif stream_cot_service == True:
        trigger_stream_geo("#kismet", name, lat, lon)

def handle_timestamp(data):
    global current_timestamp
    #print("handle_timestamp...")
    current_timestamp = data.get('kismet.system.timestamp.sec')

def trigger_target(remarks, target): #used by kismet alerts and tak tracker
    global current_lat, current_lon, takserver_service, takserver_address, takserver_port, udp_service, udp_list, udp_list_filter, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("trigger_target")
    if (notification_cot_service):
        print("send notification cot")
        if (current_lat != "0.0" and current_lon != "0.0"):
            marker = "cot"
            if (notification_cot_type == "a-f-G-U-C"):
                marker = "teammate"
            elif (notification_cot_type == "b-m-p-s-m"):
                marker = "spot"
            elif (notification_cot_type == "pushpin"):
                marker = "pushpin"
            elif (notification_cot_type == "caution"):
                marker = "caution"
            if (multicast_service):
                print("send notification cot over multicast")
                cot = cot_template(marker, notification_cot_type, notification_cot_color, target, target, remarks, target, current_lat, current_lon)
                cot_send_multicast(cot, multicast_address, multicast_port, multicast_interface)
            if (udp_service):
                for clients in udp_list:
                    print("send notification cot over udp")
                    cot = cot_template(marker, notification_cot_type, notification_cot_color, target, target, remarks, target, current_lat, current_lon)
                    cot_send_multicast(cot, clients, 4242, multicast_interface)
            if (takserver_service):
                print("send notification cot over takserver")
                cot = cot_template(marker, notification_cot_type, notification_cot_color, target, target, remarks, target, current_lat, current_lon)
                cot_send_takserver(cot)
    if (notification_chat_service):
        print("send notification chat")
        if (multicast_service):
            print("send notification chat over multicast")
            cot = cot_template("chat", "cot_type", "cot_color", "Kismet-Chat-Multicast", "uid_chat_temporary3", remarks, random.uniform(1000, 0), current_lat, current_lon)
            cot_send_multicast(cot, multicast_address, multicast_port, multicast_interface)
        if (udp_service):
            for clients in udp_list:
                print("send notification chat over udp")
                cot = cot_template("chat", "cot_type", "cot_color", "Kismet-Chat-Udp", "uid_chat_temporary3", remarks, random.uniform(1000, 0), current_lat, current_lon)
                cot_send_multicast(cot, clients, 4242, multicast_interface)
        if (takserver_service):
            print("send notification chat over takserver")
            cot = cot_template("chat", "cot_type", "cot_color", "Kismet-Chat-Takserver", "uid_chat_temporary4", remarks, random.uniform(1000, 0), current_lat, current_lon)
            cot_send_takserver(cot)

def trigger_target_geo(remarks, target, lat, lon): #used by monitor ws for targets
    global current_timestamp, target_chat_service, target_chat_format, target_cot_service, target_cot_type, target_cot_color, udp_service, udp_list, udp_list_filter, current_lat, current_lon, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("trigger_target_geo")
    if (target_cot_service):
        print("send notification cot")
        if (lat != "0.0" and lon != "0.0"):
            marker = "cot"
            if (target_cot_type == "a-f-G-U-C"):
                marker = "teammate"
            elif (target_cot_type == "b-m-p-s-m"):
                marker = "spot"
            elif (target_cot_type == "pushpin"):
                marker = "pushpin"
            elif (target_cot_type == "caution"):
                marker = "caution"
            if (multicast_service):
                print("send target cot over multicast")
                cot = cot_template(marker, target_cot_type, target_cot_color, target, target, remarks, target, lat, lon)
                cot_send_multicast(cot, multicast_address, multicast_port, multicast_interface)
            if (udp_service):
                for clients in udp_list:
                    print("send target cot over udp")
                    cot = cot_template(marker, target_cot_type, target_cot_color, target, target, remarks, target, lat, lon)
                    cot_send_multicast(cot, clients, 4242, multicast_interface)
            if (takserver_service):
                print("send target cot over takserver")
                cot = cot_template(marker, target_cot_type, target_cot_color, target, target, remarks, target, lat, lon)
                cot_send_takserver(cot)
    if (target_chat_service):
        print("send notification chat")
        current_timestamp_str = str(current_timestamp)[:7]
        if (multicast_service):
            print("send notification chat over multicast")
            cot = cot_template("chat", "cot_type", "cot_color", "Kismet-Chat-Multicast", target, remarks, target+current_timestamp_str, lat, lon)
            cot_send_multicast(cot, multicast_address, multicast_port, multicast_interface)
        if (udp_service):
            for clients in udp_list:
                print("send notification chat over udp")
                cot = cot_template("chat", "cot_type", "cot_color", "Kismet-Chat-Udp", target, remarks, target+current_timestamp_str, lat, lon)
                cot_send_multicast(cot, clients, 4242, multicast_interface)
        if (takserver_service):
            print("send notification chat over takserver")
            cot = cot_template("chat", "cot_type", "cot_color", "Kismet-Chat-Takserver", target, remarks, target+current_timestamp_str, lat, lon)
            cot_send_takserver(cot)

def trigger_stream_geo(remarks, target, lat, lon): #used by monitor ws for targets
    global current_timestamp, stream_cot_service, stream_cot_type, stream_cot_color, target_chat_service, target_chat_format, target_cot_service, target_cot_type, target_cot_color, udp_service, udp_list, udp_list_filter, current_lat, current_lon,  takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface
    #print("trigger_stream_geo")
    if (stream_cot_service):
        #print("send stream cot")
        if (lat != "0.0" and lon != "0.0"):
            marker = "cot"
            if (stream_cot_type == "a-f-G-U-C"):
                marker = "teammate"
            elif (stream_cot_type == "b-m-p-s-m"):
                marker = "spot"
            elif (stream_cot_type == "pushpin"):
                marker = "pushpin"
            elif (stream_cot_type == "caution"):
                marker = "caution"
            if (multicast_service):
                print("send target cot over multicast")
                cot = cot_template(marker, stream_cot_type, stream_cot_color, target, target, remarks, target, lat, lon)
                cot_send_multicast(cot, multicast_address, multicast_port, multicast_interface)
            if (udp_service):
                for clients in udp_list:
                    print("send target cot over udp")
                    cot = cot_template(marker, stream_cot_type, stream_cot_color, target, target, remarks, target, lat, lon)
                    cot_send_multicast(cot, clients, 4242, multicast_interface)
            if (takserver_service):
                print("send target cot over takserver")
                cot = cot_template(marker, stream_cot_type, stream_cot_color, target, target, remarks, target, lat, lon)
                cot_send_takserver(cot)

def trigger_tracker():
    global current_lat, current_lon, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, udp_service, udp_list, udp_list_filter, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("tracker trigger")
    while (tracker_service == True):
        if (current_lat != "0.0" and current_lon != "0.0"):
            marker = "cot"
            if (tracker_cot == "a-f-G-U-C"):
                marker = "teammate"
            elif (tracker_cot == "b-m-p-s-m"):
                marker = "spot"
            elif (tracker_cot == "pushpin"):
                marker = "pushpin"
            elif (tracker_cot == "caution"):
                marker = "caution"
            if (multicast_service == True):
                print("send tracker cot over multicast")
                cot = cot_template(marker, tracker_cot, tracker_color, tracker_callsign, tracker_callsign, "", "", current_lat, current_lon)
                cot_send_multicast(cot, multicast_address, multicast_port, multicast_interface)
            if (udp_service == True):
                for clients in udp_list:
                    print("send tracker cot over udp")
                    cot = cot_template(marker, tracker_cot, tracker_color, tracker_callsign, tracker_callsign, "", "", current_lat, current_lon)
                    cot_send_multicast(cot, clients, 4242, multicast_interface)
            if (takserver_service == True):
                print("send tracker cot over takserver")
                cot = cot_template(marker, tracker_cot, tracker_color, tracker_callsign, tracker_callsign, "", "", current_lat, current_lon)
                cot_send_takserver(cot)
            time.sleep(int(tracker_rate))

def target_find_mac(target):
    print("target_find_mac...")

def create_kml_network_link(link):
    print("create_kml_network_link...")
    with open(os.path.expanduser("~/.kismet/plugins/atakCompanion/kml/networklink.kml"), 'w') as file:
        file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        file.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        file.write('  <Document>\n')
        file.write('    <name>KML</name>\n')
        file.write('    <description>KML Network Link</description>\n')
        file.write('    <NetworkLink\n')
        file.write('        <name>Dynamic Data</name>\n')
        file.write('        <description>External Source</description>\n')
        file.write('        <Link>\n')
        file.write(f'          <href>{link}</href>\n')
        file.write('          <refreshMode>onInterval</refreshMode>\n')
        file.write('          <refreshInterval>3600</refreshInterval>\n')
        file.write('        </Link>\n')
        file.write('    </NetworkLink>\n')
        file.write('  </Document>\n')
        file.write('</kml>\n')

def update_kml():
    global device_array
    while True:
        print("update_kml...")
        create_kml(device_array)
        time.sleep(60)

def create_kml(arr):
    #print("create_kml...")
    global device_array
    with open(os.path.expanduser("~/.kismet/plugins/atakCompanion/kml/stream.kml"), 'w') as file:
        file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        file.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        file.write('  <Document>\n')
        for device in arr:
            location = "0,0"
            name = device.get('name')
            if device.get('location') and len(device.get('location')) == 2:
                lat = str(device['location'][1])
                lon = str(device['location'][0])
                location = lon+","+lat
            if location != "0,0":
                file.write('    <Placemark>\n')
                file.write(f'      <name>{name}</name>\n')
                file.write('      <Point>\n')
                file.write(f'        <coordinates>{location}</coordinates>\n')
                file.write('      </Point>\n')
                file.write('    </Placemark>\n')
        file.write('  </Document>\n')
        file.write('</kml>\n')

   #for device in device_array:
   #    print(device['name'])
   #    print(device['mac'])
   #    print(device['location'])

def add_device_filter(arr, device):
    global device_array
    for i, obj in enumerate(arr):
        if obj['name'] == device['name']:
            #print("obj already exists, updating lat/lon")
            arr[i] = device
            return
        #if obj.get('location') and len(obj.get('location') == 2:
        #obj['location'] = device['location']
        #print(obj.get('location'))
    arr.append(device)

def check_services():
    global tracker_service
    if tracker_service == True:
        start_tracker_service()
    start_kml_service()

def start_tracker_service(): #start tracker pings in threading so other code can continue to run
    tracker_thread = threading.Thread(target=trigger_tracker)
    tracker_thread.daemon = True
    tracker_thread.start()

def start_kml_service():
    kml_thread = threading.Thread(target=update_kml)
    kml_thread.daemon = True
    kml_thread.start()

#def start_recording_service(device): #start video url recording in threading so other code can continue to run
#    video_thread = threading.Thread(target=start_recording, args=(device,current_timestamp))
#    video_thread.daemon = True
#    video_thread.start()

async def update_date():
    global current_time, date, stale
    while True:
        current_time = datetime.now()
        date = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        stale = (current_time + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        await asyncio.sleep(10)

async def subscribe_to_ws_monitor():
    global uri_monitor, device_array
    print("subscribe_to_ws_monitor is running")
    while True:
        try:
            async with websockets.connect(uri_monitor) as websocket:
                subscription_message = {"monitor": "*", "request":69696, "rate":10, "fields": ["kismet.device.base.macaddr", "kismet.device.base.location/kismet.common.location.last/kismet.common.location.geopoint", "kismet.device.base.last_time", "kismet.device.base.signal/kismet.common.signal.last_signal", "kismet.device.base.commonname", "kismet.device.base.key", "kismet.device.base.name"],}
                await websocket.send(json.dumps(subscription_message))

                while True:
                    data = await websocket.recv()
                    json_data = json.loads(data)
                    device_name = json_data.get('kismet.device.base.commonname')
                    device_mac = json_data.get('kismet.device.base.macaddr')
                    device_location = json_data.get('kismet.common.location.geopoint') #last location seen
                    device_object = {"name":device_name, "mac":device_mac, "location":device_location}
                    #device_array.append(device_object)
                    if device_location and len(device_location) == 2:
                        device_lat = str(json_data['kismet.common.location.geopoint'][1])
                        device_lon = str(json_data['kismet.common.location.geopoint'][0])
                    elif current_lat != "0.0" and current_lon != "0.0":
                        device_lat = current_lat
                        device_lon = current_lon
                    else:
                        device_lat = "0.0"
                        device_lon = "0.0"
                    device_location = [device_lon, device_lat]
                    device_object = {"name":device_name, "mac":device_mac, "location":device_location}
                    add_device_filter(device_array, device_object)
                    handle_monitor(device_name, device_mac, device_lat, device_lon)
                    #print("Received message:", json_data)
        except Exception as e:
            print("WebSocket connection closed. Reconnecting ws_monitor...")
            await asyncio.sleep(5) #reconnect to ws every 5 sec

async def subscribe_to_ws():
    global uri
    print("subscribe_to_ws is running")
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                topics = ["TIMESTAMP", "ALERT", "GPS_LOCATION", "MESSAGE"] #kismet ws event topics
                for topic in topics:
                    subscription_message = {"SUBSCRIBE": topic}
                    await websocket.send(json.dumps(subscription_message))

                while True:
                    data = await websocket.recv()
                    json_data = json.loads(data)
                    if json_data.get('GPS_LOCATION'):
                        gps_data = json_data.get('GPS_LOCATION')
                        handle_gps(gps_data)
                    elif json_data.get('ALERT'):
                        alert_data = json_data.get('ALERT')
                        handle_alert(alert_data)
                    elif json_data.get('MESSAGE'):
                        message_data = json_data.get('MESSAGE')
                        handle_message(message_data)
                    elif json_data.get('TIMESTAMP'):
                        message_data = json_data.get('TIMESTAMP')
                        handle_timestamp(message_data)
                    #print("Received message:", json_data)
        except Exception as e:
            print("WebSocket connection closed. Reconnecting...")
            await asyncio.sleep(5) #reconnect to ws every 5 sec

async def main_ws():
    while True: #while loop to attempt to reconnect to ws if disconnected
        await asyncio.gather(
            #subscribe_to_ws(),
            subscribe_to_ws_monitor(),
            update_date(),
        )

def main_server(server_class=HTTPServer, handler_class=RequestHandler, host='', port=8000):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    httpd
    print(f'Starting server on port {port}...')
    get_config()
    check_services()
    httpd.serve_forever()

if __name__ == '__main__':

    http_thread = threading.Thread(target=main_server)
    http_thread.start() #starts http api server
    asyncio.run(main_ws()) #starts websocket connection
    #asyncio.run(monitor_ws()) #starts websocket connection
