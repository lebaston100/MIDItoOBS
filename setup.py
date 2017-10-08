import mido, threading, sys, atexit, json
from tinydb import TinyDB, Query
from websocket import create_connection

import time

db = TinyDB("config.json")
buttonActions = ["SetCurrentScene", "SetPreviewScene", "TransitionToProgram", "SetCurrentTransition", "SetSourceRender", "ToggleMute", "SetMute", "StartStopStreaming", "StartStreaming",
                 "StopStreaming", "StartStopRecording", "StartRecording", "StopRecording", "StartStopReplayBuffer", "StartReplayBuffer", "StopReplayBuffer", "SaveReplayBuffer", "SetTransitionDuration"]
faderActions = ["SetVolume", "SetSceneItemPosition", "SetSyncOffset", "SetTransitionDuration"]
jsonArchive = {"SetCurrentScene": """{"request-type": "SetCurrentScene", "message-id" : "1", "scene-name" : "%s"}""",
               "SetPreviewScene": """{"request-type": "SetPreviewScene", "message-id" : "1","scene-name" : "%s"}""",
               "TransitionToProgram": """{"request-type": "TransitionToProgram", "message-id" : "1"%s}""",
               "SetCurrentTransition": """{"request-type": "SetCurrentTransition", "message-id" : "1", "transition-name" : "%s"}""",
               "StartStopStreaming": """{"request-type": "StartStopStreaming", "message-id" : "1"}""",
               "StartStreaming": """{"request-type": "StartStreaming", "message-id" : "1"}""",
               "StopStreaming": """{"request-type": "StopStreaming", "message-id" : "1"}""",
               "StartStopRecording": """{"request-type": "StartStopRecording", "message-id" : "1"}""",
               "StartRecording": """{"request-type": "StartStreaming", "message-id" : "1"}""",
               "StopRecording": """{"request-type": "StopStreaming", "message-id" : "1"}""",
               "SetSourceRender": """{"request-type": "SetSourceRender", "message-id" : "1", "source": "%s", "render": %s}""",               
               "ToggleMute": """{"request-type": "ToggleMute", "message-id" : "1", "source": "%s"}""",
               "SetMute": """{"request-type": "SetMute", "message-id" : "1", "source": "%s", "mute": "%s"}""",
               "StartStopReplayBuffer": """{"request-type": "StartStopReplayBuffer", "message-id" : "1"}""",
               "StartReplayBuffer": """{"request-type": "StartReplayBuffer", "message-id" : "1"}""",
               "StopReplayBuffer": """{"request-type": "StopReplayBuffer", "message-id" : "1"}""",
               "SaveReplayBuffer": """{"request-type": "SaveReplayBuffer", "message-id" : "1"}""",
               "SetTransitionDuration": """{"request-type": "SetTransitionDuration", "message-id" : "1", "duration": %s}""",
               "SetVolume": """{"request-type": "SetVolume", "message-id" : "1", "source": "%s", "volume": %s}""",
               "SetSyncOffset": """{"request-type": "SetSyncOffset", "message-id" : "1", "source": "%s", "offset": %s}""",
               "SetSceneItemPosition": """{"request-type": "SetSceneItemPosition", "message-id" : "1", "item": "%s", "scene-name": "%s"%s}"""}

sceneListShort = []
sceneListLong = []
transitionList = []
specialSourcesList = []

ignore = 255
savetime1 = time.time()

def exitScript():
    port.close()
    print("Exiting")
    sys.exit()

