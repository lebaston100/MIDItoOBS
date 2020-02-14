import mido, threading, sys, atexit, json, time, signal
from tinydb import TinyDB, Query
from websocket import create_connection

####Change IP and Port here
serverIP = "localhost"
serverPort = "4444"
####

database = TinyDB("config.json", indent=4)
db = database.table("keys", cache_size=0)
devdb = database.table("devices", cache_size=0)
buttonActions = ["SetCurrentScene", "SetPreviewScene", "TransitionToProgram", "SetCurrentTransition", "SetSourceVisibility", "ToggleSourceVisibility", "ToggleMute", "SetMute",
                 "StartStopStreaming", "StartStreaming", "StopStreaming", "StartStopRecording", "StartRecording", "StopRecording", "StartStopReplayBuffer",
                 "StartReplayBuffer", "StopReplayBuffer", "SaveReplayBuffer", "PauseRecording", "ResumeRecording", "SetTransitionDuration", "SetCurrentProfile","SetCurrentSceneCollection",
                 "ResetSceneItem", "SetTextGDIPlusText", "SetBrowserSourceURL", "ReloadBrowserSource", "TakeSourceScreenshot", "EnableSourceFilter", "DisableSourceFilter", "ToggleSourceFilter"]
faderActions = ["SetVolume", "SetSyncOffset", "SetSourcePosition", "SetSourceRotation", "SetSourceScale", "SetTransitionDuration", "SetGainFilter"]
jsonArchive = {"SetCurrentScene": """{"request-type": "SetCurrentScene", "message-id" : "1", "scene-name" : "%s"}""",
               "SetPreviewScene": """{"request-type": "SetPreviewScene", "message-id" : "1","scene-name" : "%s"}""",
               "TransitionToProgram": """{"request-type": "TransitionToProgram", "message-id" : "1"%s}""",
               "SetCurrentTransition": """{"request-type": "SetCurrentTransition", "message-id" : "1", "transition-name" : "%s"}""",
               "StartStopStreaming": """{"request-type": "StartStopStreaming", "message-id" : "1"}""",
               "StartStreaming": """{"request-type": "StartStreaming", "message-id" : "1"}""",
               "StopStreaming": """{"request-type": "StopStreaming", "message-id" : "1"}""",
               "StartStopRecording": """{"request-type": "StartStopRecording", "message-id" : "1"}""",
               "StartRecording": """{"request-type": "StartRecording", "message-id" : "1"}""",
               "StopRecording": """{"request-type": "StopRecording", "message-id" : "1"}""",              
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
               "SetSourcePosition": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene-name": "%s", "item": "%s", "position": {"%s": %s}}""",
               "SetSourceRotation": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene-name": "%s", "item": "%s", "rotation": %s}""",
               "SetSourceVisibility": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "item": "%s", "visible": %s}""",
               "ToggleSourceVisibility": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "item": "%s", "visible": %s}""",
               "SetSourceScale": """{{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene-name": "%s", "item": "%s", "scale": {{"%s": %s}}}}""",
               "ReloadBrowserSource": """{"request-type": "SetBrowserSourceProperties", "message-id" : "1", "source": "%s", "url": "%s"}""",
               "TakeSourceScreenshot": """{"request-type": "TakeSourceScreenshot", "message-id" : "MIDItoOBSscreenshot","sourceName" : "%s", "embedPictureFormat": "png"}""",
               "SetGainFilter": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"db": %s}}""",
               "EnableSourceFilter": """{"request-type": "SetSourceFilterVisibility", "sourceName": "%s", "filterName": "%s", "filterEnabled": true, "message-id": "MIDItoOBS-EnableSourceFilter"}""",
               "DisableSourceFilter": """{"request-type": "SetSourceFilterVisibility", "sourceName": "%s", "filterName": "%s", "filterEnabled": false, "message-id": "MIDItoOBS-DisableSourceFilter"}""",
               "PauseRecording": """{"request-type": "PauseRecording", "message-id" : "MIDItoOBS-PauseRecording"}""",
               "ResumeRecording": """{"request-type": "ResumeRecording", "message-id" : "MIDItoOBS-ResumeRecording"}""",
               "ToggleSourceFilter": """{"request-type": "SetSourceFilterVisibility", "sourceName": "%s", "filterName": "%s", "filterEnabled": %s, "message-id": "MIDItoOBS-EnableSourceFilter"}"""}

sceneListShort = []
sceneListLong = []
transitionList = []
specialSourcesList = []
profilesList = []
sceneCollectionList = []
gdisourcesList = []

midiports = []

ignore = 255
savetime1 = time.time()

def ScriptExit(signal, frame):
    print("Closing midi ports...")
    for port in midiports:
        port["object"].close()
    print("Closing database...")
    database.close()
    print("Exiting...")
    sys.exit(0)

def midicallback(message, deviceID, deviceName):
    global ignore
    print()
    print("Received message", message)
    print("from device", deviceName)
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
            setupButtonEvents(action, message.note, message.type, deviceID)
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
            setupButtonEvents(action, message.program, message.type, deviceID)
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
                        setupButtonEvents(action, message.control, message.type, deviceID)
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
                        setupFaderEvents(action, message.control, message.type, deviceID)
        except ValueError:
            print("Please try again and enter a valid number")

#I know this is very messy, but i challange you to make a better version(as a native plugin or pull request to obs-studio)
def setupFaderEvents(action, NoC, msgType, deviceID):
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
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetVolume", deviceID)
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
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSyncOffset", deviceID)
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
            saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSourcePosition", deviceID)
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
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSourceRotation", deviceID)
    elif action == "SetTransitionDuration":
        scale = askForInputScaling()
        action = jsonArchive["SetTransitionDuration"]
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetTransitionDuration", deviceID)
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
        tempTargetList = ["x", "y", 'x": {0}, "y']
        target = int(input("\n0: X\n1: Y\n2: Both\nSelect Target to change (0-2): "))
        if target in range(0, 3):
            scale = askForInputScaling()
            action = jsonArchive["SetSourceScale"] % (selected["scene"], selected["source"], tempTargetList[target], "{0}")
            saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSourceScale", deviceID)
    elif action == "SetGainFilter":
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
        filtername = checkIfSourceHasGainFilter(source)
        if filtername:
            print("You will now be asked for the input scaling. The valid range for the gain filter is -30 (db) to 30 (db). You can select any range inside -30 to 30")
            scale = askForInputScaling()
            action = jsonArchive["SetGainFilter"] % (source, filtername, "%s")
            saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetGainFilter", deviceID)
        else:
            print("The selected source has no gain filter. Please add it in the source filter dialog and try again.")
        
def setupButtonEvents(action, NoC, msgType, deviceID):
    print()
    print("You selected: %s" % action)
    if action == "SetCurrentScene":
        updateSceneList()
        scene = printArraySelect(sceneListShort)
        action = jsonArchive["SetCurrentScene"] % scene
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "SetPreviewScene":
        updateSceneList()
        scene = printArraySelect(sceneListShort)
        action = jsonArchive["SetPreviewScene"] % scene
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "TransitionToProgram":
        updateTransitionList()
        print("Please select a transition to be used:")
        transitionList.append("--Current--")
        transition = printArraySelect(transitionList)
        print(transition)
        if transition != "--Current--":
            tmp = ' , "with-transition": {"name": "' + transition + '"}'
            action = jsonArchive["TransitionToProgram"] % tmp
        else:
            action = jsonArchive["TransitionToProgram"] % ""
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "SetCurrentTransition":
        updateTransitionList()
        transition = printArraySelect(transitionList)
        action = jsonArchive["SetCurrentTransition"] % transition
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "StartStopStreaming":
        action = jsonArchive["StartStopStreaming"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "StartStreaming":
        action = jsonArchive["StartStreaming"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "StopStreaming":
        action = jsonArchive["StopStreaming"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "StartStopRecording":
        action = jsonArchive["StartStopRecording"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "StartRecording":
        action = jsonArchive["StartRecording"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "StopRecording":
        action = jsonArchive["StopRecording"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "StartStopReplayBuffer":
        action = jsonArchive["StartStopReplayBuffer"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "StartReplayBuffer":
        action = jsonArchive["StartReplayBuffer"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "StopReplayBuffer":
        action = jsonArchive["StopReplayBuffer"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "SaveReplayBuffer":
        action = jsonArchive["SaveReplayBuffer"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "PauseRecording":
        action = jsonArchive["PauseRecording"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "ResumeRecording":
        action = jsonArchive["ResumeRecording"]
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "SetSourceVisibility":
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
            source = source + '", "scene-name": "' + scene
        action = jsonArchive["SetSourceVisibility"] % (source, str(render))
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "ToggleSourceVisibility":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = source1 = printArraySelect(tempSceneList)
        sceneListShort.append("--Current--")
        scene = printArraySelect(sceneListShort)
        if scene != "--Current--":
            source = source + '", "scene": "' + scene
        action = jsonArchive["ToggleSourceVisibility"] % (source, "%s")
        saveTODOButtonToFile(msgType, NoC, "button" , action, "ToggleSourceVisibility", source1, "" , deviceID)
    elif action == "ToggleMute":
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
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "SetMute":
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
            muted = "true"
        else:
            muted = "false"
        action = jsonArchive["SetMute"] % (source, muted)
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "SetTransitionDuration":
        time = int(input("Input the desired time(in milliseconds): "))
        action = jsonArchive["SetTransitionDuration"] % time
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "SetCurrentProfile":
        updateProfileList()
        profilename = printArraySelect(profilesList)
        action = jsonArchive["SetCurrentProfile"] % profilename
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "SetRecordingFolder":
        recpath = str(input("Input the desired path: "))
        action = jsonArchive["SetRecordingFolder"] % recpath
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "SetCurrentSceneCollection":
        updatesceneCollectionList()
        scenecollection = printArraySelect(sceneCollectionList)
        action = jsonArchive["SetCurrentSceneCollection"] % scenecollection
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "ResetSceneItem":
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
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
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
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
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
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "ReloadBrowserSource":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList and line["type"] == "browser_source":
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        action = jsonArchive["ReloadBrowserSource"] % (source, "%s")
        saveTODOButtonToFile(msgType, NoC, "button" , action, "ReloadBrowserSource", source, "", deviceID)
    elif action == "TakeSourceScreenshot":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        for scene in sceneListShort:
            tempSceneList.append(scene)
        source = printArraySelect(tempSceneList)
        action = jsonArchive["TakeSourceScreenshot"] % (source)
        saveButtonToFile(msgType, NoC, "button" , action, deviceID)
    elif action == "EnableSourceFilter":
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
        filters = getSourceFilters(source)
        if filters:
            tempFilterList = []
            for line in filters:
                tempFilterList.append(line["name"])
            selectedFilter = printArraySelect(tempFilterList)
            action = jsonArchive["EnableSourceFilter"] % (source, selectedFilter)
            saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        else:
            print("\nThis source has no filters")
    elif action == "DisableSourceFilter":
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
        filters = getSourceFilters(source)
        if filters:
            tempFilterList = []
            for line in filters:
                tempFilterList.append(line["name"])
            selectedFilter = printArraySelect(tempFilterList)
            action = jsonArchive["DisableSourceFilter"] % (source, selectedFilter)
            saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        else:
            print("\nThis source has no filters")
    elif action == "ToggleSourceFilter":
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
        filters = getSourceFilters(source)
        if filters:
            tempFilterList = []
            for line in filters:
                tempFilterList.append(line["name"])
            selectedFilter = printArraySelect(tempFilterList)
        action = jsonArchive["ToggleSourceFilter"] % (source, selectedFilter, "%s")
        saveTODOButtonToFile(msgType, NoC, "button" , action, "ToggleSourceFilter", source, selectedFilter, deviceID)

        
def saveFaderToFile(msg_type, msgNoC, input_type, action, scale, cmd, deviceID):
    print("Saved %s with control %s for action %s on device %s" % (msg_type, msgNoC, cmd, deviceID))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
    if result:
        db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": scale[0], "scale_high": scale[1], "action": action, "cmd": cmd, "deviceID": deviceID})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": scale[0], "scale_high": scale[1], "action": action, "cmd": cmd, "deviceID": deviceID})

def saveButtonToFile(msg_type, msgNoC, input_type, action, deviceID):
    print("Saved %s with note/control %s for action %s on device %s" % (msg_type, msgNoC, action, deviceID))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
    if result:
        db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "deviceID": deviceID})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "deviceID": deviceID})

def saveTODOButtonToFile(msg_type, msgNoC, input_type, action, request, target, field2, deviceID):
    print("Saved %s with note/control %s for action %s on device %s" % (msg_type, msgNoC, action, deviceID))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
    if result:
        db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "request": request, "target": target, "deviceID": deviceID, "field2": field2})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "request": request, "target": target, "deviceID": deviceID, "field2": field2})

def printArraySelect(array):
    counter = 0
    for line in array:
        print("%s: %s" % (counter, line))
        counter += 1
    if counter > 1:
        return array[int(input("Select 0-%s: " % str(len(array)-1)))]
    else:
        return array[int(input("Select 0: "))]

def askForInputScaling():
    print("Setup input scale")
    low = int(input("Select lower output value: "))
    high = int(input("Select higher output value: "))
    return low, high

def updateTransitionList():
    global transitionList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    print("\nUpdating transition list, plase wait")
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
    print("\nUpdating scene list, plase wait")
    ws.send("""{"request-type": "GetSceneList", "message-id": "9999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    sceneListShort = []
    sceneListLong = []
    if jsn["message-id"] == "9999999":
        sceneListLong = jsn["scenes"]
        for item in jsn["scenes"]:
            sceneListShort.append(item["name"])
        print("Scenes updated")
    else:
        print("Failed to update")
    ws.close()

def updateSpecialSources():
    global specialSourcesList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    print("\nUpdating special sources, plase wait")
    ws.send("""{"request-type": "GetSpecialSources", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    specialSourcesList = []
    if jsn["message-id"] == "99999999":
        for line in jsn:
            if line == "status" or line == "message-id":
                pass
            else:
                specialSourcesList.append(jsn[line])
        print("Special sources updated")
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
        print("Profiles List updated")
    else:
        print("Failed to update")
    ws.close()

def updatesceneCollectionList():
    global sceneCollectionList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    print("\nUpdating Scene Collection List, plase wait")
    ws.send("""{"request-type": "ListSceneCollections", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    sceneCollectionList = []
    if jsn["message-id"] == "99999999":
        for line in jsn["scene-collections"]:
            sceneCollectionList.append(line["sc-name"])
        print("Scene Collection List updated")
    else:
        print("Failed to update")
    ws.close()

def checkIfSourceHasGainFilter(sourcename):
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    print("\nChecking source filters, plase wait")
    ws.send('{"request-type": "GetSourceFilters", "message-id": "MIDItoOBS-checksourcegainfilter", "sourceName": "' + sourcename + '"}')
    result =  ws.recv()
    ws.close()
    jsn = json.loads(result)
    if jsn["message-id"] == "MIDItoOBS-checksourcegainfilter":
        for line in jsn["filters"]:
            if line["type"] == "gain_filter":
                return line["name"]
    return False

def getSourceFilters(sourcename):
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    print("\nChecking source filters, plase wait")
    ws.send('{"request-type": "GetSourceFilters", "message-id": "MIDItoOBS-getSourceFilters", "sourceName": "' + sourcename + '"}')
    result =  ws.recv()
    ws.close()
    jsn = json.loads(result)
    if jsn["message-id"] == "MIDItoOBS-getSourceFilters":
        return jsn["filters"]
    else:
        return False
    

def configureDevices(switch):
    dbresult = devdb.all()
    if switch:
        print("\nTell me: What do you want to do?\n1: Rename a device and transfer their action assignments (because you plugged it into another USB port and windows decided to give the device a new name now)\n2: Delete all devices from config and re-add (Warning: this will dereference all button and fader actions(so they will no longer work). This might cause device confusion later.\n3: Remove a single device from the configuration INCLUDING their midi assignments\n4: Add new device\n5: Skip device configuration (Warning: If no device has been configured before, MIDItoOBS will NOT work)")
        action_select = int(input("Select 1-4: "))
        if action_select == 1:
            renameDevice()
            return
        elif action_select == 2:
            print("Removing all devices from the database....")
            devdb.purge() #purge database table before adding new devices
        elif action_select == 3:
            removeDevice()
            return
        elif action_select == 4:
            pass
        else:
            return
    
    print("\nWhich device do you want to add?")
    exitflag = 0
    while not exitflag:
        availableDeviceList = mido.get_input_names()
        deviceList = []
        counter = 0
        inUseDeviceList = devdb.all()
        for device in availableDeviceList:
            if devInDB(device, inUseDeviceList):
                pass
            else:
                print("%s: %s" % (counter, device))
                counter += 1
                deviceList.append(device)
            
        if len(deviceList) == 0:
            print("No midi input device available")
            return
        if len(deviceList) < 2:
            input_select = int(input("Select 0: "))
        else:
            input_select = int(input("Select 0-%s: " % str(len(deviceList)-1)))
        print("Adding:", deviceList[input_select])
        result = devdb.search(Query().devicename == deviceList[input_select])
        if not result:
            deviceID = devdb.insert({"devicename": deviceList[input_select]})
        print("Do you want to add another device?\n1: Yes\n2: No")
        action_select = int(input("Select 1 or 2: "))
        if action_select == 2:
            exitflag = 1

def devInDB(devicename, devicedatabase):
    for entry in devicedatabase:
        if entry["devicename"] == devicename:
            return True
    return False

def removeDevice():
    devices = devdb.all()
    print("So you want to remove a device. Please keep in mind that this will not only remove the device but remove every action assigned to the device.\nWhich device and configuration do you want to remove?")
    counter = 0
    for (index, device) in enumerate(devices):
        print("%s: %s" % (counter, device["devicename"]))
        counter += 1
    device_select = int(input("Select 0-%s: " % str(len(devices)-1)))
    print("Selected:", devices[device_select]["devicename"])
    yousure = input("Are you really sure you want to remove the devices and all it's assignments?\nType 'YES' and press enter: ")
    if yousure == "YES":
        print("As you wish. Deleting now......")
        try:
            result = devdb.get(Query().devicename == devices[device_select]["devicename"])
            devdb.remove(doc_ids=[result.doc_id])
            db.remove(Query().deviceID == result.doc_id)
        except:
            print("There was an error removing the device")
        

def renameDevice():
    devices = devdb.all()
    counter = 0
    print("Please select a device for your configuration that you want to \"rename\" to another device:")
    for (index, device) in enumerate(devices):
        print("%s: %s" % (counter, device["devicename"]))
        counter += 1
    old_device_select = int(input("Select 0-%s: " % str(len(devices)-1)))
    old_device_name = devices[old_device_select]["devicename"]
    print("Selected:", old_device_name)
    print("Please select the new device name now:")
    availableDeviceList = mido.get_input_names()
    deviceList = []
    for device in availableDeviceList:
            if devInDB(device, devices):
                pass
            else:
                deviceList.append(device)
    if len(deviceList) > 0:
        counter = 0
        for (index, device) in enumerate(deviceList):
            print("%s: %s" % (counter, device))
            counter += 1
        new_device_select = int(input("Select 0-%s: " % str(len(deviceList)-1)))
        new_device_name = deviceList[new_device_select]
        print("Selected:", new_device_name, "as the new device name")
        print("Updating \"", old_device_name, "\" to \"", new_device_name, "\" now", sep="")
        try:
            devdb.update({"devicename": new_device_name}, Query().devicename == old_device_name)
            print("Sucessfully renamed the device")
        except:
            print("There was an error renaming the device")
    else:
        print("There is no other device available to switch over to. Aborting...")
        
def mainLoop():
    global ignore
    global savetime1
    while True:
        for device in midiports:
            try:
                msg = device["object"].poll()
                if msg:
                    if msg.type == "note_on":
                        if msg.note != ignore:
                            midicallback(msg, device["id"], device["devicename"])
                            savetime1 = time.time()
                    if msg.type == "program_change":
                        if msg.program != ignore:
                            midicallback(msg, device["id"], device["devicename"])
                            savetime1 = time.time()
                    if msg.type == "control_change":
                        if msg.control != ignore:
                            midicallback(msg, device["id"], device["devicename"])
                            savetime1 = time.time()
                if time.time() - savetime1 > 3:
                    savetime1 = time.time()
                    ignore = 255
            except KeyboardInterrupt:
                ScriptExit(0, 0)
                break

if __name__ == "__main__":
    print("MIDItoOBS made by https://github.com/lebaston100\n")
    print("This setup assistant will guide you though the initial setup. If you experience any problems that you can not solve on your own feel free to open an issue on Github\n")
    print("!!Important!!")
    print("!!MAKE SURE OBS IS RUNNING OR THIS SCRIPT WILL CRASH!!")
    print("!!MAKE SURE THAT THE MIDI DEVICE(S) ARE NOT IN USE BY ANOTHER APPLICATION!!\n")

    signal.signal(signal.SIGINT, ScriptExit)

    #search if config available and a device configuration is present
    result = devdb.all()
    if result:
        print("Please select the number of what you want to do:\n1: Re-Setup the midi devices that are used.\n2: Leave the selected midi devices as-is and just edit button/fader assignment")
        action_select = int(input("Select 1 or 2: "))
        if action_select == 1:
            configureDevices(1) #start device settings dialog because user choice
        elif action_select == 2:
            pass #leave configuration as is
        else:
            print("Invalid selection")
            ScriptExit(0, 0)
    else:
        configureDevices(0) #start device settings dialog because nothing is set up yet
        #the functions will return and we'll continue here

    devices = devdb.all()
    for device in devices: #gave up on documentation here
        try:
            tempmidiport = mido.open_input(device["devicename"])
            tempobj = {"id": device.doc_id, "object": tempmidiport, "devicename": device["devicename"]}
            midiports.append(tempobj)
        except:
            print("\nCould not open", device["devicename"])
            print("The midi device might be used by another application/not plugged in/have a different name.")
            print("Please close the device in the other application/plug it in/select the rename option in the device management menu and restart this script.\n")
            database.close()
            sys.exit(5)

    print("\nPlease press key or move fader/knob on midi controller")
    mainLoop()
    ScriptExit(0, 0)
