import os
import config
import pymysql
import requests
import telebot
from bs4 import BeautifulSoup as BS
from telebot import types
bot = telebot.TeleBot(config.telebot_key)

try:
    db = pymysql.connect(
        host=config.host,
        port=3306,
        user=config.user,
        password=config.password,
        database=config.db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
except Exception as ex:
    print(ex)

def keyboard_start():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Создали клавиатуру
    d = {
        '1': "Мой профиль",
        '2': "Изменить логин, пароль",
        '3': "просто кнопка",
        '4': "Изменить жизни",
        '5': "Выгрузить домашку"
    }
    # Наполнили ее кнопками
    for i in d:
        if int(i) % 2 == 1 and int(i) < 5:
            markup.add(types.KeyboardButton(d[i]), types.KeyboardButton(d[str(int(i) + 1)]))
        elif i == '5':
            markup.add(types.KeyboardButton(d[i]))
    return markup  # Отправили


def keyboard_lk():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    d = {
        '1': "Изменить модуль",
        '2': "Настройки выгрузки",
        '3': "Изменить курс",
        '4': "Изменить группу",
        '5': "Назад",
    }

    for i in d:
        if int(i) % 2 == 1 and int(i) < 5:
            markup.add(types.KeyboardButton(d[i]), types.KeyboardButton(d[str(int(i) + 1)]))
        elif i == '5':
            markup.add(types.KeyboardButton(d[i]))

    return markup


def inlinekeyboard_settings(user_id):
    d = {
        '1': "Ссылка на дз: ",
        '2': "Отправлено на проверку: ",
        '3': "Процент выполнения ДЗ: ",
        '4': "Проверка от куратора: ",
        '5': "Тестовая часть: ",
        '6': "Назад"
    }
    keyboard = types.InlineKeyboardMarkup()  # Создали inlinekeyboard
    with db.cursor() as cursor:
        insert_query = "SELECT url_homework, test_part, curators_check, percent_of_completion, time_homework FROM parsing_settings WHERE user_id = " + str(
            user_id)  # Достали нужные строки из БД
        cursor.execute(insert_query)
        results = cursor.fetchall()

        if results[0]["url_homework"] == 0:
            keyboard.add(types.InlineKeyboardButton(text=d['1'] + str('False\n'), callback_data=53))
        else:
            keyboard.add(types.InlineKeyboardButton(text=d['1'] + str('True\n'), callback_data=54))

        if results[0]["time_homework"] == 0:
            keyboard.add(types.InlineKeyboardButton(text=d['2'] + str('False\n'), callback_data=55))
        else:
            keyboard.add(types.InlineKeyboardButton(text=d['2'] + str('True\n'), callback_data=56))

        if results[0]["percent_of_completion"] == 0:
            keyboard.add(types.InlineKeyboardButton(text=d['3'] + str('False\n'), callback_data=57))
        else:
            keyboard.add(types.InlineKeyboardButton(text=d['3'] + str('True\n'), callback_data=58))

        if results[0]["curators_check"] == 0:
            keyboard.add(types.InlineKeyboardButton(text=d['4'] + str('False\n'), callback_data=59))
        else:
            keyboard.add(types.InlineKeyboardButton(text=d['4'] + str('True\n'), callback_data=60))

        if results[0]["test_part"] == 0:
            keyboard.add(types.InlineKeyboardButton(text=d['5'] + str('False\n'), callback_data=61))
        else:
            keyboard.add(types.InlineKeyboardButton(text=d['5'] + str('True\n'), callback_data=62))

        keyboard.add(types.InlineKeyboardButton(text=d['6'], callback_data=99))
        #################Добавили все кнопки и вернули клавиатуру
    return keyboard


def inline_students_lifes(user_id, cource_id):
    keyboard = types.InlineKeyboardMarkup()
    with db.cursor() as cursor:
        select_query = "SELECT name_student,count_lifes,student_id FROM students_list WHERE curator_id = '" + str(
            user_id) + "' AND cource_id = '" + str(cource_id) + "'"
        cursor.execute(select_query)
        results = cursor.fetchall()
        for x in results:
            keyboard.add(
                types.InlineKeyboardButton(text=x["name_student"] + " | Количество жизней: " + str(x["count_lifes"]),
                                           callback_data=x["student_id"]))
        keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="close_inline_students_lifes"))
    return keyboard


def inline_students_lifes_dop(user_id, cource_id):
    keyboard = types.InlineKeyboardMarkup()

    with db.cursor() as cursor:
        select_query = "SELECT selected_cource_id FROM user WHERE userId = " + str(user_id)
        cursor.execute(select_query)
        result = cursor.fetchall()
        _selected_course = result[0]["selected_cource_id"]

    payload = authorization_on_api(user_id)
    with requests.session() as session:
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get(
            "https://api.100points.ru/user/index?email=&name=&vk_id=&registration_date=&course_id="+str(_selected_course)+"&authorization_variant=",
            data=payload)
        html_after_authorization = BS(response.content, 'html.parser')
        current_class_page_link = ""
        prev_class_page_link = ""
        try:
            for i in html_after_authorization.select(".pagination"):
                d1 = i.find_all("a", class_="page-link")  # Ищем все строчки html кода с нумерацией страниц
                for j in d1:
                    prev_class_page_link = current_class_page_link  # Запоминаем текущую страницу и предыдущую, т.к самый последний html код - это кнопка Next
                    current_class_page_link = j
            count_pages = int(((prev_class_page_link.text).replace(' ', '')))  # Убираем пробельчики
        except Exception as ex:
            count_pages = 1
        for i in range(1, count_pages+1):
            response = session.get("https://api.100points.ru/user/index?course_id="+str(_selected_course)+"&export_type=all&page=" + str(i))
            html = BS(response.content, 'html.parser')
            for el in html.select(".odd"):
                url_user_link = el.find("a", class_="btn btn-xs bg-blue").get("href")
                student_id = url_user_link[35:]
                response = session.get(url_user_link)
                html = BS(response.content, 'html.parser')
                username = html.select(".form-control")[4].get("value")
                count = 0
                for x in html.select("td", class_="odd"):
                    if (str(cource_id) in x.find("a").get("href")):
                        #print(str(html.select("td", class_="odd")[count + 1].select("b"))[4], url_user_link)
                        #print((html.select("td", class_="odd")[count + 1].select("b"))[4])
                        try:
                            count_lifes = str(html.select("td", class_="odd")[count + 1].select("b"))[4]
                        except Exception as ex:
                            count_lifes = '0'
                        break
                    count += 1
                # print(url_user_link, username, student_id, count_lifes)
                with db.cursor() as cursor:
                    update_query = "UPDATE students_list SET count_lifes = '" + str(
                        count_lifes) + "' WHERE student_id = '" + student_id + "' AND cource_id = '" + str(
                        cource_id) + "'"
                    # print(update_query)
                    cursor.execute(update_query)
                    row = cursor.fetchall()
                    select_query = "SELECT name_student FROM students_list WHERE student_id = '" + str(
                        student_id) + "';"
                    cursor.execute(select_query)
                    row = cursor.fetchone()
                    # print(row)
                    if row is None:
                        insert_query = "INSERT INTO students_list (cource_id, name_student, student_id, count_lifes, curator_id) VALUES (%s,%s,%s,%s,%s)"
                        data = (cource_id, username, student_id, count_lifes, user_id)
                        cursor.execute(insert_query, data)
                        db.commit()
                    else:
                        update_query = "UPDATE students_list SET count_lifes = '" + str(
                            count_lifes) + "' WHERE student_id = '" + str(student_id) + "';"
                        cursor.execute(update_query)
                        db.commit()
                keyboard.add(types.InlineKeyboardButton(
                    text=username + " | Количество жизней: " + str(count_lifes),
                    callback_data=student_id))
    keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="close_inline_students_lifes"))
    return keyboard


