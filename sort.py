import sys
import os
import glob
import shutil
from shutil import ReadError
from pathlib import Path
from datetime import datetime
import uuid

CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ ʼ'\"@"
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "je", "i", "ji", "g",
               "_", "_", "_", "_", "_")
TRANS = {}
NOW = datetime.now().strftime('_%d_%m_')
UUID = str(uuid.uuid1())[:8]
sorted_folders_path = f'{os.getcwd()}/sorted{NOW}{UUID}'
path_of_files = []
ext_list_known = []
ext_list_unknown = []
tip = """Run script with ONLY one argument --> full path to unsorted folder:
python3 sort.py <path to folder>
"""

extensions = {
    'archive': ['zip', 'gz', 'tar'],

    'video': ['mp4', 'mov', 'avi', 'mkv', 'wmv', '3gp', '3g2', 'mpg', 'mpeg', 'm4v',
              'h264', 'flv', 'rm', 'swf', 'vob'],

    'data': ['sql', 'sqlite', 'sqlite3', 'csv', 'dat', 'db', 'log', 'mdb', 'sav', 'xml'],

    'audio': ['mp3', 'wav', 'ogg', 'flac', 'aif', 'mid', 'midi', 'mpa', 'wma', 'wpl', 'cda'],

    'image': ['jpg', 'png', 'bmp', 'ai', 'psd', 'ico', 'jpeg', 'svg', 'tif', 'tiff', 'gif'],

    'text': ['pdf', 'txt', 'doc', 'docx', 'rtf', 'tex', 'wpd', 'odt', 'md'],

    'script': ['py', ],

    'other': []
}


def get_path_from_args(path):
    """Checking path to unsorted source-folder does exist"""
    if path.exists():
        make_sorted_folders(extensions)
        get_path_unsorted(path)
    else:
        print(f'Folder "{os.path.abspath(path)}" does not exist.')
        sys.exit(0)


def make_sorted_folders(ext):
    """Make empty folders for sorting files"""
    for name in ext:
        os.makedirs(f'{sorted_folders_path}/{name}')


def get_path_unsorted(path, depth=0, symbol='_', pipe='|', is_sort=False):
    """Getting list of full-paths for unsorted files"""
    margin = depth * symbol
    fold = depth * ' '
    if path.is_dir():
        if is_sort:
            print(f'{fold}{margin}/{path.name}/')
        for folder in path.iterdir():
            if is_sort:
                get_path_unsorted(folder, depth=depth+1, is_sort=True)
            else:
                get_path_unsorted(folder)
    else:
        ext = path.name[-3:].lstrip('.')
        file_name = path.name[:-3].rstrip('.')
        path_of_files.append([str(path), str(file_name), str(ext)])
        if is_sort:
            print(f'{pipe:>7}{margin}{path.name}')
    return path_of_files


def move_to_sorted(list_files, ext, count=0):
    """
        Moving files from source to sorted foldes.
        Renaming of duplicate if file or folder is already exist.
        Known archives will unpack to separate folders. Archives with unpacking errors
        and files with an unknown extensions will move to "/other/" folder
        (archives with an errors will be commented in the file-name).
    """
    not_empty_folders = True
    for k, v in ext.items():
        for item in list_files:
            if item[2] in v:
                ext_list_known.append(item[2])
                if item[2] in ext['archive']:
                    path_to_sorted = f'{sorted_folders_path}/{k}/{normalise(item[1])}/'
                    try:
                        if not os.path.exists(path_to_sorted):
                            shutil.unpack_archive(item[0], path_to_sorted)
                            os.remove(item[0])
                        else:
                            count += 1
                            shutil.unpack_archive(item[0], f'{path_to_sorted[:-1]}({count})/')
                            os.remove(item[0])
                    except ReadError as er:
                        print(f'*** Archive unpacking error: {er} ***')
                        shutil.move(item[0], f'{sorted_folders_path}/other/{item[1]}(ERROR).{item[2]}')
                        pass
                else:
                    path_to_sorted = f'{sorted_folders_path}/{k}/{normalise(item[1])}.{item[2]}'
                    if not os.path.exists(path_to_sorted):
                        shutil.move(item[0], path_to_sorted)
                    else:
                        count += 1
                        shutil.move(item[0], f'{sorted_folders_path}/{k}/{normalise(item[1])}({count}).{item[2]}')

    try:
        while not_empty_folders:
            path_of_files.clear()
            not_empty_folders = get_path_unsorted(path)
            for item in not_empty_folders:
                ext_list_unknown.append(item[2])
                path_to_unsorted = f'{sorted_folders_path}/other/{item[1]}.{item[2]}'
                if not os.path.exists(path_to_unsorted):
                    shutil.move(item[0], path_to_unsorted)
                else:
                    count += 1
                    shutil.move(item[0], f'{sorted_folders_path}/other/{item[1]}{count}.{item[2]}')
    except FileNotFoundError:
        pass


def normalise(name):
    """
    Translit cyrillic symbols, replacing spaces
    and some of non-letter symbols in a file-names
    """
    for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
        TRANS[ord(c)] = l
        TRANS[ord(c.upper())] = l.upper()
    return name.translate(TRANS)


def remove_empty_folders(path):
    """Removing empty target folder with empty subfolders"""
    for p in glob.glob(str(path)):
        shutil.rmtree(p)


def main():
    """Main func"""
    get_path_from_args(path)
    move_to_sorted(path_of_files, extensions)
    get_path_unsorted(Path(sorted_folders_path), is_sort=True)
    print(f'Known extensions: {sorted(list(set(ext_list_known)))}')
    print(f'Unknown extensions: {sorted(list(set(ext_list_unknown)))}')
    remove_empty_folders(path)


if __name__ == '__main__':
    try:
        path = Path(sys.argv[1])
        if len(sys.argv) > 2:
            raise IndexError
        # path = Path(f'{os.getcwd()}/unsort')  # for debugging
        main()
    except IndexError:
        print(tip)
