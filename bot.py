#TeleggammBot.
#Создает виртуальную скидочную карту для гостей бара при регистрации (10%) и хранит данные в SQL-таблице.
#Скидка может быть изменена лидо удалена Старшим администратором или администраторами, утвержденными Старшим,
#Информация об администраторах хранится в отдельной таблице SQL.
#Пользователь также имеет доступ к набору клавишь с информацией баров сети и доступ к контактданным каждого бара.
#Также имеет возможность общей рассылки пользователям какой-либо информации: акции, события, мероприятия и т.д.
#Рассылка осуществляется ст. администратором и администратороми.
#Бот самомтоятельно в 15:00 рассылает поздравления пользоватеям с Днём Рождения и за 3 дня до него со спецпредложением.
#Ст. администратор определяется по message.chat.id и находится внутри кода. Строки: 808 и 2153
#Администраторы добавляются командой '''/add_admin''' с дальнейшим подтверждением.
#Информация о пользователе и скидке может быть проверена посредством команды '''/start'''
#При запуске необходим запус командой '''/start_Bot''' для создания таблиц базы данных.
#запуск функции с автоматическими поздравлениями '''/start_congratulation'''

import telebot
from telebot import types
import datetime
import re
import sqlite3
import schedule

TOKEN = '5303502076:AAErUfMh1r2xZH3HRtnR5VsZkvZPl0jN2f0'
bot = telebot.TeleBot(TOKEN)

#Класс для временных данных
class Temp:
    pass

#MessageObject
@bot.message_handler(commands=['message'])
def m(message):
    bot.send_message(message.chat.id, message)

#WorkCommand
#Start
@bot.message_handler(commands=['start_Bot'])
def start(message):
    conn = sqlite3.connect("guests.db")
    cur = conn.cursor()
    sql = """\
        CREATE TABLE guest (
            id_user INTEGER PRIMARY KEY AUTOINCREMENT,
            mess_id INTEGER,
            surname TEXT,
            name TEXT,
            date_b DATE,
            phone INTEGER,
            sale INTEGER
            );
            """
    try:
        cur.executescript(sql)
    except sqlite3.DatabaseError as err:
        bot.send_message(message.chat.id, "База данных гостей уже создавалась")
    else:
        bot.send_message(message.chat.id, "База данных гостей создана")
    cur.close()
    conn.close()

    conn = sqlite3.connect("guests.db")
    cur = conn.cursor()
    sql = """\
            CREATE TABLE admin (
                id_admin INTEGER PRIMARY KEY AUTOINCREMENT,
                mess_id INTEGER,
                surname TEXT,
                name TEXT,
                bar TEXT,
                action TEXT
                );
                """
    try:
        cur.executescript(sql)
    except sqlite3.DatabaseError as err:
        bot.send_message(message.chat.id, "База данных гостей уже создавалась")
    else:
        bot.send_message(message.chat.id, "База данных гостей создана")
    cur.close()
    conn.close()

#Запуск автопоздравлений
@bot.message_handler(commands=['start_congratulation'])
def start_cong(message):
    bot.send_message(message.chat.id, 'Автомат поздравлений запущен')
    schedule.every().day.at("15:00").do(congrat)
    while True:
        schedule.run_pending()

#Команда на добавление Администратора
@bot.message_handler(commands=['add_admin'])
def add_admin(message):
    conn = sqlite3.connect('guests.db')
    cur = conn.cursor()
    sql = f"SELECT id_admin, mess_id, surname, name, bar, action FROM admin WHERE mess_id = {message.chat.id}"
    cur.execute(sql)
    temp = cur.fetchone()
    cur.close()
    conn.close()
    if not temp:
        sent = bot.send_message(message.chat.id, 'Введите Вашу фамилию')
        bot.register_next_step_handler(sent, reg_admin_1)
    else:
        bot.send_message(message.chat.id, f'Вы уже зарегистрированы\nФамилия: {temp[2]}\nИмя: {temp[3]}\nЗаведение: {temp[4]}\nID: {str(temp[0]).rjust(4, "0")}\nАктивность: {temp[5]}')

#Команда на главное меню Головы
@bot.message_handler(commands=['sokol'])
def sokol(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    k1 = types.InlineKeyboardButton(text='РАССЫЛКА', callback_data='1send_all1')
    k2 = types.InlineKeyboardButton(text='УПРАВЛЕНИЕ КАРТАМИ', callback_data='1_Card_Contol_1_1')
    k3 = types.InlineKeyboardButton(text='УПРАВЛЕНИЕ АДМИНИСТРАТОРАМИ', callback_data='1_2_Admin_Contol_1_1')
    kb.add(k1, k2, k3)
    bot.send_message(message.chat.id, 'Здравствуйте', reply_markup=kb)

#Команда на общ. тест карты
@bot.message_handler(commands=['test'])
def test(message):
    sent = bot.send_message(message.chat.id, 'Введите номер карты')
    bot.register_next_step_handler(sent, card_test)

#BUTTONS
@bot.callback_query_handler(func=lambda x: x.data)
def chek(callback):
#Регистрация пользователя/Ошибка в указанных данных пользователя
    if callback.data == '1Registration1':
        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"DELETE FROM guest WHERE mess_id = {callback.message.chat.id}"
        cur.execute(sql)
        cur.close()
        conn.close()
        sent1 = bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text="Введите Вашу фамилию")
        bot.register_next_step_handler(sent1, review1)

#Подтверждение регистрации пользователя
    elif callback.data == '2Registration2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text="Бары", callback_data='1_1_Bar_Info_2_1')
        kb.add(k1)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT id_user FROM guest WHERE mess_id = {callback.message.chat.id}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.send_message(callback.message.chat.id, text=f'Карта готова!!!\n№{str(temp[0]).rjust(6, "0")}', reply_markup=kb)

#Основное меню ГОЛОВЫ/Администрвтора
    elif callback.data == '/sokol':
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb2 = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='РАССЫЛКА', callback_data='1send_all1')
        k2 = types.InlineKeyboardButton(text='УПРАВЛЕНИЕ КАРТАМИ', callback_data='1_Card_Contol_1_1')
        k3 = types.InlineKeyboardButton(text='УПРАВЛЕНИЕ АДМИНИСТРАТОРАМИ', callback_data='1_2_Admin_Contol_1_1')
        k4 = types.InlineKeyboardButton(text='ПРОВЕРИТЬ КАРТУ', callback_data='1_Admin_Test_Card_2')
        kb.add(k1, k2, k3, k4)
        kb2.add(k4, k1, k2)
        if callback.message.chat.id == 572750004:     #!!!!!!!!ЗАМЕНИТЬ!!!!!
            bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text='Здравствуйте', reply_markup=kb)
        else:
            bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text='Здравствуйте', reply_markup=kb2)

#Рассылка пользователям и админам
    elif callback.data == '1send_all1':
        sent = bot.send_message(callback.message.chat.id, 'Введите сообщение для рассылки')
        bot.register_next_step_handler(sent, send_all)

#Управление картами пользователя Администратором
    elif callback.data == '1_Card_Contol_1_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='ПОИСК', callback_data='1find_guest1')
        k2 = types.InlineKeyboardButton(text='СПИСОК', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='НАЗАД', callback_data='/sokol')
        kb.add(k1, k2, k3)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text='Поиск по номеру карты или просмотреть список?', reply_markup=kb)

#Выбор параметра для поиска карты пользователя
    elif callback.data == '1find_guest1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='ПОИСК ПО НОМЕРУ КАРТЫ', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='ПОИСК ПО ФАМИЛИИ', callback_data='1_find_first_name_1')
        k3 = types.InlineKeyboardButton(text='ПОИСК ПО ИМЕНИ', callback_data='1_find_last_name_1')
        kb.add(k1, k2, k3)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text='Выберите параметр для поиска', reply_markup=kb)

#Поиск по номеру карты
    elif callback.data == '1_find_num_1':
        sent = bot.send_message(callback.message.chat.id, "Введите номер карты")
        bot.register_next_step_handler(sent, find_ncard)

#Выбор параметра для изменения данных пользователя Администратором
    elif callback.data == '2_edit_guest_2':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='Изменить данные', callback_data='2_edit_guest_data_2')
        k2 = types.InlineKeyboardButton(text='Изменить скидку', callback_data='1_edit_guest_sale_1')
        k3 = types.InlineKeyboardButton(text='Удалить', callback_data='11_delete_guest1_2')
        k4 = types.InlineKeyboardButton(text='Отмена', callback_data='/sokol')
        kb.add(k1, k2, k3, k4)
        bot.send_message(callback.message.chat.id, f"Выберите", reply_markup=kb)

#Изменение данных пользователя Администратором
    elif callback.data == '2_edit_guest_data_2':
        sent3 = bot.send_message(callback.message.chat.id, "Введите номер карты Гостя")
        bot.register_next_step_handler(sent3, edit_data)

#Ввод номера карты для замены скидки
    elif callback.data == '1_edit_guest_sale_1':
        sent = bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                                     text='Введите номер карты')
        bot.register_next_step_handler(sent, f_num_sale)

#Изменение скидки пользователя на 10%
    elif callback.data == '2_edit_guest_sale_10_1':
        kbok = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kbok.add(k1)

        t = Temp.user_edit4

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE guest SET sale = {int(10)} WHERE id_user = {t};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()
        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, date_b, id_user, sale FROM guest"
        cur.execute(sql)
        i = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %\nСкидка изменена",
                              reply_markup=kbok)

# Изменение скидки пользователя на 20%
    elif callback.data == '1_edit_guest_sale_20_1':
        kbok = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kbok.add(k1)

        t = Temp.user_edit4

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE guest SET sale = {int(20)} WHERE id_user = {t};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, date_b, id_user, sale FROM guest"
        cur.execute(sql)
        i = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %\nСкидка изменена",
                              reply_markup=kbok)

