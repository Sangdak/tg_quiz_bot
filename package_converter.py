import json
from pprint import pprint


def read_txt_file(filename: str, filepath: str, encode: str = 'KOI8-R') -> str:
    file = f'{filepath}/{filename}'
    with open(file, 'r', encoding=encode) as data:
        file_contents = data.read()
        return file_contents


def create_json_quiz_package(filename: str, filepath: str, data: dict, encode: str = 'utf-8') -> None:
    filename = filename.split('.')[0]
    file = f'{filepath}/{filename}.json'
    with open(file, 'w', encoding=encode) as output_file:
        json.dump(data, output_file)


def convert_txt_to_dict(data: str) -> dict:
    quiz_package = {
        'questions': {},
    }

    key_names = {
        'Комментарий:': 'comment',
        'Чемпионат:': 'championship',
        'Дата:': 'date',
        'Тур:': 'tour',
        'Вопрос': 'question',
        'Ответ:': 'answer',
        'Автор:': 'author',
        'Источник:': 'source',
        'extra_info_block': True,
    }

    question_number: int = 0

    for text_block in data.split('\n\n\n'):
        for section in text_block.split('\n\n'):
            if not section:
                continue
            title, text = section.split('\n', maxsplit=1)
            if title.startswith('Вопрос'):
                key_names['extra_info_block'] = False
                question_order = title.replace(':', '').split()[1]
                question_number = int(question_order)
                quiz_package['questions'].setdefault(question_number, {})
                quiz_package['questions'][question_number]['question'] = text.replace('\n', ' ')
            elif title == 'Ответ:':
                quiz_package['questions'][question_number][key_names[title]] = text.replace('\n', ' ')
            else:
                if key_names['extra_info_block']:
                    quiz_package[key_names[title]] = text
                else:
                    quiz_package['questions'][question_number][key_names[title]] = text

    return quiz_package


def main():
    filepath = './quiz-questions'
    filename = '1vs1200.txt'

    contents = read_txt_file(filename, filepath)
    package_data = convert_txt_to_dict(contents)
    create_json_quiz_package(filename, filepath, package_data)


if __name__ == '__main__':
    main()