def inline_cources(user_id):
    keyboard = types.InlineKeyboardMarkup()
    with db.cursor() as cursor:
        select_query = "SELECT selected_cource_id FROM user WHERE userId = " + str(user_id)
        cursor.execute(select_query)
        result = cursor.fetchall()
        _selected_course = result[0]["selected_cource_id"]

    payload = authorization_on_api(user_id)
    #######################################################################
    with requests.session() as session:
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get(
            "https://api.100points.ru/student_homework/index?email=&name=&course_id=&module_id=&lesson_id=&group_id=",
            data=payload)
        html_after_authorization = BS(response.content, 'html.parser')
        for x in html_after_authorization.select(".form-group"):
            if ('<select class="form-control" data-select="" id="course_id" name="course_id">') in str(x) and ('<option value="">Выберите курс</option>') in str(x):
                cource = x.select("option")
                for i in cource:
                    if (i.get("value") != ""):
                        keyboard.add(
                            types.InlineKeyboardButton(text=i.get_text().strip(), callback_data=i.get("value")))
    keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="close_inline_cources"))
    return keyboard


def inline_groups(user_id):
    keyboard = types.InlineKeyboardMarkup()
    with db.cursor() as cursor:
        select_query = "SELECT selected_cource_id FROM user WHERE userId = " + str(user_id)
        cursor.execute(select_query)
        result = cursor.fetchall()
        _selected_course = result[0]["selected_cource_id"]

    payload = authorization_on_api(user_id)
    #######################################################################
    with requests.session() as session:
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get(
            "https://api.100points.ru/student_homework/index?email=&name=&course_id=" + str(
                _selected_course) + "&module_id=&lesson_id=&group_id=",
            data=payload)
        html_after_authorization = BS(response.content, 'html.parser')
        for x in html_after_authorization.select(".form-group"):
            if ('<select class="form-control" data-select="" id="group_id" name="group_id">') in str(x):
                group = x.select("option")
                for i in group:
                    if (i.get("value") != ""):
                        keyboard.add(
                            types.InlineKeyboardButton(text=i.get_text().strip(), callback_data=i.get("value")))
    keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="close_inline_groups"))
    return keyboard


def authorization_on_api(user_id):
    with db.cursor() as cursor:
        select_query = "SELECT user_login,user_password,selected_cource_id FROM user WHERE userId = " + str(user_id)
        cursor.execute(select_query)
        result = cursor.fetchall()
        _login = result[0]["user_login"]
        _password = result[0]["user_password"]

    s = requests.Session()
    auth_html = s.get("https://api.100points.ru/login")
    auth_bs = BS(auth_html.content, "html.parser")
    token = auth_bs.select("input[name=_token]")[0]['value']

    login = _login
    password = _password
    payload = {
        "_token": token,
        "returnUrl": '/',
        "email": login,  # Логин
        "password": password  # Пароль
    }
    return payload


def inline_modules(user_id):
    keyboard = types.InlineKeyboardMarkup()
    with db.cursor() as cursor:
        select_query = "SELECT selected_cource_id FROM user WHERE userId = " + str(user_id)
        cursor.execute(select_query)
        result = cursor.fetchall()
        _selected_course = result[0]["selected_cource_id"]
    payload = authorization_on_api(user_id)
    #######################################################################
    with requests.session() as session:
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get(
            "https://api.100points.ru/student_homework/index?email=&name=&course_id=" + str(
                _selected_course) + "&module_id=&lesson_id=&group_id=",
            data=payload)
        html_after_authorization = BS(response.content, 'html.parser')
        for x in html_after_authorization.select(".form-group"):
            if ('<select class="form-control" data-select="" id="module_id" name="module_id">') in str(x):
                module = x.select("option")
                for i in module:
                    if (i.get("value") != ""):
                        keyboard.add(
                            types.InlineKeyboardButton(text=i.get_text().strip(), callback_data=i.get("value")))
                        update_modules_db(i.get("value"), i.get_text().strip())

    keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="close_inline_module"))
    return keyboard


def update_modules_db(module_id, module_name):
    with db.cursor() as cursor:
        select_query = "SELECT module_name FROM modules WHERE module_id = " + str(module_id)
        cursor.execute(select_query)
        result_selecting_module = cursor.fetchall()
        if bool(result_selecting_module) is False:
            insert_query = "INSERT INTO modules (module_id, module_name) VALUES (%s,%s)"
            data = (module_id, module_name)
            cursor.execute(insert_query, data)
            db.commit()


def inlinekeyboard_select_lesson(user_id):
    keyboard = types.InlineKeyboardMarkup()
    with db.cursor() as cursor:
        select_query = "SELECT selected_cource_id, selected_module_id FROM user WHERE userId = " + str(
            user_id)
        cursor.execute(select_query)
        result = cursor.fetchall()
        _selected_course = result[0]["selected_cource_id"]
        _selected_module_id = result[0]["selected_module_id"]

    payload = authorization_on_api(user_id)
    #######################################################################
    with requests.session() as session:
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get("https://api.100points.ru/student_homework/index?email=&name=&course_id=" + str(
            _selected_course) + "&module_id=" + str(_selected_module_id) + "&lesson_id=&group_id=", data=payload)
        html_after_authorization = BS(response.content, 'html.parser')
        for x in html_after_authorization.select(".form-group"):
            if ('<select class="form-control" data-select="" id="lesson_id" name="lesson_id">') in str(x):
                lesson = x.select("option")
                for i in lesson:
                    if (i.get("value") != ""):
                        keyboard.add(
                            types.InlineKeyboardButton(text=i.get_text().strip(), callback_data=i.get("value")))
                        add_lesson_to_db(i.get("value"), i.get_text().strip())

    keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="close_inline_lesson"))
    return keyboard


def add_lesson_to_db(lesson_id, lesson_name):
    with db.cursor() as cursor:
        select_query = "SELECT lesson_id FROM lessons WHERE lesson_id = " + str(lesson_id)
        cursor.execute(select_query)
        result_selecting_module = cursor.fetchall()
        if bool(result_selecting_module) is False:
            insert_query = "INSERT INTO lessons (lesson_id, lesson_name) VALUES (%s,%s)"
            data = (lesson_id, lesson_name)
            cursor.execute(insert_query, data)
            db.commit()


