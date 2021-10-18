from cx_Freeze import setup, Executable

base = None

executables = [Executable("./main.py", base=base)]

packages = ["idna", "os", "pprint", "typing", "re", "datetime", "pathlib", "pydub", "speech_recognition", "yt_dlp"]
options = {
    'build_exe': {
        'optimize': 2,
        'packages': packages,
        'include_msvcr': True,
        'include_files': [('ffmpeg/ffmpeg.exe', 'ffmpeg/ffmpeg.exe')]
    },
}

setup(
    name='YoutubeTextSearch',
    version='1.0.0',
    url='',
    license='',
    author='Massil',
    author_email='',
    description='',
    options=options,
    executables=executables,
)
