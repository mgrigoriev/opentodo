# -*- coding: utf-8 -*-

from django.forms import ModelForm
from django import forms
from todo.models import *

class OpentodoModelForm(ModelForm):
    class Media:
        css = { 'all': ('forms.css',) }
        js = ('jquery-1.2.6.pack.js', 'jquery.formvalidation.1.1.5.js',)

# Форма редактирования проекта
class ProjectFormEdit(OpentodoModelForm):
    title = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Project
        fields = ('title', 'info')

# Форма редактирования задачи
class TaskFormEdit(OpentodoModelForm):
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