# Изменение скидки пользователя на 30%
    elif callback.data == '11_edit_guest1_sale_30_2':
        kbok = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kbok.add(k1)

        t = Temp.user_edit4

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE guest SET sale = {int(30)} WHERE id_user = {t};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, date_b, id_user, sale FROM guest"
        cur.execute(sql)
        i = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %\nСкидка изменена",
                              reply_markup=kbok)

# Изменение скидки пользователя на 40%
    elif callback.data == '1_edit_guest_sale_40_11':
        kbok = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kbok.add(k1)

        t = Temp.user_edit4

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE guest SET sale = {int(40)} WHERE id_user = {t};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, date_b, id_user, sale FROM guest"
        cur.execute(sql)
        i = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %\nСкидка изменена",
                              reply_markup=kbok)

# Изменение скидки пользователя на 50%
    elif callback.data == '1_edit_guest_sale_50_12':
        kbok = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kbok.add(k1)

        t = Temp.user_edit4

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE guest SET sale = {int(50)} WHERE id_user = {t};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, date_b, id_user, sale FROM guest"
        cur.execute(sql)
        i = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %\nСкидка изменена",
                              reply_markup=kbok)

#Ввод фамилии пользователя для поиска
    elif callback.data == '1_find_first_name_1':
        sent31 = bot.send_message(callback.message.chat.id, "Введите фамилию")
        bot.register_next_step_handler(sent31, find_fname)

# Ввод имени пользователя для поиска
    elif callback.data == '1_find_last_name_1':
        sent3 = bot.send_message(callback.message.chat.id, "Введите имя")
        bot.register_next_step_handler(sent3, find_lname)

#Удаление пользователя
    elif callback.data == '11_delete_guest1_2':
        sent3 = bot.send_message(callback.message.chat.id, "Введите номер карты")
        bot.register_next_step_handler(sent3, delete_user)

#Выбор параметров сортировки при запросе полного списка пользователей
    elif callback.data == '1_list_guests_1_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='Сортировать по фамилиям', callback_data='12_sort_surname_21')
        k2 = types.InlineKeyboardButton(text='Сортировать по именам', callback_data='12_sort_name_21')
        k3 = types.InlineKeyboardButton(text='Сортировать по номерам карт', callback_data='12_sort_num_card_21')
        k4 = types.InlineKeyboardButton(text='Сортировать по размеру скидки', callback_data='12_sort_sale_21')
        kb.add(k1, k2, k3, k4)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text='Выберите параметр сотировки', reply_markup=kb)

#Вывод списка всех пользователей, сортировка по фамилии
    elif callback.data == '12_sort_surname_21':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='Новый поиск', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = """SELECT surname, name, date_b, id_user, sale FROM guest ORDER BY surname"""
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id, f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %")
        bot.send_message(callback.message.chat.id, 'Чтобы изменить данные, запомните номер карты гостя и нажмите изменить', reply_markup=kb)

# Вывод списка всех пользователей, сортировка по имени
    elif callback.data == '12_sort_name_21':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='Новый поиск', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = """SELECT surname, name, date_b, id_user, sale FROM guest ORDER BY name"""
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %")
        bot.send_message(callback.message.chat.id,
                         'Чтобы изменить данные, запомните номер карты гостя и нажмите изменить', reply_markup=kb)

# Вывод списка всех пользователей, сортировка по id
    elif callback.data == '12_sort_num_card_21':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='Новый поиск', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = """SELECT surname, name, date_b, id_user, sale FROM guest ORDER BY id_user"""
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %")
        bot.send_message(callback.message.chat.id,
                         'Чтобы изменить данные, запомните номер карты гостя и нажмите изменить', reply_markup=kb)

#Выбор размера скидки для вывода списка пользователей
    elif callback.data == '12_sort_sale_21':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Все', callback_data='33_all_sale_list_33')
        k2 = types.InlineKeyboardButton(text='10%', callback_data='33_10_sale_list_33')
        k3 = types.InlineKeyboardButton(text='20%', callback_data='33_20_sale_list_33')
        k4 = types.InlineKeyboardButton(text='30%', callback_data='33_30_sale_list_33')
        k5 = types.InlineKeyboardButton(text='40%', callback_data='33_40_sale_list_33')
        k6 = types.InlineKeyboardButton(text='50%', callback_data='33_50_sale_list_33')
        k7 = types.InlineKeyboardButton(text='Анулированные', callback_data='33_00_sale_list_33')
        k8 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3, k4, k5, k6, k7, k8)
        bot.send_message(callback.message.chat.id, 'Выберите скидку', reply_markup=kb)

#Вывод всего списка пользователей, сортировка по размеру скидки
    elif callback.data == '33_all_sale_list_33':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='Новый поиск', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = """SELECT surname, name, date_b, id_user, sale FROM guest ORDER BY sale"""
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %")
        bot.send_message(callback.message.chat.id,
                         'Чтобы изменить данные, запомните номер карты гостя и нажмите изменить', reply_markup=kb)

#Вывод списка пользователей с 10% скидкой
    elif callback.data == '33_10_sale_list_33':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='Новый поиск', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = """SELECT surname, name, date_b, id_user, sale FROM guest WHERE sale = 10 ORDER BY id_user"""
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %")
        bot.send_message(callback.message.chat.id,
                         'Чтобы изменить данные, запомните номер карты гостя и нажмите изменить', reply_markup=kb)

#Вывод списка пользователей с 20% скидкой
    elif callback.data == '33_20_sale_list_33':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='Новый поиск', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = """SELECT surname, name, date_b, id_user, sale FROM guest WHERE sale = 20 ORDER BY id_user"""
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %")
        bot.send_message(callback.message.chat.id,
                         'Чтобы изменить данные, запомните номер карты гостя и нажмите изменить', reply_markup=kb)

#Вывод списка всех пользователей со скидкой 30%
    elif callback.data == '33_30_sale_list_33':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='Новый поиск', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = """SELECT surname, name, date_b, id_user, sale FROM guest WHERE sale = 30 ORDER BY id_user"""
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                     f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %")
        bot.send_message(callback.message.chat.id,
                 'Чтобы изменить данные, запомните номер карты гостя и нажмите изменить', reply_markup=kb)

#Вывод списка пользователей со скидкой 40%
    elif callback.data == '33_40_sale_list_33':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='Новый поиск', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = """SELECT surname, name, date_b, id_user, sale FROM guest WHERE sale = 40 ORDER BY id_user"""
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %")
        bot.send_message(callback.message.chat.id,
                         'Чтобы изменить данные, запомните номер карты гостя и нажмите изменить', reply_markup=kb)

#Вывод списка пользователей со скидкой 50%
    elif callback.data == '33_50_sale_list_33':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='Новый поиск', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = """SELECT surname, name, date_b, id_user, sale FROM guest WHERE sale = 50 ORDER BY id_user"""
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %")
        bot.send_message(callback.message.chat.id,
                         'Чтобы изменить данные, запомните номер карты гостя и нажмите изменить', reply_markup=kb)

#Вывод списка пользователей с анулироваными скидками
    elif callback.data == '33_00_sale_list_33':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
        k2 = types.InlineKeyboardButton(text='Новый поиск', callback_data='1_list_guests_1_1')
        k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1, k2, k3)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = """SELECT surname, name, date_b, id_user, sale FROM guest WHERE sale = 'Анулирована' ORDER BY id_user"""
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %")
        bot.send_message(callback.message.chat.id,
                         'Чтобы изменить данные, запомните номер карты гостя и нажмите изменить', reply_markup=kb)

#Управление администраторами
    elif callback.data == '1_2_Admin_Contol_1_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Найти по ID', callback_data='1_search_admin__id_1')
        k2 = types.InlineKeyboardButton(text='Список', callback_data='21_List_admin_1_2')
        kb.add(k1, k2)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text='Выберите', reply_markup=kb)

#Параметры для списков администраторов
    elif callback.data == '21_List_admin_1_2':
        kb = types.InlineKeyboardMarkup(row_width=2)
        k1 = types.InlineKeyboardButton(text='ВСЕ', callback_data='1_all_admin_list_11')
        k2 = types.InlineKeyboardButton(text='По заведениям', callback_data='1_Bar_admin_list_2_1')
        k3 = types.InlineKeyboardButton(text='Активные', callback_data='1_Action_YES_admin_list_2_1')
        k4 = types.InlineKeyboardButton(text='Неактивные', callback_data='1_Action_NO_admin_list_2_1')
        k6 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
        kb.add(k1, k2, k3, k4, k6)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text='Выберите', reply_markup=kb)

#Запись бара Администратора хелп
    elif callback.data == '1_Help_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK, всё верно', callback_data='2_Regist_Admin')
        k2 = types.InlineKeyboardButton(text='ОШИБКА, исправить', callback_data='/add_admin')
        kb.add(k1, k2)
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Mr. Help & Friends" WHERE mess_id = {callback.message.chat.id};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE mess_id = {callback.message.chat.id}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введенную информацию:\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}",
                              reply_markup=kb)

# Запись бара Администратора Stay_True
    elif callback.data == '1_Stay_True_2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK, всё верно', callback_data='2_Regist_Admin')
        k2 = types.InlineKeyboardButton(text='ОШИБКА, исправить', callback_data='/add_admin')
        kb.add(k1, k2)

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Stay True" WHERE mess_id = {callback.message.chat.id};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE mess_id = {callback.message.chat.id};"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введенную информацию:\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}",
                              reply_markup=kb)

# Запись бара Администратора Black-Hat Sadovoe
    elif callback.data == '1_Black_Hat_2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK, всё верно', callback_data='2_Regist_Admin')
        k2 = types.InlineKeyboardButton(text='ОШИБКА, исправить', callback_data='/add_admin')
        kb.add(k1, k2)

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Black-Hat Sadovoe" WHERE mess_id = {callback.message.chat.id};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE mess_id = {callback.message.chat.id};"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введенную информацию:\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}",
                              reply_markup=kb)

