# -*- coding: utf-8 -*-

from datetime import datetime, date
import re
from django.contrib.auth.models import User
from todo.models import Status
from django.utils.safestring import mark_safe
from django import template

register = template.Library()

months = ('янв.','февр.','марта','апр.','мая','июня','июля','авг.','сент.','окт.','нояб.','дек.')

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
    Размер файла в килобайтах
"""
@register.filter
def size_kb(attached_file):
    try:
        size = attached_file.size
        import math
        return "%s Кб" % (int(math.ceil(float(size)/1024)))
    except:
        return u'размер неизвестен'

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

"""
    Параметры доп. фильтра для отображения в подсказке ссылки
"""
@register.filter
def filter_options(params, folder):
    out = ''

    STATES_PLURAL = {1: u'Новые', 2: u'Принятые', 3: u'Завершенные', 4: u'Завершенные и одобренные'}

    author = assigned_to = status = search_title = ''
    if params.get('status', False):
        if params['status'] in (1, 2, 3, 4):
            status = STATES_PLURAL[params['status']]
        elif params['status'] == 'all_active':
            status = u'Активные'
        out = u"<i>%s</i> + " % status

    if params.get('author', False) and not folder == 'outbox':
        author_id = params['author']
        author = User.objects.get(pk=author_id)
        author = username(author)
        out += u"автор: <i>%s</i> + " % author

    if params.get('assigned_to', False) and not folder == 'inbox':
        assigned_to_id = params['assigned_to']
        assigned_to = User.objects.get(pk=assigned_to_id)
        assigned_to = username(assigned_to)
        out += u"ответственный: <i>%s</i> + " % assigned_to

    if params.get('search_title', False):
        out += u"название: <i>&laquo;%s&raquo;</i>" % params['search_title']
  
    p = re.compile(' \+ $')
    out = p.sub('', out)
    if out:
        out = '<nobr>(' + out + ')</nobr>'
        
    return mark_safe(out)


"""
    Замена '<' и '>' на '&lt;' и '&gt;' в html-тегах за исключением разрешенных;
    расстановка <br /> в конце строк за исключением текста внутри <pre>;
    форматирование списков: "- " в начале строки заменяется на тире.

    Разрешено: <a href="">, <b>, <i>, <pre> (для вставки кода)
"""
def sanitize_html(value):
    out = ''
    linebreaks = True
    lt = '&lt;'
    gt = '&gt;'

    value = re.sub('<', lt, value)
    value = re.sub('>', gt, value)

    # Сформировать теги по найденным совпадениям
    def href_subber(match):
        if re.search('javascript', match.group(2)):
            return '<a href="#">%s</a>' % (match.group(4))
        return '<a href="%s">%s</a>' % (match.group(2), match.group(4))
    def tag_subber(match):
        return '<%s>%s</%s>' % (match.group(1), match.group(2), match.group(1))

    # Ссылки
    href_re = re.compile(lt + '(a +href=")([^"]+)(" ?' + gt + ')' + '(.+?)' + lt + '/a' + gt, re.I)
    value = href_re.sub(href_subber, value)

    # Другие разрешенные теги.
    # Регистр игнорируется, а в тег pre может быть заключено несколько строк.
    for tag in ('b', 'i', 'pre'):
        opt = re.I
        if tag == 'pre':
            opt =  re.I | re.S
        tag_re = re.compile(lt + '(' + tag + ')' + gt + '(.*?)' + lt + '/' + tag + gt, opt)
        value = tag_re.sub(tag_subber, value)

    for line in value.split("\n"):
        if '<pre>' in line: linebreaks = False
        if '</pre>' in line: linebreaks = True
        
        if linebreaks:
            # В списках заменяем минус на тире
            line = re.sub('^- ', '&#151;&nbsp;', line)

            # Выделяем цветом цитаты (если есть '>' в начале строки)
            match = re.search('(^' + gt + '.*)', line)
            if match:
                line = '<span class="comment-quote">' + match.group(0) + '</span>'
            out += line + "<br />"
        else:
            # внутри тега pre заменяем угловые скобки на коды
            # это было сделано вначале, но затем была вставка разрешенных тегов, а они тут не нужны
            line = re.sub('<', lt, line)
            line = re.sub('>', gt, line)
            line = re.sub(lt + 'pre' + gt, '<pre>', line)
            out += line

    return mark_safe(out)
register.filter('sanitize', sanitize_html)