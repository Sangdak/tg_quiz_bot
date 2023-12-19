import logging
from logging.handlers import RotatingFileHandler
import os
import pathlib
import random
import string

import redis
import vk_api as vk
from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

from get_question import get_random_question


logger = logging.getLogger(__name__)


def start_keyboard():
    keyboard_start = VkKeyboard(one_time=True)
    keyboard_start.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard_start.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)
    return keyboard_start.get_keyboard()


def continue_keyboard():
    keyboard_continue = VkKeyboard(one_time=True)
    keyboard_continue.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard_continue.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)
    return keyboard_continue.get_keyboard()


def right_answer_keyboard():
    keyboard_right = VkKeyboard(one_time=True)
    keyboard_right.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard_right.add_button('Комментарий', color=VkKeyboardColor.SECONDARY)
    keyboard_right.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)
    return keyboard_right.get_keyboard()


def start(vk_api, event):
    vk_api.messages.send(
        user_id=event.user_id,
        message='Начнём нашу викторину!',
        random_id=random.randint(1, 1000),
        keyboard=start_keyboard(),
    )


def new_question(vk_api, event, redis_connection):
    question_set = get_random_question()

    question = question_set['question']
    answer = question_set['answer']
    comment = question_set['comment']

    redis_connection.set('question', question)
    redis_connection.set('answer', answer)
    redis_connection.set('comment', comment)

    vk_api.messages.send(
        user_id=event.user_id,
        message=redis_connection.get('question'),
        random_id=random.randint(1, 1000),
        keyboard=continue_keyboard(),
    )


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler(pathlib.PurePath.joinpath(pathlib.Path.cwd(), 'tg_bot.log'),
                                       maxBytes=100000,
                                       backupCount=3)
    file_handler.setFormatter(logging.Formatter('level=%(levelname)s time="%(asctime)s" message="%(message)s"'))
    logger.addHandler(file_handler)

    load_dotenv()

    vk_group_token = os.environ.get('VK_TOKEN')
    redis_host = os.environ.get('REDIS_HOST')
    redis_port = os.environ.get('REDIS_PORT')
    redis_db = os.environ.get('REDIS_DATABASES')

    redis_connection = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

    while True:
        try:
            vk_session = vk.VkApi(token=vk_group_token)
            vk_api = vk_session.get_api()
            longpoll = VkLongPoll(vk_session)
            logger.info('Bot starting...')
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if event.text == "start":
                        start(vk_api, event)

                    elif event.text == "Сдаться":
                        vk_api.messages.send(
                            user_id=event.user_id,
                            message=f'Правильный ответ: {redis_connection.get("answer").decode("utf-8")}',
                            random_id=random.randint(1, 1000),
                            keyboard=right_answer_keyboard(),
                        )

                    elif event.text == 'Новый вопрос':
                        new_question(vk_api, event, redis_connection)

                    elif event.text == 'Комментарий':
                        if redis_connection.get('comment') != '':
                            vk_api.messages.send(
                                user_id=event.user_id,
                                message=redis_connection.get('comment').decode("utf-8"),
                                random_id=random.randint(1, 1000),
                                keyboard=start_keyboard(),
                            )

                        else:
                            vk_api.messages.send(
                                user_id=event.user_id,
                                message='Комментарии для этого вопроса отсутствуют!',
                                random_id=random.randint(1, 1000),
                                keyboard=start_keyboard(),
                            )

                    else:
                        answer = redis_connection.get('answer').decode("utf-8")
                        answer_short, answer_continue = answer.split('.', maxsplit=1)
                        table = str.maketrans("", "", string.punctuation)

                        if event.text.translate(table).lower() in answer_short.translate(table).lower():
                            vk_api.messages.send(
                                user_id=event.user_id,
                                message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
                                random_id=random.randint(1, 1000),
                                keyboard=right_answer_keyboard()
                            )
                        else:
                            vk_api.messages.send(
                                user_id=event.user_id,
                                message='Неправильно… Попробуешь ещё раз?',
                                random_id=random.randint(1, 1000),
                                keyboard=continue_keyboard(),
                            )

        except Exception as error:
            logger.exception(f'Бот упал с ошибкой: {error}')
            continue


if __name__ == '__main__':
    main()
