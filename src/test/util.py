import os

from src.parser import Parser


def list_test_files(directory):
    if not os.path.isabs(directory):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        directory = os.path.join(current_directory, directory)
    for file in os.listdir(directory):
        if file.endswith('.tig'):
            yield os.path.join(directory, file)


def get_file_name(path):
    return os.path.basename(path)


def read_file(path):
    with open(path, 'r') as file:
        return file.read()


def parse_file(path):
    contents = read_file(path)
    parser = Parser(contents, path)
    return parser.parse()
