# whispercppGUI
GUI for [whispercpp](https://github.com/ggerganov/whisper.cpp), a high performance C++ port of OpenAI's [whisper](https://github.com/openai/whisper).

For this GUI to work properly, all of whispercpp files (from the official releases) should be copied to the same location of "whisperGUI.exe". Also, you need to copy a binary of ffmpeg to the same location of "whisperGUI.exe". In this way, you could update the program yourself manually in case the development on this repository stops.

FFMPEG is also used to implement a variable-rate speedup option for the audio (whispercpp no longer has this option).

Not all options are implemented yet, only those that are of common use. For using options not present in this GUI, now you can use the textbox included in the bottom of the main window. For example you can type "-t 8" (without quotes) for using 8 threads when processing the audio.

## Requirements

If you want to run whispercppGUI from the python source code, the [Gooey](https://github.com/chriskiehl/Gooey) library is required. You can install Gooey with the command:

`pip install Gooey`

The included executable for windows x64 was created using pyinstaller, as described in the documentation of Gooey library. If you don't trust the executable on this repository, you can easily recreate your own executable file.  
