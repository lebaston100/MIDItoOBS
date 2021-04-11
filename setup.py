#!/usr/bin/env python3
import mido, threading, sys, atexit, json, time, signal, argparse
from tinydb import TinyDB, Query
from websocket import create_connection

parser = argparse.ArgumentParser(description='MIDItoOBS Config Setup')

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


####Change IP and Port here
serverIP = args.host
serverPort = args.port
####

database = TinyDB(args.config, indent=4)
db = database.table("keys", cache_size=0)
devdb = database.table("devices", cache_size=0)
buttonActions = ["SetCurrentScene", "SetPreviewScene", "TransitionToProgram", "SetCurrentTransition", "SetSourceVisibility", "ToggleSourceVisibility", "ToggleMute", "SetMute",
                 "StartStopStreaming", "StartStreaming", "StopStreaming", "StartStopRecording", "StartRecording", "StopRecording", "StartStopReplayBuffer",
                 "StartReplayBuffer", "StopReplayBuffer", "SaveReplayBuffer", "PauseRecording", "ResumeRecording", "SetTransitionDuration", "SetCurrentProfile","SetCurrentSceneCollection",
                 "ResetSceneItem", "SetTextGDIPlusText", "SetBrowserSourceURL", "ReloadBrowserSource", "TakeSourceScreenshot", "EnableSourceFilter", "DisableSourceFilter", "ToggleSourceFilter", "SetAudioMonitorType",
                 "EnableStudioMode", "DisableStudioMode", "ToggleStudioMode", "TriggerHotkeyByName", "TriggerHotkeyBySequence", "PlayPauseMedia", "ToggleMediaState", "RestartMedia", "StopMedia", "NextMedia", "PreviousMedia"]
