#!/usr/bin/env python3
# coding: utf-8

import concurrent.futures
import os.path
import pprint
import shutil
import sys
import time
from pathlib import Path

import yt_dlp
from thefuzz import fuzz

from YoutubeTextSearch import Subtitles, SpeechToText, helpers

global_time: float = 0
processed_files = set()
file_count = 0
videos = []
opts: any


def print_timed(label: str, start: float):
    label = f"{label}: {time.perf_counter() - start:.2f}s"
    print_label(label)


def print_label(label):
    label = f' {label} '
    total_len = len(label) + 20
    filler = '#'
    box = ''.center(total_len, filler)
    print('', box, label.center(total_len, filler), box, '', sep='\n')


def add_match(matches, search_terms, ratio, matched, len_limit):
    if ratio >= 70 and len(search_terms) - len(matched.split("--- ")[1]) <= len_limit:
        matches.append((matched, ratio))


def search():
    search_terms: str = opts.query[0]
    search_len = len(search_terms)
    splitter = "--- "
    for filepath in Path("output").glob("*.txt"):
        print_label(helpers.get_filename_with_extensions(filepath))
        with open(filepath, 'r', encoding="utf-8") as file:
            matches: list[tuple[str, int]] = []
            prev_line = ""
            prev_line_txt = ""
            for i, line in enumerate(file):
                line = line.strip()
                line_txt = line.split(splitter)[1]
                ratio = fuzz.partial_token_sort_ratio(search_terms.lower(), line_txt, force_ascii=True, full_process=True)
                add_match(matches, search_terms, ratio, line, search_len / 1.25)
                if len(search_terms) > len(line) and i > 0:
                    ratio = fuzz.partial_token_sort_ratio(search_terms.lower(), prev_line_txt + ' ' + line_txt,
                                                          force_ascii=True, full_process=True)
                    add_match(matches, search_terms, ratio, prev_line + ' ' + line_txt, search_len / 1.25)

                prev_line = line
                prev_line_txt = line_txt

            for match, percent in sorted(matches, key=lambda x: (x[1], len(x[0]) - search_len)):
                print(f'{percent}% confidence => {match}')


def check_all_videos_processed():
    if len(processed_files) >= file_count:
        print_timed("total time", global_time)
        for file in list(dict.fromkeys(map(lambda x: helpers.get_filepath_without_extensions(x), processed_files))):
            path = Path(file)
            entries = path.parent.glob(path.name + "*")
            for entry in entries:
                try:
                    if entry.is_dir():
                        shutil.rmtree(entry)
                    else:
                        os.remove(entry)
                except Exception as err:
                    print(err)
        search()


def process_subs(d: dict[str, any]):
    if d['status'] == 'finished':
        filename = d['filename']
        print()
        print(f'Done downloading: {filename}', flush=True)
        if 'formats' not in d['info_dict']:
            print(f"Processing subtitles for: {filename}")
            if filename is not None:
                Subtitles.process(filename)
                os.remove(filename)

        if 'acodec' not in d['info_dict']:
            processed_files.add(helpers.get_filepath_with_extensions(filename).resolve())
        check_all_videos_processed()


def process_audio(filename: str):
    print(f"Processing audio for: {filename}")
    start = time.perf_counter()
    chunks, basename = SpeechToText.split_on_silence(filename)
    with concurrent.futures.ThreadPoolExecutor() as thread_pool:
        SpeechToText.process_chunks(chunks, basename, thread_pool)

    print_timed("Post-processing time", start)
    processed_files.add(helpers.get_filepath_with_extensions(filename).resolve())
    check_all_videos_processed()


options = {
    "extract-audio": True,
    'format': 'worstaudio/worst',
    'ffmpeg-location': 'ffmpeg/ffmpeg.exe',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio'
    }],
    'progress_hooks': [process_subs],
    'post_hooks': [process_audio],
    'outtmpl': 'input/%(extractor)s--%(id)s.%(ext)s',
    'subtitleslangs': ['fr'],
    'writesubtitles': True,
    'writeautomaticsub': True,
    'concurrent_fragment_downloads': os.cpu_count() / 2
}


def has_required_subtitles(info: dict[str, any]) -> int:
    counter = 0
    languages = options['subtitleslangs']
    subtitles: dict[str, any] = info.get('subtitles', {})
    auto_subs: dict[str, any] = info.get('automatic_captions', {})
    for lang in languages:
        counter += 1 if lang in subtitles or lang in auto_subs else 0
    return counter


def run(opt):
    global opts
    global global_time
    global file_count
    global videos
    opts = opt
    pprint.pp(opts)
    global_time = time.perf_counter()
    if opts.videos is not None:
        videos = opts.videos
    elif opts.file is not None:
        with open(opts.file[0], "r") as file:
            videos = file.read().splitlines(keepends=False)

    subs_and_audio = opts.subs == 0
    only_subs = opts.subs == 1
    only_audio = opts.subs == 2
    if only_subs:
        options['skip_download'] = True
    elif only_audio:
        options.pop('subtitleslangs')
        options.pop('writesubtitles')
        options.pop('writeautomaticsub')

    with yt_dlp.YoutubeDL(options) as ydl:
        for vid in videos:
            info = ydl.extract_info(vid, download=False)
            if only_subs or subs_and_audio:
                file_count += has_required_subtitles(info)
            if only_audio or subs_and_audio:
                file_count += 1

        ydl.download(list(dict.fromkeys(videos)))


def main(argv=None):
    try:
        opt = helpers.arg_parser().parse_args(argv)
        run(opt)
    except KeyboardInterrupt:
        sys.exit('\nERROR: Interrupted by user')
    except BrokenPipeError:
        # https://docs.python.org/3/library/signal.html#note-on-sigpipe
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(r'\nERROR: {err}')
    # except Exception as err:
    #     sys.exit(f"ERROR: An unexpected error occurred: {err}")


__license__ = 'Public Domain'

__all__ = ['main']