def parsing_concrete_user_life(user_id, student_id):
    with db.cursor() as cursor:
        select_query = "SELECT selected_cource_id FROM user WHERE userId = " + str(user_id)
        cursor.execute(select_query)
        result = cursor.fetchall()
        _selected_course = result[0]["selected_cource_id"]

    payload = authorization_on_api(user_id)
    with requests.session() as session:
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get("https://api.100points.ru/user/edit/" + str(student_id), data=payload)
        html = BS(response.content, 'html.parser')
        count = 0
        for x in html.select("td", class_="odd"):
            if str(_selected_course) in x.find("a").get("href"):
                count_lifes = str(html.select("td", class_="odd")[count + 1].select("b"))[4]
                break
            count += 1

        with db.cursor() as cursor:
            update_query = "UPDATE students_list SET count_lifes = '" + str(
                count_lifes) + "' WHERE student_id = " + str(student_id)
            cursor.execute(update_query)
            db.commit()


def display_profile(user_Id):
    with db.cursor() as cursor:
        update_query = "SELECT user_name, selected_cource_id, selected_module_id, selected_lesson_id, selected_group_id, user_status FROM user WHERE userId = " + str(
            user_Id)
        cursor.execute(update_query)
        results = cursor.fetchall()
        user_name = results[0]["user_name"]
        selected_course = results[0]["selected_cource_id"]
        selected_module = results[0]["selected_module_id"]
        selected_lesson = results[0]["selected_lesson_id"]
        selected_group = results[0]["selected_group_id"]
        user_status = results[0]["user_status"]
        try:
            select_query = "SELECT module_name from modules WHERE module_id = " + str(selected_module)
            cursor.execute(select_query)
            results = cursor.fetchall()
            module_name = results[0]["module_name"]
        except Exception as ex:
            module_name = selected_module
        try:
            select_query = "SELECT cource_name FROM cources WHERE cource_id = " + str(selected_course)
            cursor.execute(select_query)
            results = cursor.fetchall()
            course_name = results[0]["cource_name"]
        except Exception as exm:
            course_name = 'None'

        bot.send_message(user_Id,
                         f"Ваш никнейм: {user_name} \n Выбранный курс: {course_name}\n Выбранный модуль: {module_name}\n Выбранный урок: {selected_lesson}\n Выбранная группа [id]: {selected_group}\n Ваш статус: {user_status}",
                         reply_markup=keyboard_lk())
        try:
            with db.cursor() as cursor:
                update_query2 = "UPDATE user SET name_process = 'profile_menu' WHERE userId = " + str(user_Id)
                cursor.execute(update_query2)
                db.commit()
        except Exception as Ex:
            print(Ex)


def inline_concrete_student_life(user_id, student_id):
    keyboard = types.InlineKeyboardMarkup()
    with db.cursor() as cursor:
        select_query = "SELECT name_student, count_lifes FROM students_list WHERE student_id = " + str(student_id)
        cursor.execute(select_query)
        results = cursor.fetchall()
        keyboard.add(types.InlineKeyboardButton(text=results[0]["name_student"], callback_data="1"))
        keyboard.add(types.InlineKeyboardButton(text='-', callback_data="remove_life_" + str(student_id)),
                     types.InlineKeyboardButton(text='Жизни: ' + str(results[0]["count_lifes"]), callback_data="0"),
                     types.InlineKeyboardButton(text='+', callback_data="add_life_" + str(student_id)))
    keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="student life list"))
    return keyboard


def students_update(user_id):
    ########################################################################
    with db.cursor() as cursor:
        select_query = "SELECT selected_cource_id FROM user WHERE userId = " + str(user_id)
        cursor.execute(select_query)
        results = cursor.fetchall()
        selected_cource = results[0]["selected_cource_id"]
    payload = authorization_on_api(user_id)
    #######################################################################

    # Запрашиваем ссылку на домашку#
    with requests.session() as session:
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get(
            "https://api.100points.ru/user/index?email=&name=&vk_id=&registration_date=&course_id=36&authorization_variant=",
            data=payload)
        html_after_authorization = BS(response.content, 'html.parser')
        current_class_page_link = ""
        prev_class_page_link = ""
        for i in html_after_authorization.select(".pagination"):
            d1 = i.find_all("a", class_="page-link")
            for j in d1:
                prev_class_page_link = current_class_page_link  # Запоминаем текущую страницу и предыдущую, т.к самый последний html код - это кнопка Next
                current_class_page_link = j
        count_pages = int(((prev_class_page_link.text).replace(' ', '')))  # Убираем пробельчики
        for i in range(1, count_pages + 1):
            response = session.get("https://api.100points.ru/user/index?course_id=" + str(
                selected_cource) + "&export_type=all&page=" + str(i))
            html = BS(response.content, 'html.parser')
            for el in html.select(".odd"):
                url_user_link = el.find("a", class_="btn btn-xs bg-blue").get("href")
                student_id = url_user_link[35:]
                response = session.get(url_user_link)
                html = BS(response.content, 'html.parser')
                print(html.select(".form-control")[4])
                username = html.select(".form-control")[4].get("value")
                count = 0
                for x in html.select("td", class_="odd"):
                    if (str(selected_cource) in x.find("a").get("href")):
                        count_lifes = str(html.select("td", class_="odd")[count + 1].select("b"))[4]
                        break
                    count += 1
                # print(url_user_link, username, user_id, count_lifes)
                with db.cursor() as cursor:
                    select_query = "SELECT name_student FROM students_list WHERE student_id = '" + str(
                        student_id) + "';"
                    cursor.execute(select_query)
                    row = cursor.fetchone()
                    # print(row)
                    if row is None:
                        insert_query = "INSERT INTO students_list (cource_id, name_student, student_id, count_lifes, curator_id) VALUES (%s,%s,%s,%s,%s)"
                        data = (selected_cource, username, student_id, count_lifes, user_id)
                        cursor.execute(insert_query, data)
                        db.commit()
                    else:
                        update_query = "UPDATE students_list SET count_lifes = '" + str(
                            count_lifes) + "' WHERE student_id = '" + str(student_id) + "';"
                        cursor.execute(update_query)
                        db.commit()


def remove_life(student_id, user_id):
    with db.cursor() as cursor:
        select_query = "SELECT selected_cource_id FROM user WHERE userId = " + str(user_id)
        cursor.execute(select_query)
        result = cursor.fetchall()
        _selected_course = result[0]["selected_cource_id"]

    payload = authorization_on_api(user_id)
    # Запрашиваем ссылку на домашку#
    with requests.session() as session:
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get(
            "https://api.100points.ru/course_progress/remove_live/" + str(_selected_course) + "/" + str(student_id),
            data=payload)

    with db.cursor() as cursor:
        select_query = "SELECT count_lifes FROM students_list WHERE student_id = '" + str(
            student_id) + "' AND cource_id = '" + str(_selected_course) + "'"
        cursor.execute(select_query)
        result = cursor.fetchall()
        count_lifes_from_db = result[0]["count_lifes"]
        if (count_lifes_from_db >= 0):
            update_query = "UPDATE students_list SET count_lifes = '" + str(
                count_lifes_from_db - 1) + "' WHERE student_id = '" + str(student_id) + "' AND cource_id = '" + str(
                _selected_course) + "'"
            cursor.execute(update_query)
            db.commit()


