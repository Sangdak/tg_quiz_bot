import json
from os import path, scandir
from random import choice

from package_converter import convert_package


def get_random_question(filename: str = '', filepath: str = 'quiz_questions_packages') -> dict:
    filenames_in_dir = []
    if not filename:
        with scandir(f'./{filepath}') as listOfEntries:
            for entry in listOfEntries:
                if entry.is_file():
                    filenames_in_dir.append(entry.name)
        filename = choice(filenames_in_dir)

    file: str = f'{filepath}/json/{filename.split(".")[0]}.json'
    if not path.isfile(file):
        convert_package(filename, filepath)

    with open(file, 'r', encoding='utf-8') as json_file:
        quiz_package: dict = json.load(json_file)

    question_numbers = [key for key in quiz_package['questions'].keys()]

    random_question: dict = quiz_package['questions'][choice(question_numbers)]
    data = {
        'question': random_question['question'],
        'answer': random_question['answer'],
        'comment': random_question['comment'] if 'comment' in random_question else '',
    }

    print(data)

    return data


if __name__ == '__main__':
    get_random_question()
