# Midi OBS what???
This script lets you use a MIDI controller like the Novation Launchpad, Ableton Push, Akai LPD or the Korg nanoPAD to switch scenes, start/stop recording/streaming, control volume/delay/transition time and much more in [obs-studio](https://github.com/jp9000/obs-studio).

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
- For instructions how to install TinyDB click [here](https://tinydb.readthedocs.io/en/latest/getting-started.html#installing-tinydb)
- For instructions how to install mido click [here](https://github.com/olemb/mido#installing)
- For instructions how to install python-rtmidi click [here](http://trac.chrisarndt.de/code/wiki/python-rtmidi#Quicklinks)
- For instructions how to install websocket-client click [here](https://github.com/websocket-client/websocket-client#installation)

## Setup Part 2 OBS Websocket

- Install the plugin [(How to install a plugin in obs-studio)](https://obsproject.com/forum/resources/obs-and-obs-studio-install-plugins-windows.421/)
- Open the "Tools" menu and select "websocket server settings"
- Make sure that "Enable Websocket server" is checked, "Server Port" is 4444 and "Enable authentification" is unchecked

## Setup Part 3

- [Download the repository](https://github.com/lebaston100/) or clone it
- Connect your MIDI controller
- Launch obs-studio
- Launch the setup.py
- You will get a list of available MIDI devices. Type the number you want to select and press Enter
- Now you will be asked to press a button or move a fader on your MIDI controller, do that
- If your midi controller sends control change messages, you will also be asked for the type of the input(fader or button)
- Select an action from the list and press enter. The names represent the request-type in obs-websocket
- Depending on the action, you will also be asked for the scene and source name
- Available for buttons:
  - SetCurrentScene: Switches to the scene
  - SetPreviewScene: Puts a scene into preview when in studio mode
  - TransitionToProgram: Transitions the current preview scene to program
  - SetCurrentTransistion: Sets the transition that is used with SetCurrentScene
  - StartStopStreaming: Toggles the Streaming
  - StartStreaming: Starts streaming
  - StopStreaming: Stops streaming
  - StartStopRecording: Toggles the Recording
  - StartRecording: Starts recording
  - StopRecording: Stops recording
  - SetSourceRender: Hides or unhides a source(Nto possible to toggle atm, you need to assign a second button for the other action)
  - ToggleMute: Toggels the mute status from a source
  - SetMute: Mutes or unmutes a source
  - StartStopReplayBuffer: Toggles the replay buffer
  - StartReplayBuffer: Starts the replay buffer
  - StopReplayBuffer: Stops the replay buffer
  - SaveReplayBuffer: Save the replay buffer
- Available for faders
  - SetTransitionDuration: Sets the lenght of the currently selected transistion if supported(fade)(in ms)
  - SetVolume: Sets the volume of a source
  - SetSyncOffset: Sets the sync offset of a source(in ns)
  - SetSceneItemPosition: Sets the X/Y position or rotation of a source
  
For a detailed description see the [obs-websocket protocol documentation](https://github.com/Palakis/obs-websocket/blob/master/docs/generated/protocol.md)
  
  
### Understanding input scaling

A midi value can be something between 0-127. That is a very limited number.

You will only be asked for Input Scale setup if it's required for the function(SetSceneItemPosition, SetSyncOffset, SetTransitionDuration).

The first value you have to enter(lower output value) is the value that will be sent when the fader is sending a 0. The second value you have to enter(higher output value) is the value that will be sent when the fader is sending a 127. The range between the 2 numbers will be interpolated.
  

## Using it

- If you're a first time use make sure to follow setup steps 1-3
  - You can launch setup.py anytime(as long as main.py is not running) to change the configuration of a single button/fader without reconfiguring the whole controller
- Always make sure that obs is running before launching any of the scripts
- Launch the main.py file
- The console gives you information when it successfully connects to OBS
- Also, if there is an error it will be printed out(If you ignore case sensitive fields or the scene doesn't exist)
- Now just leave it running in the background