def add_life(student_id, user_id):
    with db.cursor() as cursor:
        select_query = "SELECT selected_cource_id FROM user WHERE userId = " + str(user_id)
        cursor.execute(select_query)
        result = cursor.fetchall()
        _selected_course = result[0]["selected_cource_id"]

    payload = authorization_on_api(user_id)
    with requests.session() as session:
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get(
            "https://api.100points.ru/course_progress/add_live/" + str(_selected_course) + "/" + str(student_id),
            data=payload)

    with db.cursor() as cursor:
        select_query = "SELECT count_lifes FROM students_list WHERE student_id = '" + str(
            student_id) + "' AND cource_id = '" + str(_selected_course) + "'"
        cursor.execute(select_query)
        result = cursor.fetchall()
        count_lifes_from_db = result[0]["count_lifes"]
        if (count_lifes_from_db < 3):
            update_query = "UPDATE students_list SET count_lifes = '" + str(
                count_lifes_from_db + 1) + "' WHERE student_id = '" + str(student_id) + "' AND cource_id = '" + str(
                _selected_course) + "'"
            cursor.execute(update_query)
            db.commit()


def update_cources(user_id):
    payload = authorization_on_api(user_id)
    with requests.session() as session:
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get("https://api.100points.ru/user/index", data=payload)
        html_after_authorization = BS(response.content, 'html.parser')
        for x in html_after_authorization.select("option", name_="course_id", class_="form-control"):
            if (x.get("value")).isdigit():
                id_cource_from_api = x.get("value")
                name_cource_from_api = x.get_text().strip()
                print(x.get("value"), x.get_text().strip())
                with db.cursor() as cursor:
                    select_query = "SELECT cource_name FROM cources WHERE cource_id = " + str(id_cource_from_api)
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    if bool(results) is False:
                        try:
                            insert_query = "INSERT INTO cources (cource_id, cource_name, modules_course_id) VALUES (%s,%s,%s)"
                            data = (id_cource_from_api, name_cource_from_api, '0')
                            cursor.execute(insert_query, data)
                            db.commit()
                            print("Курс был добавлен в базу")
                        except Exception as ex:
                            print(ex)


@bot.message_handler(commands=['start'])  # Обработчик команды /start
def start(message):
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    with db.cursor() as cursor:
        select_all_rows = "SELECT * FROM user WHERE userId =" + str(user_id)
        cursor.execute(select_all_rows)
        rows = cursor.fetchall()  # Выгрузили все столбцы

        # Проверяем на наличие аккаунта =)
        if cursor.rowcount == 0:
            print('Регистрация нового пользователя')
            try:
                with db.cursor() as cursor:
                    insert_query = "INSERT INTO user (userId, user_name, name_process,user_status)" \
                                   "VALUES (%s,%s,%s,%s)"
                    data = (user_id, message.from_user.first_name, 'Register', 'Куратор')
                    cursor.execute(insert_query, data)
                    db.commit()
                    insert_query = "INSERT INTO parsing_settings (user_id, curators_check, percent_of_completion, time_homework)   ('" + str(
                        user_id) + "',False,False,False);"  # Заполнили основные данные в БД
                    cursor.execute(insert_query)  # Для дальнейшей корректной работы, я устал писать это в 5:30
                    db.commit()
            except Exception as Ex:
                print(Ex)
            bot.send_message(message.from_user.id, "Привет! Я помощник по выгрузке домашки с api.100points.ru")
            bot.send_message(message.from_user.id, "Введи логин с api.100points.ru")
        else:
            with db.cursor() as cursor:
                update_query = "UPDATE user SET name_process = 'start_menu', selected_cource_id = '0', selected_module_id = '0', selected_lesson_id = '0', selected_group_id ='0', inline_message_id = '0'  WHERE userId = " + str(
                    user_id)  # Если человек написал старт, будучи зареганным - просто отправляем ему клавиатуру стартовую
                cursor.execute(update_query)
                db.commit()
            bot.send_message(user_id, "Привет! Я помощник по выгрузке домашки с api.100points.ru",
                             reply_markup=keyboard_start())


