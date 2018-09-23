import mido, threading, sys, atexit, json, time
from tinydb import TinyDB, Query
from websocket import create_connection

####Change IP and Port here
serverIP = "localhost"
serverPort = "4444"
####

db = TinyDB("config.json", indent=4)
buttonActions = ["SetCurrentScene", "SetPreviewScene", "TransitionToProgram", "SetCurrentTransition", "SetSourceVisibility", "ToggleSourceVisibility", "ToggleMute", "SetMute",
                 "StartStopStreaming", "StartStreaming", "StopStreaming", "StartStopRecording", "StartRecording", "StopRecording", "StartStopReplayBuffer",
                 "StartReplayBuffer", "StopReplayBuffer", "SaveReplayBuffer", "SetTransitionDuration", "SetCurrentProfile","SetCurrentSceneCollection",
                 "ResetSceneItem", "SetTextGDIPlusText", "SetBrowserSourceURL", "ReloadBrowserSource"]
faderActions = ["SetVolume", "SetSyncOffset", "SetSourcePosition", "SetSourceRotation", "SetSourceScale", "SetTransitionDuration"]
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
               "ToggleMute": """{"request-type": "ToggleMute", "message-id" : "1", "source": "%s"}""",
               "SetMute": """{"request-type": "SetMute", "message-id" : "1", "source": "%s", "mute": %s}""",
               "StartStopReplayBuffer": """{"request-type": "StartStopReplayBuffer", "message-id" : "1"}""",
               "StartReplayBuffer": """{"request-type": "StartReplayBuffer", "message-id" : "1"}""",
               "StopReplayBuffer": """{"request-type": "StopReplayBuffer", "message-id" : "1"}""",
               "SaveReplayBuffer": """{"request-type": "SaveReplayBuffer", "message-id" : "1"}""",
               "SetTransitionDuration": """{"request-type": "SetTransitionDuration", "message-id" : "1", "duration": %s}""",
               "SetVolume": """{"request-type": "SetVolume", "message-id" : "1", "source": "%s", "volume": %s}""",
               "SetSyncOffset": """{"request-type": "SetSyncOffset", "message-id" : "1", "source": "%s", "offset": %s}""",
               "SetCurrentProfile": """{"request-type": "SetCurrentProfile", "message-id" : "1", "profile-name": "%s"}""",
               "SetCurrentSceneCollection": """{"request-type": "SetCurrentSceneCollection", "message-id" : "1", "sc-name": "%s"}""",
               "ResetSceneItem": """{"request-type": "ResetSceneItem", "message-id" : "1", "item": %s}""",
               "SetTextGDIPlusText": """{"request-type": "SetTextGDIPlusProperties", "message-id" : "1", "source": "%s", "text": "%s"}""",
               "SetBrowserSourceURL": """{"request-type": "SetBrowserSourceProperties", "message-id" : "1", "source": "%s", "url": "%s"}""",
               "SetSourcePosition": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene": "%s", "item": "%s", "position": {"%s": %s}}""",
               "SetSourceRotation": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene": "%s", "item": "%s", "rotation": %s}""",
               "SetSourceVisibility": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "item": "%s", "visible": %s}""",
               "ToggleSourceVisibility": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "item": "%s", "visible": %s}""",
               "SetSourceScale": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene": "%s", "item": "%s", "scale": {"%s": %s}}""",
               "ReloadBrowserSource": """{"request-type": "SetBrowserSourceProperties", "message-id" : "1", "source": "%s", "url": "%s"}"""}

sceneListShort = []
sceneListLong = []
transitionList = []
specialSourcesList = []
profilesList = []
sceneCollectionList = []
gdisourcesList = []

ignore = 255
savetime1 = time.time()

def exitScript():
    print("Exiting...")
    midiport.close()
    db.close()

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
    elif message.type == "program_change": #button only
        ignore = message.program
        print("Select Action:")
        counter = 0
        for action in buttonActions:
            print("%s: %s" % (counter, action))
            counter += 1
        input_select = int(input("Select 0-%s: " % str(len(buttonActions)-1)))
        if input_select in range(0, len(buttonActions)):
            action = buttonActions[input_select]
            setupButtonEvents(action, message.program, message.type)
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

