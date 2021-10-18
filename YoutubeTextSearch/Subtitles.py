import re
from pathlib import Path
from typing import Iterable, TypeVar

from YoutubeTextSearch import helpers

T = TypeVar('T')


def dedupe(lines: Iterable[T]) -> Iterable[T]:
    return list(dict.fromkeys(lines))


def format_lines(lines: Iterable[str]) -> Iterable[str]:
    output = []
    to_exclude = re.compile(r'^\d\d:.+\.\d\d\d\s*$')
    for line in dedupe(lines):
        if line.startswith("0"):
            output.append(line)
        elif len(output) > 0:
            output[-1] += f" --- {line}"

    return filter(lambda l: not to_exclude.search(l), output)


def process(filename: str):
    try:
        output_lines = []
        if not Path(filename).exists():
            print(f"[{filename}] Not found")
            return

        print(f"accessing file [{filename}]")
        with open(filename, 'r', encoding="utf-8") as subtitle:
            replacer = re.compile(r'<\d\d:\d\d:\d\d\.\d\d\d><c>|</c>|(align:(\w+)\sposition:(\d+)%)')
            for line in subtitle:
                cleaned_line = replacer.sub("", line).strip()
                if len(cleaned_line) > 0:
                    output_lines.append(cleaned_line)

        outfile = f"{helpers.input_to_output_filepath(filename)}.subtitle.txt"
        helpers.make_dirs(Path(outfile).parent.absolute())
        with open(outfile, 'w', encoding="utf-8") as subtitle:
            subtitle.writelines(helpers.newline_generator(format_lines(output_lines)))

    except Exception as err:
        print(err)