@bot.message_handler(func=lambda message: True)  # Обработка входящих сообщений
def echo_message(message):
    user_Id = message.from_user.id
    with db.cursor() as cursor:
        update_query = "SELECT name_process,selected_cource_id FROM user WHERE userId = " + str(user_Id)
        cursor.execute(update_query)
        results = cursor.fetchall()
        name_process = results[0]["name_process"]
        selected_cource = results[0]["selected_cource_id"]

    if (name_process == "Register") and ('@100points.ru' in message.text):
        try:
            with db.cursor() as cursor:
                update_query = "UPDATE user SET user_login = '" + str(
                    message.text) + "', name_process = 'Login received' WHERE userId = " + str(
                    user_Id)  # Отметили как вписанный логiн
                cursor.execute(update_query)
                db.commit()
            bot.send_message(user_Id, "Логин добавлен, введите пароль")
        except Exception as Ex:
            print(Ex)

    if name_process == "Login received":
        try:
            with db.cursor() as cursor:
                update_query = "UPDATE user SET user_password = '" + str(
                    message.text) + "', name_process = 'start_menu' WHERE userId = " + str(
                    user_Id)  # Отметили процесс как "Заполненные данные"
                cursor.execute(update_query)
                db.commit()
            bot.send_message(user_Id, "Пароль добавлен. Успешного пользования!", reply_markup=keyboard_start())
        except Exception as Ex:
            print(Ex)

    if (message.text == "Мой профиль") and (name_process == "start_menu"):
        display_profile(user_Id)

    if (message.text == "Назад") and (name_process == "profile_menu"):
        try:
            bot.send_message(user_Id, message.text, reply_markup=keyboard_start())
            with db.cursor() as cursor:
                update_query = "UPDATE user SET name_process = 'start_menu' WHERE userId = " + str(user_Id)
                cursor.execute(update_query)
                db.commit()
        except Exception as ex:
            print(ex)
    if (message.text == "Настройки выгрузки") and (name_process == "profile_menu"):
        bot.send_message(user_Id, 'Загружаю настройки выгрузки', reply_markup=types.ReplyKeyboardRemove())
        message_id = bot.send_message(user_Id, text=message.text,
                                      reply_markup=inlinekeyboard_settings(user_Id)).message_id
        with db.cursor() as cursor:
            update_query = "UPDATE parsing_settings SET message_id = '" + str(message_id) + "' WHERE user_id = " + str(
                user_Id)
            cursor.execute(update_query)
            db.commit()

            update_query2 = "UPDATE user SET name_process = 'parsing_setting' WHERE userId = " + str(user_Id)
            cursor.execute(update_query2)
            db.commit()

    if (message.text == "Выгрузить домашку") and (name_process == 'start_menu'):
        try:
            with db.cursor() as cursor:
                select_query = "SELECT selected_cource_id,selected_group_id,selected_module_id FROM user WHERE userId = " + str(
                    user_Id)
                cursor.execute(select_query)
                results = cursor.fetchall()
                _selected_cource_id = results[0]["selected_cource_id"]
                _selected_group_id = results[0]["selected_group_id"]
                _selected_module_id = results[0]["selected_module_id"]
            if (_selected_cource_id != 0) and (_selected_module_id != 0) and (_selected_group_id != 0):
                bot.send_message(user_Id, 'Выберите урок:', reply_markup=types.ReplyKeyboardRemove())
                try:
                    message_id = bot.send_message(user_Id, text='Выберите урок:',
                                                  reply_markup=inlinekeyboard_select_lesson(user_Id)).message_id
                    with db.cursor() as cursor:
                        update_query = "UPDATE user SET inline_message_id = '" + str(
                            message_id) + "' WHERE userId = " + str(
                            user_Id)
                        cursor.execute(update_query)
                        db.commit()

                        update_query2 = "UPDATE user SET name_process = 'select_lesson' WHERE userId = " + str(user_Id)
                        cursor.execute(update_query2)
                        db.commit()
                except Exception as ex:
                    print("Ошибка message_id", ex)
            else:
                bot.send_message(user_Id, "Не заполнен один из пунктов выгрузки домашнего задания (курс/группа/модуль)",
                                 reply_markup=keyboard_start())
        except Exception as ex:
            print("Ошибка message_id", ex)
            bot.send_message(user_Id, "Не заполнен один из пунктов выгрузки домашнего задания (курс/группа/модуль)",
                             reply_markup=keyboard_start())

    if (message.text == "Изменить жизни") and (name_process == "start_menu"):
        if (selected_cource > 0):
            bot.send_message(user_Id, 'Загружаю список учеников...', reply_markup=types.ReplyKeyboardRemove())
            message_id = bot.send_message(user_Id, text="Список учеников: ",
                                          reply_markup=inline_students_lifes_dop(user_Id, selected_cource)).message_id
            with db.cursor() as cursor:
                update_query = "UPDATE user SET name_process = 'Inlinekeyboard_users_lifes',inline_message_id = '" + \
                               str(message_id) + "' WHERE userId = " + str(user_Id)
                cursor.execute(update_query)
                db.commit()
        else:
            bot.send_message(user_Id, "Для изменения жизней необходимо выбрать курс")

    if (message.text == "Изменить курс") and (name_process == "profile_menu"):
        try:
            bot.send_message(user_Id, 'Загружаю список курсов...', reply_markup=types.ReplyKeyboardRemove())
            message_id = bot.send_message(user_Id, text="Список курсов: ",
                                          reply_markup=inline_cources(user_Id)).message_id
            with db.cursor() as cursor:
                update_query = "UPDATE user SET name_process = 'Inlinekeyboard_cources', selected_module_id = '0', selected_lesson_id = '0', selected_group_id = '0',inline_message_id = '" + \
                               str(message_id) + "' WHERE userId = " + str(user_Id)
                cursor.execute(update_query)
                db.commit()
        except Exception as ex:
            print("Ошибка выбора курса", ex)

    if (message.text == "Изменить группу") and (name_process == "profile_menu"):
        with db.cursor() as cursor:
            select_query = "SELECT selected_cource_id FROM user WHERE userId = " + str(user_Id)
            cursor.execute(select_query)
            selected_cource_id_from_change_group = cursor.fetchall()[0]["selected_cource_id"]
            if (selected_cource_id_from_change_group != 0):
                try:
                    bot.send_message(user_Id, 'Загружаю список групп...', reply_markup=types.ReplyKeyboardRemove())
                    message_id = bot.send_message(user_Id, text="Список групп: ",
                                                  reply_markup=inline_groups(user_Id)).message_id
                    with db.cursor() as cursor:
                        update_query = "UPDATE user SET name_process = 'Inlinekeyboard_groups',inline_message_id = '" + \
                                       str(message_id) + "' WHERE userId = " + str(user_Id)
                        cursor.execute(update_query)
                        db.commit()
                except Exception as ex:
                    print("Ошибка выбора группы", ex)
            else:
                bot.send_message(user_Id, "Чтоб изменить/выбрать группу изначально необходимо выбрать курс")

    if (message.text == "Изменить модуль") and (name_process == "profile_menu"):
        with db.cursor() as cursor:
            select_query = "SELECT selected_cource_id FROM user WHERE userId = " + str(user_Id)
            cursor.execute(select_query)
            if cursor.fetchall()[0]["selected_cource_id"] != 0:
                try:
                    bot.send_message(user_Id, 'Загружаю список модулей...', reply_markup=types.ReplyKeyboardRemove())
                    message_id = bot.send_message(user_Id, text="Список модулей: ",
                                                  reply_markup=inline_modules(user_Id)).message_id
                    with db.cursor() as cursor:
                        update_query = "UPDATE user SET name_process = 'Inlinekeyboard_modules',inline_message_id = '" + \
                                       str(message_id) + "' WHERE userId = " + str(user_Id)
                        cursor.execute(update_query)
                        db.commit()
                except Exception as ex:
                    print("Ошибка выбора модуля", ex)
            else:
                bot.send_message(user_Id, "Чтоб изменить модуль, необходимо выбрать курс")


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    # print(call.data)
    user_id = call.from_user.id
    name_process = ""

    ######### Достали из БД текущее название процесса
    with db.cursor() as cursor:
        update_query = "SELECT name_process,selected_cource_id FROM user WHERE userId = " + str(user_id)
        cursor.execute(update_query)
        results = cursor.fetchall()
        name_process = results[0]["name_process"]
        selected_cource = results[0]["selected_cource_id"]
        #####################'

    if (name_process == 'select_lesson'):
        # print('select lesson', call.data)
        if (call.data == 'close_inline_lesson'):
            try:
                # print('Close inline lesson')
                with db.cursor() as cursor:
                    select_query = "SELECT inline_message_id FROM user WHERE userId = " + str(
                        user_id)  # Достали айди сообщения для удаления клавиатуры
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    message_id = results[0]["inline_message_id"]
                    bot.delete_message(user_id, message_id)  # Удалили сообщение с клавиатурой
                    update_query = "UPDATE user SET inline_message_id = '" + str(0) + "' WHERE userId = " + str(
                        user_id)  # Обнулили id клавиатуры в БД
                    cursor.execute(update_query)
                    db.commit()
                    update_query = "UPDATE user SET name_process = 'start_menu' WHERE userId = " + str(
                        user_id)  # Обновили имя процесса
                    cursor.execute(update_query)
                    db.commit()
                    bot.send_message(user_id, "Главное меню", reply_markup=keyboard_start())
            except Exception as ex:
                print(ex, 'Ошибка в close inline lesson')
        else:
            try:
                with db.cursor() as cursor:
                    update_query = "UPDATE user SET selected_lesson_id = '" + call.data + "' WHERE userId = " + str(
                        user_id)
                    cursor.execute(update_query)
                    db.commit()
                    select_query = "SELECT inline_message_id FROM user WHERE userId = " + str(
                        user_id)  # Достали айди сообщения для удаления клавиатуры
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    message_id = results[0]["inline_message_id"]
                    bot.delete_message(user_id, message_id)  # Удалили сообщение с клавиатурой
                    update_query = "UPDATE user SET inline_message_id = '" + str(0) + "' WHERE userId = " + str(
                        user_id)  # Обнулили id клавиатуры в БД
                    cursor.execute(update_query)
                    db.commit()

                    try:
                        select_query = "SELECT user_login, user_password,selected_cource_id,selected_lesson_id,selected_group_id,selected_module_id FROM user WHERE userId = " + str(
                            user_id)
                        cursor.execute(select_query)
                        results = cursor.fetchall()
                        _login = results[0]["user_login"]
                        _password = results[0]["user_password"]
                        _selected_cource_id = results[0]["selected_cource_id"]
                        _selected_lesson_id = results[0]["selected_lesson_id"]
                        _selected_group_id = results[0]["selected_group_id"]
                        _selected_module_id = results[0]["selected_module_id"]
                        if (_selected_cource_id != 0) and (_selected_module_id != 0) and (_selected_group_id != 0) and (
                                _selected_lesson_id != 0):
                            print(f"Куратор {user_id} запустил выгрузку домашнего задания")
                            update_query = "UPDATE user SET name_process = 'start_menu', selected_lesson_id = '0' WHERE userId = " + str(
                                user_id)  # Обновили имя процесса
                            cursor.execute(update_query)
                            db.commit()
                            try:
                                parsing(user_id, _login, _password, _selected_cource_id, _selected_lesson_id,
                                        _selected_group_id, _selected_module_id)
                            except Exception as problem_parsing:
                                print(problem_parsing, "Проблема в парсинге")

                            bot.send_message(user_id, "Главное меню", reply_markup=keyboard_start())
                        else:
                            bot.send_message(user_id,
                                             "Не заполнен один из пунктов выгрузки домашнего задания (курс/группа/модуль)",
                                             reply_markup=keyboard_start())
                            update_query = "UPDATE user SET name_process = 'start_menu' WHERE userId = " + str(
                                user_id)  # Обновили имя процесса
                            cursor.execute(update_query)
                            db.commit()
                    except Exception as problem:
                        print(problem, 'Ошибка в select_lesson после запуска парсинга')

            except Exception as ex:
                print(ex, 'Ошибка в select_lesson')

    if name_process == 'Inlinekeyboard_modules':
        if call.data == 'close_inline_module':
            try:
                with db.cursor() as cursor:
                    select_query = "SELECT inline_message_id FROM user WHERE userId = " + str(
                        user_id)  # Достали айди сообщения для удаления клавиатуры
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    message_id = results[0]["inline_message_id"]
                    bot.delete_message(user_id, message_id)  # Удалили сообщение с клавиатурой
                    update_query = "UPDATE user SET inline_message_id = '" + str(0) + "' WHERE userId = " + str(
                        user_id)  # Обнулили id клавиатуры в БД
                    cursor.execute(update_query)
                    db.commit()
                    update_query = "UPDATE user SET name_process = 'profile_menu' WHERE userId = " + str(
                        user_id)  # Обновили имя процесса
                    cursor.execute(update_query)
                    db.commit()
                    display_profile(user_id)
            except Exception as ex:
                print(ex, 'Ошибка в close inline_module')
        else:
            try:
                with db.cursor() as cursor:
                    update_query = "UPDATE user SET selected_module_id = '" + call.data + "' WHERE userId = " + str(
                        user_id)
                    cursor.execute(update_query)
                    db.commit()
                    select_query = "SELECT inline_message_id FROM user WHERE userId = " + str(
                        user_id)  # Достали айди сообщения для удаления клавиатуры
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    message_id = results[0]["inline_message_id"]
                    bot.delete_message(user_id, message_id)  # Удалили сообщение с клавиатурой
                    update_query = "UPDATE user SET inline_message_id = '" + str(0) + "' WHERE userId = " + str(
                        user_id)  # Обнулили id клавиатуры в БД
                    cursor.execute(update_query)
                    db.commit()
                    update_query = "UPDATE user SET name_process = 'profile_menu' WHERE userId = " + str(
                        user_id)  # Обновили имя процесса
                    cursor.execute(update_query)
                    db.commit()
                    display_profile(user_id)

            except Exception as ex:
                print(ex, 'Ошибка в close_inline_keyboard последнее else')

    if (name_process == 'Inlinekeyboard_groups'):
        if (call.data == "close_inline_groups"):
            try:
                with db.cursor() as cursor:
                    select_query = "SELECT inline_message_id FROM user WHERE userId = " + str(
                        user_id)  # Достали айди сообщения для удаления клавиатуры
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    message_id = results[0]["inline_message_id"]
                    bot.delete_message(user_id, message_id)  # Удалили сообщение с клавиатурой
                    update_query = "UPDATE user SET inline_message_id = '" + str(0) + "' WHERE userId = " + str(
                        user_id)  # Обнулили id клавиатуры в БД
                    cursor.execute(update_query)
                    db.commit()
                    update_query = "UPDATE user SET name_process = 'profile_menu' WHERE userId = " + str(
                        user_id)  # Обновили имя процесса
                    cursor.execute(update_query)
                    db.commit()
                    display_profile(user_id)
            except Exception as ex:
                print(ex)
        else:
            try:
                with db.cursor() as cursor:
                    update_query = "UPDATE user SET selected_group_id = '" + call.data + "' WHERE userId = " + str(
                        user_id)
                    cursor.execute(update_query)
                    db.commit()
                    select_query = "SELECT inline_message_id FROM user WHERE userId = " + str(
                        user_id)  # Достали айди сообщения для удаления клавиатуры
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    message_id = results[0]["inline_message_id"]
                    bot.delete_message(user_id, message_id)  # Удалили сообщение с клавиатурой
                    update_query = "UPDATE user SET inline_message_id = '" + str(0) + "' WHERE userId = " + str(
                        user_id)  # Обнулили id клавиатуры в БД
                    cursor.execute(update_query)
                    db.commit()
                    update_query = "UPDATE user SET name_process = 'profile_menu' WHERE userId = " + str(
                        user_id)  # Обновили имя процесса
                    cursor.execute(update_query)
                    db.commit()
                    display_profile(user_id)

            except Exception as ex:
                print(ex)

    if (name_process == 'Inlinekeyboard_cources'):
        if (call.data == "close_inline_cources"):
            try:
                with db.cursor() as cursor:
                    select_query = "SELECT inline_message_id FROM user WHERE userId = " + str(
                        user_id)  # Достали айди сообщения для удаления клавиатуры
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    message_id = results[0]["inline_message_id"]
                    bot.delete_message(user_id, message_id)  # Удалили сообщение с клавиатурой
                    update_query = "UPDATE user SET inline_message_id = '" + str(0) + "' WHERE userId = " + str(
                        user_id)  # Обнулили id клавиатуры в БД
                    cursor.execute(update_query)
                    db.commit()
                    update_query = "UPDATE user SET name_process = 'profile_menu' WHERE userId = " + str(
                        user_id)  # Обновили имя процесса
                    cursor.execute(update_query)
                    db.commit()
                    display_profile(user_id)
            except Exception as ex:
                print(ex, 'Close inline cources ошибка db')
        else:
            try:
                with db.cursor() as cursor:
                    update_query = "UPDATE user SET selected_cource_id = '" + call.data + "' WHERE userId = " + str(
                        user_id)
                    cursor.execute(update_query)
                    db.commit()
                    select_query = "SELECT inline_message_id FROM user WHERE userId = " + str(
                        user_id)  # Достали айди сообщения для удаления клавиатуры
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    message_id = results[0]["inline_message_id"]
                    bot.delete_message(user_id, message_id)  # Удалили сообщение с клавиатурой
                    update_query = "UPDATE user SET inline_message_id = '" + str(0) + "' WHERE userId = " + str(
                        user_id)  # Обнулили id клавиатуры в БД
                    cursor.execute(update_query)
                    db.commit()
                    update_query = "UPDATE user SET name_process = 'profile_menu' WHERE userId = " + str(
                        user_id)  # Обновили имя процесса
                    cursor.execute(update_query)
                    db.commit()
                    display_profile(user_id)

            except Exception as ex:
                print(ex, 'Ошибка в else inline_cources')

    if (name_process == 'Inlinekeyboard_users_lifes'):
        # print("name_process == 'Inlinekeyboard_users_lifes'")
        # call.data = user_id
        try:
            with db.cursor() as cursor:
                update_query = "SELECT inline_message_id FROM user WHERE userId = " + str(user_id)
                cursor.execute(update_query)
                results = cursor.fetchall()
                message_id = results[0]["inline_message_id"]
            # print(call.data)
            if call.data == "student life list":
                bot.edit_message_reply_markup(user_id, message_id,
                                              reply_markup=inline_students_lifes(user_id,
                                                                                 selected_cource))  # Обновили клавиатуру
            elif ("add_life_" in call.data) or ("remove_life_" in call.data):
                if ("add_life_" in call.data):
                    student_id_for_lifes = call.data[9:]
                    add_life(student_id_for_lifes, user_id)
                    bot.edit_message_reply_markup(user_id, message_id,
                                                  reply_markup=inline_concrete_student_life(user_id,
                                                                                            student_id_for_lifes))  # Обновили клавиатуру
                else:
                    student_id_for_lifes = call.data[12:]
                    remove_life(student_id_for_lifes, user_id)
                    bot.edit_message_reply_markup(user_id, message_id,
                                                  reply_markup=inline_concrete_student_life(user_id,
                                                                                            student_id_for_lifes))  # Обновили клавиатуру
                # print(student_id_for_lifes)
            elif call.data == "close_inline_students_lifes":
                try:
                    with db.cursor() as cursor:
                        update_query = "UPDATE user SET name_process = 'start_menu' WHERE userId = " + str(
                            user_id)
                        cursor.execute(update_query)
                        db.commit()
                        update_query = "UPDATE user SET inline_message_id = '0' WHERE userId = " + str(
                            user_id)  # Обновили имя процесса
                        cursor.execute(update_query)
                        db.commit()
                    bot.delete_message(user_id, message_id)
                    bot.send_message(user_id, "Главное меню", reply_markup=keyboard_start())
                except Exception as Ex:
                    bot.send_message(user_id,
                                     'Не удалось удалить клавиатуру')  # Если не получилось удалить - то просто сообщаем об этом
                    print(Ex)
                    with db.cursor() as cursor:
                        update_query = "UPDATE user SET name_process = 'start_menu' WHERE userId = " + str(
                            user_id)
                        cursor.execute(update_query)
                        db.commit()
                        update_query = "UPDATE user SET inline_message_id = '0' WHERE userId = " + str(
                            user_id)  # Обновили имя процесса
                        cursor.execute(update_query)
                        db.commit()

            else:
                bot.edit_message_reply_markup(user_id, message_id,
                                              reply_markup=inline_concrete_student_life(user_id,
                                                                                        call.data))  # Обновили клавиатуру

        except Exception as Ex:
            print("Ошибка в Inlinekeyboard_users_lifes")
            print(Ex)

    ############# Обработка кнопки удаления ("Назад") на inlinekeyboard
    if name_process == "parsing_setting":
        if (call.data == "99"):
            try:
                with db.cursor() as cursor:
                    select_query = "SELECT message_id FROM parsing_settings WHERE user_id = " + str(
                        user_id)  # Достали айди сообщения для удаления клавиатуры
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    message_id = results[0]["message_id"]
                    bot.delete_message(user_id, message_id)  # Удалили сообщение с клавиатурой
                    update_query = "UPDATE parsing_settings SET message_id = '" + str(0) + "' WHERE user_id = " + str(
                        user_id)  # Обнулили id клавиатуры в БД
                    cursor.execute(update_query)
                    db.commit()
                    update_query = "UPDATE user SET name_process = 'profile_menu' WHERE userId = " + str(
                        user_id)  # Обновили имя процесса
                    cursor.execute(update_query)
                    db.commit()
                    bot.send_message(user_id, "Мой профиль", reply_markup=keyboard_lk())
            except Exception as Ex:
                bot.send_message(user_id,
                                 'Не удалось удалить клавиатуру')  # Если не получилось удалить - то просто сообщаем об этом
                print(Ex)
                with db.cursor() as cursor:
                    update_query = "UPDATE user, SET process_name = 'profile_menu' WHERE userId = " + str(user_id)
                    cursor.execute(update_query)
                    db.commit()

        else:
            rows = {
                '53': "url_homework",
                '54': "url_homework",
                '55': "time_homework",
                '56': "time_homework",
                '57': "percent_of_completion",
                '58': "percent_of_completion",
                '59': "curators_check",
                '60': "curators_check",
                '61': "test_part",
                '62': "test_part"

            }
            # '1': "Ссылка на дз",
            # '2': "Отправлено на проверку",
            # '3': "Процент выполнения ДЗ: ",
            # '4': "Проверка от куратора:",
            # '5': "Тестовая часть:",
            try:
                with db.cursor() as cursor:
                    select_query = "SELECT message_id FROM parsing_settings WHERE user_id = " + str(
                        user_id)  # Достали айди сообщения с клавиатурой для редактирования
                    cursor.execute(select_query)
                    results = cursor.fetchall()
                    message_id = results[0]["message_id"]
                    if (int(call.data) % 2 == 1):  # Проверка на то, ставить нам в БД true or false
                        update_query = "UPDATE parsing_settings SET " + rows[
                            call.data] + " = '1' WHERE user_id = " + str(user_id)
                    else:
                        update_query = "UPDATE parsing_settings SET " + rows[
                            call.data] + " = '0' WHERE user_id = " + str(user_id)
                    cursor.execute(update_query)
                    db.commit()
                    bot.edit_message_reply_markup(user_id, message_id,
                                                  reply_markup=inlinekeyboard_settings(user_id))  # Обновили клавиатуру
            except Exception as ex:
                bot.send_message(user_id, 'Не удалось изменить настройку')
                print(ex)
    #######################Обработка кнопок настроек (true/false)

    #########################################################