faderActions = ["SetVolume", "SetSyncOffset", "SetSourcePosition", "SetSourceRotation", "SetSourceScale", "SetTransitionDuration", "SetGainFilter", "MoveTbar",
                "Filter/Chroma Key - Contrast", "Filter/Chroma Key - Brightness", "Filter/Chroma Key - Gamma", "Filter/Chroma Key - Opacity", "Filter/Chroma Key - Spill Reduction", "Filter/Chroma Key - Similarity",
                "Filter/Luma Key - Luma Max", "Filter/Luma Key - Luma Max Smooth", "Filter/Luma Key - Luma Min", "Filter/Luma Key - Luma Min Smooth", "Filter/Color Correction - Saturation", "Filter/Color Correction - Contrast",
                "Filter/Color Correction - Brightness", "Filter/Color Correction - Gamma", "Filter/Color Correction - Hue Shift", "Filter/Color Correction - Opacity", "Filter/Color Key - Similarity", "Filter/Color Key - Smoothness", "Filter/Color Key - Brightness", "Filter/Color Key - Contrast",
                "Filter/Color Key - Gamma", "Filter/Sharpen - Sharpness", "Filter/Scroll - Horizontal Speed", "Filter/Scroll - Vertical Speed", "Filter/Video Delay (Async) - Delay", "Filter/Render Delay - Delay",
                "Filter/Generic Filter - Generic Setting"]
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
               "SetBrowserSourceURL": """{"request-type": "SetSourceSettings", "message-id" : "1", "sourceName": "%s", "sourceSettings": {"url": "%s"}}""",
               "SetSourcePosition": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene-name": "%s", "item": "%s", "position": {"%s": %s}}""",
               "SetSourceRotation": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene-name": "%s", "item": "%s", "rotation": %s}""",
               "SetSourceVisibility": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "item": "%s", "visible": %s}""",
               "ToggleSourceVisibility": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "item": "%s", "visible": %s}""",
               "SetSourceScale": """{{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene-name": "%s", "item": "%s", "scale": {{"%s": %s%s}}}}""",
               "ReloadBrowserSource": """{"request-type": "RefreshBrowserSource", "message-id" : "1", "sourceName": "%s"}""",
               "TakeSourceScreenshot": """{"request-type": "TakeSourceScreenshot", "message-id" : "MIDItoOBSscreenshot","sourceName" : "%s", "embedPictureFormat": "png"}""",
               "SetGainFilter": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"db": %s}}""",
               "EnableSourceFilter": """{"request-type": "SetSourceFilterVisibility", "sourceName": "%s", "filterName": "%s", "filterEnabled": true, "message-id": "MIDItoOBS-EnableSourceFilter"}""",
               "DisableSourceFilter": """{"request-type": "SetSourceFilterVisibility", "sourceName": "%s", "filterName": "%s", "filterEnabled": false, "message-id": "MIDItoOBS-DisableSourceFilter"}""",
               "PauseRecording": """{"request-type": "PauseRecording", "message-id" : "MIDItoOBS-PauseRecording"}""",
               "ResumeRecording": """{"request-type": "ResumeRecording", "message-id" : "MIDItoOBS-ResumeRecording"}""",
               "ToggleSourceFilter": """{"request-type": "SetSourceFilterVisibility", "sourceName": "%s", "filterName": "%s", "filterEnabled": %s, "message-id": "MIDItoOBS-EnableSourceFilter"}""",
               "Filter/Chroma Key - Contrast": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"contrast": %s}}""",
               "Filter/Chroma Key - Brightness": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"brightness": %s}}""",
               "Filter/Chroma Key - Gamma": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"gamma": %s}}""",
               "Filter/Chroma Key - Opacity": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"opacity": %s}}""",
               "Filter/Chroma Key - Spill Reduction": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"spill": %s}}""",
               "Filter/Chroma Key - Similarity": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"similarity": %s}}""",
               "Filter/Luma Key - Luma Max": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"luma_max": %s}}""",
               "Filter/Luma Key - Luma Max Smooth": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"luma_max_smooth": %s}}""",
               "Filter/Luma Key - Luma Min": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"luma_min": %s}}""",
               "Filter/Luma Key - Luma Min Smooth": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"luma_min_smooth": %s}}""",
               "Filter/Color Correction - Saturation": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"saturation": %s}}""",
               "Filter/Color Correction - Contrast": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"contrast": %s}}""",
               "Filter/Color Correction - Brightness": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"brightness": %s}}""",
               "Filter/Color Correction - Gamma": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"gamma": %s}}""",
               "Filter/Color Correction - Hue Shift": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"hue_shift": %s}}""",
               "Filter/Color Correction - Opacity": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"opacity": %s}}""",
               "Filter/Color Key - Similarity": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"similarity": %s}}""",
               "Filter/Color Key - Smoothness": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"smoothness": %s}}""",
               "Filter/Color Key - Brightness": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"brightness": %s}}""",
               "Filter/Color Key - Contrast": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"contrast": %s}}""",
               "Filter/Color Key - Gamma": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"gamma": %s}}""",
               "Filter/Sharpen - Sharpness": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"sharpness": %s}}""",
               "Filter/Scroll - Horizontal Speed": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"speed_x": %s}}""",
               "Filter/Scroll - Vertical Speed": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"speed_y": %s}}""",
               "Filter/Video Delay (Async) - Delay": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"delay_ms": %s}}""",
               "Filter/Render Delay - Delay": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"delay_ms": %s}}""",
               "Filter/Generic Filter - Generic Setting": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"%s": %s}}""",
               "SetAudioMonitorType": """{"request-type": "SetAudioMonitorType", "message-id" : "1","sourceName" : "%s", "monitorType": "%s"}""",
               "EnableStudioMode": """{"request-type": "EnableStudioMode", "message-id" : "1"}""",
               "DisableStudioMode": """{"request-type": "DisableStudioMode", "message-id" : "1"}""",
               "ToggleStudioMode": """{"request-type": "ToggleStudioMode", "message-id" : "1"}""",
               "MoveTbar": """{"request-type": "SetTBarPosition", "message-id" : "1", "release": false, "position": %s}""",
               "TriggerHotkeyByName": """{"request-type": "TriggerHotkeyByName", "message-id" : "1", "hotkeyName": "%s"}""",
               "TriggerHotkeyBySequence": """{"request-type": "TriggerHotkeyBySequence", "message-id" : "1", "keyId": "%s"%s}""",
               "PlayPauseMedia": """{"request-type": "PlayPauseMedia", "message-id" : "1", "sourceName": "%s", "playPause": %s}""",
               "ToggleMediaState": """{"request-type": "PlayPauseMedia", "message-id" : "1", "sourceName": "%s", "playPause": %s}""",
               "RestartMedia": """{"request-type": "RestartMedia", "message-id" : "1", "sourceName": "%s"}""",
               "StopMedia": """{"request-type": "StopMedia", "message-id" : "1", "sourceName": "%s"}""",
               "NextMedia": """{"request-type": "NextMedia", "message-id" : "1", "sourceName": "%s"}""",
               "PreviousMedia": """{"request-type": "PreviousMedia", "message-id" : "1", "sourceName": "%s"}"""}

