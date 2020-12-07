#!/usr/bin/env python3
from __future__ import division
from websocket import WebSocketApp
from tinydb import TinyDB
from sys import exit, stdout
from os import path
from time import time

import logging, json, mido, base64, argparse

try:
   from dbj import dbj
except ImportError:
   print("Could not import dbj. Please install it using 'pip install dbj'")

TEMPLATES = {
"ToggleSourceVisibility": """{
  "request-type": "GetSceneItemProperties",
  "message-id": "%d",
  "item": "%s"
}""",
"ReloadBrowserSource": """{
  "request-type": "GetSourceSettings",
  "message-id": "%d",
  "sourceName": "%s"
}""",
"ToggleSourceFilter": """{
  "request-type": "GetSourceFilterInfo",
  "message-id": "%d",
  "sourceName": "%s",
  "filterName": "%s"
}""",
"SetCurrentScene": """{
  "request-type": "GetCurrentScene",
  "message-id": "%d",
  "_unused": "%s"
}""",
"SetPreviewScene": """{
  "request-type": "GetPreviewScene",
  "message-id": "%d",
  "_unused": "%s"
}""",
"ReleaseTBar": """{
  "request-type": "ReleaseTBar",
  "message-id": "ReleaseTBarPlease"
}""",
"ResetTBar": """{
  "request-type": "SetTBarPosition",
  "message-id": "ResetTBar",
  "release": true,
  "position": %s
}"""
}

SCRIPT_DIR = path.dirname(path.realpath(__file__))

parser = argparse.ArgumentParser(description='MIDItoOBS')

parser.add_argument('--config', 
                    default='config.json', 
                    help='Path to config file. Default: ./config.json')

parser.add_argument('--port', 
                    default=4444,
                    type=int,
                    help='Set port. Default: 4444')

parser.add_argument('--host', 
                    default='localhost', 
                    help='Hostname. Default: localhost')

args = parser.parse_args()


def map_scale(inp, ista, isto, osta, osto):
    return osta + (osto - osta) * ((inp - ista) / (isto - ista))

def get_logger(name, level=logging.INFO):
    log_format = logging.Formatter('[%(asctime)s] (%(levelname)s) T%(thread)d : %(message)s')

    std_output = logging.StreamHandler(stdout)
    std_output.setFormatter(log_format)
    std_output.setLevel(level)

    file_output = logging.FileHandler(path.join(SCRIPT_DIR, "debug.log"))
    file_output.setFormatter(log_format)
    file_output.setLevel(level)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_output)
    logger.addHandler(std_output)
    return logger

class DeviceHandler:
    def __init__(self, device, deviceid):
        self.log = get_logger("midi_to_obs_device")
        self._id = deviceid
        self._devicename = device["devicename"]
        self._port_in = 0
        self._port_out = 0

        try:
            self.log.debug("Attempting to open midi port `%s`" % self._devicename)
            # a device can be input, output or ioport. in the latter case it can also be the other two
            # so we first check if we can use it as an ioport
            if self._devicename in mido.get_ioport_names():
                self._port_in = mido.open_ioport(name=self._devicename, callback=self.callback, autoreset=True)
                self._port_out = self._port_in
            # otherwise we try to use it separately as input and output
            else:
                if self._devicename in mido.get_input_names():
                    self._port_in = mido.open_input(name=self._devicename, callback=self.callback)
                if self._devicename in mido.get_output_names():
                    self._port_out = mido.open_output(name=self._devicename, callback=self.callback, autoreset=True)
        except:
            self.log.critical("\nCould not open device `%s`" % self._devicename)
            self.log.critical("The midi device might be used by another application/not plugged in/have a different name.")
            self.log.critical("Please close the device in the other application/plug it in/select the rename option in the device management menu and restart this script.")
            self.log.critical("Currently connected devices:")
            for name in mido.get_input_names():
                self.log.critical("  - %s" % name)
            # EIO 5 (Input/output error)
            exit(5)

    def callback(self, msg):
        handler.handle_midi_input(msg, self._id, self._devicename)

    def close(self):
        if self._port_in:
            self._port_in.close()
        # when it's an ioport we don't want to close the port twice
        if self._port_out and self._port_out != self._port_in:
            self._port_out.close()
        self._port_in = 0
        self._port_out = 0