# Запись бара Администратора Black Hat (Балчуг)
    elif callback.data == '2_Black_Hat_balch_3_2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK, всё верно', callback_data='2_Regist_Admin')
        k2 = types.InlineKeyboardButton(text='ОШИБКА, исправить', callback_data='/add_admin')
        kb.add(k1, k2)

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Black Hat (Балчуг)" WHERE mess_id = {callback.message.chat.id};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE mess_id = {callback.message.chat.id}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введенную информацию:\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}",
                              reply_markup=kb)

# Запись бара Администратора Lawsons
    elif callback.data == '1_Lawsons_2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK, всё верно', callback_data='2_Regist_Admin')
        k2 = types.InlineKeyboardButton(text='ОШИБКА, исправить', callback_data='/add_admin')
        kb.add(k1, k2)

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Lawsons" WHERE mess_id = {callback.message.chat.id};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE mess_id = {callback.message.chat.id}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введенную информацию:\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}",
                              reply_markup=kb)

# Запись бара Администратора Perepel
    elif callback.data == '1_Perepel_1_2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK, всё верно', callback_data='2_Regist_Admin')
        k2 = types.InlineKeyboardButton(text='ОШИБКА, исправить', callback_data='/add_admin')
        kb.add(k1, k2)

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Perepel" WHERE mess_id = {callback.message.chat.id};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE mess_id = {callback.message.chat.id}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введенную информацию:\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}",
                              reply_markup=kb)

#Клавиша исправления данных администратора при регистрации
    elif callback.data == '/add_admin':
        sent = bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text='Введите Вашу фамилию')
        bot.register_next_step_handler(sent, reg_admin_3)

#Подтверждение регистрации Администратора
    elif callback.data == '2_Regist_Admin':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Подтвердить', callback_data='1_go_admin_OK_1')
        k2 = types.InlineKeyboardButton(text='Отменить', callback_data='/sokol')
        kb.add(k1, k2)

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET action = "Неактивен" WHERE mess_id = {callback.message.chat.id};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin FROM admin WHERE mess_id = {callback.message.chat.id}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()

        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,text=f'ГОТОВО!\nВаш id: {str(temp[3]).rjust(4, "0")}\nЖдите подтверждения')
        bot.send_message(572750004, f'Новый администратор!!!\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}\nID: {str(temp[3]).rjust(4, "0")}', reply_markup=kb)
        # !!!!!!!!ЗАМЕНИТЬ!!!

#Поиск Администратора по ID
    elif callback.data == '1_search_admin__id_1':
        sent4 = bot.send_message(callback.message.chat.id, 'Введите ID администратора')
        bot.register_next_step_handler(sent4, s_admin_id)

#Активация Администратора
    elif callback.data == '1_admin_action_OK_2':
        adm = Temp.admin_id
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1)

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET action = "Активен" WHERE id_admin = {int(adm)};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, mess_id FROM admin WHERE id_admin = {int(adm)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f'Администратор добавлен\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}\nID: {str(temp[3]).rjust(4, "0")}', reply_markup=kb)

#Отмена регистрации Администратора
    elif callback.data == '1_admin_action_NO_1_2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k1)

        adm = Temp.admin_id

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET action = "Неактивен" WHERE id_admin = {int(adm)};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, mess_id FROM admin WHERE id_admin = {int(adm)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f'Администратор деактевирован\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}\nID: {str(temp[3]).rjust(4, "0")}',
                              reply_markup=kb)



#Изменение данных Администратора
    elif callback.data == '1_admin_data_create_2':
        sent = bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text='Введите фамилию')
        bot.register_next_step_handler(sent, create_admin_1)

#Клавиши заведения Администратора при изменении его данных
    elif callback.data == '21_Help_2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Верно, изменить', callback_data='/sokol')
        k2 = types.InlineKeyboardButton(text='Ошибка, исправить', callback_data='1_admin_data_create_2')#######
        kb.add(k1, k2)
        adm = Temp.admin_id

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Mr. Help & Friends" WHERE id_admin = {int(adm)};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE id_admin = {int(adm)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f"Проверьте введённую информацию\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}\nID: {str(adm).rjust(4, '0')}", reply_markup=kb)

    elif callback.data == '21_stay_2':

        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Верно, изменить', callback_data='/sokol')
        k2 = types.InlineKeyboardButton(text='Ошибка, исправить', callback_data='1_admin_data_create_2')
        kb.add(k1, k2)
        adm = Temp.admin_id

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Stay True" WHERE id_admin = {int(adm)};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE id_admin = {int(adm)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введённую информацию\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}\nID: {str(adm).rjust(4, '0')}",
                              reply_markup=kb)

    elif callback.data == '21_black_sad_2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Верно, изменить', callback_data='/sokol')
        k2 = types.InlineKeyboardButton(text='Ошибка, исправить', callback_data='1_admin_data_create_2')  #######
        kb.add(k1, k2)
        adm = Temp.admin_id

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Black-Hat Sadovoe" WHERE id_admin = {int(adm)};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE id_admin = {int(adm)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введённую информацию\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}\nID: {str(adm).rjust(4, '0')}",
                              reply_markup=kb)


    elif callback.data == '21_black_balch_2':

        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Верно, изменить', callback_data='/sokol')
        k2 = types.InlineKeyboardButton(text='Ошибка, исправить', callback_data='1_admin_data_create_2')  #######
        kb.add(k1, k2)
        adm = Temp.admin_id

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Black Hat (Балчуг)" WHERE id_admin = {int(adm)};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE id_admin = {int(adm)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введённую информацию\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}\nID: {str(adm).rjust(4, '0')}",
                              reply_markup=kb)

    elif callback.data == '21_lawson_2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Верно, изменить', callback_data='/sokol')
        k2 = types.InlineKeyboardButton(text='Ошибка, исправить', callback_data='1_admin_data_create_2')  #######
        kb.add(k1, k2)
        adm = Temp.admin_id

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Lawsons" WHERE id_admin = {int(adm)};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE id_admin = {int(adm)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введённую информацию\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}\nID: {str(adm).rjust(4, '0')}",
                              reply_markup=kb)

    elif callback.data == '21_PerepeL_2':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Верно, изменить', callback_data='/sokol')
        k2 = types.InlineKeyboardButton(text='Ошибка, исправить', callback_data='1_admin_data_create_2')  #######
        kb.add(k1, k2)
        adm = Temp.admin_id

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET bar = "Perepel" WHERE id_admin = {int(adm)};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar FROM admin WHERE id_admin = {int(adm)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Проверьте введённую информацию\nФамилия: {temp[0]}\nИмя: {temp[1]}\nЗаведение: {temp[2]}\nID: {str(adm).rjust(4, '0')}",
                              reply_markup=kb)

#Вывод всего списка администраторов
    elif callback.data == '1_all_admin_list_11':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_search_admin__id_1')
        k2 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
        kb.add(k1, k2)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, action FROM admin"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nЗаведение: {i[2]}\nID: {str(i[3]).rjust(6, '0')}\nАктивность: {i[4]}")
        bot.send_message(callback.message.chat.id, 'Чтобы изменить данные или статус запомните ID администратора',
                         reply_markup=kb)

#Список администраторов, выбор по заведениям
    elif callback.data == '1_Bar_admin_list_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text="Mr. Help & Friends", callback_data='3_Help_3')
        k2 = types.InlineKeyboardButton(text="Stay True", callback_data='3_stay_true_3')
        k3 = types.InlineKeyboardButton(text="Black Hat (САДОВОЕ)", callback_data='3_black_hat_sad_3')
        k4 = types.InlineKeyboardButton(text="Black Hat (БАЛЧУГ)", callback_data='3_black_hat_balch_3')
        k5 = types.InlineKeyboardButton(text="Lawson's", callback_data='3_lawson_3')
        k6 = types.InlineKeyboardButton(text="Перепел", callback_data='3_perepel_3')
        kb.add(k1, k2, k3, k4, k5, k6)
        bot.send_message(callback.message.chat.id, 'Выберите заведение', reply_markup=kb)

#Список администраторов ХЕЛП бар
    elif callback.data == '3_Help_3':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_search_admin__id_1')
        k2 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
        kb.add(k1, k2)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, action FROM admin WHERE bar = 'Mr. Help & Friends'"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()

        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nЗаведение: {i[2]}\nID: {str(i[3]).rjust(6, '0')}\nАктивность: {i[4]}")
        bot.send_message(callback.message.chat.id, 'Чтобы изменить данные или статус запомните ID администратора',
                         reply_markup=kb)

# Список администраторов Stay True бар
    elif callback.data == '3_stay_true_3':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_search_admin__id_1')
        k2 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
        kb.add(k1, k2)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, action FROM admin WHERE bar = 'Stay True'"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()
        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nЗаведение: {i[2]}\nID: {str(i[3]).rjust(6, '0')}\nАктивность: {i[4]}")
        bot.send_message(callback.message.chat.id, 'Чтобы изменить данные или статус запомните ID администратора',
                         reply_markup=kb)

# Список администраторов Black-Hat Sadovoe бар
    elif callback.data == '3_black_hat_sad_3':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_search_admin__id_1')
        k2 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
        kb.add(k1, k2)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, action FROM admin WHERE bar = 'Black-Hat Sadovoe'"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()
        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nЗаведение: {i[2]}\nID: {str(i[3]).rjust(6, '0')}\nАктивность: {i[4]}")
        bot.send_message(callback.message.chat.id, 'Чтобы изменить данные или статус запомните ID администратора',
                         reply_markup=kb)

# Список администраторов Black Hat (Балчуг) бар
    elif callback.data == '3_black_hat_balch_3':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_search_admin__id_1')
        k2 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
        kb.add(k1, k2)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, action FROM admin WHERE bar = 'Black Hat (Балчуг)'"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()
        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nЗаведение: {i[2]}\nID: {str(i[3]).rjust(6, '0')}\nАктивность: {i[4]}")
        bot.send_message(callback.message.chat.id, 'Чтобы изменить данные или статус запомните ID администратора',
                         reply_markup=kb)