sceneListShort = []
sceneListLong = []
transitionList = []
specialSourcesList = []
profilesList = []
sceneCollectionList = []
gdisourcesList = []

midiports = []

OBS_ALIGN_CENTER = (0)
OBS_ALIGN_LEFT = (1 << 0)
OBS_ALIGN_RIGHT = (1 << 1)
OBS_ALIGN_TOP = (1 << 2)
OBS_ALIGN_BOTTOM = (1 << 3)

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
    if message.type in ["note_on", "note_off"]: #button only
        ignore = message.note
        print("Select Action:")
        counter = 0
        for action in buttonActions:
            print("%s: %s" % (counter, action))
            counter += 1
        input_select = int(input("Select 0-%s: " % str(len(buttonActions)-1)))
        if input_select in range(0, len(buttonActions)):
            action = buttonActions[input_select]
            setupButtonEvents(action, message.channel, message.note, message.velocity, message.type, deviceID)
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
            setupButtonEvents(action, message.channel, message.program, message.value, message.type, deviceID)
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
                        setupButtonEvents(action, message.channel, message.control, message.value, message.type, deviceID)
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
                        setupFaderEvents(action, message.channel, message.control, message.value, message.type, deviceID)
        except ValueError:
            print("Please try again and enter a valid number")

#I know this is very messy, but i challange you to make a better version(as a native plugin or pull request to obs-studio)
def setupFaderEvents(action, channel, NoC, VoV, msgType, deviceID):
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
        saveFaderToFile(channel, msgType, NoC, VoV, "fader" , action, scale, "SetVolume", deviceID)
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
        saveFaderToFile(channel, msgType, NoC, VoV, "fader" , action, scale, "SetSyncOffset", deviceID)
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
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , action, scale, "SetSourcePosition", deviceID)
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
        saveFaderToFile(channel, msgType, NoC, VoV, "fader" , action, scale, "SetSourceRotation", deviceID)
    elif action == "SetTransitionDuration":
        scale = askForInputScaling()
        action = jsonArchive["SetTransitionDuration"]
        saveFaderToFile(channel, msgType, NoC, VoV, "fader" , action, scale, "SetTransitionDuration", deviceID)
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
            alignmentlist = ["NONE", "Top Left", "Top Center", "Top Right", "Center Left", "Center", "Center Right", "Bottom Left", "Bottom Center", "Bottom Right"]
            alignmentvaluelist = ["NONE", OBS_ALIGN_TOP | OBS_ALIGN_LEFT, OBS_ALIGN_TOP | OBS_ALIGN_CENTER, OBS_ALIGN_TOP | OBS_ALIGN_RIGHT,
                                  OBS_ALIGN_CENTER | OBS_ALIGN_LEFT, OBS_ALIGN_CENTER | OBS_ALIGN_CENTER, OBS_ALIGN_CENTER | OBS_ALIGN_RIGHT,
                                  OBS_ALIGN_BOTTOM | OBS_ALIGN_LEFT, OBS_ALIGN_BOTTOM | OBS_ALIGN_CENTER, OBS_ALIGN_BOTTOM | OBS_ALIGN_RIGHT]
            counter = 0
            print()
            for line in alignmentlist:
                print("%s: %s" % (counter, line))
                counter += 1
            alignment = int(input("Select source alignment (0-{}): ".format(len(alignmentlist)-1)))
            if alignment in range(0, len(alignmentlist)-1):
                alignmentplaceholder = ""
                if type(alignmentvaluelist[alignment]) == int:
                    alignmentplaceholder = '}}, "position": {{"alignment": %d' % alignmentvaluelist[alignment]
                action = jsonArchive["SetSourceScale"] % (selected["scene"], selected["source"], tempTargetList[target], "{0}", alignmentplaceholder)
                saveFaderToFile(channel, msgType, NoC, VoV, "fader" , action, scale, "SetSourceScale", deviceID)
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
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , action, scale, "SetGainFilter", deviceID)
        else:
            print("The selected source has no gain filter. Please add it in the source filter dialog and try again.")
    elif action == "MoveTbar":
        action = jsonArchive["MoveTbar"]# % ("%s")
        saveFaderToFile(channel, msgType, NoC, VoV, "fader" , action, [0, 1], "MoveTbar", deviceID)
    elif action == "Filter/Chroma Key - Contrast":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "chroma_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Chroma Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Chroma Key - Brightness":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "chroma_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Chroma Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Chroma Key - Gamma":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "chroma_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Chroma Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Chroma Key - Opacity":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "chroma_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Chroma Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Chroma Key - Spill Reduction":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "chroma_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Chroma Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Chroma Key - Similarity":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "chroma_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Chroma Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Luma Key - Luma Max":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "luma_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Luma Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Luma Key - Luma Max Smooth":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "luma_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Luma Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Luma Key - Luma Min":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "luma_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Luma Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Luma Key - Luma Min Smooth":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "luma_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Luma Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Correction - Saturation":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Correction\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Correction - Contrast":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Correction\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Correction - Brightness":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Correction\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Correction - Gamma":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Correction\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Correction - Hue Shift":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Correction\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Correction - Opacity":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Correction\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Key - Similarity":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Key - Smoothness":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Key - Brightness":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Key - Contrast":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Color Key - Gamma":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "color_key_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Color Key\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Sharpen - Sharpness":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "sharpness_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Sharpen\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Scroll - Horizontal Speed":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "scroll_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Scroll\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Scroll - Vertical Speed":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "scroll_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Scroll\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Video Delay (Async) - Delay":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "async_delay_filter")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Video Delay (Async)\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Render Delay - Delay":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        filters = getCompatibleFiltersFromSource(source, "gpu_delay")
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 1:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
            else:
                filterName = tempFilterList[0]
                print("Automatically selected filter \"{}\" because it's the only one that fit's this request type".format(filterName))
            scale = askForInputScaling()
            obsaction = jsonArchive[action] % (source, filterName, "%s")
            saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, action, deviceID)
        else:
            print("The selected source has no \"Render Delay\" filter. Please add it in the source filter dialog and try again.")
    elif action == "Filter/Generic Filter - Generic Setting":
        updateSpecialSources()
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        for item in specialSourcesList:
            tempSceneList.append(item)
        source = printArraySelect(tempSceneList)
        filters = getSourceFilters(source)
        if filters:
            tempFilterList = [f["name"] for f in filters]
            if len(tempFilterList) > 0:
                filterName = printArraySelect(tempFilterList)
                print("Selected filtername:", filterName)
                filterProperties = next(list(f["settings"].keys()) for f in filters if f["name"] == filterName)
                print("Here are some filter properties that have been changed. If you want the setting to show up here you must first change it's value inside obs away from the default.")
                for line in filterProperties:
                    print("'{0}'".format(line))
                propName = str(input("Please enter the full name of the property, without the quotes (even if it didn't show up in the list above but you know the name): "))
                isInt = int(input("Should the data be a:\n0: Int\n1: Float\nSelect 0-1: "))
                scale = askForInputScaling()
                obsaction = jsonArchive[action] % (source, filterName, propName, "%s")
                if not isInt:
                    saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, "Filter-Generic-Int", deviceID)
                else:
                    saveFaderToFile(channel, msgType, NoC, VoV, "fader" , obsaction, scale, "Filter-Generic-Float", deviceID)
        else:
            print("There are currently no filters on this source")


