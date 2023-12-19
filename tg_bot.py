import os
import string

from dotenv import load_dotenv
import redis.asyncio as redis

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from get_question import get_random_question


ATTEMPTS = 2  # + 1 попытка


load_dotenv('.env')

redis_host = os.environ.get('REDIS_HOST')
redis_port = os.environ.get('REDIS_PORT')
redis_db = os.environ.get('REDIS_DATABASES')
tg_api_token = os.environ.get('TG_TOKEN')

bot = Bot(tg_api_token)
dp = Dispatcher()

button_1 = KeyboardButton(text='Новый вопрос')
button_2 = KeyboardButton(text='Сдаться')
button_3 = KeyboardButton(text='Мой счёт')
button_4 = KeyboardButton(text='Комментарий')
button_5 = KeyboardButton(text='Завершить игру')
button_6 = KeyboardButton(text='Начать игру')

keyboard_start = ReplyKeyboardMarkup(
    keyboard=[[button_6]],
    resize_keyboard=True,
    one_time_keyboard=True
)

keyboard_menu = ReplyKeyboardMarkup(
    keyboard=[[button_1],
              [button_3, button_5]],
    resize_keyboard=True,
    one_time_keyboard=True
)

keyboard_question = ReplyKeyboardMarkup(
    keyboard=[[button_2],
              [button_3, button_4]],
    resize_keyboard=True,
    one_time_keyboard=True
)

keyboard_answer = ReplyKeyboardMarkup(
    keyboard=[[button_1, button_4],
              [button_3, button_5]],
    resize_keyboard=True,
    one_time_keyboard=True
)


# Получение случайного вопроса из доступных пакетов
def get_random_question_set() -> dict:
    return get_random_question()


# Хендлер обработки команды "/start"
@dp.message(CommandStart())
async def process_start_command(message: Message):
    client = redis.Redis()
    user_exist = await client.get(f'{message.from_user.id}_in_game')

    if user_exist is None:
        await client.set(f'{message.from_user.id}_in_game', 0)
        await client.set(f'{message.from_user.id}_attempts', 0)
        await client.set(f'{message.from_user.id}_total_games', 0)
        await client.set(f'{message.from_user.id}_wins', 0)
        await client.set(f'{message.from_user.id}_current_question', '')
        await client.set(f'{message.from_user.id}_current_answer', '')
        await client.set(f'{message.from_user.id}_current_comment', '')
    await client.aclose()

    await message.answer(
        text='Привет!\nДавайте начнём нашу викторину.\n\n'
             'Чтобы получить правила игры и список доступных '
             'команд - отправьте команду /help',
        reply_markup=keyboard_start
    )


# Хендлер обработки команды "/help"
@dp.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(
        text=f'Правила игры:\n\nПри нажатии на кнопку "Новый вопрос", '
        f'Вы получаете случайный вопрос, вам нужно написать ответ.\n'
        f'У вас есть {ATTEMPTS} попыток\n\nДоступные команды:'
        f'\n/help - правила игры и список команд'
        f'\n/cancel - выйти из игры'
        f'\n/stat - посмотреть статистику\n\nГотовы сыграть?',
        reply_markup=keyboard_menu
    )


# Хендлер обработки команды "/cancel"
@dp.message(Command(commands='cancel'))
async def process_cancel_command(message: Message):
    client = redis.Redis()
    is_user_in_game = await client.get(f'{message.from_user.id}_in_game')
    if bool(is_user_in_game):
        await client.set(f'{message.from_user.id}_in_game', int(False))
        await message.answer(
            text='Вы вышли из игры. Если захотите '
                 'сыграть снова - нажмите кнопку.',
            reply_markup=keyboard_start,
        )

    else:
        await message.answer(
            text='А мы и так с вами не играем. '
            'Может, сыграем разок?',
            reply_markup=keyboard_start,
        )

    await client.aclose()


# Хендлер обработки команды "мой счёт"
@dp.message(F.text.lower().in_(['мой счёт', 'счёт']))
async def process_stat_command(message: Message):
    client = redis.Redis()
    is_user_in_game = await client.get(f'{message.from_user.id}_in_game')
    total_games_num = await client.get(f'{message.from_user.id}_total_games')
    wins_num = await client.get(f'{message.from_user.id}_wins')
    await client.aclose()

    if int(is_user_in_game):
        await message.answer(
            text=f'Всего игр сыграно: '
                 f'{int(total_games_num)}\n'
                 f'Игр выиграно: {int(wins_num)}',
            reply_markup=keyboard_question,
        )

    else:
        await message.answer(
            text=f'Всего игр сыграно: '
                 f'{int(total_games_num)}\n'
                 f'Игр выиграно: {int(wins_num)}',
            reply_markup=keyboard_menu,
        )




# Хендлер обработки выбора юзера сдаться
@dp.message(F.text.lower().in_(['сдаться', 'пропустить']))
async def process_user_give_up(message: Message):
    client = redis.Redis()
    is_user_in_game_cancel = await client.get(f'{message.from_user.id}_in_game')
    total_games = await client.get(f'{message.from_user.id}_total_games')
    answer = await client.get(f'{message.from_user.id}_current_answer')
    if bool(is_user_in_game_cancel):
        await client.set(f'{message.from_user.id}_in_game', int(False))
        await client.set(f'{message.from_user.id}_total_games', int(total_games) + 1)
        await message.answer(
            text=f"Ну, раз уж вы решили сдаться, "
            f"вот вам правильный ответ: "
            f"\n{str(answer.decode('utf-8'))}",
            reply_markup=keyboard_answer,
        )
    else:
        await message.answer(
            text='Вы не можете сдаться если не играете!',
            reply_markup=keyboard_start,
        )

    await client.aclose()


