# -*- coding: utf-8 -*-
#------------------------------------------------------------
# opentodo (c) 2009 Mikhail Grigoriev <mgrigoriev@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#------------------------------------------------------------

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, get_list_or_404
from annoying.functions import get_object_or_None
from annoying.decorators import render_to
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage
from todo.models import *
from todo.forms import *

@login_required
def index(request):
    return HttpResponseRedirect(reverse('tasks_list'))

# Список задач
# Доступ: все - видят задачи проектов, участниками которых они являются; администраторы
@login_required
@render_to('todo/todo_list.html')
def list(request, state=0):
    order = direct = ''
    project = None
    filter_on = False
    
    # Получаем проекты и задачи, к которым есть доступ
    projects = Project.objects.available_for(request.user)
    tasks = Task.objects.filter(project__in=projects)
    
    # Пользователи и статусы задач - для фильтра
    users = users_in_projects(projects)
    states = Status.objects.all()
    
    # Запоминаем в сессии id проекта, если передано в GET
    if request.GET.get('project_id', False):
        try:
            project_id = int(request.GET['project_id'])
        except:
            raise Http404
        if project_id != 0:
            project = get_object_or_404(Project, pk=project_id)
        request.session['project_id'] = project_id

    # Запоминаем в сессии группу задач (вх., исх., все) и сортировку, если передано в GET
    if request.GET.get('folder', False):
        request.session['folder'] = request.GET['folder']
    if request.GET.get('order', False):
        request.session['order'] = request.GET['order']
    if request.GET.get('dir', False):
        request.session['dir'] = request.GET['dir']

    # Если сменили группу задач либо настройки фильтра сброшены или изменены, удаляем существующие
    if request.GET.get('folder', False) or (request.GET.get('filter', False) in ('on', 'off')):
        for key in ('author', 'assigned_to', 'status', 'search_title'):
            try:
                del request.session[key]
            except KeyError:
                pass

    # Запоминаем в сессии параметры доп. фильтра
    if request.GET.get('filter', False) == 'on':
        if request.GET.get('author', False):
            request.session['author'] = request.GET['author']
        if request.GET.get('assigned_to', False):
            request.session['assigned_to'] = request.GET['assigned_to']
        if request.GET.get('status', False):
            request.session['status'] = request.GET['status']
        if request.GET.get('search_title', False):
            request.session['search_title'] = request.GET['search_title']

    params = request.session

    # Фильтруем по проекту
    if params.get('project_id', False):
        if params['project_id'] != '0':
            params['project_id'] = int(params['project_id'])
            try:
                project = Project.objects.get(pk=params['project_id'])
                if not project.is_avail(request.user):
                    request.session['project_id'] = '0'
                    return HttpResponseRedirect(reverse('tasks_list'))
                else:
                    tasks = tasks.filter(project__id = params['project_id'])
            except Project.DoesNotExist:
                request.session['project_id'] = '0'
    
    # Фильтруем по группе
    if params.get('folder', False):
        folder = params['folder']
        if not (folder == 'inbox' or folder == 'outbox' or folder == 'all'):
            folder = 'inbox'
    else:
        folder = 'inbox'

    if folder == 'inbox':
        tasks = tasks.filter(assigned_to=request.user)
    elif folder == 'outbox':
        tasks = tasks.filter(author=request.user)
    
    # Доп. фильтр:
    if (params.get('author', False) and not folder == 'outbox') or (params.get('assigned_to', False) and not folder == 'inbox') or params.get('status', False) or params.get('search_title', False):
        filter_on = True
        # Автор
        if params.get('author', False) and not folder == 'outbox':
            try:
                params['author'] = int(params['author'])
                tasks = tasks.filter(author__id=params['author'])
            except ValueError:
                pass
        # Ответственный
        if params.get('assigned_to', False) and not folder == 'inbox':
            try:
                params['assigned_to'] = int(params['assigned_to'])
                tasks = tasks.filter(assigned_to__id=params['assigned_to'])
            except ValueError:
                pass
        # Статус
        if params.get('status', False):            
            if params['status'] == 'all_active':
                tasks = tasks.exclude(status__id=3).exclude(status__id=4)
            try:
                params['status'] = int(params['status'])
                if params['status'] in (1, 2, 3, 4):
                    tasks = tasks.filter(status__id=params['status'])
            except ValueError:
                pass
        # Название
        if params.get('search_title', False):
            tasks = tasks.filter(title__icontains=params['search_title'])

    # Сортировка:
    if params.get('order', False):
        order = params['order']
    else:
        order = 'created_at'
    if params.get('dir', False):
        direct = params['dir']
    else:
        direct = 'desc'

    if order == 'created_at':
        if direct == 'desc':
            tasks = tasks.order_by('-created_at')
        else:
            tasks = tasks.order_by('created_at')
    elif order == 'deadline':
        if direct == 'desc':
            tasks = tasks.order_by('has_deadline', '-deadline', '-created_at')
        else:
            tasks = tasks.order_by('-has_deadline', 'deadline', '-created_at')
    elif order == 'project':
        if direct == 'desc':
            tasks = tasks.order_by('-project__title', '-created_at')
        else:
            tasks = tasks.order_by('project__title', '-created_at')
    elif order == 'task':
        if direct == 'desc':
            tasks = tasks.order_by('-title', '-created_at')
        else:
            tasks = tasks.order_by('title', '-created_at')
    elif order == 'status':
        if direct == 'desc':
            tasks = tasks.order_by('-status__id', '-created_at')
        else:
            tasks = tasks.order_by('status__id', '-created_at')
    elif order == 'assigned_to':
        if direct == 'desc':
            tasks = tasks.order_by('-assigned_to__first_name', '-assigned_to__last_name', '-created_at')
        else:
            tasks = tasks.order_by('assigned_to__first_name', 'assigned_to__last_name', '-created_at')
    elif order == 'author':
        if direct == 'desc':
            tasks = tasks.order_by('-author__first_name', '-author__last_name', '-created_at')
        else:
            tasks = tasks.order_by('author__first_name', 'author__last_name', '-created_at')
    else:
        order = 'created_at'
        direct = 'desc'
        tasks = tasks.order_by('-created_at')
    
    # Разбиение на страницы
    paginator = Paginator(tasks, 100)
    page_num = int(request.GET.get('page', '1'))
    page = paginator.page(page_num)

    return {'tasks': page.object_list, 'page': page, 'paginator': paginator, 'current_page': page_num, 'projects': projects, 'project': project, 'params': params, 'folder': folder, 'order': order, 'dir': direct, 'menu_active': 'tasks', 'users': users, 'states': states, 'filter_on': filter_on}

