# -*- coding: utf-8 -*-

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpRequest, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage
from todo.models import *
from todo.forms import *
from django.db.models import Q

@login_required
def index(request):
    return HttpResponseRedirect(reverse('tasks_list'))

# Список задач
# access control +
@login_required
def list(request, state=0):
    order = direct = ''
    project = None
    filter_on = False
    
    # Получаем проекты и задачи, к которым есть доступ
    projects = request.user.avail_projects.all()
    tasks = Task.objects.filter(project__in=projects)
    
    # Пользователи и статусы задач - для фильтра
    users = User.objects.filter(avail_projects__in=projects).distinct().order_by('first_name', 'last_name')
    states = Status.objects.all()
    
    # Запоминаем в сессии id проекта, если передано в GET
    if request.GET.get('project_id', False):
        try:
            project_id = int(request.GET['project_id'])
        except:
            raise Http404
        if project_id != 0:
            try:
                project = Project.objects.get(pk=project_id)
            except Project.DoesNotExist:
                raise Http404
        request.session['project_id'] = project_id

    # Запоминаем в сессии группу задач (вх., исх., все) и сортировку, если передано в GET
    if request.GET.get('folder', False):
        request.session['folder'] = request.GET['folder']
    if request.GET.get('order', False):
        request.session['order'] = request.GET['order']
    if request.GET.get('dir', False):
        request.session['dir'] = request.GET['dir']

    # Если настройки фильтра сброшены или изменены, удаляем существующие
    if request.GET.get('filter', False) in ('on', 'off'):
        for key in ('author', 'assigned_to', 'status'):
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
    if (params.get('author', False) and not folder == 'outbox') or (params.get('assigned_to', False) and not folder == 'inbox') or params.get('status', False):
        filter_on = True
        # Автор
        if params.get('author', False):
            try:
                params['author'] = int(params['author'])
                tasks = tasks.filter(author__id=params['author'])
            except ValueError:
                pass
        # Ответственный
        if params.get('assigned_to', False):
            try:
                params['assigned_to'] = int(params['assigned_to'])
                tasks = tasks.filter(assigned_to__id=params['assigned_to'])
            except ValueError:
                pass
        # Статус
        if params.get('status', False):
            if params['status'] in ('1','2','3','4'):
                params['status'] = int(params['status'])
                tasks = tasks.filter(status__id=params['status'])
            elif params['status'] == 'all_active':
                tasks = tasks.exclude(status__id=3).exclude(status__id=4)
            elif params['status'] == 'all_done':
                tasks = tasks.exclude(status__id=1).exclude(status__id=2)

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

    return render_to_response('todo/todo_list.html', {'tasks':page.object_list, 'page':page, 'paginator':paginator, 'current_page':page_num, 'projects':projects, 'project':project, 'params':params, 'folder':folder, 'order':order, 'dir':direct, 'menu_active':'tasks', 'users':users, 'states':states, 'filter_on':filter_on }, context_instance=RequestContext(request))