#I know this is kinda messy, but i challange you to make a better version(as a native plugin or pull request to obs-studio)
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
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetVolume")
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
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSyncOffset")
    elif action == "SetSourcePosition":
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
        tempTargetList = ["x", "y"]
        target = int(input("\n0: X\n1: Y\nSelect Target to change (0-1): "))
        if target in range(0, 2):
            scale = askForInputScaling()
            action = jsonArchive["SetSourcePosition"] % (selected["scene"], selected["source"], tempTargetList[target], "%s")
            saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSourcePosition")
    elif action == "SetSourceRotation":
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
        scale = askForInputScaling()
        action = jsonArchive["SetSourceRotation"] % (selected["scene"], selected["source"], "%s")
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSourceRotation")
    elif action == "SetTransitionDuration":
        scale = askForInputScaling()
        action = jsonArchive["SetTransitionDuration"]
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetTransitionDuration")
    elif action == "SetSourceScale":
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
        tempTargetList = ["x", "y"]
        target = int(input("\n0: X\n1: Y\nSelect Target to change (0-1): "))
        if target in range(0, 2):
            scale = askForInputScaling()
            action = jsonArchive["SetSourceScale"] % (selected["scene"], selected["source"], tempTargetList[target], "%s")
            saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSourceScale")
        
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
    elif action == "SetSourceVisibility": #fertig
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
            render = "false"
        else:
            render = "true"
        sceneListShort.append("--Current--")
        scene = printArraySelect(sceneListShort)
        if scene != "--Current--":
            source = source + '", "scene": "' + scene
        action = jsonArchive["SetSourceVisibility"] % (source, str(render))
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "ToggleSourceVisibility": #fertig
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        sceneListShort.append("--Current--")
        scene = printArraySelect(sceneListShort)
        if scene != "--Current--":
            source = source + '", "scene": "' + scene
        action = jsonArchive["ToggleSourceVisibility"] % (source, "%s")
        saveTODOButtonToFile(msgType, NoC, "button" , action, "ToggleSourceVisibility", "x")
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
            muted = "false"
        else:
            muted = "true"
        action = jsonArchive["SetMute"] % (source, muted)
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetTransitionDuration": #fertig
        time = int(input("Input the desired time(in milliseconds): "))
        action = jsonArchive["SetTransitionDuration"] % time
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetCurrentProfile": #fertig
        updateProfileList()
        profilename = printArraySelect(profilesList)
        action = jsonArchive["SetCurrentProfile"] % profilename
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetRecordingFolder": #fertig
        recpath = str(input("Input the desired path: "))
        action = jsonArchive["SetRecordingFolder"] % recpath
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetCurrentSceneCollection": #fertig
        updatesceneCollectionList()
        scenecollection = printArraySelect(sceneCollectionList)
        print(scenecollection)
        action = jsonArchive["SetCurrentSceneCollection"] % scenecollection
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "ResetSceneItem": #fertig
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        sceneListShort.append("--Current--")
        scene = printArraySelect(sceneListShort)
        if scene != "--Current--":
            render = '"' + str(source) + '", "scene-name": "' + scene + '"'
        else:
            render = '"' + str(source) + '"'
        action = jsonArchive["ResetSceneItem"] % (render)
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetTextGDIPlusText":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList and line["type"] == "text_gdiplus":
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        text = str(input("Input the desired text: "))
        action = jsonArchive["SetTextGDIPlusText"] % (source, text)
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "SetBrowserSourceURL":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList and line["type"] == "browser_source":
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        url = str(input("Input the desired URL: "))
        action = jsonArchive["SetBrowserSourceURL"] % (source, url)
        saveButtonToFile(msgType, NoC, "button" , action)
    elif action == "ReloadBrowserSource":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList and line["type"] == "browser_source":
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        action = jsonArchive["ReloadBrowserSource"] % (source, "%s")
        saveTODOButtonToFile(msgType, NoC, "button" , action, "ReloadBrowserSource", source)

        
def saveFaderToFile(msg_type, msgNoC, input_type, action, scale, cmd):
    print("Saved %s with control %s for action %s" % (msg_type, msgNoC, cmd))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC))
    if result:
        db.remove(Search.msgNoC == msgNoC)
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": scale[0], "scale_high": scale[1], "action": action, "cmd": cmd})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": scale[0], "scale_high": scale[1], "action": action, "cmd": cmd})

def saveButtonToFile(msg_type, msgNoC, input_type, action):
    print("Saved %s with note/control %s for action %s" % (msg_type, msgNoC, action))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC))
    if result:
        db.remove(Search.msgNoC == msgNoC)
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action})

def saveTODOButtonToFile(msg_type, msgNoC, input_type, action, request, target):
    print("Saved %s with note/control %s for action %s" % (msg_type, msgNoC, action))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC))
    if result:
        db.remove(Search.msgNoC == msgNoC)
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "request": request, "target": target})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "request": request, "target": target})

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
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
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
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
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
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
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

def updateProfileList():
    global profilesList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    print("Updating Profiles List, plase wait")
    ws.send("""{"request-type": "ListProfiles", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    profilesList = []
    if jsn["message-id"] == "99999999":
        for line in jsn["profiles"]:
            profilesList.append(line["profile-name"])
        print("Profiles List updatet")
    else:
        print("Failed to update")
    ws.close()

def updatesceneCollectionList():
    global sceneCollectionList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    print("Updating Scene Collection List, plase wait")
    ws.send("""{"request-type": "ListSceneCollections", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    sceneCollectionList = []
    if jsn["message-id"] == "99999999":
        for line in jsn["scene-collections"]:
            sceneCollectionList.append(line["sc-name"])
        print("Scene Collection List updatet")
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
                if msg.type == "program_change":
                    if msg.program != ignore:
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
    print("MIDItoOBS made by lebaston100.de")
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
        result = db.search(Query().value == deviceList[input_select])
        if result:
                db.remove(Query().type == "device")
                db.insert({"type" : "device", "value": deviceList[input_select]})
        else:
                db.insert({"type" : "device", "value": deviceList[input_select]})
        try:
            midiport = mido.open_input(deviceList[input_select])
        except:
            print("The midi device might be used by another application.")
            print("Please close the device in the other application and restart this script.")
            time.sleep(8)
            sys.exit()
        atexit.register(exitScript)
        print("Please press key or move fader/knob on midi controller")
        mainLoop()
    else:
        print("Please select a valid device and restart the script")
        sys.exit()