# Хендлер обработки команды согласия пользователя сыграть в игру
@dp.message(F.text.lower().in_(
    ['да', 'давай', 'игра', 'играть', 'начать игру', 'новый вопрос', 'сыграем', 'хочу играть']
))
async def process_positive_answer(message: Message):
    question_set = get_random_question_set()
    # print('QS', question_set)

    client = redis.Redis()
    is_user_in_game = await client.get(f'{message.from_user.id}_in_game')
    if not bool(is_user_in_game):
        question = await client.get(f'{message.from_user.id}_current_question')
        await message.answer(
            text=f"Вы уже получили вопрос:\n"
                 f"\n{question.decode('utf-8')}",
            reply_markup=keyboard_question,
        )

    else:
        await client.set(f'{message.from_user.id}_current_question', question_set['question'])
        await client.set(f'{message.from_user.id}_current_answer', question_set['answer'])
        await client.set(f'{message.from_user.id}_current_comment', question_set['comment'])
        await client.set(f'{message.from_user.id}_attempts', ATTEMPTS)
        await client.set(f'{message.from_user.id}_in_game', int(True))

        question = await client.get(f'{message.from_user.id}_current_question')
        await message.answer(
            text=f"Вопрос:\n"
                 f"\n{question.decode('utf-8')}",
            reply_markup=keyboard_question,
        )

    await client.aclose()


# Хендлер обработки запроса комментария
@dp.message(F.text.lower().in_(['комментарий', 'подробнее', 'подрбности']))
async def process_user_answer(message: Message):
    client = redis.Redis()
    is_user_in_game = await client.get(f'{message.from_user.id}_in_game')
    if int(is_user_in_game):
        await message.answer(
            text='Пока не определились с ответом,'
                 'комментарий недоступен!',
            reply_markup=keyboard_question,
        )

    else:
        comment = await client.get(f'{message.from_user.id}_current_comment')
        if not comment:
            await message.answer(
                text='К этому ответу нет комментариев!',
                reply_markup=keyboard_menu,
            )

        else:
            await message.answer(
                text=f"Комментарий к ответу: "
                     f"{comment.decode('utf-8')}",
                reply_markup=keyboard_menu,
            )

        await client.aclose()


# Хендлер обработки команды отказа пользователя сыграть в игру
@dp.message(F.text.lower().in_(['завершить игру', 'не', 'нет', 'не буду', 'не хочу']))
async def process_negative_answer(message: Message):
    client = redis.Redis()
    is_user_in_game = await client.get(f'{message.from_user.id}_in_game')
    await client.aclose()

    if int(is_user_in_game):
        await message.answer(
            text='Мы же сейчас с вами играем,'
                 'придётся сначала сдаться!',
            reply_markup=keyboard_question,
        )

    else:
        await message.answer(
            text='Вы вышли из игры. Если захотите '
                 'сыграть снова - нажмите кнопку.',
            reply_markup=keyboard_start,
        )


# Хендлер обработки отправки пользователем ответа
@dp.message()
async def process_user_answer(message: Message):
    client = redis.Redis()
    is_user_in_game = await client.get(f'{message.from_user.id}_in_game')
    total_games = await client.get(f'{message.from_user.id}_total_games')
    wins = await client.get(f'{message.from_user.id}_wins')
    attempts = await client.get(f'{message.from_user.id}_attempts')
    answer = await client.get(f'{message.from_user.id}_current_answer')

    answer_short, answer_addition = answer.decode('utf-8').split('.', maxsplit=1)
    table = str.maketrans("", "", string.punctuation)

    if bool(is_user_in_game):
        if message.text.lower() == answer_short.translate(table).lower():
            await client.set(f'{message.from_user.id}_in_game', int(False))
            await client.set(f'{message.from_user.id}_total_games', int(total_games) + 1)
            await client.set(f'{message.from_user.id}_wins', int(wins) + 1)

            await message.answer(
                text=f"Верно!\n"
                     f"{answer.decode('utf-8')}\n\n"
                     f"Может, сыграем еще?",
                reply_markup=keyboard_answer,
            )

        elif int(attempts) == 0:
            await client.set(f'{message.from_user.id}_in_game', int(False))
            await client.set(f'{message.from_user.id}_total_games', int(total_games) + 1)

            await message.answer(
                text=f"К сожалению, у вас больше не осталось "
                     f"попыток. Вы проиграли :(\n\nПравильный ответ: "
                     f"{answer.decode('utf-8')}"
                     f"\n\nДавайте сыграем еще?",
                reply_markup=keyboard_answer,
            )

        else:
            await client.set(f'{message.from_user.id}_attempts', int(attempts) - 1)
            await message.answer(
                text=f"Похоже, это неправильный ответ, "
                     f"количество оставшихся попыток: {int(attempts)}, "
                     f"попробуйте ещё раз!",
                reply_markup=keyboard_question,
            )

    else:
        await message.answer(
            text='Мы еще не играем. Хотите сыграть?',
            reply_markup=keyboard_start
        )

    await client.aclose()


if __name__ == '__main__':
    dp.run_polling(bot)
