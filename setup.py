import mido, threading, sys, atexit
from tinydb import TinyDB, Query

db = TinyDB("config.json")
actions = ["SetCurrentScene", "SetPreviewScene", "TransitionToProgram", "SetCurrentTransition", "StartStopStreaming", "StartStopRecording"]

def exitScript():
    port.close()

def midicallback(message):
    if message.type == "note_on":
        note = message.note
        print("Select Action:")
        counter = 0
        for action in actions:
            print("%s: %s" % (counter, action))
            counter += 1
        input_select = int(input("Select 0-%s: " % str(len(actions)-1)))
        if input_select in range(0, len(actions)):
            action = actions[input_select]
            input_select = input("Select target: ")
            Search = Query()
            result = db.search(Search.note == note)
            if result:
                db.remove(Search.note == note)
                db.insert({"note" : note, "action": action, "target": input_select})
            else:
                db.insert({"note" : note, "action": action, "target": input_select})
            print("""Saved action "%s" for target "%s" with trigger note %s""" % (action, input_select, note))
            print("Please press key on midi controller")
        else:
            print("Fail. Please press next key on midi controller")

def mainLoop():
    while True:
        try:
            x = 1
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    print("MIDItoOBS made by lebaston100.de")
    print("Setup")
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
        midiport = mido.open_input(deviceList[input_select], callback=midicallback)
        atexit.register(exitScript)
        print("Please press key on midi controller")
        mainLoop()
    else:
        print("Please select a valid device")
        sys.exit()