# Информация о задаче + загрузка файлов
# access control +
@login_required
def details(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404

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

    return render_to_response('todo/task_details.html', {'task': task, 'menu_active':'tasks', 'attachments':attachments, 'f':f }, context_instance=RequestContext(request))

# Редактировать задачу
# access control +
@login_required
def edit(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404

    if not task.project.is_avail(request.user):
        return HttpResponseForbidden()

    try:
        author = task.author
    except User.DoesNotExist:
        author = None

    if not (request.user.has_perm('todo.change_task') or request.user == author):
        return HttpResponseForbidden()

    if request.method == 'POST':
        f = TaskFormEdit(request.user, request.POST, instance = task)
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
        f = TaskFormEdit(request.user, instance = task)
    
    projects = request.user.avail_projects.all()    
    users = User.objects.filter(avail_projects__in=projects).distinct().order_by('first_name', 'last_name')

    return render_to_response('todo/task_edit.html', {'form': f, 'task': task, 'users': users, 'menu_active':'tasks' }, context_instance=RequestContext(request))

# Добавить задачу
@login_required
def add_task(request):
    if request.method == 'POST':
        f = TaskFormEdit(request.user, request.POST)
        if f.is_valid():
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
        f = TaskFormEdit(request.user, initial=init_data)
    
    projects = request.user.avail_projects.all()    
    users = User.objects.filter(avail_projects__in=projects).distinct().order_by('first_name', 'last_name')

    return render_to_response('todo/task_edit.html', {'form': f, 'add': True, 'users': users, 'menu_active':'tasks' }, context_instance=RequestContext(request))

# Удалить задачу
# access control +
@login_required
def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404

    if not task.project.is_avail(request.user):
        return HttpResponseForbidden()

    try:
        author = task.author
    except User.DoesNotExist:
        author = None

    if not (request.user.has_perm('todo.delete_task') or request.user == author):
        return HttpResponseForbidden()

    task.delete()
    return HttpResponseRedirect(reverse('tasks_list'))

# Список проектов
# access control +
@login_required
def projects_list(request, state=0):
    projects = request.user.avail_projects.order_by('title')
    return render_to_response('todo/projects_list.html', {'projects': projects, 'menu_active':'projects' }, context_instance=RequestContext(request))

# Информация о проекте + загрузка файлов
# access control +
@login_required
def project_details(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        raise Http404

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

    return render_to_response('todo/project_details.html', {'project':project, 'menu_active':'projects', 'attachments':attachments, 'f':f }, context_instance=RequestContext(request))

# Удалить файл, прикрепленный к проекту
# access control +
@login_required
def delete_project_attach(request, attach_id):
    try:
        attach = ProjectAttach.objects.get(pk=attach_id)
    except ProjectAttach.DoesNotExist:
        raise Http404
    try:
        author = attach.author
    except User.DoesNotExist:
        author = None

    if not attach.project.is_avail(request.user):
        return HttpResponseForbidden()

    if not (request.user.has_perm('todo.delete_projectattach') or request.user == author):
        return HttpResponseForbidden()

    attach.delete()
    return HttpResponseRedirect(reverse('project_details', args=(attach.project.id,)))
    

# Удалить файл, прикрепленный к задаче
# access control +
@login_required
def delete_task_attach(request, attach_id):
    try:
        attach = TaskAttach.objects.get(pk=attach_id)
    except TaskAttach.DoesNotExist:
        raise Http404
    try:
        author = attach.author
    except User.DoesNotExist:
        author = None

    if not attach.task.project.is_avail(request.user):
        return HttpResponseForbidden()

    if not (request.user.has_perm('todo.delete_taskattach') or request.user == author):
        return HttpResponseForbidden()

    attach.delete()
    return HttpResponseRedirect(reverse('task_details', args=(attach.task.id,)))

# Добавить проект
@login_required
def add_project(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    if request.method == 'POST':
        f = ProjectFormEdit(request.user, request.POST)
        if f.is_valid():
            prj = f.save(commit = False)
            prj.author = request.user
            prj.save()            
            f.save_m2m()
            for su in User.objects.filter(is_superuser=True):
                prj.users.add(su)
            return HttpResponseRedirect(reverse('projects_list'))
    else:
        f = ProjectFormEdit(request.user)
    
    return render_to_response('todo/project_edit.html', {'form': f, 'add': True, 'menu_active':'projects' }, context_instance=RequestContext(request))

# Редактировать проект
# access control +
@login_required
def edit_project(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Task.DoesNotExist:
        raise Http404

    if not request.user.is_superuser:
        return HttpResponseForbidden()

    if request.method == 'POST':
        f = ProjectFormEdit(request.user, request.POST, instance = project)
        if f.is_valid():
            p = f.save(commit = False)
            p.save()
            f.save_m2m()
            for su in User.objects.filter(is_superuser=True):
                p.users.add(su)
            return HttpResponseRedirect(reverse('project_details', args=(project_id,)))
    else:
        f = ProjectFormEdit(request.user, instance = project)
    
    return render_to_response('todo/project_edit.html', {'form': f, 'project': project, 'menu_active':'projects' }, context_instance=RequestContext(request))

# Удалить проект
# access control +
@login_required
def delete_project(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        raise Http404

    if not project.is_avail(request.user):
        return HttpResponseForbidden()

    try:
        author = project.author
    except User.DoesNotExist:
        author = None

    if not (request.user.has_perm('todo.delete_project') or request.user == author):
        return HttpResponseForbidden()

    if project.tasks_count > 0:
        return render_to_response('todo/project_delete_cannot.html', {'project': project, 'menu_active':'projects' }, context_instance=RequestContext(request))
    else:
        project.delete()
        return HttpResponseRedirect(reverse('projects_list'))
        

# Принять задачу
# Имеет право: assigned_to (тот, кому назначена задача)
@login_required
def task_to_accepted(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404
    try:
        assigned_to = task.assigned_to
    except User.DoesNotExist:
        assigned_to = None

    if not request.user == assigned_to:
        return HttpResponseForbidden()

    task.status = Status.objects.get(pk=2)
    task.save()
    task.mail_notify(request.get_host())    

    return HttpResponseRedirect(reverse('task_details', args=(task_id,)))

# Завершить задачу
# Имеет право: assigned_to (тот, кому назначена задача)
@login_required
def task_to_done(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404
    try:
        assigned_to = task.assigned_to
    except User.DoesNotExist:
        assigned_to = None

    if not request.user == assigned_to:
        return HttpResponseForbidden()

    task.status = Status.objects.get(pk=3)
    task.save()
    task.mail_notify(request.get_host())

    return HttpResponseRedirect(reverse('task_details', args=(task_id,)))

# Подтвердить завершение задачи (контроль)
# Имеет право: author (тот, кто назначил)
@login_required
def task_to_checked(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404
    try:
        author = task.author
    except User.DoesNotExist:
        author = None

    if not request.user == author:
        return HttpResponseForbidden()

    task.status = Status.objects.get(pk=4)
    task.save()
    task.mail_notify(request.get_host())

    return HttpResponseRedirect(reverse('task_details', args=(task_id,)))

# Открыть заново задачу
# Имеет право: author (тот, кто назначил)
@login_required
def task_to_new(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404
    try:
        author = task.author
    except User.DoesNotExist:
        author = None

    if not request.user == author:
        return HttpResponseForbidden()

    task.status = Status.objects.get(pk=1)
    task.save()
    task.mail_notify(request.get_host(), True)
    return HttpResponseRedirect(reverse('task_details', args=(task_id,)))

# Добавить комментарий к задаче
# access control +
@login_required
def add_comment(request, task_id):    
    if request.method == 'POST' and request.POST.get('message', '') != '':
        try:
            t = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise Http404

        if not t.project.is_avail(request.user):
            return HttpResponseForbidden()

        m = request.POST.get('message', '')
        c = Comment(author=request.user, task=t, message=m)
        c.save()
        c.mail_notify(request.get_host())

    return HttpResponseRedirect(reverse('task_details', args=(task_id,)))

# Удалить комментарий к задаче
@login_required
def del_comment(request, comment_id):
    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        raise Http404
    try:
        author = comment.author
    except User.DoesNotExist:
        author = None

    if not comment.task.project.is_avail(request.user):
        return HttpResponseForbidden()

    if not (request.user.has_perm('todo.delete_comment') or request.user == author):
        return HttpResponseForbidden()
    comment.delete()
    return HttpResponseRedirect(reverse('task_details', args=(comment.task.id,)))

# Список пользователей, имеющих доступ к проекту, в формате JSON (для формы задачи)
@login_required
def json_project_users(request):
    if request.GET.get('id', '') != '':
        project_id = request.GET['id']
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise Http404
        if not project.is_avail(request.user):
            return HttpResponseForbidden()
        users = project.users.order_by('first_name', 'last_name')
    else:
        projects = request.user.avail_projects.all()
        users = User.objects.filter(avail_projects__in=projects).distinct().order_by('first_name', 'last_name')        
    return render_to_response('todo/json_project_users.html', {'users': users}, context_instance=RequestContext(request))


# 403 Forbidden
@login_required
def forbidden(request, template_name='403.html'):
    t = loader.get_template(template_name)
    return HttpResponseForbidden(t.render(RequestContext(request)))