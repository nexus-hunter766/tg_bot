#7579968313:AAE_q7cdlMbgpseyQAmZ9s2gEBPucmlTKlw

import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import asyncio
import nest_asyncio  # Импортируем nest_asyncio для Jupyter Notebook

# Применяем nest_asyncio для Jupyter Notebook
nest_asyncio.apply()

# Функция для загрузки данных из CSV-файла
def load_data():
    try:
        return pd.read_csv('students_data.csv')
    except FileNotFoundError:
        return pd.DataFrame(columns=['Группа', 'Задание', 'Фамилия', 'Балл'])

# Функция для сохранения данных в CSV-файл
def save_data(df):
    df.to_csv('students_data.csv', index=False)

# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Привет! Я бот для учета баллов студентов.\n'
        'Используйте /help для просмотра доступных команд.'
    )

# Функция для обработки команды /help
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Доступные команды:\n'
        '/start - Начать работу\n'
        '/help - Показать доступные команды\n'
        '/show - Показать все данные\n'
        '/group <группа> - Показать данные по группе\n'
        '/student <фамилия> - Показать данные по студенту\n'
        '/delete <группа> <задание> <фамилия> - Удалить запись\n'
        '/clear - Очистить все записи\n'
        '/export - Выгрузить данные в Excel\n'
        '/upload - Загрузить данные из файла (CSV или Excel)'
    )

# Функция для обработки команды /clear
async def clear_data(update: Update, context: CallbackContext) -> None:
    try:
        # Создаем пустой DataFrame
        df = pd.DataFrame(columns=['Группа', 'Задание', 'Фамилия', 'Балл'])
        save_data(df)
        await update.message.reply_text('Все записи успешно очищены!')
    except Exception as e:
        await update.message.reply_text(f'Ошибка: {e}')

# Функция для обработки команды /show
async def show_data(update: Update, context: CallbackContext) -> None:
    df = load_data()
    if df.empty:
        await update.message.reply_text('Данные отсутствуют.')
    else:
        await update.message.reply_text(df.to_string(index=False))

# Функция для обработки команды /group
async def show_group_data(update: Update, context: CallbackContext) -> None:
    try:
        group_name = context.args[0]
        df = load_data()
        group_data = df[df['Группа'] == group_name]
        if group_data.empty:
            await update.message.reply_text(f'Данные для группы {group_name} отсутствуют.')
        else:
            await update.message.reply_text(group_data.to_string(index=False))
    except IndexError:
        await update.message.reply_text('Пожалуйста, укажите название группы. Например: /group Группа1')

# Функция для обработки команды /student
async def show_student_data(update: Update, context: CallbackContext) -> None:
    try:
        surname = context.args[0]
        df = load_data()
        student_data = df[df['Фамилия'] == surname]
        if student_data.empty:
            await update.message.reply_text(f'Данные для студента {surname} отсутствуют.')
        else:
            await update.message.reply_text(student_data.to_string(index=False))
    except IndexError:
        await update.message.reply_text('Пожалуйста, укажите фамилию студента. Например: /student Иванов')

# Функция для обработки команды /delete
async def delete_record(update: Update, context: CallbackContext) -> None:
    try:
        if len(context.args) < 3:
            raise ValueError("Неверный формат команды. Пример: /delete Группа1 Задание1 Иванов")

        group = context.args[0]
        task_name = context.args[1]
        surname = context.args[2]

        df = load_data()
        # Удаляем запись
        initial_size = len(df)
        df = df[~((df['Группа'] == group) & (df['Задание'] == task_name) & (df['Фамилия'] == surname))]
        if len(df) == initial_size:
            await update.message.reply_text('Запись не найдена.')
        else:
            save_data(df)
            await update.message.reply_text('Запись успешно удалена!')
    except Exception as e:
        await update.message.reply_text(f'Ошибка: {e}')

# Функция для обработки команды /export
async def export_to_excel(update: Update, context: CallbackContext) -> None:
    try:
        df = load_data()
        if df.empty:
            await update.message.reply_text('Данные отсутствуют.')
        else:
            # Сохраняем данные в Excel
            df.to_excel('students_data.xlsx', index=False)
            await update.message.reply_document(document=open('students_data.xlsx', 'rb'))
    except Exception as e:
        await update.message.reply_text(f'Ошибка: {e}')

