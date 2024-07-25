import os
import re
import os
import fnmatch
import concurrent.futures
from pathlib import Path
import platform

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.verbose = os.environ.get('VERBOSE', 'false').lower() == 'true'
        return cls._instance

    @classmethod
    def set_verbose(cls, verbose):
        cls().verbose = verbose

    @classmethod
    def is_verbose(cls):
        return cls().verbose

def verbose_print(*args, **kwargs):
    if Config.is_verbose():
        print(*args, **kwargs)


# @helper
def extract_numeric(value):
    if type(value) in [int, float]:
        return value
    # find all digits and decimal points in the value
    numeric_part = ''.join(re.findall(r'\d+\.?\d*', value))
    return float(numeric_part)

# @helper
def extract_string(value):
    str_part = ''.join(re.findall(r'[a-zA-Z]+', value))
    return str_part

# @helper
def extract_unit(value):
    unit_part = ''.join(re.findall(r'[^\d.]+', value)).strip()
    return unit_part


def get_common_directories():
    """
    Returns a list of common directories to prioritize in the search.
    """
    home = Path.home()
    common_dirs = [
        home / "Documents",
        home / "Downloads",
        home / "Desktop",
        home / "Pictures",
        home / "Videos",
        home / "Music",
    ]

    windows_specific_dirs = [
        home / "OneDrive",
        home / "Saved Games",
        home / "Favorites",
        home / "Links",
    ]

    mac_specific_dirs = [
        home / "Applications",
        home / "Library",
        home / "Movies",
        home / "Sites",
    ]

    linux_specific_dirs = [
        home / "bin",
        home / ".local" / "share",
        Path("/usr/local/bin"),
        Path("/etc"),
        home / "Templates",
    ]

    current_os = platform.system()
    if current_os == "Windows":
        common_dirs.extend(windows_specific_dirs) 
    elif current_os == "Darwin":
        common_dirs.extend(mac_specific_dirs)
    elif current_os == "Linux":
        common_dirs.extend(linux_specific_dirs)
    # Add more common directories as needed
    return [str(dir) for dir in common_dirs if dir.exists()]


def file_explorer(file_pattern, search_root='/', use_regex=False, case_sensitive=False, max_depth=None):
    """
    Searches for files matching a pattern, including partial paths, prioritizing common directories.
    """
    found_files = []
    search_root = os.path.expanduser(search_root)
    print(search_root)
    # Split the file_pattern into directory part and file part
    pattern_parts = file_pattern.split('/')
    dir_pattern = '/'.join(pattern_parts[:-1])
    file_pattern = pattern_parts[-1]

    if not case_sensitive and not use_regex:
        file_pattern = file_pattern.lower()
        dir_pattern = dir_pattern.lower()

    if use_regex:
        file_regex = re.compile(file_pattern, re.IGNORECASE if not case_sensitive else 0)
        dir_regex = re.compile(dir_pattern, re.IGNORECASE if not case_sensitive else 0) if dir_pattern else None
    else:
        if '.' not in file_pattern and '*' not in file_pattern:
            file_pattern = file_pattern + '.*'
        file_regex = re.compile(fnmatch.translate(file_pattern), re.IGNORECASE if not case_sensitive else 0)
        dir_regex = re.compile(fnmatch.translate(dir_pattern), re.IGNORECASE if not case_sensitive else 0) if dir_pattern else None

    def search_in_directory(root, current_depth=0):
        if max_depth is not None and current_depth > max_depth:
            return []

        local_found = []
        try:
            for entry in os.scandir(root):
                relative_path = os.path.relpath(entry.path, search_root)
                if not case_sensitive:
                    relative_path = relative_path.lower()

                if entry.is_file():
                    if (dir_regex is None or dir_regex.search(os.path.dirname(relative_path))) and \
                       file_regex.search(entry.name if case_sensitive else entry.name.lower()):
                        local_found.append(entry.path)
                elif entry.is_dir():
                    if dir_regex is None or dir_regex.search(relative_path):
                        local_found.extend(search_in_directory(entry.path, current_depth + 1))
        except PermissionError:
            print(f"Permission denied: {root}")
        except Exception as e:
            print(f"Error accessing {root}: {e}")

        return local_found

    # First, search in common directories
    common_dirs = get_common_directories()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        common_futures = [executor.submit(search_in_directory, dir) for dir in common_dirs]
        for future in concurrent.futures.as_completed(common_futures):
            found_files.extend(future.result())

    # If files are found in common directories, return them
    if found_files:
        return found_files

    # If no files found in common directories, search from the specified root
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(search_in_directory, os.path.join(search_root, dir))
                   for dir in os.listdir(search_root) if os.path.isdir(os.path.join(search_root, dir))]
        for future in concurrent.futures.as_completed(futures):
            found_files.extend(future.result())

    return found_files


def get_valid_path(path,search_root='/',**kwargs):
    """
    Returns the full path of the specified file or directory if it exists, otherwise tries to find it on device.

    Parameters:
    path (str): The path to the file or directory.

    Returns:
    str: The full path of the file or directory if it exists, otherwise None.

    """
    path = os.path.expanduser(path)
    if os.path.exists(path):
        return path
    else:
        found_paths = file_explorer(path,search_root,**kwargs)
        if found_paths:
            return found_paths[0]
        else:
            return None
