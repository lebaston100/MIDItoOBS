import mido, websocket, threading, sys, json, atexit, ast
from tinydb import TinyDB, Query

db = TinyDB("config.json", cache_size=0)

jsonArchive = {"SetSceneItemPosition": """{"request-type" : "SetSceneItemPosition", "message-id" : "1", "item": "%s", "scene-name": "%s", "x": %s, "y": %s}""",
               "SetSceneItemTransform": """{"request-type" : "SetSceneItemTransform", "message-id" : "1", "item": "%s", "scene-name": "%s", "x-scale": %s, "y-scale": %s, "rotation": %s}"""}

actionbuffer = []
actioncounter = 2

def midicallback(message):
    global actioncounter
    if message.type == "note_on":
        Search = Query()
        result = db.search((Search.msg_type == message.type) & (Search.msgNoC == message.note))
        if result:
            string = result[0]["action"]
            obs_ws.send(string)
        print(message)
    elif message.type == "control_change":
        Search = Query()
        result = db.search((Search.msg_type == message.type) & (Search.msgNoC == message.control))
        if result:
            if  result[0]["input_type"] == "button":
                if message.value == 127:
                    string = result[0]["action"]
                    obs_ws.send(string)
            elif  result[0]["input_type"] == "fader":
                if result[0]["cmd"] == "SetSceneItemPosition":
                    actioncounter += 1
                    actionbuffer.append([str(actioncounter), result[0], scalemap(message.value, 0, 127, result[0]["scale_low"], result[0]["scale_high"])])
                    obs_ws.send('{"request-type": "GetSceneList", "message-id": "%s"}' % actioncounter)
                elif result[0]["cmd"] == "SetVolume":
                    scaled = scalemap(message.value, 0, 127, result[0]["scale_low"], result[0]["scale_high"])
                    string = result[0]["action"] % (scaled)
                    obs_ws.send(string)
                elif result[0]["cmd"] == "SetTransitionDuration":
                    scaled = scalemap(message.value, 0, 127, result[0]["scale_low"], result[0]["scale_high"])
                    string = result[0]["action"] % (int(scaled))
                    obs_ws.send(string)
                elif result[0]["cmd"] == "SetSyncOffset":
                    scaled = scalemap(message.value, 0, 127, result[0]["scale_low"], result[0]["scale_high"])
                    string = result[0]["action"] % (int(scaled))
                    obs_ws.send(string)
                elif result[0]["cmd"] == "SetSceneItemTransform": #can not be implemented because of a limit in the websocket plugin
                    actioncounter += 1
                    actionbuffer.append([str(actioncounter), result[0], scalemap(message.value, 0, 127, result[0]["scale_low"], result[0]["scale_high"])])
                    obs_ws.send('{"request-type": "GetSceneList", "message-id": "%s"}' % actioncounter)
        print(message)

def exitScript():
    port.close()

def obs_on_message(ws, message):
    global actioncounter
    jsn = json.loads(message)
    if "error" in jsn:
        print("Error: %s" % jsn["error"])
    else:
        for line in actionbuffer:
            if jsn["message-id"] == line[0]:
                if line[1]["cmd"] == "SetSceneItemPosition":
                    if line[1]["target"] == "X":
                        y = getPosfromJson(jsn["scenes"], line[1]["scene"], line[1]["source"], "y")
                        action = jsonArchive["SetSceneItemPosition"] % (line[1]["source"], line[1]["scene"], line[2], y)
                        obs_ws.send(action)
                    elif line[1]["target"] == "Y":
                        x = getPosfromJson(jsn["scenes"], line[1]["scene"], line[1]["source"], "x")
                        action = jsonArchive["SetSceneItemPosition"] % (line[1]["source"], line[1]["scene"], x, line[2])
                        obs_ws.send(action)
                #elif line[1]["cmd"] == "SetSceneItemPosition": can not be implemented because of a limit in the websocket plugin
                    #if line[1]["target"] == "X-scale":
                        #yscale = getPosfromJson(jsn["scenes"], line[1]["scene"], line[1]["source"], "y")
                        #rotation = getPosfromJson(jsn["scenes"], line[1]["scene"], line[1]["source"], "y")
                    #elif line[1]["target"] == "Y-scale":
                    #elif line[1]["target"] == "X+Y-scale":
                    #elif line[1]["target"] == "rotation":
                actionbuffer.remove([line[0], line[1], line[2]])
                break

def getPosfromJson(jsn, scene, source, what):
    for line in jsn:
        if line["name"] == scene:
            for line2 in line["sources"]:
                if line2["name"] == source:
                    return line2[what]
                    break
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
    print("MIDItoOBS made by lebaston100.de")
    print("!!MAKE SURE OBS IS RUNNING OR THIS SCRIPT WILL CRASH!!")
    print("Main program started.")
    Search = Query()
    result = db.search(Search.type.exists())
    if result:
        try:
            port = mido.open_input(result[0]["value"], callback=midicallback)
        except:
            print("The midi device you setup is not connected or now under a different name.")
            print("Please plugin in the device or run setup.py again and restart this script.")
            time.sleep(8)
            sys.exit()
        obs_ws = websocket.WebSocketApp("ws://localhost:4444", on_message = obs_on_message, on_error = obs_on_error, on_close = obs_on_close)
        obs_ws.on_open = obs_on_open
        atexit.register(exitScript)
        threading.Thread(target=obs_start).start()
    else:
        print("Please run setup.py")
        time.sleep(5)
        sys.exit()