# Функция для обработки команды /upload
async def upload_file(update: Update, context: CallbackContext) -> None:
    try:
        # Проверяем, что пользователь отправил файл
        if not update.message.document:
            await update.message.reply_text('Пожалуйста, отправьте файл в формате CSV или Excel.')
            return

        # Получаем файл
        file = await update.message.document.get_file()
        file_path = f"uploaded_{file.file_id}.{file.file_name.split('.')[-1]}"
        await file.download_to_drive(file_path)

        # Загружаем данные из файла
        if file_path.endswith('.csv'):
            new_data = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            new_data = pd.read_excel(file_path)
        else:
            await update.message.reply_text('Неподдерживаемый формат файла. Используйте CSV или Excel.')
            return

        # Проверяем структуру файла
        if not {'Группа', 'Задание', 'Фамилия', 'Балл'}.issubset(new_data.columns):
            await update.message.reply_text('Файл должен содержать колонки: Группа, Задание, Фамилия, Балл.')
            return

        # Загружаем текущие данные
        df = load_data()

        # Объединяем данные
        df = pd.concat([df, new_data], ignore_index=True)

        # Сохраняем данные
        save_data(df)

        await update.message.reply_text('Данные успешно загружены и объединены!')
    except Exception as e:
        await update.message.reply_text(f'Ошибка: {e}')

# Функция для интерактивного добавления записей
async def add_record_interactive(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Введите данные в формате: "Группа Название_задания Фамилия1, Фамилия2, ... Балл"'
    )
    context.user_data['adding'] = True

# Функция для обработки текстовых сообщений
async def handle_message(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('adding'):
        text = update.message.text
        try:
            # Разбиваем введенный текст на части
            parts = text.split()
            if len(parts) < 4:
                raise ValueError("Неверный формат ввода. Пример: Группа1 Задание1 Иванов, Петров 10")

            # Извлекаем группу и название задания
            group = parts[0]
            task_name = parts[1]

            # Объединяем оставшиеся части для обработки фамилий и балла
            rest = ' '.join(parts[2:])

            # Разделяем фамилии и балл
            if ',' not in rest:
                raise ValueError("Фамилии должны быть разделены запятыми. Пример: Иванов, Петров 10")

            # Разделяем фамилии и балл
            surnames_part, score_part = rest.rsplit(' ', 1)  # Разделяем по последнему пробелу
            surnames = [surname.strip() for surname in surnames_part.split(',')]

            # Проверяем, что балл — это число
            try:
                score = int(score_part)
            except ValueError:
                raise ValueError("Балл должен быть числом. Пример: Иванов, Петров 10")

            # Загружаем данные из CSV-файла
            df = load_data()

            # Добавляем новые данные в таблицу
            for surname in surnames:
                new_row = {'Группа': group, 'Задание': task_name, 'Фамилия': surname, 'Балл': score}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # Сохраняем данные
            save_data(df)

            # Создаем inline-клавиатуру
            keyboard = [
                [InlineKeyboardButton("Добавить еще", callback_data='add_more')],
                [InlineKeyboardButton("Завершить", callback_data='finish')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text('Данные успешно добавлены! Что дальше?', reply_markup=reply_markup)
        except Exception as e:
            await update.message.reply_text(f'Ошибка: {e}')
    else:
        await update.message.reply_text('Используйте команду /add для добавления записей.')

# Обработчик inline-клавиатуры
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'add_more':
        await query.message.reply_text('Введите данные в формате: "Группа Название_задания Фамилия1, Фамилия2, ... Балл"')
    elif query.data == 'finish':
        # Выгружаем данные в Excel и отправляем пользователю
        df = load_data()
        if df.empty:
            await query.message.reply_text('Данные отсутствуют.')
        else:
            df.to_excel('students_data.xlsx', index=False)
            await query.message.reply_document(document=open('students_data.xlsx', 'rb'))
        context.user_data['adding'] = False

# Функция для запуска бота
async def run_bot():
    # Вставьте сюда ваш токен
    application = Application.builder().token("7579968313:AAE_q7cdlMbgpseyQAmZ9s2gEBPucmlTKlw").build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("show", show_data))
    application.add_handler(CommandHandler("group", show_group_data))
    application.add_handler(CommandHandler("student", show_student_data))
    application.add_handler(CommandHandler("delete", delete_record))
    application.add_handler(CommandHandler("clear", clear_data))
    application.add_handler(CommandHandler("export", export_to_excel))
    application.add_handler(CommandHandler("upload", upload_file))
    application.add_handler(CommandHandler("add", add_record_interactive))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запускаем бота
    await application.run_polling()

# Запуск бота в интерактивной среде
if __name__ == '__main__':
    # Используем asyncio.run для запуска бота
    asyncio.run(run_bot())