def midicallback(message):
    global ignore
    print()
    print(message)
    print()
    if message.type == "note_on": #button only
        ignore = message.note
        print("Select Action:")
        counter = 0
        for action in buttonActions:
            print("%s: %s" % (counter, action))
            counter += 1
        input_select = int(input("Select 0-%s: " % str(len(buttonActions)-1)))
        if input_select in range(0, len(buttonActions)):
            action = buttonActions[input_select]
            setupButtonEvents(action, message.note, message.type)
    elif message.type == "control_change": #button or fader
        ignore = message.control
        print("Select input type:\n0: Button\n1: Fader/Knob\n2: Ignore")
        try:
            input_select = int(input("Select 0-2: "))
            if input_select in range(0, 3):
                if input_select == 0:
                    print()
                    print("Select Action:")
                    counter = 0
                    for action in buttonActions:
                        print("%s: %s" % (counter, action))
                        counter += 1
                    input_select = int(input("Select 0-%s: " % str(len(buttonActions)-1)))
                    if input_select in range(0, len(buttonActions)):
                        action = buttonActions[input_select]
                        setupButtonEvents(action, message.control, message.type)
                elif input_select == 1:
                    print()
                    print("Select Action:")
                    counter = 0
                    for action in faderActions:
                        print("%s: %s" % (counter, action))
                        counter += 1
                    input_select = int(input("Select 0-%s: " % str(len(faderActions)-1)))
                    if input_select in range(0, len(faderActions)):
                        action = faderActions[input_select]
                        setupFaderEvents(action, message.control, message.type)
        except ValueError:
            print("Please try again and enter a valid number")

def setupFaderEvents(action, NoC, msgType):
    print()
    print("You selected: %s" % action)
    if action == "SetVolume":
        updateSceneList()
        updateSpecialSources()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        for item in specialSourcesList:
            tempSceneList.append(item)
        source = printArraySelect(tempSceneList)
        scale = (0,1)
        action = jsonArchive["SetVolume"] % (source, "%s")
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetVolume", "")
    elif action == "SetSyncOffset":
        updateSceneList()
        updateSpecialSources()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        for item in specialSourcesList:
            tempSceneList.append(item)
        source = printArraySelect(tempSceneList)
        scale = askForInputScaling()
        action = jsonArchive["SetSyncOffset"] % (source, "%s")
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSyncOffset", source)
    elif action == "SetSceneItemPosition":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                tmpOBJ = {"scene": scene["name"], "source": line["name"]}
                tempSceneList.append(tmpOBJ)
        counter = 0
        for line in tempSceneList:
            print("%s: Source '%s' in scene '%s'" % (counter, line["source"], line["scene"]))
            counter += 1
        selected = tempSceneList[int(input("Select 0-%s: " % str(len(tempSceneList)-1)))]
        tempTargetList = ["X", "Y"]
        target = int(input("\n0: X\n1: Y\nSelect Target to change (0-1): "))
        if target in range(0, 2):
            action = ""
            scale = askForInputScaling()
            Search = Query()
            result = db.search((Search.msg_type == msgType) & (Search.msgNoC == NoC))
            if result:
                db.remove((Search.msg_type == msgType) & (Search.msgNoC == NoC))
                db.insert({"msg_type": msgType, "msgNoC": NoC, "input_type": "fader", "scale_low": scale[0],
                           "scale_high": scale[1], "action": action, "cmd": "SetSceneItemPosition",
                           "target": tempTargetList[target], "scene": selected["scene"], "source": selected["source"]})
            else:
                db.insert({"msg_type": msgType, "msgNoC": NoC, "input_type": "fader", "scale_low": scale[0],
                           "scale_high": scale[1], "action": action, "cmd": "SetSceneItemPosition",
                           "target": tempTargetList[target], "scene": selected["scene"], "source": selected["source"]})
            print("Saved %s with control %s for action %s" % (msgType, NoC, "SetSceneItemPosition"))
    elif action == "SetTransitionDuration":
        scale = askForInputScaling()
        action = jsonArchive["SetTransitionDuration"]
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetTransitionDuration", "")
    elif action == "SetSceneItemTransform": #can not be implemented because of a limit in the websocket plugin
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                tmpOBJ = {"scene": scene["name"], "source": line["name"]}
                tempSceneList.append(tmpOBJ)
        counter = 0
        for line in tempSceneList:
            print("%s: Source '%s' in scene '%s'" % (counter, line["source"], line["scene"]))
            counter += 1
        selected = tempSceneList[int(input("Select 0-%s: " % str(len(tempSceneList)-1)))]
        tempTargetList = ["X-scale", "Y-scale", "X+Y-scale", "rotation"]
        target = int(input("\n0: X-scale\n1: Y-scale\n2: X+Y-scale\n3: rotation\nSelect Target to change (0-3): "))
        if target in range(0, 4):
            action = ""
            scale = askForInputScaling()
            Search = Query()
            result = db.search((Search.msg_type == msgType) & (Search.msgNoC == NoC))
            if result:
                db.remove((Search.msg_type == msgType) & (Search.msgNoC == NoC))
                db.insert({"msg_type": msgType, "msgNoC": NoC, "input_type": "fader", "scale_low": scale[0],
                           "scale_high": scale[1], "action": action, "cmd": "SetSceneItemTransform",
                           "target": tempTargetList[target], "scene": selected["scene"], "source": selected["source"]})
            else:
                db.insert({"msg_type": msgType, "msgNoC": NoC, "input_type": "fader", "scale_low": scale[0],
                           "scale_high": scale[1], "action": action, "cmd": "SetSceneItemTransform",
                           "target": tempTargetList[target], "scene": selected["scene"], "source": selected["source"]})
        