# Список администраторов Lawsons бар
    elif callback.data == '3_lawson_3':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_search_admin__id_1')
        k2 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
        kb.add(k1, k2)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, action FROM admin WHERE bar = 'Lawsons'"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()
        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nЗаведение: {i[2]}\nID: {str(i[3]).rjust(6, '0')}\nАктивность: {i[4]}")
        bot.send_message(callback.message.chat.id, 'Чтобы изменить данные или статус запомните ID администратора',
                         reply_markup=kb)

# Список администраторов Perepel бар
    elif callback.data == '3_perepel_3':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_search_admin__id_1')
        k2 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
        kb.add(k1, k2)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, action FROM admin WHERE bar = 'Perepel'"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()
        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nЗаведение: {i[2]}\nID: {str(i[3]).rjust(6, '0')}\nАктивность: {i[4]}")
        bot.send_message(callback.message.chat.id, 'Чтобы изменить данные или статус запомните ID администратора',
                         reply_markup=kb)

    elif callback.data == '1_2_Test_CARD_1_1':
        sent = bot.send_message(callback.message.chat.id, 'Введите номер карты')
        bot.register_next_step_handler(sent, card_test)

    elif callback.data == '1_Admin_Test_Card_2':
        sent = bot.send_message(callback.message.chat.id, 'Введите номер карты')
        bot.register_next_step_handler(sent, card_test)


    elif callback.data == '1_go_admin_OK_1':
        sent4 = bot.send_message(callback.message.chat.id, 'Введите ID администратора')
        bot.register_next_step_handler(sent4, s_admin_id)

