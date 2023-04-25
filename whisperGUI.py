from gooey import Gooey, GooeyParser
import subprocess
import os
import re

@Gooey(program_name='whisper.cppGUI',
       menu=[{'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'Download GGML models',
                'name': 'Download the GGML models below',                                
                'website': 'https://huggingface.co/datasets/ggerganov/whisper.cpp/tree/main'                               
            },{
                'type': 'Link',
                'menuTitle': 'Visit Our Site',
                'url': 'https://github.com/Topping1/whispercppGUI'
            }]
        }]
        )
def main():
    parser = GooeyParser(description='GUI for whisper.cpp, a high-performance C++ port of OpenAI\'s Whisper')

    parser.add_argument(
        '--file',
        metavar='File to transcribe',
        help='supports all file types supported by FFMPEG',
        widget='FileChooser')

    parser.add_argument(
        '--model',
        metavar='GGML model (.bin)',
        help='select GGML model (tiny,base,small,medium,large)',
        widget='FileChooser')

    parser.add_argument(
        '--language',
        metavar='Language',
        help='select language for transcription',
        choices=['en','zh','de','es','ru','ko','fr','ja','pt','tr','pl','ca','nl','ar','sv','it','id','hi','fi','vi','iw','uk','el','ms','cs','ro','da','hu','ta','no','th','ur','hr','bg','lt','la','mi','ml','cy','sk','te','fa','lv','bn','sr','az','sl','kn','et','mk','br','eu','is','hy','ne','mn','bs','kk','sq','sw','gl','mr','pa','si','km','sn','yo','so','af','oc','ka','be','tg','sd','gu','am','yi','lo','uz','fo','ht','ps','tk','nn','mt','sa','lb','my','bo','tl','mg','as','tt','haw','ln','ha','ba','jw','su'],
        widget='FilterableDropdown')

    parser.add_argument(
        '--translate',
        action='store_true',
        help='check to translate transcription to english')

    parser.add_argument(
        '-otxt',
        '--output-txt',
        action='store_true',
        help='check to output result in a text file')

    parser.add_argument(
        '-osrt',
        '--output-srt',
        action='store_true',
        help='check to output result in a srt file')

    parser.add_argument(
        '-ovtt',
        '--output-vtt',
        action='store_true',
        help='check to output result in a vtt file')

    parser.add_argument(
        '-su',
        '--speed-up',
        action='store_true',
        help='check to speed up audio by factor of 2 (faster processing, reduced accuracy)')

    parser.add_argument(
        '--speed-up2',
        action='store',
        default=1,
        help='alternative speed up based on FFMPEG. Type here the speed up factor (e.g. 1.5). This enables automatically SRT output with corrected timestamps',
        widget='DecimalField')

    parser.add_argument(
        '--others',
        action='store',
        default="",
        help='This textbox lets the user add other command line parameters that are not included in this GUI')

    parser.add_argument(
        '--shell',
        action='store_true',
        help='check to show the shell window instead of using the Gooey window. This can fix some UTF-8 errors')

    
    args = parser.parse_args()
#enable for debugging
#    print(args) 
#pass args for later use in args=main()
    return args
    
    
    
if __name__ == '__main__':


# this section is inspired by
# https://stackoverflow.com/questions/48767005/using-python-gooey-how-to-open-another-gui-after-clicking-one-out-of-multiple-bu

#get arguments from main() for use here   
    args=main()

#workaround to process the arguments that evaluate to "True" or "False"
    
    if args.translate == True:
        arg_translate = "--translate"
    else:
        arg_translate = ""

    if args.output_txt == True:
        arg_out_txt = "--output-txt"
    else:
        arg_out_txt = ""

    if args.output_srt == True:
        arg_out_srt = "--output-srt"
    else:
        arg_out_srt = ""

    if args.output_vtt == True:
        arg_out_vtt = "--output-vtt"
    else:
        arg_out_vtt = ""

    if args.speed_up == True:
        arg_speed = "--speed-up"
    else:
        arg_speed = ""

#check if ffmpeg speedup was selected. If true, disable txt and vtt output
#and disable whispercpp internal speed up.
    if float(args.speed_up2) != 1.0:
        arg_out_txt = ""
        arg_out_vtt = ""
        arg_speed = ""
        arg_out_srt = "--output-srt"


#first we process the input file with ffmpeg
#here we construct the command line for ffmpeg and apply the FFMPEG speedup IF selected     
    if float(args.speed_up2) != 1.0:
        cmd = f"ffmpeg.exe -y -i \"{args.file}\" -ar 16000 -ac 1 -c:a pcm_s16le -af atempo={args.speed_up2} output.wav"
    else:
        cmd = f"ffmpeg.exe -y -i \"{args.file}\" -ar 16000 -ac 1 -c:a pcm_s16le output.wav"

    if args.shell == True:
        #here we call the program with extra parameters to capture ffmpeg output
        process=subprocess.Popen(cmd, text=True)
    else:
    #workaround required to show ffmpeg output in the Gooey window
    #reference https://github.com/chriskiehl/Gooey/issues/355
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    #here we call the program with extra parameters to capture ffmpeg output
        process=subprocess.Popen(cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    #here we print ffmpeg output to the Gooey window
        for line in process.stdout:
            line1=line.decode('utf-8')
            print(line1.rstrip())




#here we run whisperCPP
#here we construct the command line for whisperCPP    
    cmd = f"main.exe -f output.wav -m {args.model} -l {args.language} {arg_translate} {arg_out_txt} {arg_out_srt} {arg_out_vtt} {arg_speed} {args.others}"


    if args.shell == True:
        #here we call the program with extra parameters to capture ffmpeg output
        process=subprocess.Popen(cmd, text=True)
    else:    

    #workaround required to show whisperCPP output in the Gooey window
    #reference https://github.com/chriskiehl/Gooey/issues/355
            
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    #here we call the program with extra parameters to capture whisperCPP output
        process=subprocess.Popen(cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    #here we print whisperCPP output to the Gooey window
        for line in process.stdout:
            line1=line.decode('utf-8')
            print(line1.rstrip())

#this section fixes the timestamps of the SRT file if the FFMPEG speedup was selected
#

    if float(args.speed_up2) != 1.0:
        speedup_factor = float(args.speed_up2) # assign the speedup factor
        with open("output.wav.srt", "r") as file: # Open the input SRT file
            content = file.read()
        file.close()
        matches = re.findall(r"\d{2}:\d{2}:\d{2},\d{3}", content) # Use regular expressions to match timestamps in the SRT file
        for match in matches: # Multiply the timestamps by the speedup factor
            parts = match.split(":")
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2].split(",")[0])
            milliseconds = int(parts[2].split(",")[1])
            total_milliseconds = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
            total_milliseconds *= speedup_factor
            new_hours = f'{int(total_milliseconds // 3600000):02d}'
            new_minutes = f'{int((total_milliseconds % 3600000) // 60000):02d}'
            new_seconds = f'{int(((total_milliseconds % 3600000) % 60000) // 1000):02d}'
            new_milliseconds = f'{int(((total_milliseconds % 3600000) % 60000) % 1000):03d}'
            new_time = f"{new_hours}:{new_minutes}:{new_seconds},{new_milliseconds}"
            content = content.replace(match, new_time)
        with open("output-fix.wav.srt", "w") as file: # Write the adjusted SRT file to the output file
            file.write(content)
        file.close()
        os.remove("output.wav.srt")  #remove output.srt temporary file
#end of section that fixes the timestamps

#remove output.wav temporary file created by ffmpeg
os.remove("output.wav")