# Информация о задаче + загрузка файлов
# Доступ: участники проекта, администраторы
@login_required
@render_to('todo/task_details.html')
def details(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if not task.project.is_avail(request.user):
        return HttpResponseForbidden()

    # Список файлов
    attachments = TaskAttach.objects.filter(task=task).order_by('-id')

    # Загрузка файлов
    task_attach = TaskAttach(task=task, author=request.user)
    if request.method == 'POST':
        f = TaskAttachForm(request.POST, request.FILES, instance=task_attach)
        if f.is_valid():
            attach = f.save(commit = False)
            attach.save()
            attach.mail_notify(request.get_host())

            return HttpResponseRedirect(reverse('task_details', args=(task_id,)))
    else:
        f = TaskAttachForm(instance=task_attach)

    return {'task': task, 'menu_active': 'tasks', 'attachments': attachments, 'f': f}

# Редактирование задачи
# Доступ: автор задачи, администраторы
@login_required
@render_to('todo/task_edit.html')
def edit(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if not task.project.is_avail(request.user):
        return HttpResponseForbidden()

    author = get_object_or_None(User, id=task.author_id)
    if not (request.user.has_perm('todo.change_task') or request.user == author):
        return HttpResponseForbidden()

    if request.method == 'POST':
        f = TaskForm(request.user, request.POST, instance = task)
        if f.is_valid():
            t = f.save(commit = False)
            if t.deadline:
                t.has_deadline = True
            else:
                t.has_deadline = False

            assigned_to_id = request.POST.get('assigned_to', '')
            if assigned_to_id:
                t.assigned_to = User.objects.get(pk=assigned_to_id)
            else:
                t.assigned_to = None
            t.save()
            return HttpResponseRedirect(reverse('task_details', args=(task_id,)))
    else:
        f = TaskForm(request.user, instance = task)
    
    projects = Project.objects.available_for(request.user)
    users = users_in_projects(projects)

    return {'form': f, 'task': task, 'users': users, 'menu_active': 'tasks'}

# Добавление задачи
# Доступ: участники проекта, администраторы
@login_required
@render_to('todo/task_edit.html')
def add_task(request):
    projects = Project.objects.available_for(request.user)
    if not projects:
        return {'no_available_projects': True, 'menu_active': 'tasks', 'add': True}

    if request.method == 'POST':
        f = TaskForm(request.user, request.POST)
        if f.is_valid():
            if not f.cleaned_data['project'].is_avail(request.user):
                return HttpResponseForbidden()

            t = f.save(commit = False)
            if t.deadline:
                t.has_deadline = True
            t.author = request.user
            t.save()

            assigned_to_id = request.POST.get('assigned_to', '')
            if assigned_to_id:
                t.assigned_to = User.objects.get(pk=assigned_to_id)
                t.save()
                t.mail_notify(request.get_host())
            
            return HttpResponseRedirect(reverse('task_details', args=(t.id,)))
    else:        
        init_data = {
            'project': request.session.get('project_id',''),
        }
        f = TaskForm(request.user, initial=init_data)
    
    users = users_in_projects(projects)

    return {'form': f, 'add': True, 'users': users, 'menu_active': 'tasks'}

# Удаление задачи
# Доступ: автор задачи, администраторы
@login_required
def delete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if not task.project.is_avail(request.user):
        return HttpResponseForbidden()

    author = get_object_or_None(User, id=task.author_id)
    if not (request.user.has_perm('todo.delete_task') or request.user == author):
        return HttpResponseForbidden()

    task.delete()
    return HttpResponseRedirect(reverse('tasks_list'))

# Список проектов
# Доступ: все - видят проекты, в которых участвуют; администраторы
@login_required
@render_to('todo/projects_list.html')
def projects_list(request, state=0):
    projects = Project.objects.available_for(request.user)
    return {'projects': projects, 'menu_active': 'projects'}

# Информация о проекте + загрузка файлов
# Доступ: участники проекта, администраторы
@login_required
@render_to('todo/project_details.html')
def project_details(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.is_avail(request.user):
        return HttpResponseForbidden()

    # Список файлов
    attachments = ProjectAttach.objects.filter(project=project).order_by('-id')
    
    # Загрузка файлов
    project_attach = ProjectAttach(project=project, author=request.user)
    if request.method == 'POST':
        f = ProjectAttachForm(request.POST, request.FILES, instance=project_attach)
        if f.is_valid():
            attach = f.save(commit = False)
            attach.save()
            return HttpResponseRedirect(reverse('project_details', args=(project_id,)))
    else:
        f = ProjectAttachForm(instance=project_attach)

    return {'project':project, 'menu_active':'projects', 'attachments':attachments, 'f':f}

# Удаление файла, прикрепленного к проекту
# Доступ: автор файла, администраторы
@login_required
def delete_project_attach(request, attach_id):
    attach = get_object_or_404(ProjectAttach, pk=attach_id)

    if not attach.project.is_avail(request.user):
        return HttpResponseForbidden()

    author = get_object_or_None(User, id=attach.author_id)
    if not (request.user.has_perm('todo.delete_projectattach') or request.user == author):
        return HttpResponseForbidden()

    attach.delete()
    return HttpResponseRedirect(reverse('project_details', args=(attach.project.id,)))
    

# Удаление файла, прикрепленного к задаче
# Доступ: автор файла, администраторы
@login_required
def delete_task_attach(request, attach_id):
    attach = get_object_or_404(TaskAttach, pk=attach_id)

    if not attach.task.project.is_avail(request.user):
        return HttpResponseForbidden()

    author = get_object_or_None(User, id=attach.author_id)
    if not (request.user.has_perm('todo.delete_taskattach') or request.user == author):
        return HttpResponseForbidden()

    attach.delete()
    return HttpResponseRedirect(reverse('task_details', args=(attach.task.id,)))

# Добавление проекта
# Доступ: администраторы
@login_required
@render_to('todo/project_edit.html')
def add_project(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    if request.method == 'POST':
        f = ProjectForm(request.POST)
        if f.is_valid():
            prj = f.save(commit = False)
            prj.author = request.user
            prj.save()            
            f.save_m2m()
            return HttpResponseRedirect(reverse('projects_list'))
    else:
        f = ProjectForm()
    
    return {'form': f, 'add': True, 'menu_active': 'projects'}

# Редактирование проекта
# Доступ: администраторы
@login_required
@render_to('todo/project_edit.html')
def edit_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not request.user.is_superuser:
        return HttpResponseForbidden()

    if request.method == 'POST':
        f = ProjectForm(request.POST, instance = project)
        if f.is_valid():
            p = f.save(commit = False)
            p.save()
            f.save_m2m()
            return HttpResponseRedirect(reverse('project_details', args=(project_id,)))
    else:
        f = ProjectForm(instance = project)

    return {'form': f, 'project': project, 'menu_active': 'projects'}

# Удаление проекта
# Доступ: администраторы
@login_required
@render_to('todo/project_delete_cannot.html')
def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not project.is_avail(request.user):
        return HttpResponseForbidden()

    author = get_object_or_None(User, id=project.author_id)
    if not (request.user.has_perm('todo.delete_project') or request.user == author):
        return HttpResponseForbidden()

    if project.tasks_count > 0:
        return {'project': project, 'menu_active': 'projects'}
    else:
        project.delete()
        return HttpResponseRedirect(reverse('projects_list'))

# Принять задачу
# Доступ: assigned_to (тот, кому назначена задача)
@login_required
def task_to_accepted(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    assigned_to = get_object_or_None(User, id=task.assigned_to_id)
    if not request.user == assigned_to:
        return HttpResponseForbidden()

    task.status = Status.objects.get(pk=2)
    task.save()
    task.mail_notify(request.get_host())    

    return HttpResponseRedirect(reverse('task_details', args=(task_id,)))

# Завершить задачу
# Доступ: assigned_to (тот, кому назначена задача)
@login_required
def task_to_done(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    assigned_to = get_object_or_None(User, id=task.assigned_to_id)
    if not request.user == assigned_to:
        return HttpResponseForbidden()

    task.status = Status.objects.get(pk=3)
    task.save()
    task.mail_notify(request.get_host())

    return HttpResponseRedirect(reverse('task_details', args=(task_id,)))

# Подтвердить завершение задачи (контроль)
# Доступ: author (тот, кто назначил)
@login_required
def task_to_checked(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    author = get_object_or_None(User, id=task.author_id)
    if not request.user == author:
        return HttpResponseForbidden()

    task.status = Status.objects.get(pk=4)
    task.save()
    task.mail_notify(request.get_host())

    return HttpResponseRedirect(reverse('task_details', args=(task_id,)))

# Открыть заново задачу
# Доступ: author (тот, кто назначил)
@login_required
def task_to_new(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    author = get_object_or_None(User, id=task.author_id)
    if not request.user == author:
        return HttpResponseForbidden()

    task.status = Status.objects.get(pk=1)
    task.save()
    task.mail_notify(request.get_host(), True)
    return HttpResponseRedirect(reverse('task_details', args=(task_id,)))

# Добавление комментария к задаче
# Доступ: участники проекта
@login_required
def add_comment(request, task_id):
    if request.method == 'POST' and request.POST.get('message', '') != '':
        task = get_object_or_404(Task, pk=task_id)

        if not task.project.is_avail(request.user):
            return HttpResponseForbidden()

        message = request.POST.get('message', '')
        comment = Comment(author=request.user, task=task, message=message)
        if request.POST.get('reply_to', False):
            try:
                reply_to_id = int(request.POST['reply_to'])
                try:
                    comment.reply_to = Comment.objects.get(pk=reply_to_id)
                except Comment.DoesNotExist:
                    pass
            except ValueError:
                pass
        comment.save()
        comment.mail_notify(request.get_host())

    return HttpResponseRedirect(reverse('task_details', args=(task_id,)) + '#comment_form')

# Удаление комментария к задаче
# Доступ: автор комментария
@login_required
def del_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
 
    author = get_object_or_None(User, id=comment.author_id)
    if not comment.task.project.is_avail(request.user):
        return HttpResponseForbidden()

    if not (request.user.has_perm('todo.delete_comment') or request.user == author):
        return HttpResponseForbidden()
    comment.delete()
    return HttpResponseRedirect(reverse('task_details', args=(comment.task.id,)))

# Список пользователей, имеющих доступ к проекту, в формате JSON
# Используется в форме задачи, подгружается в поле 'Ответственный' при выборе проекта.
# Если выбран проект, то в списке пользователей - участники проекта, администраторы.
# Если проект не выбран - участники всех проектов, к которым имеет доступ текущий пользователь; администраторы.
@login_required
@render_to('todo/json_project_users.html')
def json_project_users(request):
    if request.GET.get('id', '') != '':
        project_id = request.GET['id']
        projects = get_list_or_404(Project, pk=project_id)
        if not projects[0].is_avail(request.user):
            return HttpResponseForbidden()
    else:
        projects = Project.objects.available_for(request.user)

    users = users_in_projects(projects)
    return {'users': users}

# Отображение страницы 403 Forbidden - доступ запрещен
@login_required
def forbidden(request, template_name='403.html'):
    t = loader.get_template(template_name)
    return HttpResponseForbidden(t.render(RequestContext(request)))