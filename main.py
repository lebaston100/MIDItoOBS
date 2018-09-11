from __future__ import division
import mido, websocket, threading, sys, json, atexit, ast, time
from tinydb import TinyDB, Query

####Change IP and Port here
serverIP = "localhost"
serverPort = "4444"
####

db = TinyDB("config.json", cache_size=0)
jsonArchive = {"ToggleSourceVisibility": """{"request-type": "GetSceneItemProperties", "message-id" : "%s", "item": "%s"}""",
               "GetBrowserSourceURL": """{"request-type": "GetSourceSettings", "message-id" : "%s", "sourceName": "%s"}"""}
actionbuffer = []
actioncounter = 2

def midicallback(message):
    global actioncounter
    if message.type == "note_on":
        result = db.search((Query().msg_type == message.type) & (Query().msgNoC == message.note))
        if result:
            for res in result:
                if "request" in res:
                    if res["request"] == "ToggleSourceVisibility":
                        obsrequest = jsonArchive["ToggleSourceVisibility"] % (str(actioncounter), res["target"])
                        actionbuffer.append([str(actioncounter), res["action"], res["request"]])
                        obs_ws.send(obsrequest)
                        actioncounter += 1
                    elif res["request"] == "ReloadBrowserSource":
                        obsrequest = jsonArchive["GetBrowserSourceURL"] % (str(actioncounter), res["target"])
                        actionbuffer.append([str(actioncounter), res["action"], res["request"]])
                        obs_ws.send(obsrequest)
                        actioncounter += 1
                else:
                    string = res["action"]
                    obs_ws.send(string)
        print(message)
    elif message.type == "program_change": #program_change messages can be used as buttons. they have no extra value so no fader control
        Search = Query()
        result = db.search((Search.msg_type == message.type) & (Search.msgNoC == message.program))
        if result:
            for res in result:
                if "request" in res:
                    if res["request"] == "ToggleSourceVisibility":
                        obsrequest = jsonArchive["ToggleSourceVisibility"] % (str(actioncounter), res["target"])
                        actionbuffer.append([str(actioncounter), res["action"], res["request"]])
                        obs_ws.send(obsrequest)
                        actioncounter += 1
                    elif res["request"] == "ReloadBrowserSource":
                        obsrequest = jsonArchive["GetBrowserSourceURL"] % (str(actioncounter), res["target"])
                        actionbuffer.append([str(actioncounter), res["action"], res["request"]])
                        obs_ws.send(obsrequest)
                        actioncounter += 1
                else:
                    string = res["action"]
                    obs_ws.send(string)
        print(message)
    elif message.type == "control_change":
        results = db.search((Query().msg_type == message.type) & (Query().msgNoC == message.control))
        if results:
            for result in results:
                if  result["input_type"] == "button":
                    if message.value == 127:
                        if "request" in result:
                            if result["request"] == "ToggleSourceVisibility":
                                obsrequest = jsonArchive["ToggleSourceVisibility"] % (str(actioncounter), result["target"])
                                actionbuffer.append([str(actioncounter), result["action"], result["request"]])
                                obs_ws.send(obsrequest)
                                actioncounter += 1
                            elif res["request"] == "ReloadBrowserSource":
                                obsrequest = jsonArchive["GetBrowserSourceURL"] % (str(actioncounter), res["target"])
                                actionbuffer.append([str(actioncounter), res["action"], res["request"]])
                                obs_ws.send(obsrequest)
                                actioncounter += 1
                        else:
                            string = result["action"]
                            obs_ws.send(string)
                elif  result["input_type"] == "fader":
                    if result["cmd"] == "SetSourcePosition":
                        scaled = scalemap(message.value, 0, 127, result["scale_low"], result["scale_high"])
                        string = result["action"] % (scaled)
                        obs_ws.send(string)
                    elif result["cmd"] == "SetSourceRotation":
                        scaled = scalemap(message.value, 0, 127, result["scale_low"], result["scale_high"])
                        string = result["action"] % (int(scaled))
                        obs_ws.send(string)
                    elif result["cmd"] == "SetVolume":
                        scaled = scalemap(message.value, 0, 127, result["scale_low"], result["scale_high"])
                        string = result["action"] % (scaled)**3
                        obs_ws.send(string)
                    elif result["cmd"] == "SetTransitionDuration":
                        scaled = scalemap(message.value, 0, 127, result["scale_low"], result["scale_high"])
                        string = result["action"] % (int(scaled))
                        obs_ws.send(string)
                    elif result["cmd"] == "SetSyncOffset":
                        scaled = scalemap(message.value, 0, 127, result["scale_low"], result["scale_high"])
                        string = result["action"] % (int(scaled))
                        obs_ws.send(string)
                    elif result["cmd"] == "SetSourceScale":
                        scaled = scalemap(message.value, 0, 127, result["scale_low"], result["scale_high"])
                        string = result["action"] % (scaled)
                        obs_ws.send(string)
        print(message)

def exitScript():
    print("Exiting...")
    db.close()
    port.close()

def obs_on_message(ws, message):
    global actioncounter
    jsn = json.loads(message)
    if "error" in jsn:
        print("Error: %s" % jsn["error"])
    else:
        for line in actionbuffer:
            if jsn["message-id"] == line[0]:
                if line[2] == "ToggleSourceVisibility":
                    if jsn["visible"] == False:
                        render = "true"
                    else:
                        render = "false"
                    obs_ws.send(line[1] % render)
                elif line[2] == "ReloadBrowserSource":
                    url = jsn["sourceSettings"]["url"]
                    if url[-1] == "#":
                        url = url[0:-1]
                    else:
                        url += "#"
                    obs_ws.send(line[1] % url)
                actionbuffer.remove([line[0], line[1], line[2]])
                break
            
def obs_on_error(ws, error):
    print("Websocket Error: %" % str(error))

def obs_on_close(ws):
    print("OBS disconnected/timed out/is not running. Please restart script with OBS open.")

def obs_on_open(ws):
    print("OBS connected")
    
def obs_start():
    obs_ws.run_forever()

def scalemap(inp, ista, isto, osta, osto):
    return osta + (osto - osta) * ((inp - ista) / (isto - ista))

if __name__ == "__main__":
    print("MIDItoOBS made by github.com/lebaston100")
    print("!!MAKE SURE OBS IS RUNNING OR THIS SCRIPT WILL CRASH!!")
    print("Main program started")
    result = db.search(Query().type.exists())
    if result:
        try:
            port = mido.open_input(result[0]["value"], callback=midicallback)
        except:
            print("The midi device you setup is not connected or now under a different name.")
            print("Please plugin in the device or run setup.py again and restart this script.")
            time.sleep(8)
            sys.exit()
        obs_ws = websocket.WebSocketApp("ws://" + serverIP + ":" + serverPort, on_message = obs_on_message, on_error = obs_on_error, on_close = obs_on_close)
        obs_ws.on_open = obs_on_open
        atexit.register(exitScript)
        threading.Thread(target=obs_start).start()
    else:
        print("Please run setup.py")
        time.sleep(5)
        sys.exit()