def setupButtonEvents(action, NoC, msgType):
    print()
    print("You selected: %s" % action)
    if action == "SetCurrentScene": #fertig
        updateSceneList()
        scene = printArraySelect(sceneListShort)
        action = jsonArchive["SetCurrentScene"] % scene
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetPreviewScene": #fertig
        updateSceneList()
        scene = printArraySelect(sceneListShort)
        action = jsonArchive["SetPreviewScene"] % scene
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "TransitionToProgram": #fertig
        updateTransitionList()
        transitionList.append("--Current--")
        transition = printArraySelect(transitionList)
        print(transition)
        if transition != "--Current--":
            tmp = ' , "with-transition": {"name": "' + transition + '"}'
            action = jsonArchive["TransitionToProgram"] % tmp
        else:
            action = jsonArchive["TransitionToProgram"] % ""
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetCurrentTransition": #fertig
        updateTransitionList()
        transition = printArraySelect(transitionList)
        action = jsonArchive["SetCurrentTransition"] % transition
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "StartStopStreaming": #fertig
        action = jsonArchive["StartStopStreaming"]
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "StartStreaming": #fertig
        action = jsonArchive["StartStreaming"]
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "StopStreaming": #fertig
        action = jsonArchive["StopStreaming"]
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "StartStopRecording": #fertig
        action = jsonArchive["StartStopRecording"]
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "StartRecording": #fertig
        action = jsonArchive["StartRecording"]
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "StopRecording": #fertig
        action = jsonArchive["StopRecording"]
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "StartStopReplayBuffer": #fertig
        action = jsonArchive["StartStopReplayBuffer"]
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "StartReplayBuffer": #fertig
        action = jsonArchive["StartReplayBuffer"]
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "StopReplayBuffer": #fertig
        action = jsonArchive["StopReplayBuffer"]
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SaveReplayBuffer": #fertig
        action = jsonArchive["SaveReplayBuffer"]
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetSourceRender": #fertig
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        renderArray = ["0 (Invisible)", "1 (Visible)"]
        render = printArraySelect(renderArray)
        if render == "0 (Invisible)":
            render = 0
        else:
            render = 1
        sceneListShort.append("--Current--")
        scene = printArraySelect(sceneListShort)
        if scene != "--Current--":
            render = str(render) + ', "scene-name": "' + scene + '"'
        action = jsonArchive["SetSourceRender"] % (source, render)
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "ToggleMute": #fertig
        updateSceneList()
        updateSpecialSources()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        for item in specialSourcesList:
            tempSceneList.append(item)
        source = printArraySelect(tempSceneList)
        action = jsonArchive["ToggleMute"] % source
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetMute": #fertig
        updateSceneList()
        updateSpecialSources()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        for item in specialSourcesList:
            tempSceneList.append(item)
        source = printArraySelect(tempSceneList)
        tempArray = ["0 (Muted)", "1 (Unmuted)"]
        muted = printArraySelect(tempArray)
        if muted == "0 (Muted)":
            muted = 0
        else:
            muted = 1
        action = jsonArchive["SetMute"] % (source, muted)
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetTransitionDuration":
        time = int(input("Input the desired time(in milliseconds): "))
        action = jsonArchive["SetTransitionDuration"] % time
        saveButtonToFile(msgType, NoC, "button" , action)

