# -*- coding: utf-8 -*-

from datetime import datetime, date
from django.utils.safestring import mark_safe
from django import template

register = template.Library()

months = ('янв.','февр.','мар.','апр.','мая','июн.','июл.','авг.','сент.','окт.','нояб.','дек.')

"""
    Форматирует дату срока задачи.
    Дата в прошлом, сегодня или завтра помечается красным цветом (если задача не завершена).
    Пример: dt|format_deadline:"1"
        где dt - переменная типа Date, 1 - статус задачи
"""
@register.filter
def format_deadline(dt, status):
    if isinstance(dt, date):
        dt_str = format_date(dt)        
        diff = ( dt - datetime.now().date() ).days
        if diff <= 1 and int(status) != 3 and int(status) != 4:
            dt_str = '<span class="red">%s</span>' % dt_str
    else:
        dt_str = "&nbsp;"
    return mark_safe(dt_str)

"""
    Дата в формате '6 февр.' если год = текущему (иначе - в формате dd.mm.yyyy)
    Если есть время, выводится также и оно (а если дата - сегодня, выводится только время)
"""
@register.filter
def format_date(dt, option=""):
    dt_str = ''
    today = tomorrow = False
    dt_now = datetime.now().date()
    if isinstance(dt, date) or isinstance(dt, datetime):
        if isinstance(dt, datetime):
            dt_date = dt.date()
        else:
            dt_date = dt

        if dt_date == dt_now:
            today = True
        if (dt_date - dt_now).days == 1:
            tomorrow = True

        if dt.year == datetime.now().year:
            dt_str = '%s&nbsp;%s' % (dt.day, months[dt.month-1])
        else:
            dt_str = dt.strftime('%d.%m.%Y')

        if isinstance(dt, datetime):
            if today:
                dt_str = dt.strftime('%H:%M')
            elif option != 'short':
                dt_str += ' ' + dt.strftime('%H:%M')
        else:
            if today:
                dt_str = 'сегодня'
            if tomorrow:
                dt_str = 'завтра'                
    else:
        dt_str = "&nbsp;"
    return mark_safe(dt_str)

"""
    Выделяет имя файла из пути
"""
@register.filter
def attach(path):
    import os
    return os.path.basename(path)

"""
    Преобразование числа байт в килобайты
"""
@register.filter
def kilobytes(size):
    import math
    return "%s" % (int(math.ceil(float(size)/1024)))

"""
    Имя пользователя: Имя Фамилия (если указаны) или логин
"""
@register.filter
def username(user):
    try:
        if user.first_name and user.last_name:
            return "%s %s" % (user.first_name, user.last_name)
        else:
            return "%s" % user.username
    except:
        return ""

"""
    Вычисляет высоту дополнительной (нижней) строки в списке задач в зависимости от параметра - количества задач
    (для того чтобы высота таблицы не была меньше высоты левого меню при небольшом количестве задач)
"""
@register.filter
def extra_td_height(tasks_count):
    height1 = 130
    height2 = int(tasks_count)*27
    if (height1 > height2):
        height = (height1 - height2)
    else:
        height = 20
        
    return "%s" % height

"""
    Обрезает длинные строки
"""
@register.filter
def crop(text, count):
    out = text[:int(count)]
    if len(text) > len(out):
        out += '&hellip;'
    return mark_safe(out)