def parsing(userid, _login, _password, selected_cource_id, selected_lesson_id, selected_group_id, selected_module_id):
    curators_check_setting = False
    percent_completion_setting = False
    time_homework_setting = False
    url_homework_setting = False
    test_part_setting = False

    #################### Достали из БД настройки парсинга, после чего по ним добавляем необходимые столбцы
    with db.cursor() as cursor:
        select_query = "SELECT curators_check, percent_of_completion, time_homework, url_homework, test_part FROM parsing_settings WHERE user_id = " + str(
            userid)
        cursor.execute(select_query)
        results = cursor.fetchall()
        if (results[0]["curators_check"] == 1):
            curators_check_setting = True
        if (results[0]["percent_of_completion"] == 1):
            percent_completion_setting = True
        if (results[0]["time_homework"] == 1):
            time_homework_setting = True
        if (results[0]["url_homework"] == 1):
            url_homework_setting = True
        if (results[0]["test_part"] == 1):
            test_part_setting = True
        # select_query2 = "SELECT selected_cource_id, selected_module_id, selected_group_id,selected_lesson_id FROM user WHERE userId = " + str(
        #     userid)
        # cursor.execute(select_query2)
        # row = cursor.fetchall()
        # # selected_group_id = row[0]["selected_group_id"]
        # # selected_lesson_id = row[0]["selected_lesson_id"]
        # # selected_module_id = row[0]["selected_module_id"]
        # # print("Зашли перед select_query3")
        select_query3 = "SELECT lesson_name FROM lessons WHERE lesson_id = " + str(selected_lesson_id)
        cursor.execute(select_query3)
        row = cursor.fetchall()
        filename = str(row[0]["lesson_name"])
    ###################################################################
    user_id = userid
    try:
        os.remove(filename + ".txt")
    except Exception as ex:
        pass
    f = open(str(filename) + ".txt", 'w')  # Открыли файл на запись результатов домашки
    bot.send_message(user_id, "Начал выгрузку...")

    url_homework = "https://api.100points.ru/student_homework/index?status=passed&email=&name=&course_id=" + str(
        selected_cource_id) \
                   + "&module_id=" + str(selected_module_id) + "&lesson_id=" + str(selected_lesson_id) \
                   + "&group_id=" + str(selected_group_id)

    payload = authorization_on_api(user_id)
    with requests.session() as session:  # Обрабатываем домашку
        session.post("https://api.100points.ru/login", data=payload)
        response = session.get(url_homework + "&page=" + str(1))
        html_after_authorization = BS(response.content, 'html.parser')

        ##################Получаем кол-во страниц для проверки################################
        current_class_page_link = ""
        prev_class_page_link = ""
        try:
            for i in html_after_authorization.select(".pagination"):
                d1 = i.find_all("a", class_="page-link")  # Ищем все строчки html кода с нумерацией страниц
                for j in d1:
                    prev_class_page_link = current_class_page_link  # Запоминаем текущую страницу и предыдущую, т.к самый последний html код - это кнопка Next
                    current_class_page_link = j
            count_pages = int(((prev_class_page_link.text).replace(' ', '')))  # Убираем пробельчики
        except Exception as ex:
            count_pages = 1
        print(count_pages)
        #######################################################################################
        for i in range(1, count_pages + 1):  # Проходимся по каждой странице
            response = session.get(url_homework + "&page=" + str(i))  # Получаем текущую страницу
            html = BS(response.content, 'html.parser')
            for el in html.select(".odd "):  # Проходимся по строкам учеников
                url = el.select("a", class_="odd")  # Получаем url-ссылку домашки определенного ученика
                find_add_div_user = el.find_all("div")
                level_homework = find_add_div_user[7].get_text().split()
                #level_homework_name = str(*level_homework)
                level_homework_name = " ".join(level_homework)
                #print(level_homework_name)
                f.write(find_add_div_user[2].text + '|' + (level_homework_name) + '|')
                #print(find_add_div_user[2].text)  ## Выводим имя юзера
                #print(level_homework_name)
                # print(find_add_div_user[7].text)  ## Сложность уровня

                #######################################################
                for url_list in url:  # Проходимся по url чтоб получить чистую ссылку
                    homework_user_url = url_list.get("href")
                    if (url_homework_setting == True):
                        f.write(homework_user_url + '|')
                ##########################################################

                # Работа со страницей дз # ## Новая версия отличается тем, что не считает кол-во "верный" и использует сразу оценку куратора
                response_homework = session.get(
                    homework_user_url + str("?status=checking"))  # Переходим на страницу домашки
                html_homework = BS(response_homework.content, 'html.parser')  # Получаем html домашки
                text_with_value = ""
                for el2 in html_homework.select(".card-body"):
                    find_all_done_tasks_user = el2.find_all("div",
                                                            class_="form-group col-md-3")  # Проходимся по домашке и считаем кол-во верных ответов
                    k = 0  # ищем по счетчику классов нужный
                    for el3 in find_all_done_tasks_user:
                        k += 1
                        if (k == 4) and (time_homework_setting):
                            time_homework = el3.text.strip().split('\n')[1].strip()
                            f.write(time_homework + '|')
                        if (k == 5) and (percent_completion_setting):
                            percent_completion = (el3.text[24:]).partition('%')[0]
                            f.write(percent_completion + '|')
                        if (k == 6) and (curators_check_setting or test_part_setting):
                            text_otvet = (el3.text).split("\n")
                            if (test_part_setting):
                                count_good_test = (text_otvet[1][17:]).partition('/')[0]
                                f.write(count_good_test)
                            if curators_check_setting:
                                count_good_curator = ((text_otvet[2][23:]).strip().partition('/')[0])[8:]
                                f.write(count_good_curator + '|')
                    # f.write('\n')
                # print("Количество верно решенных задач:", text_with_value)
                f.write('\n')
    f.close()
    try:
        file = open(filename + ".txt", "rb")
        bot.send_document(user_id, file, reply_markup=keyboard_start())
    except Exception as ex:
        bot.send_message(userid, "Домашние работы не найдены", reply_markup=keyboard_start())


bot.infinity_polling()
