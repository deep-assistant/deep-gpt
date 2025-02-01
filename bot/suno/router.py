from aiogram import Router
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup

from bot.filters import TextCommand, StateCommand, StartWithQuery
from bot.suno.command_types import suno_command, suno_text
from services import StateTypes, stateService, sunoService, tokenizeService

sunoRouter = Router()


async def suno_create_messages(message, generation):
    result = list(generation['data']['output']['clips'].values())[0]

    await message.answer_photo(
        photo=result["image_large_url"],
        caption=f"""
    Текст *«{result["title"]}»*

    {result["metadata"]["prompt"]}
    """)

    await message.answer_document(document=result["audio_url"])
    await message.answer_video(video=result["video_url"])
    await message.answer(text="Cгенерировать Suno еще? 🔥", reply_markup=InlineKeyboardMarkup(
        resize_keyboard=True,
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Сгенерировать 🔥",
                    callback_data="suno-generate"
                )
            ]
        ],
    ))


@sunoRouter.message(StateCommand(StateTypes.Suno))
async def suno_generate_handler(message: Message):
    stateService.set_current_state(message.from_user.id, StateTypes.Default)

    # message text should not exceed 200 characters
    if len(message.text) > 200:
        await message.answer("""Описание музыкальной композиции 🎵 *не может быть более 200 символов* для Suno.

*Режим генерации музыки в Suno деактивирован*.

Можете попробовать сгенерировать музыку в Suno ещё раз или продолжать пользоваться ботом как обычно.
""", reply_markup=InlineKeyboardMarkup(
            resize_keyboard=True,
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"Сгенерировать музыку в Suno 🔥",
                        callback_data="suno-generate"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Отмена ❌",
                        callback_data=f"cancel-suno-generate"
                    )
                ],
            ],
        ))
        return

    wait_message = await message.answer(
        "**⌛️Ожидайте генерацию...**\nПримерное время ожидания: *1-5 минут*.\nМожете продолжать работать с ботом.")

    await message.bot.send_chat_action(message.chat.id, "typing")

    async def task_id_get(task_id: str):
        await message.answer(f"`1:suno:{task_id}:generate`")
        await message.answer(f"""Это ID вашей генерации.

Просто отправьте этот ID в чат и получите актуальный статус вашей генерации в любой удобный для вас момент.
                             
Вы также получите результат генерации по готовности.
""")

    generation = await sunoService.generate_suno(message.text, task_id_get)

    await suno_create_messages(message, generation)

    await tokenizeService.update_token(message.from_user.id, 5000, "subtract")
    await message.answer(f"""
🤖 Затрачено на генерацию музыкальной композиции в *Suno*: *5000⚡️*

❔ /help - Информация по ⚡️
    """)

    await wait_message.delete()


@sunoRouter.message(TextCommand([suno_command(), suno_text()]))
async def suno_prepare_handler(message: Message):
    user_id = message.from_user.id
    await enter_suno_state(user_id, message)

@sunoRouter.callback_query(StartWithQuery("suno-generate"))
async def suno_prepare_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await enter_suno_state(user_id, callback_query.message)
    
@sunoRouter.callback_query(StartWithQuery("cancel-suno-generate"))
async def cancel_state(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    stateService.set_current_state(user_id, StateTypes.Default)
    await callback_query.message.delete()
    await callback_query.answer("Режим генерации музыки в Suno успешно отменён!")

async def enter_suno_state(user_id, message: Message):
    stateService.set_current_state(user_id, StateTypes.Suno)

    await message.answer(text="""*Активирован режим* генерации музыки в *Suno*.

*Следующее ваше сообщение будет интерпретировано как промпт для Suno* и после отправки сообщения будет запущена генерация музыки, которая будет стоить *5000⚡️*.

Опишите в следующем сообщении музыкальную композицию 🎵 (*не более 200 символов*), которую вы хотите сгенерировать или отмените если передумали.
""", reply_markup=InlineKeyboardMarkup(
        resize_keyboard=True,
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Отмена ❌",
                callback_data=f"cancel-suno-generate"
            )],
        ]
    ))