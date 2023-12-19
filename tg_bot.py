import os
import string

from dotenv import load_dotenv
import redis.asyncio as redis

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from get_question import get_random_question


ATTEMPTS = 2  # + 1 попытка

# Словарь, в котором будут храниться данные пользователя
users = {
    173901673: {
        'in_game': True,
        'current_question': {},
        'attempts': 0,
        'total_games': 0,
        'wins': 0,
    },
}

print(users)

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
    await message.answer(
        text='Привет!\nДавайте начнём нашу викторину.\n\n'
        'Чтобы получить правила игры и список доступных '
        'команд - отправьте команду /help',
        reply_markup=keyboard_start
    )
    # Добавление нового пользователя в словарь users
    if message.from_user.id not in users:
        users[message.from_user.id] = {
            'in_game': False,
            'current_question': {},
            'attempts': None,
            'total_games': 0,
            'wins': 0
        }

    client = redis.Redis()
    user_exist = await client.get(f'{message.from_user.id}_in_game')
    print(user_exist)
    if user_exist is None:
        await client.set(f'{message.from_user.id}_in_game', 0)
        await client.set(f'{message.from_user.id}_attempts', 0)
        await client.set(f'{message.from_user.id}_total_games', 0)
        await client.set(f'{message.from_user.id}_wins', 0)
        await client.set(f'{message.from_user.id}_current_question', '')
        await client.set(f'{message.from_user.id}_current_answer', '')
        await client.set(f'{message.from_user.id}_current_comment', '')
    await client.aclose()


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
    if users[message.from_user.id]['in_game']:
        users[message.from_user.id]['in_game'] = False
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


# Хендлер обработки команды "мой счёт"
@dp.message(F.text.lower().in_(['мой счёт', 'счёт']))
async def process_stat_command(message: Message):
    if not users[message.from_user.id]['in_game']:
        await message.answer(
            text=f'Всего игр сыграно: '
                 f'{users[message.from_user.id]["total_games"]}\n'
                 f'Игр выиграно: {users[message.from_user.id]["wins"]}',
            reply_markup=keyboard_menu,
        )

    else:
        await message.answer(
            text=f'Всего игр сыграно: '
                 f'{users[message.from_user.id]["total_games"]}\n'
                 f'Игр выиграно: {users[message.from_user.id]["wins"]}',
            reply_markup=keyboard_question,
        )


# Хендлер обработки выбора юзера сдаться
@dp.message(F.text.lower().in_(['сдаться', 'пропустить']))
async def process_user_give_up(message: Message):
    if users[message.from_user.id]['in_game']:
        users[message.from_user.id]['in_game'] = False
        await message.answer(
            text=f"Ну, раз уж вы решили сдаться, "
            f"вот вам правильный ответ: "
            f"\n{users[message.from_user.id]['current_question']['answer']}",
            reply_markup=keyboard_answer,
        )
    else:
        await message.answer(
            text='Вы не можете сдаться если не играете!',
            reply_markup=keyboard_start,
        )


# Хендлер обработки команды согласия пользователя сыграть в игру
@dp.message(F.text.lower().in_(
    ['да', 'давай', 'игра', 'играть', 'начать игру', 'новый вопрос', 'сыграем', 'хочу играть']
))
async def process_positive_answer(message: Message):
    if not users[message.from_user.id]['in_game']:
        users[message.from_user.id]['in_game'] = True
        users[message.from_user.id]['current_question'] = get_random_question_set()
        users[message.from_user.id]['attempts'] = ATTEMPTS
        await message.answer(
            text=f"Новый вопрос!\n"
                 f"\n{users[message.from_user.id]['current_question']['question']}",
            reply_markup=keyboard_question,
        )


# Хендлер обработки запроса комментария
@dp.message(F.text.lower().in_(['комментарий', 'подробнее', 'подрбности']))
async def process_user_answer(message: Message):

    if not users[message.from_user.id]['in_game']:
        if users[message.from_user.id]['current_question']['comment'] != '':
            await message.answer(
                text=f"Комментарий к ответу: "
                     f"{users[message.from_user.id]['current_question']['comment']}",
                reply_markup=keyboard_menu,
            )
        else:
            await message.answer(
                text='К этому ответу нет комментариев!',
                reply_markup=keyboard_menu,
            )

    else:
        await message.answer(
            text='Пока не определились с ответом,'
                 'комментарий недоступен!',
            reply_markup=keyboard_question,
        )


# Хендлер обработки команды отказа пользователя сыграть в игру
@dp.message(F.text.lower().in_(['завершить игру', 'не', 'нет', 'не буду', 'не хочу']))
async def process_negative_answer(message: Message):
    if not users[message.from_user.id]['in_game']:
        await message.answer(
            text='Жаль :(\n\nЕсли захотите поиграть - '
                 'просто напишите об этом',
            reply_markup=keyboard_start,
        )
    else:
        await message.answer(
            text='Мы же сейчас с вами играем,'
                 'придётся сначала сдаться!',
            reply_markup=keyboard_question,
        )


# Хендлер обработки отправки пользователем ответа
@dp.message()
# async def process_numbers_answer(message: Message):
async def process_user_answer(message: Message):
    answer_short, answer_addition = users[message.from_user.id]['current_question']['answer'].split('.', maxsplit=1)
    table = str.maketrans("", "", string.punctuation)

    users[message.from_user.id]['current_question']['answer_short'] = answer_short
    if answer_addition:
        users[message.from_user.id]['current_question']['answer_addition'] = answer_addition

    if users[message.from_user.id]['in_game']:
        if message.text.lower() == answer_short.translate(table).lower():
            users[message.from_user.id]['in_game'] = False
            users[message.from_user.id]['total_games'] += 1
            users[message.from_user.id]['wins'] += 1
            await message.answer(
                text=f"Верно!\n"
                     f"{users[message.from_user.id]['current_question']['answer_addition'] if 'answer_addition' in users[message.from_user.id]['current_question'] else ''}\n\n"
                     f"Может, сыграем еще?",
                reply_markup=keyboard_answer,
            )

        elif users[message.from_user.id]['attempts'] == 0:
            users[message.from_user.id]['in_game'] = False
            users[message.from_user.id]['total_games'] += 1
            await message.answer(
                text=f"К сожалению, у вас больше не осталось "
                     f"попыток. Вы проиграли :(\n\nПравильный ответ: "
                     f"{users[message.from_user.id]['current_question']['answer']}"
                     f"\n\nДавайте сыграем еще?",
                reply_markup=keyboard_answer,
            )

        else:
            users[message.from_user.id]['attempts'] -= 1
            await message.answer(
                text=f"Похоже, это неправильный ответ, "
                     f"количество оставшихся попыток: {users[message.from_user.id]['attempts'] + 1}, "
                     f"попробуйте ещё раз!",
                reply_markup=keyboard_question,
            )

    else:
        await message.answer(
            text='Мы еще не играем. Хотите сыграть?',
            reply_markup=keyboard_start
        )


if __name__ == '__main__':
    dp.run_polling(bot)
