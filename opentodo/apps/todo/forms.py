# -*- coding: utf-8 -*-

from django.forms import ModelForm
from django import forms
from todo.models import *
from django.contrib.auth.models import User
from todo.templatetags.todo_extras import username

class OpentodoModelForm(ModelForm):
    class Media:
        css = { 'all': ('forms.css',) }
        js = ('jquery.formvalidation.1.1.5.js',)

# Форма редактирования проекта
class ProjectForm(OpentodoModelForm):
    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        user_choices = []
        user_list = User.objects.order_by('first_name', 'last_name')
        for item in user_list:
            user_choices.append((item.id, username(item)))
        self.fields['users'].choices = user_choices

    title = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Project
        fields = ('title', 'info', 'users')

# Форма редактирования задачи
class TaskForm(OpentodoModelForm):
    def __init__(self, user, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.available_for(user)

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