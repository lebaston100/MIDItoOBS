from __future__ import division
from websocket import WebSocketApp
from tinydb import TinyDB, Query
from sys import exit, stdout
from os import path
from time import time

import logging, json, mido, base64

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
}"""
}

SCRIPT_DIR = path.dirname(path.realpath(__file__))

def map_scale(inp, ista, isto, osta, osto):
    return osta + (osto - osta) * ((inp - ista) / (isto - ista))

def get_logger(name, level=logging.INFO):
    log_format = logging.Formatter('[%(asctime)s] (%(levelname)s) %(thread)d : %(message)s')

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
        self._port = 0

        try:
            self.log.debug("Attempting to open midi port `%s`" % self._devicename)
            self._port = mido.open_input(name=self._devicename, callback=self.callback)
        except:
            self.log.critical("\nCould not open", self._devicename)
            self.log.critical("The midi device might be used by another application/not plugged in/have a different name.")
            self.log.critical("Please close the device in the other application/plug it in/select the rename option in the device management menu and restart this script.\n")
            # EIO 5 (Input/output error)
            exit(5)
        
    def callback(self, msg):
        handler.handle_midi_input(msg, self._id, self._devicename)

    def close(self):
        self._port_close()

class MidiHandler:
    # Initializes the handler class
    def __init__(self, config_path="config.json", ws_server="localhost", ws_port=4444):
        # Setting up logging first and foremost
        self.log = get_logger("midi_to_obs")

        # Internal service variables
        self._action_buffer = []
        self._action_counter = 2
        self._portobjects = []

        self.log.debug("Trying to load config file  from %s" % config_path)
        self.database = TinyDB(config_path, indent=4)
        self.db = self.database.table("keys", cache_size=100)
        self.devdb = self.database.table("devices", cache_size=20)
        
        result = self.devdb.all()
        if not result:
            self.log.critical("Config file %s doesn't exist or is damaged" % config_path)
            # ENOENT (No such file or directory)
            exit(2)

        self.log.info("Successfully parsed config file")

        self.log.debug("Retrieved MIDI port name(s) `%s`" % result)
        #create new class with handler and open from there, just create new instances
        for device in result:
            self._portobjects.append(DeviceHandler(device, device.doc_id))

        del result

        self.log.info("Successfully initialized midi port(s)")

        # Properly setting up a Websocket client
        self.log.debug("Attempting to connect to OBS using websocket protocol")
        self.obs_socket = WebSocketApp("ws://%s:%d" % (ws_server, ws_port))
        self.obs_socket.on_message = self.handle_obs_message
        self.obs_socket.on_error = self.handle_obs_error
        self.obs_socket.on_close = self.handle_obs_close
        self.obs_socket.on_open = self.handle_obs_open

    def handle_midi_input(self, message, deviceID, deviceName):
        self.log.debug("Received %s %s %s %s %s", str(message), "from device", deviceID, "/", deviceName)

        if message.type == "note_on":
            return self.handle_midi_button(deviceID, message.type, message.note)

        # `program_change` messages can be only used as regular buttons since
        # they have no extra value, unlike faders (`control_change`)
        if message.type == "program_change":
            return self.handle_midi_button(deviceID, message.type, message.program)

        if message.type == "control_change":
            return self.handle_midi_fader(deviceID, message.control, message.value)


    def handle_midi_button(self, deviceID, type, note):
        query = Query()
        results = self.db.search((query.msg_type == type) & (query.msgNoC == note) & (query.deviceID == deviceID))

        if not results:
            self.log.debug("Cound not find action for note %s", note)
            return

        for result in results:
            if self.send_action(result):
                pass

    def handle_midi_fader(self, deviceID, control, value):
        query = Query()
        results = self.db.search((query.msg_type == "control_change") & (query.msgNoC == control) & (query.deviceID == deviceID))

        if not results:
            self.log.debug("Cound not find action for fader %s", control)
            return

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

                if command == "SetGainFilter":
                    self.obs_socket.send(action % scaled)

                if command == "SetSourceRotation" or command == "SetTransitionDuration" or command == "SetSyncOffset" or command == "SetSourcePosition":
                    self.obs_socket.send(action % int(scaled))

    def handle_obs_message(self, message):
        self.log.debug("Received new message from OBS")
        payload = json.loads(message)

        self.log.debug("Successfully parsed new message from OBS")

        if "error" in payload:
            self.log.error("OBS returned error: %s" % payload["error"])
            return

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

            self.log.debug("Removing action with message id %s from buffer" % message_id)
            self._action_buffer.remove(action)
            break
        
        if message_id == "MIDItoOBSscreenshot":
            if payload["status"] == "ok":
                with open(str(time()) + ".png", "wb") as fh:
                    fh.write(base64.decodebytes(payload["img"][22:].encode()))
                

    def handle_obs_error(self, ws, error=None):
        # Protection against potential inconsistencies in `inspect.ismethod`
        if error is None and isinstance(ws, BaseException):
            error = ws

        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            self.log.info("Keyboard interrupt received, gracefully exiting...")
            self.close(teardown=True)
        else:
            self.log.error("Websocket error: %" % str(error))

    def handle_obs_close(self, ws):
        self.log.error("OBS has disconnected, timed out or isn't running")
        self.log.error("Please reopen OBS and restart the script")

    def handle_obs_open(self, ws):
        self.log.info("Successfully connected to OBS")

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
        self.log.debug("Attempting to close midi port(s)")
        result = self.devdb.all()
        for device in result:
            device.close()

        self.log.info("Midi connection has been closed successfully")

        # If close is requested during keyboard interrupt, let the websocket
        # client tear itself down and make a clean exit
        if not teardown:
            self.log.debug("Attempting to close OBS connection")
            self.obs_socket.close()

            self.log.info("OBS connection has been closed successfully")

        self.log.debug("Attempting to close TinyDB instance on config file")
        self.db.close()

        self.log.info("Config file has been successfully released")

    def __end__(self):
        self.log.info("Exiting script...")
        self.close()

if __name__ == "__main__":
    handler = MidiHandler()
    handler.start()
