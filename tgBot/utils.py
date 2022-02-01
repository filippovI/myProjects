import telebot as tb
import db
import config as cfg
import requests as rq
from datetime import datetime as dt

bot = tb.TeleBot(cfg.token)


# Класс для изменний структры сообщений (Удаление кнопок, редактирования)
class Editor:

    # Удаление кнопок у сообщения выше при написании текста
    @staticmethod
    def del_buttons_text(msg):
        try:
            bot.edit_message_reply_markup(chat_id=msg.chat.id, message_id=msg.message_id - 1,
                                          reply_markup=None)
        except Exception:
            pass

    # Удаление кнопок у сообщения выше при нажатии на кнопку
    @staticmethod
    def del_buttons(call):
        bot.edit_message_reply_markup(chat_id=call.chat.id, message_id=call.message_id,
                                      reply_markup=None)

    # Редактирование сообщения
    @staticmethod
    def edit_text(call):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=call.message.text + " " + call.data)


# Класс для создания кнопок
class CreateButtons:

    # Создание кнопок на стартовом сообщении
    @staticmethod
    def start_page():
        buttons = tb.types.InlineKeyboardMarkup()
        item_yes = tb.types.InlineKeyboardButton(text='Начать', callback_data='yes')
        buttons.add(item_yes)
        return buttons

    # Создание кнопок у сообщений с выбором валюты
    @staticmethod
    def choice_value(currencies_list, call=None):
        if call:
            currencies_list.remove(call.data)
        buttons = tb.types.InlineKeyboardMarkup()
        button_list = [tb.types.InlineKeyboardButton(text=x, callback_data=x) for x in currencies_list]
        buttons.add(*button_list)
        return buttons


# Класс для расчетов
class Calculation:

    # Проверка на корректность количества
    @staticmethod
    def check_result(count):
        try:
            if float(count.text) < 0:
                raise ValueError
        except ValueError as err:
            Logging.write_log(count, 'Неверное значение: {0}'.format(str(count.text)), err)
            return 'Неверное значение'
        except Exception as err:
            Logging.write_log(count, 'Неизвестная ошибка', err)
            return 'Неизвестная ошибка'
        else:
            return Calculation.check_answer(count)

    # Проверка на ответ от сервера
    @staticmethod
    def check_answer(count):
        end_value_sheet = []
        for v in db.get_info(table='val_for_convert', col='currency'):
            end_value_sheet.append(*v)

        # Обработка ошибки API
        try:
            url = 'https://min-api.cryptocompare.com/data/price?fsym={0}&tsyms={1}'
            request = rq.get(url.format(end_value_sheet[0], end_value_sheet[1]))

            # Запись ответа от cryptocompare в request_json
            request_json = request.json()
        except Exception as err:
            Logging.write_log(count, 'Ошибка API', err)
            return 'Ошибка ответа сервера'
        else:

            # Обработка ответа с ошибкой
            if 'Response' in request_json.keys() and request_json['Response'] in 'Error':
                Logging.write_log(count, 'Ошибка валют: {0} {1}'.format(end_value_sheet[0],
                                                                        end_value_sheet[1]), request_json['Message'])
                return 'Ошибка валют'
            else:
                return Calculation.Result(count, end_value_sheet[0], end_value_sheet[1], request_json)

        # Результирующий расчет курса
    @staticmethod
    def Result(count, end_v_0, end_v_1, rq_j):
        result = "{0} {1} = {2} {3}".format(count.text, end_v_0, rq_j[end_v_1] * float(count.text), end_v_1)
        return result


# Класс для работы со списком валют
class Values:

    # Проверка на то, что код валюты = заглавная латиница или заглавная латиница + цифры
    @staticmethod
    def check_value(msg):
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        nums = '1234567890'
        text_abc = ''
        text_num = ''
        try:
            new_cur_rub, new_cur_eng = msg.text.split(' ')
            for i in new_cur_eng:
                if i in alphabet:
                    text_abc += i
                elif i in nums:
                    text_num += i
                else:
                    raise ValueError
            if not text_abc or new_cur_eng[0] not in alphabet:
                raise ValueError
            else:
                Values.add_value(msg, new_cur_rub, new_cur_eng)
        except ValueError as err:
            bot.send_message(msg.chat.id, 'Неверное значение')
            Logging.write_log(msg, '/add_value неверное значение: {0}'.format(msg.text), err)

    # Добавление валюты в таблицу
    @staticmethod
    def add_value(msg, new_cur_rub, new_cur_eng):
        check_list = []
        for i in db.get_info(col='value', table='currencies'):
            check_list.append(*i)

        # Проверка на наличие добавляемой валюты в таблице
        if new_cur_eng not in check_list:
            db.insert_table(table='currencies', col='rus_value, value', value=[new_cur_rub, new_cur_eng])
            bot.send_message(msg.chat.id, 'Новая валюта добавлена 👍')
        else:
            bot.send_message(msg.chat.id, 'Валюта {0} уже добавлена'.format(new_cur_eng))
            Logging.write_log(msg, 'Валюта {0} уже добавлена'.format(new_cur_eng),
                              'Валюта {0} уже добавлена'.format(new_cur_eng))

    # Вывод списка доступных валют
    @staticmethod
    def show_values(msg):
        text = 'Доступные валюты: \n'
        for v, rv in db.get_info(table='currencies', col='value, rus_value'):
            text = '\n'.join((text, '{0} - {1}'.format(rv, v)))
        bot.reply_to(msg, text)


# Класс для логирования событий
class Logging:

    # Запись логов в БД
    @staticmethod
    def write_log(count, text, err):
        format_time = dt.now()
        db.insert_table(table='logs',
                        col='time,error_handled,error,user',
                        value=[str(format_time.strftime('%d/%m/%Y, %H:%M')),
                               text, str(err), count.from_user.username])

    # Запись логов из БД в text
    @staticmethod
    def get_logs():
        text = ''
        for i in db.get_info(table='logs', col='time,user,error_handled'):
            for v in i:
                text = ''.join((text, str(v) + ' | '))
            text += '\n\n'
        return text if text else 'Логов нет'