def saveFaderToFile(msg_type, msgNoC, input_type, action, scale, cmd, target):
    #print("saved", msg_type, msgNoC, input_type, action, scale, cmd, target)
    print("Saved %s with control %s for action %s" % (msg_type, msgNoC, cmd))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC))
    if result:
        db.remove(Search.msgNoC == msgNoC)
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": scale[0], "scale_high": scale[1], "action": action, "cmd": cmd, "target": target})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": scale[0], "scale_high": scale[1], "action": action, "cmd": cmd, "target": target})

def saveButtonToFile(msg_type, msgNoC, input_type, action):
    #print("saved", msg_type, msgNoC, input_type, action)
    print("Saved %s with note/control %s for action %s" % (msg_type, msgNoC, action))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC))
    if result:
        db.remove(Search.msgNoC == msgNoC)
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action})

def printArraySelect(array):
    counter = 0
    for line in array:
        print("%s: %s" % (counter, line))
        counter += 1
    return array[int(input("Select 0-%s: " % str(len(array)-1)))]

def askForInputScaling():
    print("Setup input scale")
    low = int(input("Select lower output value: "))
    high = int(input("Select higher output value: "))
    return low, high

def updateTransitionList():
    global transitionList
    ws = create_connection("ws://localhost:4444")
    print("Updating transition list, plase wait")
    ws.send("""{"request-type": "GetTransitionList", "message-id": "999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    transitionList = []
    if jsn["message-id"] == "999999":
        for item in jsn["transitions"]:
            transitionList.append(item["name"])
        print("Transitions updated")
    else:
        print("Failed to update")
    ws.close()

def updateSceneList():
    global sceneListShort
    global sceneListLong
    ws = create_connection("ws://localhost:4444")
    print("Updating scene list, plase wait")
    ws.send("""{"request-type": "GetSceneList", "message-id": "9999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    sceneListShort = []
    sceneListLong = []
    if jsn["message-id"] == "9999999":
        sceneListLong = jsn["scenes"]
        for item in jsn["scenes"]:
            sceneListShort.append(item["name"])
        print("Scenes updatet")
    else:
        print("Failed to update")
    ws.close()

def updateSpecialSources():
    global specialSourcesList
    ws = create_connection("ws://localhost:4444")
    print("Updating special sources, plase wait")
    ws.send("""{"request-type": "GetSpecialSources", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    specialSourcesList = []
    if jsn["message-id"] == "99999999":
        for line in jsn:
            if line == "status" or line == "message-id":
                x=1
            else:
                specialSourcesList.append(jsn[line])
        print("Special sources updatet")
    else:
        print("Failed to update")
    ws.close()

def mainLoop():
    global ignore
    global savetime1
    while True:
        try:
            msg = midiport.receive()
            if msg:
                if msg.type == "note_on":
                    if msg.note != ignore:
                        midicallback(msg)
                        savetime1 = time.time()
                if msg.type == "control_change":
                    if msg.control != ignore:
                        midicallback(msg)
                        savetime1 = time.time()
            if time.time() - savetime1 > 3:
                savetime1 = time.time()
                ignore = 255
        except KeyboardInterrupt:
            print("Exiting")
            sys.exit()
            break


if __name__ == "__main__":
    print("MIDItoOBS made by lebaston100.de ")
    print("!!MAKE SURE OBS IS RUNNING OR THIS SCRIPT WILL CRASH!!")
    print("Select Midi Device")
    deviceList = mido.get_input_names()
    counter = 0
    for device in deviceList:
        print("%s: %s" % (counter, device))
        counter += 1
    input_select = int(input("Select 0-%s: " % str(len(deviceList)-1)))
    if input_select in range(0, len(deviceList)):
        print("You selected: %s (%s)" % (str(input_select), deviceList[input_select]))
        Search = Query()
        result = db.search(Search.value == deviceList[input_select])
        if result:
                db.remove(Search.type == "device")
                db.insert({"type" : "device", "value": deviceList[input_select]})
        else:
                db.insert({"type" : "device", "value": deviceList[input_select]})
        midiport = mido.open_input(deviceList[input_select])
        atexit.register(exitScript)
        print("Please press key or move fader/knob on midi controller")
        mainLoop()
    else:
        print("Please select a valid device and restart the script")
        sys.exit()
