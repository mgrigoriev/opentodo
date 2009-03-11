# -*- coding: utf-8 -*-

from django.forms import ModelForm
from django import forms
from todo.models import *
from django.contrib.auth.models import User


def username(user):
    try:
        if user.first_name and user.last_name:
            return "%s %s" % (user.first_name, user.last_name)
        else:
            return "%s" % user.username
    except:
        return ""

class OpentodoModelForm(ModelForm):
    class Media:
        css = { 'all': ('forms.css',) }
        js = ('jquery.formvalidation.1.1.5.js',)

# Форма редактирования проекта
class ProjectFormEdit(OpentodoModelForm):
    # Переопределяем конструктор, чтобы исключить из списка users (пользователи имеющие доступ к проекту) автора
    # подразумевается что автор проекта имеет доступ по умолчанию и нет возможности его убрать из команды
    user_choices = []
    initial_user_choices = []
    user_list = User.objects.order_by('first_name', 'last_name')
    for item in user_list:
        user_choices.append((item.id, username(item)))
        if item.is_superuser:
            initial_user_choices.append(item.id)
            
    users = forms.MultipleChoiceField(choices=user_choices, widget=forms.CheckboxSelectMultiple(), required=False)
    title = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Project
        fields = ('title', 'info')

# Форма редактирования задачи
class TaskFormEdit(OpentodoModelForm):
    def __init__(self, user, *args, **kwargs):
        super(TaskFormEdit, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = User.objects.get(pk=user.id).avail_projects.order_by('title')

    title = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Task
        fields = ('project', 'title', 'info', 'deadline')
    class Media:
        css = { 'all': ('ui.datepicker.css',) }
        js = ('ui.datepicker.js',)

# Форма загрузки файлов для проектов
class ProjectAttachForm(OpentodoModelForm):
    class Meta:
        model = ProjectAttach
        fields = ('attached_file',)

# Форма загрузки файлов для задач
class TaskAttachForm(OpentodoModelForm):
    class Meta:
        model = TaskAttach
        fields = ('attached_file',)