def setupButtonEvents(action, channel, NoC, VoV, msgType, deviceID):
    print()
    print("You selected: %s" % action)
    if action == "SetCurrentScene":
        updateSceneList()
        scene = printArraySelect(sceneListShort)
        bidirectional = askForBidirectional()
        action = jsonArchive["SetCurrentScene"] % scene
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID, bidirectional)
    elif action == "SetPreviewScene":
        updateSceneList()
        scene = printArraySelect(sceneListShort)
        bidirectional = askForBidirectional()
        action = jsonArchive["SetPreviewScene"] % scene
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID, bidirectional)
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
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "SetCurrentTransition":
        updateTransitionList()
        transition = printArraySelect(transitionList)
        action = jsonArchive["SetCurrentTransition"] % transition
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "StartStopStreaming":
        action = jsonArchive["StartStopStreaming"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "StartStreaming":
        action = jsonArchive["StartStreaming"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "StopStreaming":
        action = jsonArchive["StopStreaming"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "StartStopRecording":
        action = jsonArchive["StartStopRecording"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "StartRecording":
        action = jsonArchive["StartRecording"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "StopRecording":
        action = jsonArchive["StopRecording"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "StartStopReplayBuffer":
        action = jsonArchive["StartStopReplayBuffer"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "StartReplayBuffer":
        action = jsonArchive["StartReplayBuffer"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "StopReplayBuffer":
        action = jsonArchive["StopReplayBuffer"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "SaveReplayBuffer":
        action = jsonArchive["SaveReplayBuffer"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "PauseRecording":
        action = jsonArchive["PauseRecording"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "ResumeRecording":
        action = jsonArchive["ResumeRecording"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
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
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "ToggleSourceVisibility":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        source = source1 = printArraySelect(tempSceneList)
        sceneListShort.append("--Current--")
        print("\nSelect if you want to target the source only in a specific scene")
        scene = printArraySelect(sceneListShort)
        if scene != "--Current--":
            source = source + '", "scene-name": "' + scene
            action = jsonArchive["ToggleSourceVisibility"] % (source, "%s")
            saveTODOButtonToFile(channel, msgType, NoC, VoV, "button" , action, "ToggleSourceVisibility2", source1, scene, deviceID)
            return
        action = jsonArchive["ToggleSourceVisibility"] % (source, "%s")
        saveTODOButtonToFile(channel, msgType, NoC, VoV, "button" , action, "ToggleSourceVisibility", source1, "", deviceID)
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
        bidirectional = askForBidirectional()
        action = jsonArchive["ToggleMute"] % source
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID, bidirectional)
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
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "SetTransitionDuration":
        time = int(input("Input the desired time(in milliseconds): "))
        action = jsonArchive["SetTransitionDuration"] % time
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "SetCurrentProfile":
        updateProfileList()
        profilename = printArraySelect(profilesList)
        action = jsonArchive["SetCurrentProfile"] % profilename
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "SetRecordingFolder":
        recpath = str(input("Input the desired path: "))
        action = jsonArchive["SetRecordingFolder"] % recpath
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "SetCurrentSceneCollection":
        updatesceneCollectionList()
        scenecollection = printArraySelect(sceneCollectionList)
        action = jsonArchive["SetCurrentSceneCollection"] % scenecollection
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
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
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
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
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
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
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "ReloadBrowserSource":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList and line["type"] == "browser_source":
                    tempSceneList.append(line["name"])
        source = printArraySelect(tempSceneList)
        action = jsonArchive["ReloadBrowserSource"] % (source)
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "TakeSourceScreenshot":
        updateSceneList()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        for scene in sceneListShort:
            tempSceneList.append(scene)
        source = printArraySelect(tempSceneList)
        action = jsonArchive["TakeSourceScreenshot"] % (source)
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "EnableSourceFilter":
        updateSceneList()
        updateSpecialSources()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
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
            saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
        else:
            print("\nThis source has no filters")
    elif action == "DisableSourceFilter":
        updateSceneList()
        updateSpecialSources()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
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
            saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
        else:
            print("\nThis source has no filters")
    elif action == "ToggleSourceFilter":
        updateSceneList()
        updateSpecialSources()
        tempSceneList = []
        for scene in sceneListLong:
            tempSceneList.append(scene["name"])
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
        saveTODOButtonToFile(channel, msgType, NoC, VoV, "button" , action, "ToggleSourceFilter", source, selectedFilter, deviceID)
    elif action == "SetAudioMonitorType":
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
        typeOfMonitor = printArraySelect(["None", "Monitor Only", "Monitor and Output"])

        if typeOfMonitor == "None":
            typeOfMonitor = "none"
        elif typeOfMonitor == "Monitor Only":
            typeOfMonitor = "monitorOnly"
        else:
            typeOfMonitor = "monitorAndOutput"

        action = jsonArchive["SetAudioMonitorType"] % (source, typeOfMonitor)
        saveButtonToFile(channel, msgType, NoC, VoV, "button", action, deviceID)
    elif action == "EnableStudioMode":
        action = jsonArchive["EnableStudioMode"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "DisableStudioMode":
        action = jsonArchive["DisableStudioMode"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "ToggleStudioMode":
        action = jsonArchive["ToggleStudioMode"]
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "TriggerHotkeyByName":
        hotkeyName = str(input("Please enter the unique name of the hotkey, as defined when registering the hotkey (This is not a physical button name but rather an internal name. You can get it by looking at the [Hotkeys] section in the profile basic.ini file): "))
        action = jsonArchive["TriggerHotkeyByName"] % (hotkeyName)
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "TriggerHotkeyBySequence":
        hotkeyName = str(input("Please enter the full name of the key as defined in https://github.com/obsproject/obs-studio/blob/master/libobs/obs-hotkeys.h (OBS_KEY_<something>): "))
        inp = input("Do you want to add any modifier keys?\n0: NO\n1: shift\n2: alt\n3: control\n4: command\nYou can select one or multiple keys by tying in the numbers of the ones you want seperated by a ',' : ")
        mods = ""
        cmap = ["", "shift", "alt", "control", "command"]
        try:
            arr = [cmap[int(i)] for i in inp.split(",") if int(i)]
            if arr:
                mods += ', "keyModifiers": {'
                for ix, i in enumerate(arr):
                    mods += f'"{i}": true'
                    mods += "" if ix == len(arr)-1 else ","
                mods += "}"
        except:
            print("Your input was wrong, make sure you follow the directions")
        action = jsonArchive["TriggerHotkeyBySequence"] % (hotkeyName, mods)
        saveButtonToFile(channel, msgType, NoC, VoV, "button" , action, deviceID)
    elif action == "PlayPauseMedia":
        tempSourceList = []
        sources = getMediaSources()
        if sources:
            for source in sources:
                tempSourceList.append(source["sourceName"])
            source = printArraySelect(tempSourceList)
            print("What do you want to do?")
            playorpause = printArraySelect(["Play", "Pause"])
            if playorpause == "Play":
                playorpause = "false"
            else:
                playorpause = "true"
            action = jsonArchive["PlayPauseMedia"] % (source, playorpause)
            saveButtonToFile(channel, msgType, NoC, VoV, "button", action, deviceID)
        else:
            print("No media source found")
    elif action == "ToggleMediaState":
        tempSourceList = []
        sources = getMediaSources()
        if sources:
            for source in sources:
                tempSourceList.append(source["sourceName"])
            source = printArraySelect(tempSourceList)
            action = jsonArchive["ToggleMediaState"] % (source, "%s")
            saveTODOButtonToFile(channel, msgType, NoC, VoV, "button" , action, "ToggleMediaState", source, "", deviceID)
        else:
            print("No media source found")
    elif action == "RestartMedia":
        tempSourceList = []
        sources = getMediaSources()
        if sources:
            for source in sources:
                tempSourceList.append(source["sourceName"])
            source = printArraySelect(tempSourceList)
            action = jsonArchive["RestartMedia"] % (source)
            saveButtonToFile(channel, msgType, NoC, VoV, "button", action, deviceID)
        else:
            print("No media source found")
    elif action == "StopMedia":
        tempSourceList = []
        sources = getMediaSources()
        if sources:
            for source in sources:
                tempSourceList.append(source["sourceName"])
            source = printArraySelect(tempSourceList)
            action = jsonArchive["StopMedia"] % (source)
            saveButtonToFile(channel, msgType, NoC, VoV, "button", action, deviceID)
        else:
            print("No media source found")
    elif action == "NextMedia":
        tempSourceList = []
        sources = getMediaSources()
        for source in sources:
            if source["sourceKind"] == "vlc_source":
                tempSourceList.append(source["sourceName"])
        if tempSourceList:
            source = printArraySelect(tempSourceList)
            action = jsonArchive["NextMedia"] % (source)
            saveButtonToFile(channel, msgType, NoC, VoV, "button", action, deviceID)
        else:
            print("No media source found")
    elif action == "PreviousMedia":
        tempSourceList = []
        sources = getMediaSources()
        for source in sources:
            if source["sourceKind"] == "vlc_source":
                tempSourceList.append(source["sourceName"])
        if tempSourceList:
            source = printArraySelect(tempSourceList)
            action = jsonArchive["PreviousMedia"] % (source)
            saveButtonToFile(channel, msgType, NoC, VoV, "button", action, deviceID)
        else:
            print("No media source found")


def saveFaderToFile(msg_channel, msg_type, msgNoC, VoV, input_type, action, scale, cmd, deviceID):
    print("Saved %s with control %s for action %s on device %s channel %s" % (msg_type, msgNoC, cmd, deviceID, msg_channel))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID) & (Search.msg_channel == msg_channel))
    if result:
        db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID) & (Search.msg_channel == msg_channel))
        db.insert({"msg_channel": msg_channel, "msg_type": msg_type, "msgNoC": msgNoC, "msgVoV": VoV, "input_type": input_type, "scale_low": scale[0], "scale_high": scale[1], "action": action, "cmd": cmd, "deviceID": deviceID})
    else:
        db.insert({"msg_channel": msg_channel, "msg_type": msg_type, "msgNoC": msgNoC, "msgVoV": VoV, "input_type": input_type, "scale_low": scale[0], "scale_high": scale[1], "action": action, "cmd": cmd, "deviceID": deviceID})

def saveButtonToFile(msg_channel, msg_type, msgNoC, VoV, input_type, action, deviceID, bidirectional=False):
    print("Saved %s with note/control %s for action %s on device %s channel %s, bidirectional: %d" % (msg_type, msgNoC, action, deviceID, msg_channel, bidirectional))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID) & (Search.msg_channel == msg_channel))
    if result:
        db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID) & (Search.msg_channel == msg_channel))
    db.insert({"msg_channel": msg_channel, "msg_type": msg_type, "msgNoC": msgNoC, "msgVoV": VoV, "input_type": input_type, "action" : action, "deviceID": deviceID, "bidirectional": bidirectional})

def saveTODOButtonToFile(msg_channel, msg_type, msgNoC, VoV, input_type, action, request, target, field2, deviceID):
    print("Saved %s with note/control %s for action %s on device %s channel %s" % (msg_type, msgNoC, action, deviceID, msg_channel))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID) & (Search.msg_channel == msg_channel))
    if result:
        db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID) & (Search.msg_channel == msg_channel))
        db.insert({"msg_channel": msg_channel, "msg_type": msg_type, "msgNoC": msgNoC, "msgVoV": VoV, "input_type": input_type, "action" : action, "request": request, "target": target, "deviceID": deviceID, "field2": field2})
    else:
        db.insert({"msg_channel": msg_channel, "msg_type": msg_type, "msgNoC": msgNoC, "msgVoV": VoV, "input_type": input_type, "action" : action, "request": request, "target": target, "deviceID": deviceID, "field2": field2})

def printArraySelect(array):
    while True:
        if len(array) == 0:
            raise RuntimeError("You most likely are missing the required source or scene in obs that you just wanted to assign. Exiting now.")
        for i, line in enumerate(array):
            print("{}: {}".format(i, line))
        if i > 0:
            select = int(input("Select 0-%s: " % str(len(array)-1)))
        else:
            select = int(input("Select 0: "))
        if select >= 0 and select <= i:
            return array[select]
        else:
            print("\nPlease select a valid number!")

def askForInputScaling():
    print("Setup input scale")
    low = int(input("Select lower output value: "))
    high = int(input("Select higher output value: "))
    return low, high

def askForBidirectional():
    print("Do you want the control to be bidirectional?\n1: Yes\n2: No")
    bidirectional = int(input("Select 1 or 2: "))
    return bidirectional == 1

def updateTransitionList():
    global transitionList
    ws = create_connection("ws://{0}:{1}".format(serverIP, serverPort))
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
    ws = create_connection("ws://{0}:{1}".format(serverIP, serverPort))
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
    ws = create_connection("ws://{0}:{1}".format(serverIP, serverPort))
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
    ws = create_connection("ws://{0}:{1}".format(serverIP, serverPort))
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
    ws = create_connection("ws://{0}:{1}".format(serverIP, serverPort))
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

def getMediaSources():
    ws = create_connection("ws://{0}:{1}".format(serverIP, serverPort))
    ws.send("""{"request-type": "GetMediaSourcesList", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    mediaSources = []
    if jsn["message-id"] == "99999999":
        mediaSources = jsn["mediaSources"]
    else:
        print("Failed to update")
    ws.close()
    return mediaSources

def checkIfSourceHasGainFilter(sourcename):
    ws = create_connection("ws://{0}:{1}".format(serverIP, serverPort))
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

def checkIfSourceHasColorCorrectionFilter(sourcename):
    ws = create_connection("ws://{0}:{1}".format(serverIP, serverPort))
    print("\nChecking source filters, plase wait")
    ws.send('{"request-type": "GetSourceFilters", "message-id": "MIDItoOBS-checksourcecolorcorrectionfilter", "sourceName": "' + sourcename + '"}')
    result =  ws.recv()
    ws.close()
    jsn = json.loads(result)
    if jsn["message-id"] == "MIDItoOBS-checksourcecolorcorrectionfilter":
        for line in jsn["filters"]:
            if line["type"] == "color_filter" and line["name"] == "miditoobs-opacity":
                return line["name"]
    return False

def getSourceFilters(sourcename):
    ws = create_connection("ws://{0}:{1}".format(serverIP, serverPort))
    print("\nChecking source filters, plase wait")
    ws.send('{"request-type": "GetSourceFilters", "message-id": "MIDItoOBS-getSourceFilters", "sourceName": "' + sourcename + '"}')
    result =  ws.recv()
    ws.close()
    jsn = json.loads(result)
    if jsn["message-id"] == "MIDItoOBS-getSourceFilters":
        return jsn["filters"]
    else:
        return False

def getCompatibleFiltersFromSource(sourceName, filterType):
    ws = create_connection("ws://{0}:{1}".format(serverIP, serverPort))
    print("\nRetrieving source filters, plase wait")
    ws.send('{"request-type": "GetSourceFilters", "message-id": "MIDItoOBS-getSourceFilters", "sourceName": "' + sourceName + '"}')
    result =  ws.recv()
    ws.close()
    jsn = json.loads(result)
    filters = list(filter(lambda d: d["type"] == filterType, jsn["filters"]))
    if filters:
        return filters
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
                    if msg.type in ["note_on","note_off"]:
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
            print("\nCould not open device", device["devicename"])
            print("The midi device might be used by another application/not plugged in/have a different name.")
            print("Please close the device in the other application/plug it in/edit the name in the config.json and restart this script.\n")
            database.close()
            sys.exit(5)

    print("\nPlease press key or move fader/knob on midi controller")
    mainLoop()
    ScriptExit(0, 0)
