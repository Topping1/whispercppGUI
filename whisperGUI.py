#!/usr/bin/env python3
"""
whisperGUI.py – A PyQt5 GUI for whisper.cpp
This GUI replicates the original Gooey-based script functionality:
• Allows selecting an input audio file and a GGML model file.
• Lets the user choose language, translation, output file types, and a ffmpeg speed-up factor.
• Uses ffmpeg to convert input files to WAV format.
• Calls whisper.cpp (whisper-cli) with the chosen options.
• Provides an “Advanced” tab for many additional whisper.cpp options.
• Saves/loads options from a JSON config file (config.ini).
• Displays process output in a log window.
"""

import sys, os, subprocess, json, re, platform, shlex

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QPushButton, QCheckBox, QComboBox, QFileDialog,
    QTextEdit, QLabel, QDoubleSpinBox, QSpinBox, QAction, QScrollArea
)
from PyQt5.QtCore import QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices

CONFIG_FILE = "config.ini"

default_config = {
    "basic": {
        "file": "",
        "model": "",
        "language": "en",
        "translate": False,
        "output_txt": False,
        "output_srt": False,
        "output_vtt": False,
        "speed_up": 1.0,
        "others": "",
        "shell": False
    },
    "advanced": {
        "threads": 4,
        "processors": 1,
        "offset_t": 0,
        "offset_n": 0,
        "duration": 0,
        "max_context": -1,
        "max_len": 0,
        "split_on_word": False,
        "best_of": 5,
        "beam_size": 5,
        "audio_ctx": 0,
        "word_thold": 0.01,
        "entropy_thold": 2.40,
        "logprob_thold": -1.00,
        "temperature": 0.00,
        "temperature_inc": 0.20,
        "debug_mode": False,
        "diarize": False,
        "tinydiarize": False,
        "no_fallback": False,
        "output_lrc": False,
        "output_words": False,
        "font_path": "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
        "output_csv": False,
        "output_json": False,
        "output_json_full": False,
        "output_file": "",
        "no_prints": False,
        "print_special": False,
        "print_colors": False,
        "print_progress": False,
        "no_timestamps": False,
        "detect_language": False,
        "prompt": "",
        "ov_e_device": "CPU",
        "dtw": "",
        "log_score": False,
        "no_gpu": False,
        "flash_attn": False,
        "suppress_regex": "",
        "grammar": "",
        "grammar_rule": "",
        "grammar_penalty": 100.0
    }
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading config, using defaults:", e)
            return default_config.copy()
    else:
        return default_config.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Error saving config:", e)

class Worker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.is_running = True

    def run(self):
        try:
            basic = self.settings["basic"]
            adv = self.settings["advanced"]

            audio_file = basic["file"]
            model_file = basic["model"]
            language = basic["language"]
            translate = basic["translate"]
            output_txt = basic["output_txt"]
            output_srt = basic["output_srt"]
            output_vtt = basic["output_vtt"]
            speed_up = float(basic["speed_up"])
            others = basic["others"]
            shell = basic["shell"]

            # When a speed-up factor is applied, only SRT output is processed.
            if speed_up != 1.0:
                output_txt_flag = ""
                output_vtt_flag = ""
                output_srt_flag = "--output-srt"
            else:
                output_txt_flag = "--output-txt" if output_txt else ""
                output_srt_flag = "--output-srt" if output_srt else ""
                output_vtt_flag = "--output-vtt" if output_vtt else ""

            translate_flag = "--translate" if translate else ""

            # Detect operating system and choose executables accordingly.
            if platform.system() == "Windows":
                ffmpeg_exec = "ffmpeg.exe"
                whisper_exec = "whisper-cli.exe"
            else:
                ffmpeg_exec = "ffmpeg"
                whisper_exec = "./whisper-cli"

            # Create file names based on the input audio file.
            # The WAV file is created in the same folder as the input.
            wav_file = f"{os.path.splitext(audio_file)[0]}.wav"

            # --- Run ffmpeg conversion ---
            if speed_up != 1.0:
                ffmpeg_cmd = f'{ffmpeg_exec} -y -i "{audio_file}" -ar 16000 -ac 1 -c:a pcm_s16le -af atempo={speed_up} "{wav_file}"'
            else:
                ffmpeg_cmd = f'{ffmpeg_exec} -y -i "{audio_file}" -ar 16000 -ac 1 -c:a pcm_s16le "{wav_file}"'
            self.log_signal.emit("Running ffmpeg conversion...")
            self.log_signal.emit(ffmpeg_cmd)
            if shell:
                proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            else:
                proc = subprocess.Popen(shlex.split(ffmpeg_cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
            for line in iter(proc.stdout.readline, b""):
                if not self.is_running:
                    proc.terminate()
                    self.log_signal.emit("FFmpeg process cancelled.")
                    return
                self.log_signal.emit(line.decode("utf-8").rstrip())
            proc.wait()

            # Determine the directory of the input file so that output files are placed there.
            audio_dir = os.path.dirname(os.path.abspath(audio_file))
            # Derive the base name from the WAV file (e.g. for "test.wav" get "/path/to/test")
            base_name = os.path.splitext(wav_file)[0]

            # --- Build Advanced Options String ---
            advanced_args = ""
            for key, value in adv.items():
                flag = "--" + key.replace("_", "-")
                if isinstance(value, bool):
                    if value:
                        advanced_args += f" {flag}"
                else:
                    if value != "" and value is not None:
                        advanced_args += f" {flag} {value}"

            # --- Run whisper command ---
            whisper_cmd = f'{whisper_exec} -f "{wav_file}" -m "{model_file}" -l {language} {translate_flag} {output_txt_flag} {output_srt_flag} {output_vtt_flag} {others} {advanced_args}'
            self.log_signal.emit("Running whisper command...")
            self.log_signal.emit(whisper_cmd)
            # Set the working directory to the input file’s folder so that output files go there.
            if shell:
                proc2 = subprocess.Popen(whisper_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=audio_dir)
            else:
                proc2 = subprocess.Popen(shlex.split(whisper_cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False, cwd=audio_dir)
            for line in iter(proc2.stdout.readline, b""):
                if not self.is_running:
                    proc2.terminate()
                    self.log_signal.emit("Whisper process cancelled.")
                    return
                self.log_signal.emit(line.decode("utf-8").rstrip())
            proc2.wait()

            # --- Rename output files if necessary ---
            # whisper-cli typically names outputs using the WAV filename (e.g. "test.wav.txt").
            # We want to rename them so that the base name (e.g. "test") is used.
            wav_basename = os.path.basename(wav_file)  # e.g. "test.wav"
            # For TXT output:
            if output_txt:
                orig_txt = os.path.join(audio_dir, wav_basename + ".txt")
                desired_txt = base_name + ".txt"
                if os.path.exists(orig_txt):
                    os.rename(orig_txt, desired_txt)
                    self.log_signal.emit(f"Renamed TXT output from {orig_txt} to {desired_txt}")
                else:
                    self.log_signal.emit(f"TXT output file {orig_txt} not found.")
            # For SRT output (or when speed-up factor is applied, SRT is always produced):
            if output_srt or (speed_up != 1.0):
                orig_srt = os.path.join(audio_dir, wav_basename + ".srt")
                desired_srt = base_name + ".srt"
                if os.path.exists(orig_srt):
                    os.rename(orig_srt, desired_srt)
                    self.log_signal.emit(f"Renamed SRT output from {orig_srt} to {desired_srt}")
                else:
                    self.log_signal.emit(f"SRT output file {orig_srt} not found.")
            # For VTT output:
            if output_vtt:
                orig_vtt = os.path.join(audio_dir, wav_basename + ".vtt")
                desired_vtt = base_name + ".vtt"
                if os.path.exists(orig_vtt):
                    os.rename(orig_vtt, desired_vtt)
                    self.log_signal.emit(f"Renamed VTT output from {orig_vtt} to {desired_vtt}")
                else:
                    self.log_signal.emit(f"VTT output file {orig_vtt} not found.")

            # Define srt_file using the desired base name
            srt_file = f"{base_name}.srt"

            # --- Adjust SRT timestamps if using speed-up ---
            if speed_up != 1.0:
                self.log_signal.emit("Adjusting SRT timestamps due to speed-up factor...")
                if os.path.exists(srt_file):
                    with open(srt_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    matches = re.findall(r"\d{2}:\d{2}:\d{2},\d{3}", content)
                    for match in matches:
                        parts = match.split(":")
                        hours = int(parts[0])
                        minutes = int(parts[1])
                        seconds, milliseconds = parts[2].split(",")
                        seconds = int(seconds)
                        milliseconds = int(milliseconds)
                        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
                        new_total = int(total_ms * speed_up)
                        new_hours = f'{new_total // 3600000:02d}'
                        new_minutes = f'{(new_total % 3600000) // 60000:02d}'
                        new_seconds = f'{((new_total % 3600000) % 60000) // 1000:02d}'
                        new_ms = f'{((new_total % 3600000) % 60000) % 1000:03d}'
                        new_time = f"{new_hours}:{new_minutes}:{new_seconds},{new_ms}"
                        content = content.replace(match, new_time)
                    with open(srt_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    self.log_signal.emit(f"Adjusted SRT file saved as {srt_file}")
                else:
                    self.log_signal.emit("No SRT file found to adjust.")

            # --- Cleanup temporary WAV file ---
            if os.path.exists(wav_file):
                os.remove(wav_file)
                self.log_signal.emit("Temporary WAV file removed.")

        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")
        self.finished_signal.emit()

    def cancel(self):
        self.is_running = False

class BasicTab(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config.get("basic", {})
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # Input file
        self.file_line = QLineEdit(self.config.get("file", ""))
        file_browse = QPushButton("Browse...")
        file_browse.clicked.connect(self.browse_file)
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_line)
        file_layout.addWidget(file_browse)
        layout.addRow("Audio File:", file_layout)

        # Model file
        self.model_line = QLineEdit(self.config.get("model", ""))
        model_browse = QPushButton("Browse...")
        model_browse.clicked.connect(self.browse_model)
        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_line)
        model_layout.addWidget(model_browse)
        layout.addRow("GGML Model:", model_layout)

        # Language
        self.language_combo = QComboBox()
        languages = ['en','zh','de','es','ru','ko','fr','ja','pt','tr','pl','ca','nl','ar','sv','it','id','hi','fi','vi','iw','uk','el','ms','cs','ro','da','hu','ta','no','th','ur','hr','bg','lt','la','mi','ml','cy','sk','te','fa','lv','bn','sr','az','sl','kn','et','mk','br','eu','is','hy','ne','mn','bs','kk','sq','sw','gl','mr','pa','si','km','sn','yo','so','af','oc','ka','be','tg','sd','gu','am','yi','lo','uz','fo','ht','ps','tk','nn','mt','sa','lb','my','bo','tl','mg','as','tt','haw','ln','ha','ba','jw','su']
        self.language_combo.addItems(languages)
        current_lang = self.config.get("language", "en")
        index = self.language_combo.findText(current_lang)
        if index != -1:
            self.language_combo.setCurrentIndex(index)
        layout.addRow("Language:", self.language_combo)

        # Translate?
        self.translate_check = QCheckBox("Translate to English")
        self.translate_check.setChecked(self.config.get("translate", False))
        layout.addRow("", self.translate_check)

        # Output TXT
        self.out_txt_check = QCheckBox("Output TXT file")
        self.out_txt_check.setChecked(self.config.get("output_txt", False))
        layout.addRow("", self.out_txt_check)

        # Output SRT
        self.out_srt_check = QCheckBox("Output SRT file")
        self.out_srt_check.setChecked(self.config.get("output_srt", False))
        layout.addRow("", self.out_srt_check)

        # Output VTT
        self.out_vtt_check = QCheckBox("Output VTT file")
        self.out_vtt_check.setChecked(self.config.get("output_vtt", False))
        layout.addRow("", self.out_vtt_check)

        # Speed-up factor
        self.speed_up_spin = QDoubleSpinBox()
        self.speed_up_spin.setRange(0.1, 10.0)
        self.speed_up_spin.setSingleStep(0.1)
        self.speed_up_spin.setValue(float(self.config.get("speed_up", 1.0)))
        layout.addRow("FFMPEG Speed-up Factor:", self.speed_up_spin)

        # Other parameters
        self.others_line = QLineEdit(self.config.get("others", ""))
        layout.addRow("Other Params:", self.others_line)

        # Shell window checkbox
        self.shell_check = QCheckBox("Show shell window")
        self.shell_check.setChecked(self.config.get("shell", False))
        layout.addRow("", self.shell_check)

        self.setLayout(layout)

    def browse_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "All Files (*)")
        if fname:
            self.file_line.setText(fname)

    def browse_model(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select GGML Model", "", "Binary Files (*.bin);;All Files (*)")
        if fname:
            self.model_line.setText(fname)

    def get_values(self):
        return {
            "file": self.file_line.text(),
            "model": self.model_line.text(),
            "language": self.language_combo.currentText(),
            "translate": self.translate_check.isChecked(),
            "output_txt": self.out_txt_check.isChecked(),
            "output_srt": self.out_srt_check.isChecked(),
            "output_vtt": self.out_vtt_check.isChecked(),
            "speed_up": self.speed_up_spin.value(),
            "others": self.others_line.text(),
            "shell": self.shell_check.isChecked()
        }

class AdvancedTab(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config.get("advanced", {})
        self.widgets = {}
        self.optional_widgets = {}
        self.init_ui()

    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        form = QFormLayout(inner)

        self.widgets["threads"] = QSpinBox()
        self.widgets["threads"].setRange(1, 64)
        self.widgets["threads"].setValue(self.config.get("threads", 4))
        form.addRow("Threads:", self.widgets["threads"])

        self.widgets["processors"] = QSpinBox()
        self.widgets["processors"].setRange(1, 64)
        self.widgets["processors"].setValue(self.config.get("processors", 1))
        form.addRow("Processors:", self.widgets["processors"])

        self.widgets["split_on_word"] = QCheckBox()
        self.widgets["split_on_word"].setChecked(self.config.get("split_on_word", False))
        form.addRow("Split on word:", self.widgets["split_on_word"])

        self.widgets["debug_mode"] = QCheckBox()
        self.widgets["debug_mode"].setChecked(self.config.get("debug_mode", False))
        form.addRow("Debug Mode:", self.widgets["debug_mode"])

        self.widgets["diarize"] = QCheckBox()
        self.widgets["diarize"].setChecked(self.config.get("diarize", False))
        form.addRow("Diarize:", self.widgets["diarize"])

        self.widgets["tinydiarize"] = QCheckBox()
        self.widgets["tinydiarize"].setChecked(self.config.get("tinydiarize", False))
        form.addRow("TinyDiarize:", self.widgets["tinydiarize"])

        self.widgets["no_fallback"] = QCheckBox()
        self.widgets["no_fallback"].setChecked(self.config.get("no_fallback", False))
        form.addRow("No Fallback:", self.widgets["no_fallback"])

        self.widgets["output_csv"] = QCheckBox()
        self.widgets["output_csv"].setChecked(self.config.get("output_csv", False))
        form.addRow("Output CSV:", self.widgets["output_csv"])

        self.widgets["output_json"] = QCheckBox()
        self.widgets["output_json"].setChecked(self.config.get("output_json", False))
        form.addRow("Output JSON:", self.widgets["output_json"])

        self.widgets["output_json_full"] = QCheckBox()
        self.widgets["output_json_full"].setChecked(self.config.get("output_json_full", False))
        form.addRow("Output JSON Full:", self.widgets["output_json_full"])

        self.widgets["no_prints"] = QCheckBox()
        self.widgets["no_prints"].setChecked(self.config.get("no_prints", False))
        form.addRow("No Prints:", self.widgets["no_prints"])

        self.widgets["print_special"] = QCheckBox()
        self.widgets["print_special"].setChecked(self.config.get("print_special", False))
        form.addRow("Print Special:", self.widgets["print_special"])

        self.widgets["print_colors"] = QCheckBox()
        self.widgets["print_colors"].setChecked(self.config.get("print_colors", False))
        form.addRow("Print Colors:", self.widgets["print_colors"])

        self.widgets["print_progress"] = QCheckBox()
        self.widgets["print_progress"].setChecked(self.config.get("print_progress", False))
        form.addRow("Print Progress:", self.widgets["print_progress"])

        self.widgets["no_timestamps"] = QCheckBox()
        self.widgets["no_timestamps"].setChecked(self.config.get("no_timestamps", False))
        form.addRow("No Timestamps:", self.widgets["no_timestamps"])

        self.widgets["detect_language"] = QCheckBox()
        self.widgets["detect_language"].setChecked(self.config.get("detect_language", False))
        form.addRow("Detect Language:", self.widgets["detect_language"])

        self.widgets["log_score"] = QCheckBox()
        self.widgets["log_score"].setChecked(self.config.get("log_score", False))
        form.addRow("Log Score:", self.widgets["log_score"])

        self.widgets["no_gpu"] = QCheckBox()
        self.widgets["no_gpu"].setChecked(self.config.get("no_gpu", False))
        form.addRow("No GPU:", self.widgets["no_gpu"])

        self.widgets["flash_attn"] = QCheckBox()
        self.widgets["flash_attn"].setChecked(self.config.get("flash_attn", False))
        form.addRow("Flash Attn:", self.widgets["flash_attn"])

        def add_optional_param(key, label_text, widget):
            hbox = QHBoxLayout()
            checkbox = QCheckBox("Enable")
            checkbox.setChecked(False)
            hbox.addWidget(checkbox)
            hbox.addWidget(widget)
            form.addRow(label_text, hbox)
            self.optional_widgets[key] = (checkbox, widget)

        offset_t = QSpinBox()
        offset_t.setRange(0, 100000)
        offset_t.setValue(self.config.get("offset_t", 0))
        add_optional_param("offset_t", "Offset (ms):", offset_t)

        offset_n = QSpinBox()
        offset_n.setRange(0, 100000)
        offset_n.setValue(self.config.get("offset_n", 0))
        add_optional_param("offset_n", "Segment Offset:", offset_n)

        duration = QSpinBox()
        duration.setRange(0, 1000000)
        duration.setValue(self.config.get("duration", 0))
        add_optional_param("duration", "Duration (ms):", duration)

        max_context = QSpinBox()
        max_context.setRange(-1, 1000)
        max_context.setValue(self.config.get("max_context", -1))
        add_optional_param("max_context", "Max Context:", max_context)

        max_len = QSpinBox()
        max_len.setRange(0, 1000)
        max_len.setValue(self.config.get("max_len", 0))
        add_optional_param("max_len", "Max Segment Length:", max_len)

        best_of = QSpinBox()
        best_of.setRange(1, 10)
        best_of.setValue(self.config.get("best_of", 5))
        add_optional_param("best_of", "Best-of:", best_of)

        beam_size = QSpinBox()
        beam_size.setRange(1, 10)
        beam_size.setValue(self.config.get("beam_size", 5))
        add_optional_param("beam_size", "Beam Size:", beam_size)

        audio_ctx = QSpinBox()
        audio_ctx.setRange(0, 10000)
        audio_ctx.setValue(self.config.get("audio_ctx", 0))
        add_optional_param("audio_ctx", "Audio Context Size:", audio_ctx)

        word_thold = QDoubleSpinBox()
        word_thold.setRange(0.0, 1.0)
        word_thold.setSingleStep(0.01)
        word_thold.setValue(self.config.get("word_thold", 0.01))
        add_optional_param("word_thold", "Word Threshold:", word_thold)

        entropy_thold = QDoubleSpinBox()
        entropy_thold.setRange(0.0, 10.0)
        entropy_thold.setSingleStep(0.1)
        entropy_thold.setValue(self.config.get("entropy_thold", 2.40))
        add_optional_param("entropy_thold", "Entropy Threshold:", entropy_thold)

        logprob_thold = QDoubleSpinBox()
        logprob_thold.setRange(-10.0, 10.0)
        logprob_thold.setSingleStep(0.1)
        logprob_thold.setValue(self.config.get("logprob_thold", -1.00))
        add_optional_param("logprob_thold", "Logprob Threshold:", logprob_thold)

        temperature = QDoubleSpinBox()
        temperature.setRange(0.0, 1.0)
        temperature.setSingleStep(0.01)
        temperature.setValue(self.config.get("temperature", 0.00))
        add_optional_param("temperature", "Temperature:", temperature)

        temperature_inc = QDoubleSpinBox()
        temperature_inc.setRange(0.0, 1.0)
        temperature_inc.setSingleStep(0.01)
        temperature_inc.setValue(self.config.get("temperature_inc", 0.20))
        add_optional_param("temperature_inc", "Temperature Increment:", temperature_inc)

        font_path = QLineEdit(self.config.get("font_path", "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"))
        def browse_font():
            fname, _ = QFileDialog.getOpenFileName(self, "Select Font File", "", "Font Files (*.ttf *.otf);;All Files (*)")
            if fname:
                font_path.setText(fname)
        font_browse = QPushButton("Browse...")
        font_browse.clicked.connect(browse_font)
        font_hbox = QHBoxLayout()
        font_hbox.addWidget(font_path)
        font_hbox.addWidget(font_browse)
        hbox = QHBoxLayout()
        checkbox = QCheckBox("Enable")
        checkbox.setChecked(False)
        hbox.addWidget(checkbox)
        hbox.addLayout(font_hbox)
        form.addRow("Font Path:", hbox)
        self.optional_widgets["font_path"] = (checkbox, font_path)

        output_file = QLineEdit(self.config.get("output_file", ""))
        add_optional_param("output_file", "Output File:", output_file)

        prompt = QLineEdit(self.config.get("prompt", ""))
        add_optional_param("prompt", "Prompt:", prompt)

        ov_e_device = QLineEdit(self.config.get("ov_e_device", "CPU"))
        add_optional_param("ov_e_device", "OV-E Device:", ov_e_device)

        dtw = QLineEdit(self.config.get("dtw", ""))
        add_optional_param("dtw", "DTW Model:", dtw)

        suppress_regex = QLineEdit(self.config.get("suppress_regex", ""))
        add_optional_param("suppress_regex", "Suppress Regex:", suppress_regex)

        grammar = QLineEdit(self.config.get("grammar", ""))
        add_optional_param("grammar", "Grammar:", grammar)

        grammar_rule = QLineEdit(self.config.get("grammar_rule", ""))
        add_optional_param("grammar_rule", "Grammar Rule:", grammar_rule)

        grammar_penalty = QDoubleSpinBox()
        grammar_penalty.setRange(0.0, 1000.0)
        grammar_penalty.setSingleStep(1.0)
        grammar_penalty.setValue(self.config.get("grammar_penalty", 100.0))
        add_optional_param("grammar_penalty", "Grammar Penalty:", grammar_penalty)

        inner.setLayout(form)
        scroll.setWidget(inner)
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)

    def get_values(self):
        values = {}
        for key, widget in self.widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                values[key] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                values[key] = widget.text()
        for key, (checkbox, widget) in self.optional_widgets.items():
            if checkbox.isChecked():
                if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    values[key] = widget.value()
                elif isinstance(widget, QLineEdit):
                    values[key] = widget.text()
        return values

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("whisper.cpp GUI")
        self.resize(800, 600)
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        about_action = QAction("Download GGML Models", self)
        about_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://huggingface.co/ggerganov/whisper.cpp")))
        file_menu.addAction(about_action)

        site_action = QAction("Visit Our Site", self)
        site_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/Topping1/whispercppGUI")))
        file_menu.addAction(site_action)

        self.tabs = QTabWidget()
        self.basic_tab = BasicTab(self.config)
        self.advanced_tab = AdvancedTab(self.config)
        self.tabs.addTab(self.basic_tab, "Basic Options")
        self.tabs.addTab(self.advanced_tab, "Advanced Options")

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(200)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_process)

        central_layout = QVBoxLayout()
        central_layout.addWidget(self.tabs)
        central_layout.addWidget(QLabel("Log Output:"))
        central_layout.addWidget(self.log_output)
        central_layout.addWidget(self.run_button)

        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

    def run_process(self):
        self.run_button.setText("Cancel")
        self.run_button.clicked.disconnect()
        self.run_button.clicked.connect(self.cancel_process)
        basic_settings = self.basic_tab.get_values()
        advanced_settings = self.advanced_tab.get_values()
        settings = {"basic": basic_settings, "advanced": advanced_settings}
        self.config = settings
        save_config(self.config)
        self.log_output.clear()
        self.worker = Worker(settings)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.process_finished)
        self.worker.start()

    def cancel_process(self):
        self.worker.cancel()

    def append_log(self, text):
        self.log_output.append(text)

    def process_finished(self):
        self.append_log("Process finished.")
        self.run_button.setText("Run")
        self.run_button.clicked.disconnect()
        self.run_button.clicked.connect(self.run_process)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
