from gooey import Gooey, GooeyParser
import subprocess

@Gooey(required_cols=1,
       target='main.exe',
       suppress_gooey_flag=True)
def main():
    parser = GooeyParser(description='GUI for whisper.cpp, a high-performance C++ port of OpenAI\'s Whisper')

    parser.add_argument(
        '-f',
        '--file',
        metavar='WAV file to transcribe',
        help='convert with: ffmpeg -i input.mp3 -ar 16000 -ac 1 -c:a pcm_s16le output.wav',
        widget='FileChooser')

    parser.add_argument(
        '-m',
        '--model',
        metavar='GGML model (.bin)',
        help='select GGML model (tiny,base,small,medium,large)',
        widget='FileChooser')

    parser.add_argument(
        '-l',
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

    parser.parse_args()
    
    
if __name__ == '__main__':
    main()
