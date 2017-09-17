import mido, websocket, threading, sys, json, atexit
from tinydb import TinyDB, Query

db = TinyDB("config.json")

jsonArchive = {"SetCurrentScene": """{"request-type" : "SetCurrentScene", "message-id" : "1", "scene-name" : "%s"}""", "SetPreviewScene": """{"request-type" : "SetPreviewScene", "message-id" : "1", "scene-name" : "%s"}""", "TransitionToProgram": """{"request-type" : "TransitionToProgram", "message-id" : "1" %s}""", "SetCurrentTransition": """{"request-type" : "SetCurrentTransition", "message-id" : "1", "transition-name" : "%s"}""", "StartStopStreaming": """{"request-type" : "StartStopStreaming", "message-id" : "1"}""", "StartStopRecording": """{"request-type" : "StartStopRecording", "message-id" : "1"}"""}

def midicallback(message):
    if message.type == "note_on":
        Search = Query()
        result = db.search(Search.note == message.note)
        if result[0]["action"] == "TransitionToProgram":
            if result[0]["target"]:
                tmp = ', "with-transition": {"name": "' + str(result[0]["target"]) + '"}'
                string = jsonArchive[result[0]["action"]] % tmp
            else:
                string = jsonArchive[result[0]["action"]]
        else:
            string = jsonArchive[result[0]["action"]] % result[0]["target"]
        obs_ws.send(string)

def exitScript():
    port.close()

def obs_on_message(ws, message):
    jsn = json.loads(message)
    if "error" in jsn:
        print("Error: %s" % jsn["error"])
            
def obs_on_error(ws, error):
    print("Websocket Error: %" % str(error))

def obs_on_close(ws):
    print("OBS disconnected or timed out")

def obs_on_open(ws):
    print("OBS connected")
    
def obs_start():
    obs_ws.run_forever()

if __name__ == "__main__":
    print("MIDItoOBS made by lebaston100.de")
    print("Main program started.")
    Search = Query()
    result = db.search(Search.type.exists())
    if result:
        port = mido.open_input(result[0]["value"], callback=midicallback)
        obs_ws = websocket.WebSocketApp("ws://localhost:4444", on_message = obs_on_message, on_error = obs_on_error, on_close = obs_on_close)
        obs_ws.on_open = obs_on_open
        atexit.register(exitScript)
        threading.Thread(target=obs_start).start()
    else:
        print("Please run setup.py")
        sys.exit()