#Список активных администраторов
    elif callback.data == '1_Action_YES_admin_list_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_search_admin__id_1')
        k2 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
        kb.add(k1, k2)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, action FROM admin WHERE action = 'Активен'"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()
        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nЗаведение: {i[2]}\nID: {str(i[3]).rjust(6, '0')}\nАктивность: {i[4]}")
        bot.send_message(callback.message.chat.id, 'Чтобы изменить данные или статус запомните ID администратора',
                         reply_markup=kb)

    elif callback.data == '1_Action_NO_admin_list_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_search_admin__id_1')
        k2 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
        kb.add(k1, k2)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, bar, id_admin, action FROM admin WHERE action = 'Неактивен'"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()
        for i in temp:
            bot.send_message(callback.message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nЗаведение: {i[2]}\nID: {str(i[3]).rjust(6, '0')}\nАктивность: {i[4]}")
        bot.send_message(callback.message.chat.id, 'Чтобы изменить данные или статус запомните ID администратора',
                         reply_markup=kb)


    elif callback.data == '1_1_Bar_Info_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text="Mr. Help & Friend's", callback_data='2_1_Info_Help_2_1')
        k2 = types.InlineKeyboardButton(text="Stay True", callback_data='2_1_Info_Stay_True_2_1')
        k3 = types.InlineKeyboardButton(text="Black Hat (Садовое)", callback_data='2_1_Info_Black_Hat_Sadovoe_2_1')
        k4 = types.InlineKeyboardButton(text="LoW&Son", callback_data='2_1_Info_Low&soN_2_1')
        k5 = types.InlineKeyboardButton(text="Перепел", callback_data='2_1_Info_Perepel_2_1')
        k6 = types.InlineKeyboardButton(text="Black Hat (Балчуг)", callback_data='2_1_Info_Black_Hat_Balchug_2_1')
        k7 = types.InlineKeyboardButton(text="Назад", callback_data='1_1_Menu_User_1_1')
        kb.add(k1, k2, k3, k4, k5, k6, k7)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=
'Выберите заведение', reply_markup=kb)

    elif callback.data == '2_1_Info_Help_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Фотографии', callback_data='1_1_Help_Photo_2_1')
        k2 = types.InlineKeyboardButton(text='Геолокация', callback_data='1_1_Help_Location_2_1')
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='1_1_Bar_Info_2_1')
        kb.add(k1, k2, k3)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f"1-Я ТВЕРСКАЯ-ЯМСКАЯ, 27, СТР.1\nТел: +7 (495) 627 6736\nПН-ЧТ: С 15:00 ДО 00:00\nПТ: С 15:00 ДО 06:00\nСБ: С 16:00 ДО 06:00\nВС: С 16:00 ДО 00:00\nБар Mr. Help and Friends на Белорусской существует уже много лет. Фактически, это первый коктейльный бар в столице, открытый на территории бывшего СССР. Владелец Дима Соколов - двукратный чемпион мира по барменскому искусству, поэтому он и его команда создают образцовые напитки.\nОсновное же помещение на втором этаже дома на Тверской располагает двумя залами. Интерьер выполнен в стиле европейского бара: кирпичные стены дополнены мозаичным логотипом, расположенным на полу, над барной стойкой сохранили вывеску с лозунгом бара, который предлагает поменять деньги на хорошее настроение. На верхних полках - гордость команды: огромная коллекция винтажных шейкеров (некоторые из них времён сухого закона США).", reply_markup=kb)

    elif callback.data == '1_1_Help_Photo_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1') ####
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='2_1_Info_Help_2_1')
        k4 = types.InlineKeyboardButton(text='Телефон', callback_data='2_1_Phone_Help_2_1')
        kb.add(k4, k1, k2, k3)
        file = open('help_ph.jpg', 'rb')
        bot.send_photo(callback.message.chat.id, file)
        file.close()
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)


    elif callback.data == '1_1_Help_Location_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        k4 = types.InlineKeyboardButton(text='Телефон', callback_data='2_1_Phone_Help_2_1')  ####
        kb.add(k4, k1, k2)
        bot.send_location(callback.message.chat.id, 55.77584556278546, 37.58570399843798)
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)


    elif callback.data == '2_1_Info_Stay_True_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Фотографии', callback_data='1_1_Stay_Photo_2_1')
        k2 = types.InlineKeyboardButton(text='Геолокация', callback_data='1_1_stay_Location_2_1')
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='1_1_Bar_Info_2_1')
        kb.add(k1, k2, k3)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text="ул. Славянская пл., д. 2/5/4, стр.3\nТел: +7 (495) 784 6838\n+7(965) 305 1514\nПн-Чт: 12:00-00:00\nПт:12:00-05:00\nСб: 17:00-06:00\nВс: 17:00-00:00\nStay True Bar - верный своим принципам бар, а это значит, что здесь смешивают честные коктейли по самым демократичным ценам и виртуозно работают с грилем. Stay True, это бар в американских традициях с акцентами Мексики и Техаса в кухне. Поэтому, за качество стейков, бургеров и крыльев тут ручаются.\nКоктейли в барной карте сделаны по мотивам жизни и творчества многих известных людей: Джима Моррисона, Чарльза Бувовски, Дина Мартина и других героев. Хотя, классику тут тоже всегда смешают, и про сезонные напитки с актуальными локальными ингредиентами не забудут.\nВ меню еды чередуются блюда из Чикаго, Нью-Йорка, Нового Орлеана, а также штатов Нью-Мексико и Техас. Особенная гордость: бургеры и раздел знаменитой уличной еды со всего мира. А ещё, шеф виртуозно работает со стейками и рёбрами. Добротные порции – это гордость Stay True.\nА ещё Stay True - это вечеринки. Диджей сеты и танцы по пятницам и субботам - уже традиция. В тёплый сезон в Stay True работает основательная и удобная веранда.", reply_markup=kb)

    elif callback.data == '1_1_Stay_Photo_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1') ######
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='2_1_Info_Help_2_1')
        kb.add(k1, k2,k3)
        file = open('stay_ph.jpg', 'rb')
        bot.send_photo(callback.message.chat.id, file)
        file.close()
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)

    elif callback.data == '1_1_stay_Location_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        k4 = types.InlineKeyboardButton(text='Телефон', callback_data='2_1_Phone_Stay_2_1')  ####
        kb.add(k4, k1, k2)
        bot.send_location(callback.message.chat.id, 55.75314556586509, 37.635130269638545)
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)

    elif callback.data == '2_1_Info_Black_Hat_Sadovoe_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Фотографии', callback_data='1_1_Black_Hat_SAD_Photo_2_1')
        k2 = types.InlineKeyboardButton(text='Геолокация', callback_data='1_1_Black_Hat_Location_2_1')
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='1_1_Bar_Info_2_1')
        kb.add(k1, k2, k3)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text="Садовая Каретная 20 стр. 1\nТел: +7 (495) 148 4388\nПН-ЧТ: с 15:00 – 00:00\nПТ: с 15:00 – 02:00\nСБ: с 15:00 – 02:00\nВС: с 15:00 – 00:00\nBlack Hat – не просто Карибский паб в стиле хижины на берегу Садовой-Каретной. Создатели вдохновлялись историей ирландской иммиграции на Барбадос 1620 года. Эти переселенцы сохранили свою культуру, но в Карибских условиях она приобрела самобытный и яркий контекст. Даже само словосочетание Black Hat в переводе с местного диалекта означает «сорви голова».\nИменно поэтому в меню бара не только карибская кухня, и безукоризненные тики коктейли, но и традиционно ирландские блюда с островным подтекстом.\nОднако, главная гордость Black Hat – это, конечно, одна из самых богатых коллекций рома (167 видов только на розлив) с самой обширной географией (30 стран).\nКоманда подбирает ром без погони за статусом обладателей самой большой коллекции, а по принципу самых интересных сортов, редких купажей и разнообразия вкусов. Из широких линеек одних и тех же производителей предпочтение отдаётся только самым стоящим экземплярам.\nТак в стенах Black Hat появился внушительный шкаф коллекционных и редких сортов, который пополняет не только команда, но и гости.\nОт Тринидада, Пуэрто Рико или Гаити до Дании, Японии или Индонезии, можно отследить историю и стиль рома, который там производят. Всё, что занесено в карту, можно и нужно попробовать в Black Hat.\nИ, конечно, ром, как нигде раскрывается в тики коктейлях, которым посвящена барная карта. Они подаются в керамике, сделанной на заказ и вдохновлены внушительной библиотекой – собранием книг о тики культуре.\nВ Black Hat bar можно познакомиться с карибской кухней: гавайские поке с разными морепродуктами и основами, сочный бургер с козлятиной, карибские пирожки и боулы, и просто новые сочетания привычных ингредиентов.\nА ещё, летом работает вместительная веранда с тропическими растениями.", reply_markup=kb)

    elif callback.data == '1_1_Black_Hat_SAD_Photo_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')  #######
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='2_1_Black_Hat_Sadovoe_2_1')
        kb.add(k1, k2, k3)
        file = open('black_hat_sad_ph.jpg', 'rb')
        bot.send_photo(callback.message.chat.id, file)
        file.close()
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)

    elif callback.data == '1_1_Black_Hat_Location_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        k4 = types.InlineKeyboardButton(text='Телефон', callback_data='2_1_Phone_Black_Hat_Sadovoe_2_1')  ####
        kb.add(k4, k1, k2)
        bot.send_location(callback.message.chat.id, 55.773109129077895, 37.61021824375968)
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)

    elif callback.data == '2_1_Info_Low&soN_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Фотографии', callback_data='1_1_LowSon_Photo_2_1')
        k2 = types.InlineKeyboardButton(text='Геолокация', callback_data='1_1_LowSon_Location_2_1')
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='1_1_Bar_Info_2_1')
        kb.add(k1, k2, k3)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text="Адрес: метро Маяковская или Цветной бульвар, Садовая-Каретная, д.24/7\nТел: +7 (495) 649 0189\nПН-ЧТ — с 13:00 до последнего гостя\nПятница — с 13:00 до 06:00\nСуббота — с 14:00 до 06:00\nВоскресенье — с 14:00 до последнего гостя\nLaw&Son — это единственный на сегодняшний день шотландский бар в столице. Дизайн заведения весьма лаконичный: массивные кожаные диваны, придвинутые к деревянным столам, шарфы футбольных болельщиков российских и зарубежных команд над барной стойкой, большие мониторы для просмотра матчей. Но главное: ничего лишнего.\nФутбол тут действительно любят и смотрят, но это все-таки не главное в концепции. Главное – это богатый выбор алкоголя: авторских коктейлей, пива, виски, и даже домашних настоек более 20 видов.\nВ Law&Son разработали интеллектуальную барную карту: коктейли по мотивам жизни известных британцев в России. Например, раздел, посвящённый Артуру Макферсону (Первый председатель правления Всероссийского Футбольного Союза) или Вильяму Каррику (Шотландский и Российский художник и фотограф. Открыл первое в России фотоателье). А что бы заказал Михаил Барклай — де — Толли?\nКухня Law&Son тоже сочетает в себе традиции туманного Альбиона и имеет отсылки к Шотландии, но при этом, славится качественными блюдами на гриле. Тут можно побаловать себя отличным сочным стейком, попробовать необычные блюда: суп по старинному эдинбургскому рецепту, борщ от Шона Коннери с говяжьими щечками, тот самый Хаггис и многое другое. Летом в Law&son открывается уютная веранда. С нее удобно наблюдать за широкой пешеходной зоной Садовой-Каретной.",reply_markup=kb)

    elif callback.data == '1_1_LowSon_Photo_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')  ##########
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='2_1_Info_Low&soN_2_1')
        kb.add(k1, k2, k3)
        file = open('lowson_ph.jpg', 'rb')
        bot.send_photo(callback.message.chat.id, file)
        file.close()
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)

    elif callback.data == '1_1_LowSon_Location_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        k4 = types.InlineKeyboardButton(text='Телефон', callback_data='2_1_Phone_LowSon_2_1')  ####
        kb.add(k4, k1, k2)
        bot.send_location(callback.message.chat.id, 55.773116569970455, 37.61152452862396)
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)

    elif callback.data == '2_1_Info_Perepel_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Фотографии', callback_data='1_1_Perepel_Photo_2_1')
        k2 = types.InlineKeyboardButton(text='Геолокация', callback_data='1_1_Perepel_Location_2_1')
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='1_1_Bar_Info_2_1')
        kb.add(k1, k2, k3)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text="Адрес: ул. Садовая-Каретная, д. 18. М. Цветной бульвар\nТел: +7 (495) 032 1700\nПн–Чт: 12:00 — 00:00\nПт–Сб: 12:00 — 05:00\nВс: 12:00 — 00:00\nРусский бар с вечеринками на Садовой-Каретной. Коктейльную карту построили на основе локальных продуктов — используют российский джин, виски и настойки. Наливают настойку на подмосковном киви и сливочную настойку с мандаринами и халвой. Готовят российские и советские хиты на современный лад — на закуску подают форель слабой соли с цитрусом и вермутом, карпачо из говяжьего языка с соусом из базилика, а на горячее запеченную перепелку с зеленым перлотто и пастой из пяти видов зелени. Интерьер сдержанный, но с акцентами — в основном зале большая мраморная барная стойка и стены расписали графикой в фольклорной стилистике. Каждые выходные организуют вечеринки с DJ-сетами.", reply_markup=kb)

    elif callback.data == '1_1_Perepel_Photo_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1') #######
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='2_1_Info_Perepel_2_1')
        kb.add(k1, k2, k3)
        file = open('perepel_ph.jpg', 'rb')
        bot.send_photo(callback.message.chat.id, file)
        file.close()
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)

    elif callback.data == '1_1_Perepel_Location_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        k4 = types.InlineKeyboardButton(text='Телефон', callback_data='2_1_Phone_Perepel_2_1')
        kb.add(k4, k1, k2)
        bot.send_location(callback.message.chat.id, 55.77304910483791, 37.609577955608)
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)

    elif callback.data == '2_1_Info_Black_Hat_Balchug_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Фотографии', callback_data='1_1_Black_Hat_Balchug_Photo_2_1')
        k2 = types.InlineKeyboardButton(text='Геолокация', callback_data='1_1_Black_Hat_Balchug_Location_2_1')
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='1_1_Bar_Info_2_1')
        kb.add(k1, k2, k3)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text="Москва, ул. Балчуг, 5\nТел: +7 (965) 305 1514\nНП-ЧТ: 12:00 - 24:00;\nПТ-СБ: 12:00 - 2:00\nВС: 12:00 - 24:00\nБар Black Hat Bar расположился в гастромаркете «Балчуг». Это первый карибский паб на гастромаркетке. Здесь можно попробовать яркие тики-коктейли от Дмитрия Соколова.", reply_markup=kb)

    elif callback.data == '1_1_Black_Hat_Balchug_Photo_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')  #
        k3 = types.InlineKeyboardButton(text='Назад', callback_data='2_1_Info_Black_Hat_Balchug_2_1')
        kb.add(k1, k2, k3)
        file = open('black_hat_balch_ph.jpg', 'rb')
        bot.send_photo(callback.message.chat.id, file)
        file.close()
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)

    elif callback.data == '1_1_Black_Hat_Balchug_Location_2_1':
        kb = types.InlineKeyboardMarkup(row_width=1)
        k1 = types.InlineKeyboardButton(text='К списку заведений', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        k4 = types.InlineKeyboardButton(text='Телефон', callback_data='2_1_Phone_Black_Hat_Balchug_2_1')  ####
        kb.add(k4, k1, k2)
        bot.send_location(callback.message.chat.id, 55.747223373703704, 37.62598043908848)
        bot.send_message(callback.message.chat.id, 'Выберите', reply_markup=kb)

    elif callback.data == '1_1_Menu_User_1_1':
        kb1 = types.InlineKeyboardMarkup()
        kb2 = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Зарегистрироваться', callback_data='1Registration1')
        k2 = types.InlineKeyboardButton(text='Информация о барах', callback_data='1_1_Bar_Info_2_1')
        k3 = types.InlineKeyboardButton(text='Карта', callback_data='1_1_Check_Card_2_1')
        kb1.add(k1, k2)
        kb2.add(k3, k2)
        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT name FROM guest WHERE mess_id = {callback.message.chat.id}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        if temp:
            bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f"Здравствуйте, {temp[0]}!", reply_markup=kb2)

        else:
            bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text='У Вас пока нет скидочной карты, но вы можете её получить, пройдя короткую регистрацию',
                         reply_markup=kb1)

    elif callback.data == '2_1_Phone_Help_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Бары', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        kb.add(k1, k2)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f"Телефон:\n+7 (495) 627 6736", reply_markup=kb)

    elif callback.data == '2_1_Phone_Stay_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Бары', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        kb.add(k1, k2)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Телефон:\n+7 (495) 784 6838", reply_markup=kb)

    elif callback.data == '2_1_Phone_Black_Hat_Sadovoe_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Бары', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        kb.add(k1, k2)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Телефон:\n+7 (495) 148 4388", reply_markup=kb)

    elif callback.data == '2_1_Phone_LowSon_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Бары', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        kb.add(k1, k2)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Телефон:\n+7 (495) 649 0189", reply_markup=kb)

    elif callback.data == '2_1_Phone_Perepel_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Бары', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        kb.add(k1, k2)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Телефон:\n+7 (495) 032 1700", reply_markup=kb)

    elif callback.data == '2_1_Phone_Black_Hat_Balchug_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text='Бары', callback_data='1_1_Bar_Info_2_1')
        k2 = types.InlineKeyboardButton(text='В начало', callback_data='1_1_Menu_User_1_1')
        kb.add(k1, k2)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Телефон:\n+7 (965) 305 1514", reply_markup=kb)

