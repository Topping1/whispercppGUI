# whispercppGUI
GUI for [whispercpp](https://github.com/ggerganov/whisper.cpp), a high performance C++ port of OpenAI's [whisper](https://github.com/openai/whisper)

for this GUI to work properly, the file "main.exe" and "whisper.dll" should be copied to the same location of "whisperGUI.exe". Please note that "whisper.dll" only applies to whispercpp compiled with MSVC. For whispercpp compiled with MinGW, only "main.exe" is required.

Not all options are implemented yet, only those that are of common use.

## Requirements

If you want to run whispercppGUI from the python source code, the Gooey library is required. You can install Gooey with the command:

`pip install Gooey`
