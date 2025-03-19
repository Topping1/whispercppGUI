# whispercppGUI
GUI for [whispercpp](https://github.com/ggerganov/whisper.cpp), a high performance C++ port of OpenAI's [whisper](https://github.com/openai/whisper).

![image](https://github.com/user-attachments/assets/fc869ba0-7847-44c5-8cd6-fba0f5925567)

Proper documentation is a work in progress

# Use in Windows 
- For this GUI to work properly, all of whispercpp files (from the official releases) should be copied to the same location of "whisperGUI.exe". Also, you need to copy a binary of ffmpeg to the same location of "whisperGUI.exe". In this way, you could update the program yourself manually in case the development on this repository stops.
- FFMPEG is also used to implement a variable-rate speedup option for the audio (whispercpp no longer has this option).
- All current options of whisper.cpp are implemented in the GUI but not all have been tested.
- "AllinOne" version in Releases include Ffmpeg, a compiled version of whisperGUI and the multilingual base model of OpenAI's Whisper. Two versions are available: CPU and GPU (Cuda version 12.8)

# Use in Linux
- Install ffmpeg
- Install PyQT5 library with `pip install pyqt5`
- run whisperGUI.py with `python whisperGUI.py`
- Choose whisper model (*.bin file) and audio file to process

# Requirements

To run the script from source, please install PyQT5 library `pip install pyqt5`

# Notes

The included executable for windows x64 was created using pyinstaller, using the command line `pyinstaller whisperGUI.py --onefile`. To install PyInstaller, use `pip install pyinstaller`. 