#Отправка изображения и номера карты пользователю
    elif callback.data == '1_1_Check_Card_2_1':
        kb = types.InlineKeyboardMarkup()
        k1 = types.InlineKeyboardButton(text="Бары", callback_data='1_1_Bar_Info_2_1')
        kb.add(k1)

        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT sale, id_user FROM guest WHERE mess_id = {callback.message.chat.id}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        if temp[0] == 10:
            file = open('10.jpg', 'rb')
            bot.send_photo(callback.message.chat.id, file, f"Карта № {str(temp[1]).rjust(6, '0')}")
            file.close()
        elif temp[0] == 20:
            file = open('20.jpg', 'rb')
            bot.send_photo(callback.message.chat.id, file, f"Карта № {str(temp[1]).rjust(6, '0')}")
            file.close()
        elif temp[0] == 30:
            file = open('30.jpg', 'rb')
            bot.send_photo(callback.message.chat.id, file, f"Карта № {str(temp[1]).rjust(6, '0')}")
            file.close()
        elif temp[0] == 40:
            file = open('40.jpg', 'rb')
            bot.send_photo(callback.message.chat.id, file, f"Карта № {str(temp[1]).rjust(6, '0')}")
            file.close()
        elif temp[0] == 50:
            file = open('50.jpg', 'rb')
            bot.send_photo(callback.message.chat.id, file, f"Карта № {str(temp[1]).rjust(6, '0')}")
            file.close()
        elif temp[0] == 'Анулирована':
            bot.send_message(callback.message.chat.id,
                             f"Карта № {str(temp[1]).rjust(6, '0')} АНУЛИРОВАНА")
        bot.send_message(callback.message.chat.id, ":-)", reply_markup=kb)

#Повторный поиск пользователя по номеру карты
    elif callback.data == '2_1_Search_num_card_2_1':
        sent = bot.send_message(callback.message.chat.id, 'Введите номер карты')
        bot.register_next_step_handler(sent, card_test)

#Удаление пользователя
    elif callback.data == '3_delete_user_3-1':
        kb = types.InlineKeyboardMarkup()
        k2 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
        kb.add(k2)
        t = Temp.user_edit5
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE guest SET sale = "Анулирована" WHERE id_user = {t};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'SELECT surname, name, date_b, id_user, sale FROM guest  WHERE id_user = {t};'
        cur.execute(sql_t)
        i = cur.fetchone()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]}", reply_markup=kb)

#Ввод номера карты для удаления пользователя
def delete_user(message):
    kb = types.InlineKeyboardMarkup()
    k1 = types.InlineKeyboardButton(text='Удалить', callback_data='3_delete_user_3-1')
    k2 = types.InlineKeyboardButton(text='Отмена', callback_data='/sokol')
    kb.add(k1, k2)

    if message.content_type == 'text' and message.text.isdigit():
        t = int(message.text)
        Temp.user_edit5 = t

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'SELECT surname, name, date_b, id_user, sale FROM guest  WHERE id_user = {t};'
        cur.execute(sql_t)
        i = cur.fetchone()
        cur.close()
        conn.close()

        bot.send_message(message.chat.id, f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:]}-{i[2][5:7]}-{i[2][0:4]}\nКарта номер: {str(i[3]).rjust(6, '0')}\nСкидка: {i[4]} %", reply_markup=kb)
    else:
        sent = bot.send_message(message.chat.id, 'Введите номер карты')
        bot.register_next_step_handler(sent, delete_user)

