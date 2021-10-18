import os
import argparse
from os import PathLike
from pathlib import Path
from typing import Iterable, Union


def newline_generator(lines: Iterable[str]) -> str:
    for line in lines:
        yield line
        yield '\n'


def make_dirs(end_dir: PathLike):
    path = Path(end_dir)
    if path.exists():
        return

    if not path.parent.exists():
        make_dirs(path.parent)

    os.mkdir(path)


def get_filename_with_extensions(file: Union[str, PathLike]) -> str:
    return Path(file).name


def get_filename_without_extensions(file: Union[str, PathLike]) -> str:
    path = Path(file).stem
    return path.rsplit('.')[0]


def get_filepath_with_extensions(file: Union[str, PathLike]) -> Path:
    path = Path(file)
    return path.parent.joinpath(path.name)


def get_filepath_without_extensions(file: Union[str, PathLike]) -> Path:
    path = Path(file)
    name = get_filename_without_extensions(path)
    return path.parent.joinpath(name)


def get_relative_path(file: Union[str, PathLike]) -> Path:
    path = Path(file)
    return path.resolve().relative_to(path.cwd())


def merge_path_separators_with_name(file: Union[str, PathLike]) -> str:
    path = Path(file)
    return path.as_posix().replace('/', '-')


def input_to_output_filepath(file: Union[str, PathLike]) -> str:
    return merge_path_separators_with_name(
        get_relative_path(
            get_filepath_without_extensions(file)
        ).as_posix()
    ).replace("input-", "output/")


def arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recherche du texte dans les sous-titres ou l'audio de videos.",
                                     allow_abbrev=False, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("query", type=str, nargs=1, action='store', help="Le texte à rechercher.")
    conf = parser.add_argument_group("config")
    group = conf.add_mutually_exclusive_group(required=True)
    group.add_argument("-v", metavar=("url1", "url2"), type=str, nargs='+', required=False, action='store',
                       help="Les urls des videos cibles séparées par un espace.", dest="videos")
    group.add_argument("-f", metavar="path_to_file", type=str, nargs=1, required=False, action='store', dest="file",
                       help="Indique le chemin d'un fichier qui contient les urls des videos cibles (1 url par ligne)")

    conf.add_argument("-s", type=int, required=False, choices=(0, 1, 2), default=0, action='store', dest="subs",
                      help="""
0: (default) Cherche dans les sous-titres et l'audio.
1: Ne cherche que dans les sous-titres (plus rapide, ne télécharge pas l'audio)
2: Ne cherche que dans l'audio.""")
    return parser
