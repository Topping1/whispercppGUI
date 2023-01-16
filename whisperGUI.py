from gooey import Gooey, GooeyParser
import subprocess
import os

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
    args = parser.parse_args()
    
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

#first we process the input file with ffmpeg
#workaround required to show whisperCPP output in the Gooey window
#reference https://github.com/chriskiehl/Gooey/issues/355
        
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

#here we construct the command line for ffmpeg     
    cmd = f"ffmpeg.exe -i \"{args.file}\" -ar 16000 -ac 1 -c:a pcm_s16le output.wav"

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
#workaround required to show whisperCPP output in the Gooey window
#reference https://github.com/chriskiehl/Gooey/issues/355
        
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

#here we construct the command line for whisperCPP    
    cmd = f"main.exe -f output.wav -m {args.model} -l {args.language} {arg_translate} {arg_out_txt} {arg_out_srt} {arg_out_vtt} {arg_speed}"
    
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

#remove output.wav temporary file created by ffmpeg
os.remove("output.wav")
