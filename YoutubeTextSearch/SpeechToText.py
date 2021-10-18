import os
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from queue import Queue

import speech_recognition as sr
from pydub import AudioSegment, silence

from YoutubeTextSearch import helpers


def format_timedelta(value: timedelta) -> str:
    hours, rest = divmod(value.total_seconds(), 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}.{int(value.microseconds / 1000):03}"


def transcribe_speech(file: str) -> (float, str):
    with sr.AudioFile(file) as source:
        recognizer = sr.Recognizer()
        audio_data = recognizer.record(source)
        try:
            return source.DURATION, f"{recognizer.recognize_google(audio_data, language='fr-FR')}"
        except sr.RequestError:
            return source.DURATION, "Warning: Request failed"
        except sr.UnknownValueError:
            return source.DURATION, "Warning: No intelligible speech was recognized"


def process_chunks(chunks: list[AudioSegment], basename, thread_pool: ThreadPoolExecutor):
    output = Queue()

    for i, chunk in enumerate(chunks, start=1):
        chunk_name = os.path.join(basename, f'chunk-{i}.flac')
        print(f"[{chunk_name}] processing file...", end="\t", flush=True)
        start = time.perf_counter()
        chunk.export(chunk_name, format='flac')
        end = time.perf_counter()
        print(f" DONE ! ({end - start:0.2f}s)", flush=True)
        future = thread_pool.submit(transcribe_speech, chunk_name)
        future.add_done_callback(lambda _: output.task_done())
        output.put(future)

    output.join()
    delta = timedelta()
    output_lines = []
    while not output.empty():
        duration, result = output.get().result()
        start_time = delta
        delta = delta + timedelta(seconds=duration)
        if not result.startswith("Warning"):
            timestamp = f"{format_timedelta(start_time)} --> {format_timedelta(delta)} --- "
            txt = f"{textwrap.fill(result, width=175, initial_indent=timestamp, subsequent_indent=timestamp)}"
            output_lines.append(txt)

    outfile = f"{helpers.input_to_output_filepath(basename)}.audio.txt"
    helpers.make_dirs(Path(outfile).parent)
    with open(outfile, 'w', encoding="utf-8") as subtitle:
        subtitle.writelines(helpers.newline_generator(output_lines))


def split_on_silence(filename) -> [AudioSegment, str]:
    print("Loading file...", end="\t", flush=True)
    start = time.perf_counter()
    audio = AudioSegment.from_file(filename)
    end = time.perf_counter()
    print(f"DONE ! ({end - start:0.2f}s)", flush=True)
    print("Splitting file on silences...", end="\t", flush=True)
    start = time.perf_counter()
    chunks: list[AudioSegment] = silence.split_on_silence(audio, silence_thresh=audio.dBFS - 14,
                                                          keep_silence=True, seek_step=500)
    end = time.perf_counter()
    print(f"DONE ! ({end - start:0.2f}s)", flush=True)
    file_dir, _ = os.path.splitext(filename)
    if not os.path.isdir(file_dir):
        os.mkdir(file_dir)

    print(f"Storing in [{file_dir}]", flush=True)
    if not os.path.isdir(file_dir):
        os.mkdir(file_dir)

    return chunks, file_dir
