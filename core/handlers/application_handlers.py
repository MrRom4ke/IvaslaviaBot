from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import Bot
import os

async def handle_screenshot(message: Message, state: FSMContext, bot: Bot):
    """Обрабатывает скриншот пользователя и сохраняет его в папку."""
    # Проверяем, что сообщение содержит изображение
    if not message.photo:
        await message.answer("Пожалуйста, отправьте одно изображение.")
        return

    # Получаем данные о выбранном розыгрыше из контекста состояния
    data = await state.get_data()
    drawing_id = data.get("selected_drawing_id")

    if not drawing_id:
        await message.answer("Произошла ошибка, розыгрыш не найден. Попробуйте снова.")
        return

    # Получаем фотографию в наилучшем качестве
    photo = message.photo[-1]

    # Определяем путь для сохранения изображения
    user_id = message.from_user.id
    file_path = f"images/application/{user_id}_{drawing_id}.jpg"

    # Убедимся, что папка существует
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Скачиваем файл с помощью объекта бота
    file = await bot.get_file(photo.file_id)
    await bot.download_file(file.file_path, destination=file_path)

    # Отправляем сообщение об успешной загрузке
    await message.answer("Ваш скриншот был успешно сохранен и ожидает проверки.")
    await state.clear()  # Завершаем состояние после обработки