class MidiHandler:
    # Initializes the handler class
    def __init__(self, config_path=args.config, ws_server=args.host, ws_port=args.port):
        # Setting up logging first and foremost
        self.log = get_logger("midi_to_obs")

        # Internal service variables
        self._action_buffer = []
        self._action_counter = 2
        self._portobjects = []
        self._lastTbarMove = time()
        self._tbarActive = False
        self._tbarDir = 0

        # Feedback blocking
        self.blockcount=0
        self.block = False
        
        #load tinydb configuration database
        self.log.debug("Trying to load config file  from %s" % config_path)
        tiny_database = TinyDB(config_path, indent=4)
        tiny_db = tiny_database.table("keys", cache_size=20)
        tiny_devdb = tiny_database.table("devices", cache_size=20)

        #get all mappings and devices
        self._mappings = tiny_db.all()
        self._devices = tiny_devdb.all()

        #open dbj datebase for mapping and clear
        self.mappingdb = dbj("temp-mappingdb.json")
        self.mappingdb.clear()

        #convert database to dbj in-memory
        for _mapping in self._mappings:
            self.mappingdb.insert(_mapping)

        self.log.debug("Mapping database: `%s`" % str(self.mappingdb.getall()))

        if len(self.mappingdb.getall()) < 1:
            self.log.critical("Could not cache device mappings")
            # ENOENT (No such file or directory)
            exit(2)

        self.log.debug("Successfully imported mapping database")

        result = tiny_devdb.all()
        if not result:
            self.log.critical("Config file %s doesn't exist or is damaged" % config_path)
            # ENOENT (No such file or directory)
            exit(2)

        self.log.info("Successfully parsed config file")

        self.log.debug("Retrieved MIDI port name(s) `%s`" % result)
        #create new class with handler and open from there, just create new instances
        for device in result:
            self._portobjects.append((DeviceHandler(device, device.doc_id), device.doc_id))

        self.log.info("Successfully initialized midi port(s)")
        del result

        # close tinydb
        tiny_database.close()

        # setting up a Websocket client
        self.log.debug("Attempting to connect to OBS using websocket protocol")
        self.obs_socket = WebSocketApp("ws://%s:%d" % (ws_server, ws_port))
        self.obs_socket.on_message = lambda ws, message: self.handle_obs_message(ws, message)
        self.obs_socket.on_error = lambda ws, error: self.handle_obs_error(ws, error)
        self.obs_socket.on_close = lambda ws: self.handle_obs_close(ws)
        self.obs_socket.on_open = lambda ws: self.handle_obs_open(ws)

    def getPortObject(self, mapping):
        deviceID = mapping.get("out_deviceID", mapping["deviceID"])
        for portobject, _deviceID in self._portobjects:
            if _deviceID == deviceID:
                return portobject

    def handle_midi_input(self, message, deviceID, deviceName):
        self.log.debug("Received %s %s %s %s %s", str(message), "from device", deviceID, "/", deviceName)

        if message.type == "note_on":
            return self.handle_midi_button(deviceID, message.channel, message.type, message.note)

        # `program_change` messages can be only used as regular buttons since
        # they have no extra value, unlike faders (`control_change`)
        if message.type == "program_change":
            return self.handle_midi_button(deviceID, message.channel, message.type, message.program)

        if message.type == "control_change":
            return self.handle_midi_fader(deviceID, message.channel, message.control, message.value)


    def handle_midi_button(self, deviceID, channel, type, note):
        results = self.mappingdb.getmany(self.mappingdb.find('msg_channel == %s and msg_type == "%s" and msgNoC == %s and deviceID == %s' % (channel, type, note, deviceID)))

        if not results:
            self.log.debug("Cound not find action for note %s", note)
            return

        for result in results:
            if self.send_action(result):
                pass

    def handle_midi_fader(self, deviceID, channel, control, value):
        results = self.mappingdb.getmany(self.mappingdb.find('msg_channel == %s and msg_type == "control_change" and msgNoC == %s and deviceID == %s' % (channel, control, deviceID)))

        if not results:
            self.log.debug("Cound not find action for fader %s", control)
            return
        if self.block == True:
            if self.blockcount <=4:
                self.log.debug("Blocked incoming message due to sending message")
                self.block=False
                self.blockcount+=1
        else:
            self.blockcount=0
            for result in results:
                input_type = result["input_type"]
                action = result["action"]

                if input_type == "button":
                    if value == 127 and not self.send_action(result):
                        continue

                if input_type == "fader":
                    command = result["cmd"]
                    scaled = map_scale(value, 0, 127, result["scale_low"], result["scale_high"])

                    if command == "SetSourceScale":
                        self.obs_socket.send(action.format(scaled))

                    # Super dirty hack but @AlexDash says that it works
                    # @TODO: find an explanation _why_ it works
                    if command == "SetVolume":
                        # Yes, this literally raises a float to a third degree
                        self.obs_socket.send(action % scaled**3)

                    if command in ["SetGainFilter", "SetOpacity", "SetColorCorrectionHueShift", "Filter/Chroma Key - Contrast", "Filter/Chroma Key - Brightness", "Filter/Chroma Key - Gamma", "Filter/Luma Key - Luma Max", "Filter/Luma Key - Luma Max Smooth", "Filter/Luma Key - Luma Min", "Filter/Luma Key - Luma Min Smooth", "Filter/Color Correction - Saturation", "Filter/Color Correction - Contrast", "Filter/Color Correction - Brightness", "Filter/Color Correction - Gamma", "Filter/Color Correction - Hue Shift", "Filter/Color Key - Brightness", "Filter/Color Key - Contrast", "Filter/Color Key - Gamma", "Filter/Sharpen - Sharpness"]:
                        self.obs_socket.send(action % scaled)

                    if command in ["SetSourceRotation", "SetTransitionDuration", "SetSyncOffset", "SetSourcePosition", "Filter/Chroma Key - Opacity", "Filter/Chroma Key - Spill Reduction", "Filter/Chroma Key - Similarity", "Filter/Color Key - Similarity", "Filter/Color Key - Smoothness", "Filter/Scroll - Horizontal Speed", "Filter/Scroll - Vertical Speed"]:
                        self.obs_socket.send(action % int(scaled))

                    if command == "MoveTbar":
                       self._lastTbarMove = time()
                       self._tbarActive = True
                       if self._tbarDir:
                          self.obs_socket.send(action % scaled)
                       else:
                          self.obs_socket.send(action % map_scale(value, 0, 127, result["scale_high"], result["scale_low"]))

                       if value == 0:
                          self._tbarDir = True
                       elif value == 127:
                          self._tbarDir = False
                       if value == 0 or value == 127:
                          self._tbarActive = False
                          self.obs_socket.send(TEMPLATES.get("ReleaseTBar"))
                          self.log.debug("releasing t-bar because of end reached")

    def handle_obs_message(self, ws, message):
        self.log.debug("Received new message from OBS")
        payload = json.loads(message)

        self.log.debug("Successfully parsed new message from OBS: %s" % message)

        if "error" in payload:
            self.log.error("OBS returned error: %s" % payload["error"])
            return

        if "message-id" in payload:
            message_id = payload["message-id"]

            self.log.debug("Looking for action with message id `%s`" % message_id)
            for action in self._action_buffer:
                (buffered_id, template, kind) = action

                if buffered_id != int(payload["message-id"]):
                    continue

                del buffered_id
                self.log.info("Action `%s` was requested by OBS" % kind)

                if kind == "ToggleSourceVisibility":
                    # Dear lain, I so miss decent ternary operators...
                    invisible = "false" if payload["visible"] else "true"
                    self.obs_socket.send(template % invisible)
                elif kind == "ReloadBrowserSource":
                    source = payload["sourceSettings"]["url"]
                    target = source[0:-1] if source[-1] == '#' else source + '#'
                    self.obs_socket.send(template % target)
                elif kind == "ToggleSourceFilter":
                    invisible = "false" if payload["enabled"] else "true"
                    self.obs_socket.send(template % invisible)
                elif kind in ["SetCurrentScene", "SetPreviewScene"]:
                    self.sceneChanged(kind, payload["name"])

                self.log.debug("Removing action with message id %s from buffer" % message_id)
                self._action_buffer.remove(action)
                break

            if message_id == "MIDItoOBSscreenshot":
                if payload["status"] == "ok":
                    with open(str(time()) + ".png", "wb") as fh:
                        fh.write(base64.decodebytes(payload["img"][22:].encode()))

        elif "update-type" in payload:
            update_type = payload["update-type"]
            self.log.debug(update_type)
            request_types = {"PreviewSceneChanged": "SetPreviewScene", "SwitchScenes": "SetCurrentScene"}
            if update_type in request_types:
                scene_name = payload["scene-name"]
                self.sceneChanged(request_types[update_type], scene_name)
            elif update_type == "SourceVolumeChanged":
                self.volChanged(payload["sourceName"],payload["volume"])

            # let's abuse the fact that obs sends many updates that we don't have to rely on a timer for the t-bar timeout
            # we don't actually want the use to make use of the timeout because it brings the hardware fader out of sync and there will
            # be a value jump with the next transition
            if self._tbarActive and time() - self._lastTbarMove > 30: #30 sec timeout
                self.log.debug("releasing t-bar because of timeout")
                self.obs_socket.send(TEMPLATES.get("ResetTBar") % int(self._tbarDir))
                self._lastTbarMove = time()
                self._tbarActive = False

    def volChanged(self, source_name, volume):
        self.log.info("Volume "+source_name+" changed to val: "+str(volume))
        results = self.mappingdb.getmany(self.mappingdb.find('input_type == "fader" and bidirectional == 1'))
        if not results:
            self.log.info("no fader results")
            return
        for result in results:
            j=result["action"]%"0"
            k=json.loads(j)["source"]
            self.log.info(k)
            if k == source_name:
                val = int(map_scale(volume, result["scale_low"], result["scale_high"], 0, 127))
                self.log.debug(val)

                msgNoC = result.get("out_msgNoC", result["msgNoC"])
                self.log.info(msgNoC)
                portobject = self.getPortObject(result)
                if portobject and portobject._port_out:
                    self.block=True
                    portobject._port_out.send(mido.Message('control_change', channel=0, control=int(result["msgNoC"]), value=val))


    def sceneChanged(self, event_type, scene_name):
        self.log.debug("Scene changed, event: %s, name: %s" % (event_type, scene_name))
        # only buttons can change the scene, so we can limit our search to those
        results = self.mappingdb.getmany(self.mappingdb.find('input_type == "button" and bidirectional == 1'))
        if not results:
            return
        for result in results:
            j = json.loads(result["action"])
            if j["request-type"] != event_type:
                continue
            msgNoC = result.get("out_msgNoC", result["msgNoC"])
            channel = result.get("out_channel", 0)
            portobject = self.getPortObject(result)
            if portobject and portobject._port_out:
                if result["msg_type"] == "control_change":
                    value = 127 if j["scene-name"] == scene_name else 0
                    portobject._port_out.send(mido.Message(type="control_change", channel=channel, control=msgNoC, value=value))
                elif result["msg_type"] == "note_on":
                    velocity = 1 if j["scene-name"] == scene_name else 0
                    portobject._port_out.send(mido.Message(type="note_on", channel=channel, note=msgNoC, velocity=velocity))

    def handle_obs_error(self, ws, error=None):
        # Protection against potential inconsistencies in `inspect.ismethod`
        if error is None and isinstance(ws, BaseException):
            error = ws

        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            self.log.info("Keyboard interrupt received, gracefully exiting...")
        else:
            self.log.error("Websocket error: %" % str(error))

    def handle_obs_close(self, ws):
        self.log.error("OBS has disconnected, timed out or isn't running")
        self.log.error("Please reopen OBS and restart the script")
        self.close(teardown=True)

    def handle_obs_open(self, ws):
        self.log.info("Successfully connected to OBS")

        # initialize bidirectional controls
        self.send_action({"action": 'GetCurrentScene', "request": "SetCurrentScene", "target": ":-)"})
        self.send_action({"action": 'GetPreviewScene', "request": "SetPreviewScene", "target": ":-)"})

    def send_action(self, action_request):
        action = action_request.get("action")
        if not action:
            # @NOTE: this potentionally should never happen but you never know
            self.log.error("No action supplied in current request")
            return False

        request = action_request.get("request")
        if not request:
            self.log.debug("No request body for action %s, sending action" % action)
            self.obs_socket.send(action)
            # Success, breaking the loop
            return True

        template = TEMPLATES.get(request)
        if not template:
            self.log.error("Missing template for request %s" % request)
            # Keep searching
            return False

        target = action_request.get("target")
        if not target:
            self.log.error("Missing target in %s request for %s action" % (request, action))
            # Keep searching
            return False

        field2 = action_request.get("field2")
        if not field2:
            field2 = False

        self._action_buffer.append([self._action_counter, action, request])
        if field2:
            self.obs_socket.send(template % (self._action_counter, target, field2))
        else:
            self.obs_socket.send(template % (self._action_counter, target))
        self._action_counter += 1

        # Explicit return is necessary here to avoid extra searching
        return True

    def start(self):
        self.log.info("Connecting to OBS...")
        self.obs_socket.run_forever()

    def close(self, teardown=False):
        # set bidirectional controls to their 0 state (i.e., turn off LEDs)
        self.log.debug("Attempting to turn off bidirectional controls")
        result = self.mappingdb.getmany(self.mappingdb.find('bidirectional == 1'))
        if result:
            for row in result:
                msgNoC = row.get("out_msgNoC", row["msgNoC"])
                channel = row.get("out_channel", 0)
                portobject = self.getPortObject(row)
                if portobject and portobject._port_out:
                    if row["msg_type"] == "control_change":
                        portobject._port_out.send(mido.Message(type="control_change", channel=channel, control=msgNoC, value=0))
                    elif row["msg_type"] == "note_on":
                        portobject._port_out.send(mido.Message(type="note_on", channel=channel, note=msgNoC, velocity=0))

        self.log.debug("Attempting to close midi port(s)")
        for portobject, _ in self._portobjects:
              portobject.close()

        self.log.info("Midi connection has been closed successfully")

        # If close is requested during keyboard interrupt, let the websocket
        # client tear itself down and make a clean exit
        if not teardown:
            self.log.debug("Attempting to close OBS connection")
            self.obs_socket.close()

            self.log.info("OBS connection has been closed successfully")

        self.log.info("Config file has been successfully released")

    def __end__(self):
        self.log.info("Exiting script...")
        self.close()

if __name__ == "__main__":
    handler = MidiHandler()
    handler.start()
