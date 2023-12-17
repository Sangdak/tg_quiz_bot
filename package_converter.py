import json


def convert_package(filename: str, filepath: str = 'quiz_questions_packages') -> None:
    contents = read_txt_file(filename, filepath)
    package_data = convert_txt_to_dict(contents)
    create_json_quiz_package(filename, filepath, package_data)


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
        'Зачет:': 'setoff',
        'Редактор:': 'editor',
        'Инфо:': 'info',
        'URL:': 'url',
        'Вид:': 'type',
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


def create_json_quiz_package(filename: str, filepath: str, data: dict) -> None:
    filename = filename.split('.')[0]
    file = f'{filepath}/json/{filename}.json'
    with open(file, 'w') as output_file:
        json.dump(data, output_file)


def read_txt_file(filename: str, filepath: str, encode: str = 'koi8-r') -> str:
    file = f'{filepath}/{filename}'
    with open(file, 'r', encoding=encode) as data:
        file_contents = data.read()
        return file_contents


if __name__ == '__main__':
    convert_package()