#Ввод номера карты для изменения скидки
def f_num_sale(message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    k1 = types.InlineKeyboardButton(text='10%', callback_data='2_edit_guest_sale_10_1')
    k2 = types.InlineKeyboardButton(text='20%', callback_data='1_edit_guest_sale_20_1')
    k3 = types.InlineKeyboardButton(text='30%', callback_data='11_edit_guest1_sale_30_2')
    k4 = types.InlineKeyboardButton(text='40%', callback_data='1_edit_guest_sale_40_11')
    k5 = types.InlineKeyboardButton(text='50%', callback_data='1_edit_guest_sale_50_12')
    kb.add(k1, k2, k3, k4, k5)

    if message.content_type == 'text' and message.text.isdigit():
        t = int(message.text)
        Temp.user_edit4 = t

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'SELECT surname, name, date_b, id_user, sale FROM guest  WHERE id_user = {t};'
        cur.execute(sql_t)
        temp = cur.fetchone()
        cur.close()
        conn.close()

        bot.send_message(message.chat.id,
                         f"Фамилия: {temp[0]}\nИмя: {temp[1]}\nДата рождения: {temp[2][8:]}-{temp[2][5:7]}-{temp[2][0:4]}\nКарта номер: {str(temp[3]).rjust(6, '0')}\nСкидка: {temp[4]}%\nВыберите размер скидку", reply_markup=kb)
    else:
        sent = bot.send_message(message.chat.id, 'Введите номер карты')
        bot.register_next_step_handler(sent, f_num_sale)

#Изменение фамилии Администратора
def create_admin_1(message):
    adm = Temp.admin_id
    if message.content_type == 'text' and message.text.isalpha():
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET surname = "{message.text.title()}", action = "Активен" WHERE id_admin = {int(adm)};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()
        sent = bot.send_message(message.chat.id, 'Введите имя')
        bot.register_next_step_handler(sent, create_admin_2)
    else:
        sent = bot.send_message(message.chat.id, 'Введите фамилию')
        bot.register_next_step_handler(sent, create_admin_1)

#Изменение имени Администратора и выбор заведения
def create_admin_2(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    k1 = types.InlineKeyboardButton(text="Mr. Help & Friends", callback_data='21_Help_2')
    k2 = types.InlineKeyboardButton(text="Stay True", callback_data='21_stay_2')
    k3 = types.InlineKeyboardButton(text="Black Hat (САДОВОЕ)", callback_data='21_black_sad_2')
    k4 = types.InlineKeyboardButton(text="Black Hat (БАЛЧУГ)", callback_data='21_black_balch_2')
    k5 = types.InlineKeyboardButton(text="Lawson's", callback_data='21_lawson_2')
    k6 = types.InlineKeyboardButton(text="Перепел", callback_data='21_PerepeL_2')
    kb.add(k1, k2, k3, k4, k5, k6)
    adm = Temp.admin_id
    if message.content_type == 'text' and message.text.isalpha():
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET name = "{message.text.title()}" WHERE id_admin = {int(adm)};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(message.chat.id, 'Выберите заведение', reply_markup=kb)

    else:
        sent = bot.send_message(message.chat.id, 'Введите имя')
        bot.register_next_step_handler(sent, create_admin_2)

#Поиск Администратора по id
def s_admin_id(message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    k1 = types.InlineKeyboardButton(text= 'Активировать', callback_data='1_admin_action_OK_2')
    k2 = types.InlineKeyboardButton(text='Деактивировать', callback_data='1_admin_action_NO_1_2')
    k5 = types.InlineKeyboardButton(text='Назад', callback_data='/sokol')
    k4 = types.InlineKeyboardButton(text='Именить данные', callback_data='1_admin_data_create_2')
    kb1 = types.InlineKeyboardMarkup()
    k11 = types.InlineKeyboardButton(text='Найти заново', callback_data='1_search_admin__id_1')
    k12 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
    kb.add(k1, k2, k4, k5)
    kb1.add(k11, k12)
    if message.content_type == 'text' and message.text.isdigit():
        Temp.admin_id = message.text
        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT id_admin, surname, name, bar, action FROM admin WHERE id_admin = {int(message.text)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        if temp:
            bot.send_message(message.chat.id, f'Администратор\nФамилия: {temp[1]}\nИмя: {temp[2]}\nЗаведение: {temp[3]}\nID: {str(temp[0]).rjust(4, "0")}\nАктивность: {temp[4]}', reply_markup=kb)
        else:
            bot.send_message(message.chat.id,
                         'Администратор не найден', reply_markup=kb1)
    else:
        sent = bot.send_message(message.chat.id, 'Введите ID администратора')
        bot.register_next_step_handler(sent, s_admin_id)

#Добавление фамилии, id, mess_id Администратора
def reg_admin_1(message):
    if message.content_type == 'text' and message.text.isalpha():
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        temp = (message.chat.id, message.text.title())
        sql_t = """INSERT INTO admin (mess_id, surname) VALUES(?, ?);"""
        cur.execute(sql_t, temp)
        conn.commit()
        cur.close()
        conn.close()
        sent = bot.send_message(message.chat.id, 'Введите Ваше имя')
        bot.register_next_step_handler(sent, reg_admin_2)
    else:
        sent = bot.send_message(message.chat.id, 'Введите Вашу фамилию')
        bot.register_next_step_handler(sent, reg_admin_1)



#Изменение фамилии Администратора
def reg_admin_3(message):
    if message.content_type == 'text' and message.text.isalpha():
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET surname = "{message.text.title()}" WHERE mess_id = {message.chat.id};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()
        sent = bot.send_message(message.chat.id, 'Введите Ваше имя')
        bot.register_next_step_handler(sent, reg_admin_2)
    else:
        sent = bot.send_message(message.chat.id, 'Введите Вашу фамилию')
        bot.register_next_step_handler(sent, reg_admin_3)



#Запись имени Администратора
def reg_admin_2(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    k1 = types.InlineKeyboardButton(text="Mr. Help & Friends", callback_data='1_Help_1')
    k2 = types.InlineKeyboardButton(text="Stay True", callback_data='1_Stay_True_2')
    k3 = types.InlineKeyboardButton(text="Black Hat (САДОВОЕ)", callback_data='1_Black_Hat_2')
    k4 = types.InlineKeyboardButton(text="Black Hat (БАЛЧУГ)", callback_data='2_Black_Hat_balch_3_2')
    k5 = types.InlineKeyboardButton(text="Lawson's", callback_data='1_Lawsons_2')
    k6 = types.InlineKeyboardButton(text="Перепел", callback_data='1_Perepel_1_2')
    kb.add(k1, k2, k3, k4, k5, k6)
    if message.content_type == 'text' and message.text.isalpha():
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE admin SET name = "{message.text.title()}" WHERE mess_id = {message.chat.id};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(message.chat.id, 'Выберите заведение, в котором Вы работаете', reply_markup=kb)
    else:
        sent = bot.send_message(message.chat.id, 'Введите Ваше имя')
        bot.register_next_step_handler(sent, reg_admin_2)

#Поиск пользователей по имени
def find_lname(message):
    kb1 = types.InlineKeyboardMarkup()
    kb = types.InlineKeyboardMarkup()
    k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
    k2 = types.InlineKeyboardButton(text='Найти заново', callback_data='1find_guest1')
    k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
    kb.add(k1, k2, k3)
    kb1.add(k2, k3)
    if message.content_type == 'text' and message.text.isalpha():
        sur = message.text.lower().replace("ё", "е")
        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, date_b, sale, id_user FROM guest WHERE name = '{sur.title()}'"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()
        if temp:
            for i in temp:
                bot.send_message(message.chat.id,
                                 f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:10]}-{i[2][5:7]}-{i[2][0:4]}\n<b>Скидка: {i[3]}%</b>\nНомер карты: {str(i[4]).rjust(5, '0')}",
                                 parse_mode='HTML')
            bot.send_message(message.chat.id, 'Чтобы изменить данные, запомните номер карты гостя и нажмите "Изменить"',
                             reply_markup=kb)
        else:
            bot.send_message(message.chat.id,
                             'Гость не найден', reply_markup=kb1)
    else:
        sent3 = bot.send_message(message.chat.id, "Введите фамилию")
        bot.register_next_step_handler(sent3, find_lname)

#Поиск по фамилии пользователя
def find_fname(message):
    kb1 = types.InlineKeyboardMarkup()
    kb = types.InlineKeyboardMarkup()
    k1 = types.InlineKeyboardButton(text='Изменить', callback_data='1_find_num_1')
    k2 = types.InlineKeyboardButton(text='Найти заново', callback_data='1find_guest1')
    k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
    kb.add(k1, k2, k3)
    kb1.add(k2, k3)
    if message.content_type == 'text' and message.text.isalpha():
        sur = message.text.lower().replace("ё", "е")
        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, date_b, sale, id_user FROM guest WHERE surname = '{sur.title()}'"
        cur.execute(sql)
        temp = cur.fetchall()
        cur.close()
        conn.close()
        if temp:
            for i in temp:

                bot.send_message(message.chat.id,
                             f"Фамилия: {i[0]}\nИмя: {i[1]}\nДата рождения: {i[2][8:10]}-{i[2][5:7]}-{i[2][0:4]}\n<b>Скидка: {i[3]}%</b>\nНомер карты: {str(i[4]).rjust(5,'0')}",
                             parse_mode='HTML')
            bot.send_message(message.chat.id, 'Чтобы изменить данные, запомните номер карты гостя и нажмите "Изменить"',
                             reply_markup=kb)
        else:
            bot.send_message(message.chat.id,
                         'Гость не найден', reply_markup=kb1)
    else:
        sent3 = bot.send_message(message.chat.id, "Введите фамилию")
        bot.register_next_step_handler(sent3, find_fname)

#Ввод фамилии пользователя Администратором при редактировании
def edit_data(message):
    kb = types.InlineKeyboardMarkup()
    k1 = types.InlineKeyboardButton(text='В начало', callback_data='/sokol')
    kb.add(k1)
    if message.content_type == 'text' and message.text.isdigit():
        Temp.user_edit1 = int(message.text)
        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, date_b, sale FROM guest WHERE id_user = {int(message.text)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        if temp:
            sent2 = bot.send_message(message.chat.id, f"Фамилия: {temp[0]}\nИмя: {temp[1]}\nДата рождения: {temp[2][8:10]}-{temp[2][5:7]}-{temp[2][0:4]}\nСкидка: {temp[3]}\nВведите фамилию")
            bot.register_next_step_handler(sent2, edit_data_22)
        else:
            bot.send_message(message.chat.id, 'Данной карты не существует', reply_markup=kb)
    else:
        sent3 = bot.send_message(message.chat.id, "Введите номер карты")
        bot.register_next_step_handler(sent3, edit_data)

#Изменение фамилии пользователя Администратором при редактировании и ввод имени
def edit_data_22(message):
    n = Temp.user_edit1
    if message.content_type == 'text' and message.text.isalpha():
        sur = message.text.lower().replace("ё", "е")
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE guest SET surname = "{sur.title()}" WHERE id_user = {n};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()
        Temp.user_edit2 = n
        sent3 = bot.send_message(message.chat.id, "Введите имя")
        bot.register_next_step_handler(sent3, edit_data_33)

    else:
        sent2 = bot.send_message(message.chat.id, "Введите фамилию")
        bot.register_next_step_handler(sent2, edit_data_22)

#Изменение имени пользователя Администратором и ввод даты рождения
def edit_data_33(message):
    n = Temp.user_edit2
    if message.content_type == 'text' and message.text.isalpha():
        sur = message.text.lower().replace("ё", "е")
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE guest SET name = "{sur.title()}" WHERE id_user = {n};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()
        Temp.user_edit3 = n
        sent3 = bot.send_message(message.chat.id, "Введите дату рождения в формате ДД.ММ.ГГГГ")
        bot.register_next_step_handler(sent3, edit_data_3)

    else:
        sent2 = bot.send_message(message.chat.id, "Введите имя")
        bot.register_next_step_handler(sent2, edit_data_33)

#Изменение даты рождения пользователя Администратором, подтверждение\исправление
def edit_data_3(message):
    n = Temp.user_edit3
    kb = types.InlineKeyboardMarkup()
    k1 = types.InlineKeyboardButton(text='ОК, всё верно!', callback_data='/sokol')
    k2 = types.InlineKeyboardButton(text='ОШИБКА, исправить', callback_data='2_edit_guest_data_2')
    kb.add(k1, k2)
    if message.content_type == 'text' and re.match(r'((?:\d)|(?:\d){2})[-\.\\/_]((?:\d)|(?:\d){2})[-\.\\/_](?:\d){4}',
                                                   message.text):
        d = re.search(r'\A(?:\d){0,2}', message.text)
        m = re.search(r'(\b(?:\d){0,2})(?=[-\.\\/_]\d\d\d\d)', message.text)
        y = re.search(r'(?:\d){4}', message.text)
        if (int(m[0]) in [1, 3, 5, 7, 8, 10, 12] and int(d[0]) <= 31) or (
                int(m[0]) in [4, 6, 9, 11] and int(d[0]) <= 30) or (int(m[0]) == 2 and int(d[0]) <= 29):
            date_e = datetime.date(int(y[0]), int(m[0]), int(d[0]))
            conn = sqlite3.connect("guests.db")
            cur = conn.cursor()
            sql_t = f'UPDATE guest SET date_b = "{date_e}" WHERE id_user = {n};'
            cur.execute(sql_t)
            conn.commit()
            cur.close()
            conn.close()

            conn = sqlite3.connect('guests.db')
            cur = conn.cursor()
            sql = f"SELECT surname, name, date_b, sale FROM guest WHERE id_user = {n}"
            cur.execute(sql)
            temp = cur.fetchone()
            cur.close()
            conn.close()
            bot.send_message(message.chat.id, f'Поверьте:\nФамилия: {temp[0]}\nИмя: {temp[1]}\nДата рождения: {temp[2][8:10]}-{temp[2][5:7]}-{temp[2][0:4]}\nСкидка: {temp[3]}\nНомер карты: {str(n).rjust(5,"0")}', reply_markup=kb)
        else:
            sent3 = bot.send_message(message.chat.id, "Введите дату рождения в формате ДД.ММ.ГГГГ")
            bot.register_next_step_handler(sent3, edit_data_3)
    else:
        sent3 = bot.send_message(message.chat.id, "Введите дату рождения в формате ДД.ММ.ГГГГ")
        bot.register_next_step_handler(sent3, edit_data_3)

#Поиск по номеру карты для Администратора
def find_ncard(message):
    kb = types.InlineKeyboardMarkup()
    kb1 = types.InlineKeyboardMarkup()
    k1 = types.InlineKeyboardButton(text='Изменить', callback_data='2_edit_guest_2')
    k2 = types.InlineKeyboardButton(text='Найти заново', callback_data='1find_guest1')
    k3 = types.InlineKeyboardButton(text='OK', callback_data='/sokol')
    kb.add(k1, k2, k3)
    kb1.add(k2, k3)
    if message.content_type == 'text' and message.text.isdigit():
        conn = sqlite3.connect('guests.db')
        cur = conn.cursor()
        sql = f"SELECT surname, name, date_b, sale FROM guest WHERE id_user = {int(message.text)}"
        cur.execute(sql)
        temp = cur.fetchone()
        cur.close()
        conn.close()
        if temp:
            Temp.user_edit4= int(message.text)
            bot.send_message(message.chat.id, f"Фамилия: {temp[0]}\nИмя: {temp[1]}\nДата рождения: {temp[2][8:10]}-{temp[2][5:7]}-{temp[2][0:4]}\n<b>Скидка: {temp[3]}%</b>\n<b>Номер карты: {message.text.rjust(6,'0')}</b>\nЧтобы изменить данные, запомните номер карты гостя",
                                     parse_mode='HTML', reply_markup=kb)
        else:
            bot.send_message(message.chat.id,
                             'Гость не найден', reply_markup=kb1)
    else:
        sent3 = bot.send_message(message.chat.id, "Введите номер карты")
        bot.register_next_step_handler(sent3, find_ncard)

#Отправка сообщений всем пользователям, РАССЫЛКА
def send_all(message):
    l = []
    conn = sqlite3.connect('guests.db')
    cur = conn.cursor()
    sql = """SELECT mess_id FROM guest"""
    cur.execute(sql)
    temp = cur.fetchall()
    cur.close()
    conn.close()

    for i in temp:
        l.append(i[0])
    if message.photo != None:
        for i in l:
            bot.send_photo(i, message.photo[0].file_id, caption=message.caption)
    elif message.text != None:
        for i in l:
            bot.send_message(i, message.text)
    elif message.animation != None:
        for i in l:
            bot.send_animation(i, message.document.file_id)
    elif message.sticker != None:
        for i in l:
            bot.send_animation(i, message.sticker.file_id)
    elif message.video != None:
        for i in l:
            bot.send_video(i, message.video.file_id, caption=message.caption)
    elif message.audio != None:
        for i in l:
            bot.send_audio(i, message.audio.file_id, caption=message.caption)
    elif message.voice != None:
        for i in l:
            bot.send_voice(i, message.voice.file_id, caption=message.caption)
    elif message.contact != None:
        for i in l:
            bot.send_contact(i, phone_number=message.contact.phone_number, first_name=message.contact.first_name, last_name=message.contact.last_name)
    elif message.document != None:
        for i in l:
            bot.send_document(i, message.document.file_id, caption=message.caption)
    elif message.location != None:
        x = message.location.longitude
        y = message.location.latitude
        for i in l:
            bot.send_location(i, y, x)
    elif message.poll != None:
        for i in l:
            bot.send_poll(i, options=message.poll.options, question=message.poll.question)
    else:
        bot.send_message(message.chat.id, 'ОЙ')

#Добавление фамилии и mess_id пользователя
def review1(message):
    if message.content_type == 'text' and message.text.isalpha():
        surname_save = message.text.title()

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        t_us = (message.chat.id, surname_save, 10)
        sql_t = """INSERT INTO guest (mess_id,
                surname, sale
                ) VALUES(?, ?, ?)"""
        cur.execute(sql_t, t_us)
        conn.commit()
        cur.close()
        conn.close()

        sent2 = bot.send_message(message.chat.id, "Введите Имя")
        bot.register_next_step_handler(sent2, review2)
    else:
        sent = bot.send_message(message.chat.id, 'Так не бывает, введите Вашу фамилию')
        bot.register_next_step_handler(sent, review1)

#Добавление имени пользователя
def review2(message):
    if message.content_type == 'text' and message.text.isalpha():
        name_save = message.text.title()

        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f'UPDATE guest SET name = "{name_save}" WHERE mess_id = {message.chat.id};'
        cur.execute(sql_t)
        conn.commit()
        cur.close()
        conn.close()
        sent3 = bot.send_message(message.chat.id, "Введите Вашу дату рождения в формате ДД.ММ.ГГГГ")
        bot.register_next_step_handler(sent3, review3)

    else:
        sent = bot.send_message(message.chat.id, 'Так не бывает, введите Ваше имя')
        bot.register_next_step_handler(sent, review2)

#Внесение даты рождения пользователя
def review3(message):
    kb = types.InlineKeyboardMarkup()
    k1 = types.InlineKeyboardButton(text='ОК, всё верно!', callback_data='2Registration2')
    k2 = types.InlineKeyboardButton(text='ОШИБКА, исправить', callback_data='1Registration1')
    kb.add(k1, k2)
    if message.content_type == 'text' and re.match(r'((?:\d)|(?:\d){2})[-\.\\/_]((?:\d)|(?:\d){2})[-\.\\/_](?:\d){4}', message.text):
        d = re.search(r'\A(?:\d){0,2}', message.text)
        m = re.search(r'(\b(?:\d){0,2})(?=[-\.\\/_]\d\d\d\d)', message.text)
        y = re.search(r'(?:\d){4}', message.text)
        if (int(m[0]) in [1, 3, 5, 7, 8, 10, 12] and int(d[0]) <= 31) or (int(m[0]) in [4, 6, 9, 11] and int(d[0]) <= 30) or (int(m[0]) == 2 and int(d[0]) <= 29):
            date_bs = datetime.date(int(y[0]), int(m[0]), int(d[0]))
            diff_date = datetime.date.today() - datetime.timedelta(days=6570)
            if date_bs <= diff_date:
                conn = sqlite3.connect("guests.db")
                cur = conn.cursor()
                sql_t = f"UPDATE guest SET date_b = '{date_bs}' WHERE mess_id = {message.chat.id};"
                cur.execute(sql_t)
                conn.commit()
                cur.close()
                conn.close()

                conn = sqlite3.connect("guests.db")
                cur = conn.cursor()
                sql_t = f"SELECT surname, name, date_b FROM guest WHERE mess_id = {message.chat.id};"
                cur.execute(sql_t)
                temp = cur.fetchone()
                cur.close()
                conn.close()
                bot.send_message(message.chat.id, f'Проверьте:\nФамилия: {temp[0]}\nИмя: {temp[1]}\nДата рождения: {temp[2][8:10]}-{temp[2][5:7]}-{temp[2][0:4]}' , reply_markup=kb)
            else:
                sent = bot.send_message(message.chat.id, "Вам меньше 18?")
                bot.register_next_step_handler(sent, review3)
        else:
            sent = bot.send_message(message.chat.id,
                                    "Введите Вашу дату рождения в формате ДД.ММ.ГГГГ")
            bot.register_next_step_handler(sent, review3)
    else:
        sent = bot.send_message(message.chat.id, "Введите Вашу дату рождения в формате ДД.ММ.ГГГГ")
        bot.register_next_step_handler(sent, review3)

#Проверка карты пользователя
def card_test(message):
    kb = types.InlineKeyboardMarkup()
    k1 = types.InlineKeyboardButton(text='Найти ещё', callback_data='2_1_Search_num_card_2_1')
    kb.add(k1)
    if message.content_type == 'text' and message.text.isdigit():
        conn = sqlite3.connect("guests.db")
        cur = conn.cursor()
        sql_t = f"SELECT surname, name, date_b, sale FROM guest WHERE id_user = {message.text};"
        cur.execute(sql_t)
        temp = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if temp:
            bot.send_message(message.chat.id, f'Фамилия: {temp[0]}\nИмя: {temp[1]}\nДата рождения: {temp[2][8:10]}-{temp[2][5:7]}-{temp[2][0:4]}\nСкидка: {temp[3]}%', reply_markup=kb)
        else:
            bot.send_message(message.chat.id, 'Карта не найдена', reply_markup=kb)
    else:
        sent = bot.send_message(message.chat.id, 'Введите номер карты')
        bot.register_next_step_handler(sent, card_test)

#Автоматическое поздравление м Д.Р.
def congrat():
    kb = types.InlineKeyboardMarkup(row_width=1)
    k1 = types.InlineKeyboardButton(text="Mr. Help & Friend's", callback_data='1_1_Bar_Info_2_1')
    kb.add(k1)
    a = datetime.date.today()
    b = datetime.date.today() + datetime.timedelta(days=3)
    l = []
    l1 = []
    for i in a.timetuple():
        l.append(i)
    for i in b.timetuple():
        l1.append(i)

    conn = sqlite3.connect('guests.db')
    cur = conn.cursor()
    sql = f"SELECT name, date_b, mess_id FROM guest"
    cur.execute(sql)
    temp = cur.fetchall()
    cur.close()
    conn.close()
    for i in temp:
        if int(i[1][5:7]) == l[1] and int(i[1][8:]) == l[2]:
            bot.send_message(i[2], f"{l[0]}, поздравляем Вас с Днём Рождения!!!\nВ наших барах скидка 30%!!!", reply_markup=kb)
        elif int(i[1][5:7]) == l1[1] and int(i[1][8:]) == l1[2]:
            bot.send_message(i[2], f"{l[0]}, поздравляем Вас с наступающим Днём Рождения!!!\nВ наших барах скидка 30%!!!", reply_markup=kb)

#Ответ на любое сообщение
@bot.message_handler(func=lambda x: True)
def start(message):
    kb1 = types.InlineKeyboardMarkup()
    kb2 = types.InlineKeyboardMarkup()
    kb3 = types.InlineKeyboardMarkup(row_width=1)
    kb4 = types.InlineKeyboardMarkup(row_width=1)
    k1 = types.InlineKeyboardButton(text='Зарегистрироваться', callback_data='1Registration1')
    k2 = types.InlineKeyboardButton(text='Информация о барах', callback_data='1_1_Bar_Info_2_1')
    k3 = types.InlineKeyboardButton(text='Карта', callback_data='1_1_Check_Card_2_1')
    k11 = types.InlineKeyboardButton(text='РАССЫЛКА', callback_data='1send_all1')
    k22 = types.InlineKeyboardButton(text='УПРАВЛЕНИЕ КАРТАМИ', callback_data='1_Card_Contol_1_1')
    k33 = types.InlineKeyboardButton(text='УПРАВЛЕНИЕ АДМИНИСТРАТОРАМИ', callback_data='1_2_Admin_Contol_1_1')
    kb1.add(k1, k2)
    kb2.add(k3, k2)
    kb3.add(k11, k22, k33)
    kb4.add(k11, k22)

    conn = sqlite3.connect('guests.db')
    cur = conn.cursor()
    sql = f"SELECT action, id_admin FROM admin WHERE mess_id = {message.chat.id}"
    cur.execute(sql)
    temp = cur.fetchone()
    cur.close()
    conn.close()

    conn = sqlite3.connect('guests.db')
    cur = conn.cursor()
    sql = f"SELECT name FROM guest WHERE mess_id = {message.chat.id}"
    cur.execute(sql)
    temp1 = cur.fetchone()
    cur.close()
    conn.close()
    if message.chat.id == 572750004:     #!!!!!!!!ЗАМЕНИТЬ!!!!!
        bot.send_message(message.chat.id, f"Здравствуйте", reply_markup=kb3)
    elif temp[0] == 'Активен':
        bot.send_message(message.chat.id, 'Здравствуйте', reply_markup=kb4)
    elif temp[0] == 'Неактивен':
        bot.send_message(message.chat.id, f"Профиль не подтвержден\nВаш ID: {str(temp[1]).rjust(4, '0')}")

    elif temp1:
        bot.send_message(message.chat.id, f"Здравствуйте, {temp1[0]}!", reply_markup=kb2)
    else:
        bot.send_message(message.chat.id, 'У Вас пока нет скидочной карты, но вы можете её получить, пройдя короткую регистрацию', reply_markup=kb1)

bot.polling()