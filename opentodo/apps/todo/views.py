# -*- coding: utf-8 -*-

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpRequest
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage
from todo.models import *
from todo.forms import *

@login_required
def index(request):
    return HttpResponseRedirect(reverse('tasks_list'))

# Список задач
@login_required
def list(request, state=0):
    order = direct = ''
    project = None

    projects = Project.objects.all()
    tasks = Task.objects.all()
    
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
    if request.GET.get('folder', False):
        request.session['folder'] = request.GET['folder']
    if request.GET.get('order', False):
        request.session['order'] = request.GET['order']
    if request.GET.get('dir', False):
        request.session['dir'] = request.GET['dir']
    if request.GET.get('hide_done', False):
        request.session['hide_done'] = request.GET['hide_done']

    params = request.session

    if params.get('project_id', False):
        if params['project_id'] != '0':
            params['project_id'] = int(params['project_id'])
            try:
                project = Project.objects.get(pk=params['project_id'])
                tasks = tasks.filter(project__id = params['project_id'])
            except Project.DoesNotExist:
                request.session['project_id'] = '0'
 
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

    if params.get('hide_done', False) == '1':
        hide_done = True
        tasks = tasks.exclude(status__id=3).exclude(status__id=4)
    else:
        hide_done = False


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

    paginator = Paginator(tasks, 100)
    page_num = int(request.GET.get('page', '1'))
    page = paginator.page(page_num)

    return render_to_response('todo/todo_list.html', {'tasks':page.object_list, 'page':page, 'paginator':paginator, 'current_page':page_num, 'projects':projects, 'project':project, 'query':params, 'folder':folder, 'order':order, 'dir':direct, 'hide_done':hide_done, 'menu_active':'tasks' }, context_instance=RequestContext(request))

# Информация о задаче + загрузка файлов
@login_required
def details(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404

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
@login_required
def edit(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404

    try:
        author = task.author
    except User.DoesNotExist:
        author = None

    if not (request.user.has_perm('todo.change_task') or request.user == author):
        return HttpResponse("Недостаточно прав для выполнения действия.")

    if request.method == 'POST':
        f = TaskFormEdit(request.POST, instance = task)
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
        f = TaskFormEdit(instance = task)
    
    users = User.objects.all().order_by('first_name', 'last_name')

    return render_to_response('todo/task_edit.html', {'form': f, 'task': task, 'users': users, 'menu_active':'tasks' }, context_instance=RequestContext(request))

# Добавить задачу
@login_required
def add_task(request):
    if request.method == 'POST':
        f = TaskFormEdit(request.POST)
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
        f = TaskFormEdit(initial=init_data)
    
    users = User.objects.all().order_by('first_name', 'last_name')

    return render_to_response('todo/task_edit.html', {'form': f, 'add': True, 'users': users, 'menu_active':'tasks' }, context_instance=RequestContext(request))

# Удалить задачу
@login_required
def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404

    try:
        author = task.author
    except User.DoesNotExist:
        author = None

    if not (request.user.has_perm('todo.delete_task') or request.user == author):
        return HttpResponse("Недостаточно прав для выполнения действия.")

    task.delete()
    return HttpResponseRedirect(reverse('tasks_list'))

# Список проектов
@login_required
def projects_list(request, state=0):
    projects = Project.objects.all().order_by('title')

    return render_to_response('todo/projects_list.html', {'projects': projects, 'menu_active':'projects' }, context_instance=RequestContext(request))

# Информация о проекте + загрузка файлов
@login_required
def project_details(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        raise Http404

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

    if not (request.user.has_perm('todo.delete_projectattach') or request.user == author):
        return HttpResponse("Недостаточно прав для выполнения действия.")

    attach.delete()
    return HttpResponseRedirect(reverse('project_details', args=(attach.project.id,)))
    

# Удалить файл, прикрепленный к задаче
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

    if not (request.user.has_perm('todo.delete_taskattach') or request.user == author):
        return HttpResponse("Недостаточно прав для выполнения действия.")

    attach.delete()
    return HttpResponseRedirect(reverse('task_details', args=(attach.task.id,)))


# Добавить проект
@login_required
def add_project(request):
    if request.method == 'POST':
        f = ProjectFormEdit(request.POST)
        if f.is_valid():
            prj = f.save(commit = False)
            prj.author = request.user
            prj.save()
            return HttpResponseRedirect(reverse('projects_list'))
    else:
        f = ProjectFormEdit()
    
    return render_to_response('todo/project_edit.html', {'form': f, 'add': True, 'menu_active':'projects' }, context_instance=RequestContext(request))

# Редактировать проект
@login_required
def edit_project(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Task.DoesNotExist:
        raise Http404

    try:
        author = project.author
    except User.DoesNotExist:
        author = None

    if not (request.user.has_perm('todo.change_project') or request.user == author):
        return HttpResponse("Недостаточно прав для выполнения действия.")

    if request.method == 'POST':
        f = ProjectFormEdit(request.POST, instance = project)
        if f.is_valid():
            p = f.save(commit = False)
            p.save()
            return HttpResponseRedirect(reverse('project_details', args=(project_id,)))
    else:
        f = ProjectFormEdit(instance = project)
    
    return render_to_response('todo/project_edit.html', {'form': f, 'project': project, 'menu_active':'projects' }, context_instance=RequestContext(request))

# Удалить проект
@login_required
def delete_project(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        raise Http404

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
        return HttpResponse("Недостаточно прав для выполнения действия.")

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
        return HttpResponse("Недостаточно прав для выполнения действия.")

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
        return HttpResponse("Недостаточно прав для выполнения действия.")

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
        return HttpResponse("Недостаточно прав для выполнения действия.")

    task.status = Status.objects.get(pk=1)
    task.save()
    task.mail_notify(request.get_host(), True)
    return HttpResponseRedirect(reverse('task_details', args=(task_id,)))

# Добавить комментарий к задаче
@login_required
def add_comment(request, task_id):    
    if request.method == 'POST' and request.POST.get('message', '') != '':
        try:
            t = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise Http404
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
    if not (request.user.has_perm('todo.delete_comment') or request.user == author):
        return HttpResponse("Недостаточно прав для выполнения действия.")
    comment.delete()
    return HttpResponseRedirect(reverse('task_details', args=(comment.task.id,)))