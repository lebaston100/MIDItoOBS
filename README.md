# Midi OBS what???
This script lets you use a MIDI controller like the Novation Launchpad, Ableton Push, Akai LPD or the Korg nanoPAD to switch scenes and start/stop recording/streaming (more features are planned) in OBS-Studio.

## Requirements

- Obviously a (USB) MIDI controller
- Python 3
- A few pip packages
  - [TinyDB](https://github.com/msiemens/tinydb)
  - [mido](https://github.com/olemb/mido)
  - [python-rtmidi](http://trac.chrisarndt.de/code/wiki/python-rtmidi)
  - [websocket-client](https://github.com/websocket-client/websocket-client)
- The [obs-websocket plugin](https://github.com/Palakis/obs-websocket/releases) (Version >= 4.2.0)
  
## Setup Part 1

- Install Python 3.x.x
- Make sure you install pip
- If you are not sure how this works on your platform use Google, there are about 21400000 results for "how to install python"
- For instructions how to install TinyDB click [here](https://tinydb.readthedocs.io/en/latest/getting-started.html#installing-tinydb)
- For instructions how to install mido click [here](https://github.com/olemb/mido#installing)
- For instructions how to install python-rtmidi click [here](http://trac.chrisarndt.de/code/wiki/python-rtmidi#Quicklinks)
- For instructions how to install websocket-client click [here](https://github.com/websocket-client/websocket-client#installation)

## Setup Part 2 OBS Websocket

- Install the plugin [(Guide)](https://obsproject.com/forum/resources/obs-and-obs-studio-install-plugins-windows.421/)
- Open the "Tools" menu and select "websocket server settings"
- Make sure that "Enable Websocket server" is checked, "Server Port" is 4444 and "Enable authentification" is unchecked"

## Setup Part 3

- [Download the repository](https://github.com/lebaston100/) or clone it
- Connect your MIDI controller
- Launch the setup.py
- You will get a list of available MIDI devices. Type the number you want to select and press Enter
- Now you will be asked to press a button on your MIDI controller, do that
- Select an action from the list and press enter. The names represent the request-type in obs-websocket
- Now you will be asked for the Target
  - SetCurrentScene: Switches to the scene, Target is the scene name(case sensitive)
  - SetPreviewScene: Puts a scene into preview when in studio mode, Target is the scene name(case sensitive)
  - TransitionToProgram: Transitions the current preview scene to program, Target is the transition name(optional, leave empty to use default or set by SetCurrentTransistion)(case sensitive)
  - SetCurrentTransistion: Sets the transition that is used with SetCurrentScene(case sensitive)
  - StartStopStreaming: Toggles the Streaming, leave Target empty
  - StartStopRecording: Toggles the Recording, leave Target empty
  

## Using it

- If you're a first time use make sure to follow setup steps 1-3
  - You can launch setup.py anytime(as long as main.py is not running) to change the configuration of a single button without reconfiguring the whole controller
- First make sure that OBS is running, then launch the main.py file
- The console gives you information when it successfully connects to OBS
- Also, if there is an error it will be printed out(If you ignore case sensitive fields or the scene doesn't exist
- Now just leave it running in the background
  
## Limitations

 - The script only listens to note\_on events, but implementing control\_change events is planned
 - As a result of above you can't use faders, only buttons that send note\_on data