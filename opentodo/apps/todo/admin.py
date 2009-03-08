# -*- coding: utf-8 -*-

from django.contrib import admin
from todo.models import Project

class ProjectAdmin(admin.ModelAdmin):
    pass

admin.site.register(Project, ProjectAdmin)