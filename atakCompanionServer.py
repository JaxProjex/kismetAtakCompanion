from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, HTTPServer #python api server
import xml.etree.ElementTree as ET #readable cot template
#import socketserver
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
#import cv2 #for opencv video recording

current_time = datetime.now() #system time
date = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
stale = (current_time + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
current_timestamp = 0 #kismet time seconds
device_seen = 0

current_ip = ""
current_user = ""
current_password = ""

#kismet api gps
current_lat = "0.0"
current_lon = "0.0"

# TAKServer details
takserver_user = 'certs/user_pem.pem' #update file paths .kismet/plugins/myTest
takserver_key = 'certs/user_key.key'
takserver_key_dec = 'certs/user_key_dec.key'
takserver_ca = 'certs/ca_pem.pem'
takserver_password = ""
takserver_cert_service = False
takserver_service = False
takserver_address = ""
takserver_port = ""
takserver_protocol = ""

# multicast details
multicast_service = False
multicast_select = ""
multicast_address = ""
multicast_port = ""
multicast_interface = ""

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
tracker_rate = ""
tracker_cot = ""
tracker_color = ""

# target details
target_service = False
target_list = []
target_list_filter = []
[target_list_filter.append(x) for x in target_list if x not in target_list_filter]

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

if (httpd_username is not None and httpd_password is not None):
    uri = f"ws://127.0.0.1:2501/eventbus/events.ws?user="+httpd_username+"&password="+httpd_password+""

def get_addresses(): #get network interface ips, not needed anymore until errors with get_interface_addresses arises
    local_ips = []
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            ip_pattern = r'inet (\d+\.\d+\.\d+\.\d+)'
            ip_addresses = re.findall(ip_pattern, output)
            for ip in ip_addresses:
                if not ip.startswith('127.'):
                    local_ips.append(ip)
    except Exception as e:
        print("Error:", e)
    local_addresses = local_ips
    return local_ips

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
    try:
        command = ["openssl", "rsa", "-passin", "pass:"+password, "-in", "certs/user_key.key", "-out", "certs/user_key_dec.key"]
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

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*') #unsat, find a fix for local addresses
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        global video_url, video_service, video_active, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
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
            elif message_id == 'multicast':
                handle_multicast(json_data)
            elif message_id == 'notification-cot':
                handle_notification_cot(json_data)
            elif message_id == 'notification-chat':
                handle_notification_chat(json_data)
            elif message_id == 'tracker':
                handle_tracker(json_data)
            elif message_id == 'target':
                handle_target(json_data)
#            elif message_id == 'video':
#                handle_video(json_data)
            else:
                self.handle_default(json_data)
        elif self.path == '/uploadUserPem':
            print("/upload called...")
            content_type = self.headers['Content-Type']
            print("Content-Type:", content_type)
            upload_directory = 'certs'
            file_name = 'user_pem.pem'
            absolute_file_path = os.path.join(upload_directory, file_name)
            with open(absolute_file_path, 'wb') as f:
                f.write(post_data)
        elif self.path == '/uploadUserKey':
            print("/upload called...")
            content_type = self.headers['Content-Type']
            print("Content-Type:", content_type)
            upload_directory = 'certs'
            file_name = 'user_key.key'
            absolute_file_path = os.path.join(upload_directory, file_name)
            with open(absolute_file_path, 'wb') as f:
                f.write(post_data)
        elif self.path == '/uploadCaPem':
            print("/upload called...")
            content_type = self.headers['Content-Type']
            print("Content-Type:", content_type)
            upload_directory = 'certs'
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
        global httpd_username_status, httpd_password_status, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_select, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_callsign, tracker_rate, tracker_cot, tracker_color, target_service, target_list
        if self.path == '/interfaces':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
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
            data = {"initialize": [httpd_username_status, httpd_password_status], "takserver": [takserver_service, takserver_address, takserver_port], "multicast": [multicast_service, multicast_select, multicast_interface], "notificationCot": [notification_cot_service, notification_cot_type, notification_cot_color], "notificationChat": [notification_chat_service, notification_chat_format], "tracker": [tracker_service, tracker_cot, tracker_color, tracker_rate, tracker_callsign], "target": [target_service, target_list]}
            json_data = json.dumps(data)
            print(json_data)
            self.wfile.write(json_data.encode('utf-8'))
        else:
            super().do_GET()
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
        contact = ET.SubElement(detail, 'contact')
        contact.set('callsign', cot_callsign)
        color = ET.SubElement(detail, 'color')
        color.set('argb', cot_color)
        cot_xml_str = ET.tostring(cot_xml, encoding='utf-8', method='xml')
        print("TAK CoT Message: ")
        print(cot_xml_str.decode('utf-8'))
        return cot_xml_str

    if (marker == 'cot'):
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
        color.set('argb', cot_color)
        contact = ET.SubElement(detail, 'contact')
        contact.set('callsign', cot_callsign)
        usericon = ET.SubElement(detail, 'usericon')
        usericon.set('iconsetpath', 'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/wht-pushpin.png')
        cot_xml_str = ET.tostring(cot_xml, encoding='utf-8', method='xml')
        print("TAK CoT Message: ")
        print(cot_xml_str.decode('utf-8'))
        return cot_xml_str

    if (marker == 'chat'):
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
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("cot_send_multicast...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(interface))
    sock.sendto(cot, (address, port))
    sock.close()

def cot_send_takserver(cot): #send cot over takserver
    global takserver_cert_service, takserver_user, takserver_key, takserver_key_dec, takserver_ca, takserver_password, takserver_service, takserver_address, takserver_port, takserver_protocol
    print("cot_send_takserver...")
    if (takserver_protocol == "https"):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=takserver_user, keyfile=takserver_key_dec, password=takserver_password)
        context.load_verify_locations(cafile=takserver_ca)
        with context.wrap_socket(sock, server_side=False, server_hostname=takserver_address) as ssock:
            ssock.connect((takserver_address, 8089)) #port 8089 https
            ssock.sendall(cot)
            response = ssock.recv(4096).decode()
    elif takserver_protocol == "http":
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((takserver_address, 8087)) #port 8087 http
        sock.sendall(cot)
        sock.close()

def handle_initialize(data): #ws login config
    global current_user, current_password, uri
    print("handle initialize...")
    current_user = data.get('user')
    current_password = data.get('password')
    uri = f"ws://127.0.0.1:2501/eventbus/events.ws?user="+current_user+"&password="+current_password+""
    print(current_user)
    print(current_password)
    print(uri)

def handle_takserver(data): #takserver config
    global takserver_service, takserver_address, takserver_protocol, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_takserver...")
    if data.get('service') == True:
        takserver_service = True
        takserver_password = data.get('key')
        takserver_address = data.get('url')
        takserver_protocol = data.get('proto')
        if takserver_protocol == 'https':
            key_decrypt(data.get('key'))
    elif data.get('service') == False:
        takserver_service = False

def handle_multicast(data): #multicast config
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_select, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_multicast...")
    multicast_interface = data.get('net')
    multicast_select = data.get('udp')
    if data.get('service') == True:
        multicast_service = True
        if data.get('udp') == 'default':
            multicast_address = '239.2.3.1'
            multicast_port = 6969
        elif data.get('udp') == 'sensor':
            multicast_address = '239.5.5.55'
            multicast_port = 7171
        elif data.get('udp') == 'chat':
            multicast_address = '224.10.10.1'
            multicast_port = 17012
    elif data.get('service') == False:
        multicast_service = False
    print(data.get('net'))
    print(multicast_interface)

def handle_notification_cot(data): #alert/notification config
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_notification_cot...")
    if data.get('service') == True:
        notification_cot_service = True
        notification_cot_type = data.get('cot')
        notification_cot_color = data.get('rgb')
    elif data.get('service') == False:
        notification_cot_service = False

def handle_notification_chat(data): #chat config
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_notification_chat...")
    if data.get('service') == True:
        notification_chat_service = True
        notification_chat_format = data.get('type')
    elif data.get('service') == False:
        notification_chat_service = False

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

def handle_target(data): #store target list submitted
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    print("handle_target...")
    if data.get('service') == True:
        target_service = True
        target_list = data.get('targets')
        print(str(target_list))
    elif data.get('service') == False:
        target_service = False

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

def handle_device(data):
    print("handle_device...")
    device_lat = str(data.get('lat'))
    device_lon = str(data.get('lon'))
    device = str(data.get('device'))
    if (notification_cot_service):
        print("send notification cot")
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
            cot = cot_template(marker, notification_cot_type, notification_cot_color, device, device, "", device, device_lat, device_lon)
            cot_send_multicast(cot, multicast_address, multicast_port, multicast_interface)
        if (takserver_service):
            print("send notification cot over takserver")
            cot = cot_template(marker, notification_cot_type, notification_cot_color, device, device, "", device, device_lat, device_lon)
            cot_send_takserver(cot)


def handle_default(data):
    print("handle_default...")

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
    trigger_target(alert_remark, alert_src)

def handle_message(data): #ws eventbus messages
    global takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
    #print("handle_message...")
    if (target_service == True):
        device = data.get('kismet.messagebus.message_string')
        for target in target_list:
            if target in device:
                print("target match from handle_message")
                print(target)
                trigger_target(device, target)
                start_recording_service(target)

def handle_timestamp(data):
    global current_timestamp
    #print("handle_timestamp...")
    current_timestamp = data.get('kismet.system.timestamp.sec')

def trigger_target(remarks, target): #used by kismet alerts and tak tracker
    global current_lat, current_lon, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
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
            if (takserver_service):
                print("send notification cot over takserver")
                cot = cot_template(marker, notification_cot_type, notification_cot_color, target, target, remarks, target, current_lat, current_lon)
                cot_send_takserver(cot)
        if (notification_chat_service):
            print("send notification chat")
            if (multicast_service):
                print("send notification chat over multicast")
                cot = cot_template("chat", "cot_type", "cot_color", "Kismet-Chat-multicast", "uid_chat_temporary3", remarks, random.uniform(1000, 0), current_lat, current_lon)
                cot_send_multicast(cot, multicast_address, multicast_port, multicast_interface)
            if (takserver_service):
                print("send notification chat over takserver")
                cot = cot_template("chat", "cot_type", "cot_color", "Kismet-Chat-takserver", "uid_chat_temporary4", remarks, random.uniform(1000, 0), current_lat, current_lon)
                cot_send_takserver(cot)

def trigger_tracker():
    global current_lat, current_lon, takserver_service, takserver_address, takserver_port, multicast_service, multicast_address, multicast_port, multicast_interface, notification_chat_service, notification_chat_format, notification_cot_service, notification_cot_type, notification_cot_color, tracker_service, tracker_rate, tracker_cot, tracker_color, target_service, target_list
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
            if (takserver_service == True):
                print("send tracker cot over takserver")
                cot = cot_template(marker, tracker_cot, tracker_color, tracker_callsign, tracker_callsign, "", "", current_lat, current_lon)
                cot_send_takserver(cot)
            time.sleep(int(tracker_rate))

def start_tracker_service(): #start tracker pings in threading so other code can continue to run
    tracker_thread = threading.Thread(target=trigger_tracker)
    tracker_thread.daemon = True
    tracker_thread.start()

#def start_recording_service(device): #start video url recording in threading so other code can continue to run
#    video_thread = threading.Thread(target=start_recording, args=(device,current_timestamp))
#    video_thread.daemon = True
#    video_thread.start()



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
        await subscribe_to_ws()

def main_server(server_class=HTTPServer, handler_class=RequestHandler, host='', port=8000):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':

    http_thread = threading.Thread(target=main_server)
    http_thread.start() #starts http api server

    asyncio.run(main_ws()) #starts websocket connection
