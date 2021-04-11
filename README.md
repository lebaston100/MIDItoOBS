**This is a fork of <a href="https://github.com/lebaston100/MIDItoOBS">lebaston100's MIDItoOBS</a>. Please consider checking out that team's excellent work.** This fork was created for our specific needs with the APC40 mkii.


# Midi OBS what???
This script let's you use one or multiple MIDI controller (like the Novation Launchpad, Ableton Push, Akai LPD or the Korg nanoPAD to mention a few) to switch scenes, start/stop recording/streaming, control volume/filter settings/gain/opacity/t-bar/delay/transition time and more in [obs-studio](https://github.com/obsproject/obs-studio).

If you want to play it safe, use the latest release. If you want to use the latest features then just clone the master branch.

## Requirements

- Obviously a (USB) MIDI controller
- Python 3
- A few pip packages
  - [TinyDB](https://github.com/msiemens/tinydb)
  - [mido](https://github.com/olemb/mido)
  - [python-rtmidi](https://pypi.python.org/pypi/python-rtmidi)
  - [websocket-client](https://github.com/websocket-client/websocket-client)
  - [dbj](https://github.com/pdrb/dbj)
- The [obs-websocket plugin](https://github.com/Palakis/obs-websocket/releases) (Version >= 4.9.0)
  
## Setup Part 1

- Install Python 3.x.x (whatever the latest version is)
  - On Windows: Make sure you trick "Add Python 3.x to PATH" in the setup
- Make sure you also install pip
- For instructions how to install TinyDB click [here](https://tinydb.readthedocs.io/en/latest/getting-started.html#installing-tinydb)
- For instructions how to install mido and python-rtmidi click [here](https://github.com/olemb/mido#installing)
- For instructions how to install websocket-client click [here](https://github.com/websocket-client/websocket-client#installation)
- For instructions how to install dbj click [here](https://github.com/pdrb/dbj#install)

If you want to install all packages in one go, run "pip install -r requirements.txt"

## Setup Part 2 OBS Websocket

- Download the installer and run it
- Start OBS, open the "Tools" menu and select "websocket server settings"
- Make sure that "Enable Websocket server" is checked, "Server Port" is 4444, "Enable authentification" is unchecked and "Enable System Tray Alerts" is unchecked(trust me, you don't want that on)

## Setup Part 3

- [Download the latest Release](https://github.com/lebaston100/MIDItoOBS/releases) or clone it if you want to test the bleeding edge features and bugfixes
- Connect your MIDI controller
- Launch obs-studio
- Launch the setup.py (Try double click or the "Run Setup.bat" if you are on Windows)
- If you run the setup for the first time and have no yet setup a device yet, it will automatically start the device configuration:
  - You will get a list of available MIDI devices. Type the number you want to select and press Enter
  - You will be asked if you want to ad another device.
  - If you only have a single device choose 2 and press enter, otherwise select 1 and you will get a list with remaining devices.
- Now you will be asked to press a button or move a fader on your MIDI controller, do that
- If your midi controller sends control change messages, you will also be asked for the type of the input(fader or button)
- Select an action from the list and press enter. The names represent the request-type in obs-websocket
- Depending on the action, you will also be asked for the scene and source name (selecting always works by typing in the number and pressing enter). If no source of that type is available and you are promted to "select 0--1:" then you know that is no such source available in obs and the script will crash trying to select anything. Just add the required object and restart the setup script in this case. (This is already on the todo list for a further update)
- Available for buttons:
  - SetCurrentScene: Switches to the scene
  - SetPreviewScene: Puts a scene into preview when in studio mode
  - TransitionToProgram: Transitions the current preview scene to program
  - SetCurrentTransistion: Sets the transition that is used with SetCurrentScene
  - SetSourceVisibility: Hides or unhides a source
  - ToggleSourceVisibility: Toggles the visibility of a source
  - ToggleMute: Toggles the mute status from a source
  - SetMute: Mutes or unmutes a source
  - StartStopStreaming: Toggles the Streaming
  - StartStreaming: Starts streaming
  - StopStreaming: Stops streaming
  - StartStopRecording: Toggles the Recording
  - StartRecording: Starts recording
  - StopRecording: Stops recording
  - StartStopReplayBuffer: Toggles the replay buffer
  - StartReplayBuffer: Starts the replay buffer
  - StopReplayBuffer: Stops the replay buffer
  - SaveReplayBuffer: Save the replay buffer
  - PauseRecording: Pauses the recording
  - ResumeRecording: Resume the recording that was previously paused
  - SetTransitionDuration: Sets the length of the currently selected transistion if supported(fade)(in ms) to a predefined value
  - SetCurrentProfile: Changes to the selected obs profile
  - SetCurrentSceneCollection: Changes to the selected obs scene collection
  - ResetSceneItem: Resets a scene item
  - SetTextGDIPlusText: Sets the text of a GDI text source
  - SetBrowserSourceURL: Sets the url of a BrowserSource
  - ReloadBrowserSource: Reloads a BrowserSource
  - TakeSourceScreenshot: Don't be fooled by the name; Takes a screenshot of the selected source or complete scene and saves it inside the MIDItoOBS folder as a png image
  - EnableSourceFilter: Enables a filter that is on a source (Works with "Audio Filters" and Video "Effect Filters")
  - DisableSourceFilter: Disables a filter that is on a source (Works with "Audio Filters" and Video "Effect Filters")
  - ToggleSourceFilter: Toggles the status of a filter on a source for each button press
  - SetAudioMonitor: Sets the audio monitor option on a source
  - EnableStudioMode: Enables Studio Mode
  - DisableStudioMode: Disables Studio Mode
  - ToggleStudioMode: Toggles Studio Mode
  - TriggerHotkeyByName: Triggers an obs event, see the [obs-websocket wiki](https://github.com/Palakis/obs-websocket/blob/4.9.0/docs/generated/protocol.md#triggerhotkeybyname) for details
  - TriggerHotkeyBySequence: Triggers an obs event based on the configured keyboard combination, see the [obs-websocket wiki](https://github.com/Palakis/obs-websocket/blob/4.9.0/docs/generated/protocol.md#triggerhotkeybyname) for details
  - PlayPauseMedia: Start or Pause Media/VLC Source playback
  - ToggleMediaState: Toggle Media/VLC Source playback
  - RestartMedia: Restart Media/VLC Source playback
  - StopMedia: Stop Media/VLC Source playback
  - NextMedia: Jump to the next playlist item. Only works with the vlc source.
  - PreviousMedia: Jump to the previous playlist item. Only works with the vlc source.
  
- Available for faders/knobs
  - SetVolume: Sets the volume of a source (unlike other solutions this will actually make the fader move in a visual linear way inside obs(Like a % slider))
  - SetSyncOffset: Sets the sync offset of a source [in ns]
  - SetSourcePosition: Sets the x or y position of a source [in px]
  - SetSourceRotation: Sets the rotation of a source [in degree]
  - SetSourceScale: Sets the scale for x/y OR both of a source (For the scaling 1 = original scale). You can also select around which position the source will be scaled(align).
  - SetTransitionDuration: Sets the length of the currently selected transistion if supported(fade)[in ms]
  - SetGainFilter: Sets the volume gain value inside the gain filter of a source (For the scaling -30 to 30 is a valid range you can work in). This will automatically default to the first gain filter found in a source!
  - MoveTbar: This will move the transition T-Bar. Make sure you always completely finish a T-Bar move by going to one end to the other otherwise obs will stay in the "a transition is currently happening"-state. Be careful because the state might go "out of sync" with the physical fader if you use any other tools that move the t-bar.
  - Filter/Chroma Key - Contrast: This controls the "Contrast" value for a "Chroma Key" Filter [-1 - 1]
  - Filter/Chroma Key - Brightness: This controls the "Brightness" value for a "Chroma Key" Filter [-1 - 1]
  - Filter/Chroma Key - Gamma: This controls the "Gamma" value for a "Chroma Key" Filter [-1 - 1]
  - Filter/Chroma Key - Opacity: This controls the "Opacity" value for a "Chroma Key" Filter [0 - 100]
  - Filter/Chroma Key - Spill Reduction: This controls the "Key Color Spill Reduction" value for a "Chroma Key" Filter [0 - 1000]
  - Filter/Chroma Key - Similarity: This controls the "Similarity" value for a "Chroma Key" Filter [0 - 1000]
  - Filter/Luma Key - Luma Max: Opacity: This controls the "Luma Max" value for a "Luma Key" Filter [0 - 1]
  - Filter/Luma Key - Luma Max Smooth: This controls the "Luma Max Smooth" value for a "Luma Key" Filter [0 - 1]
  - Filter/Luma Key - Luma Min: Opacity: This controls the "Luma Min" value for a "Luma Key" Filter [0 - 1]
  - Filter/Luma Key - Luma Min Smooth: This controls the "Luma Min Smooth" value for a "Luma Key" Filter [0 - 1]
  - Filter/Color Correction - Saturation: This controls the "Saturation" value for a "Color Correction" Filter [-1 - 5]
  - Filter/Color Correction - Contrast: This controls the "Contrast" value for a "Color Correction" Filter [-2 - 2]
  - Filter/Color Correction - Brightness: This controls the "Brightness" value for a "Color Correction" Filter [-1 - 1]
  - Filter/Color Correction - Gamma: This controls the "Gamma" value for a "Color Correction" Filter [-3 - 3]
  - Filter/Color Correction - Hue Shift: This controls the "Gamma" value for a "Color Correction" Filter [-180 - 180] (Replaces the old SetColorCorrectionHueShift)
  - Filter/Color Correction - Opacity: This controls the "Opacity" value for a "Color Correction" Filter [0 - 100] (Replaces the old SetOpacity)
  - Filter/Color Key - Similarity: This controls the "Similarity" value for a "Color Key" Filter [1 - 1000]
  - Filter/Color Key - Smoothness: This controls the "Smoothness" value for a "Color Key" Filter [1 - 1000]
  - Filter/Color Key - Brightness: This controls the "Brightness" value for a "Color Key" Filter [-1 - 1]
  - Filter/Color Key - Contrast: This controls the "Contrast" value for a "Color Key" Filter [-1 - 1]
  - Filter/Color Key - Gamma: This controls the "Gamma" value for a "Color Key" Filter [-1 - 1]
  - Filter/Sharpen - Sharpness: This controls the "Sharpness" value for a "Sharpen" Filter [0 - 1]
  - Filter/Scroll - Horizontal Speed: This controls the "Horizontal Speed" value for a "Scroll" Filter [-500 - 500]
  - Filter/Scroll - Vertical Speed: This controls the "Vertical Speed" value for a "Scroll" Filter [-500 - 500]
  - Filter/Video Delay (Async) - Delay: This controls the "Delay" value (in ms) for a "ideo Delay (Async)" Filter [-0 - 20000]
  - Filter/Render Delay - Delay:  This controls the "Delay" value (in ms) for a "Render Delay" Filter [0 - 500]
  - Filter/Generic Filter - Generic Setting: This can control every property of any filter, even filters added by plugins or on (global) audio sources. You have to specify what the setting property is called ,either by manually calling GetSourceFilterInfo via obs-websocket or by changing the default value via obs which then shows up in a list in the setup. You also have to specify if the data should be a Int (Whole Number) or Float (Floating Point Number)
- Now you can either setup another button/fader by repeating the steps above(except starting the script again) or just close the window to exit the configuration

Important note about all controls that involve a scene: In OBS scenes are also sources, so all the filter controls and TakeSourceScreenshot will also work on scenes. They will be part of the list that you are prompted with in the setup.
  
For a detailed description of most of the commands see the [obs-websocket protocol documentation](https://github.com/Palakis/obs-websocket/blob/master/docs/generated/protocol.md)

### Device Management

If you run the setup another time after the inital configuration you will get a dialog at startup where you can select if you want to go to the device management (1) or just continue adding new button/fader assignments with the already configured devices (2).

If you select 1 you have a few options:
- 1: Move the assignments from one device over to another. This can help when you plug the controller into another USB port and then shows up under a different name (e.g. "Devicename 1" instead of "Devicename")
- 2: Delete all devices from the database without removing their mapping. This does exactly that and be warned, will cause a device mixup when you add more devices later. You'll be better of using option 3
- 3: Remove a single device and their assignments.
- 4: Add a new device. This allows you do add more devices.
- 5: Skip device configuration. This exits the device management without changing anything and continues with the assignment dialog.
  
### Understanding input scaling

A midi value can be something between 0-127. That is a very limited number.

You will only be asked for Input Scale setup if it's required for the function(SetSourcePosition, SetSourceRotation, SetSourceScale, SetSyncOffset, SetTransitionDuration, SetGainFilter).

The first value you have to enter(lower output value) is the value that will be sent when the fader is sending a 0. The second value you have to enter(higher output value) is the value that will be sent when the fader is sending a 127. The range between the 2 numbers will be interpolated linearly.

Some limitations might apply to the range you can use (see the comments above in the action list above).

### "Bidirectional mode" !!ADVANCED/EXPERIMENTAL!!

THIS IS ONLY FOR ADVANCED USERS THAT ARE COMFORTABLE EDITING CONFIG FILES

If you enable the "bidirectional" mode while setting up SetCurrentScene or SetPreviewScene the script will try to open the input device as an output device and listen for Preview or Program scene change events. It will then send out a note_on or control_change event on midi channel 0 to the same note or control channel that is setup for the specific scene. 

The bidirectional mode for the ToggleMute function sends out a note_on with velocity 0 or 2 depending on the mute state and might only work on the AKAI APC mini.

This default approach might not work for some devices like the X-Touch Mini that have different notes/cc values for the same button depending if the data is coming in or going out. In this case you have to add a value named "out_msgNoC" to the config.json file for the button you want to light up with the right note/cc number.
To change the default channel you need to add a value named "out_channel" to config.json file.

If the midi out port for your device has a differnt name then the input port this will also not work without modifying the config.json file. For that first use the device configuration as mentioned above to add another device (could be one with a completly differnt name, this only saves you the work of manually adding the whole device which you could also do). Then add a value called "out_deviceID" to the button mapping entry with the value set to the id of the output device you just created. Also make sure that the output device name is the right one.

If you want to know more take a look at [the original pull request](https://github.com/lebaston100/MIDItoOBS/pull/19)

## Updating MIDItoOBS

As MIDItoOBS is just running from the folder you move/download it into, updating the programm itself is (most of the time) as easy as downloading it again like mentioned in Setup Part 3.

I highly recommend that you do not overwrite you existing files but rather backup the folder as is (including the config.json) and start with the freshly downloaded files in a new folder. Then just copy your config.json from the old backup folder into the new folder. Then try to run it.

It can and will happen from time-to-time that i introduce some changes that make the config now longer work with the new program version. As i don't have a changelog yet (which is definitely on the todo list) there is not really any way for you to know. Sometimes i announce such changes on the very top of this readme file. If it no longer works feel free to open an issue or contact me (See Troubleshooting).

## Running MIDItoOBS on another computer in the network:

- You can change the IP and Port of the device running obs and obs-websocket by modifying the main.py(line 5/6) and setup.py(line 6/7) with a text editor. You might have to create some firewall exceptions for the websocket port on the device running obs-websocket.

## Setting up "macros" (optional):

You can assign unlimited different actions to the same button. There is no guided GUI way to do this right now so this requires editing the config. (Sounds harder then it is)

 - Setup the functions as described above on different buttons
 - Now stop the setup.py and open the config(config.json) with a text editor.
 - Change the "msgNoC" value of the buttons you want to combine to the value of the button you want to use. Make sure you have the entry with the right device ID.
 - Here are some pictures for better understanding: [Step 1](https://cdn.lebaston100.de/git/midiobs/miditoobs_1.png) [Step 2](https://cdn.lebaston100.de/git/midiobs/miditoobs_2.png)
 - Now save and close the config file
 - Start main.py and verify that it works

## Using it (!Very important!)

- If you're a first time use make sure to follow setup steps 1-3
  - You can launch setup.py anytime(as long as main.py is not running) to change the configuration of a single button/fader without reconfiguring the whole controller.
- Always make sure that obs is running before launching any of the scripts
- Launch the main.py file (Try double click or the "Run Main.bat" if you are on Windows)
- The console gives you information when it successfully connects to OBS
- Also, if there is an error it will be printed out(If you ignore case sensitive fields or the scene doesn't exist)
- Third, it prints out a message every time you press a button that is setup
- Now just leave it running in the background
- To stop the program simply close the window (or CTRL + C)

## Command line options

You can call the main.py and the setup.py with the following command line options:
 - `--config <path/to/config/file.json>` (Default: "config.json")
 - `--port <obs-websocket port>`(Default: "4444")
 - `--host <obs-websocket hostname/ip>`(Default: "localhost")
 
## Troubleshooting/Support

A user has reported that under certain circumstances the script(setup and main) will crash after start on Windows with "ImportError: DLL load failed: The specified module could not be found".
If this happens to you, plase install the Visual C++ Redistributable from Microsoft. Make sure you get the x86 version if you are using python 32bit(Which is default) ([Download](https://aka.ms/vs/15/release/vc_redist.x86.exe))

If you have any other problem, just open a Github issue or join my [Discord Server](https://discord.gg/PCYQJwX)

## Contributors

I had never imagined that so many people would contribute something to the project. Thanks to everyone who submitted a bug report or pull request.
Special thanks to:

- [ptitodd](https://github.com/ptitodd) (Adding program_change message handling)
- [asquelt](https://github.com/asquelt) (making it work in python2)
- [Alex-Dash](https://github.com/Alex-Dash) (make the volume control linear)
- [imcrazytwkr](https://github.com/imcrazytwkr) (completly refactoring the main.py)
- [juliscrazy](https://github.com/juliscrazy) (fix typo in readme)
- [houz](https://github.com/houz) (midi feedback back to the controller)
- [cpyarger](https://github.com/cpyarger) (midi feedback for faders)
- [juandelacruz-calvo](https://github.com/juandelacruz-calvo) (Audio Monitoring command)
- [jberentsson](https://github.com/jberentsson) (command line options)
- [Sprinterfreak](https://github.com/Sprinterfreak) (bidi mode for ToggleMute)

### Tested on/with:

- Windows 10 20H2
- Ubuntu 18.04
- Python 3.8.3:6f8c832
- obs-studio 26.1 rc1
- obs-websocket 4.8.0 (Nightly build for t-bar support needed or 4.9 when it comes out)
- KORG nanoPAD
- KORG nanoKONTROL 2 (tested by [thatGuyStrike](https://twitter.com/thatGuyStrike) and [houz](https://github.com/houz))
- KORG padKONTROL (tested by [jberentsson](https://github.com/jberentsson))
- Behringer FCB-1010 + ESI MidiMate eX (tested by [thatGuyStrike](https://twitter.com/thatGuyStrike))
- Hercules DJ Control MP3
- Behringer X-Touch Mini (tested by [me-vlad](https://github.com/me-vlad))
- Behringer X-Touch Compact
- Arturia MiniLab MKII (tested by [moops44](https://github.com/moops44)). See [Issue #17](https://github.com/lebaston100/MIDItoOBS/issues/17) for notes!
- Native Instruments Maschine Mk3 (tested by [moops44](https://github.com/moops44)). See [Issue #18](https://github.com/lebaston100/MIDItoOBS/issues/18) for notes!
- Novation LaunchControl XL (tested by [lannonbr](https://github.com/lannonbr))
- Allen & Heath Xone K2
- AKAI APC mini
- loopMIDI

Let me know if you had success with your device.


**This project is not affiliated with the OBS Project or obs-websocket**
