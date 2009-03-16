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