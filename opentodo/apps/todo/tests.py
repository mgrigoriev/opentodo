# -*- coding: utf-8 -*-

from django.test import TestCase
from django.test.client import Client
from django.conf import settings

from django.contrib.auth.models import User
from todo.models import Status, Task, Project, Comment

class TestViews(TestCase):
    fixtures = ['todo.json']

    def setUp(self):
        self.c = Client()

        # user pk=1
        user = User.objects.create(username="admin", email="admin@localhost", is_active=1, is_staff=1)
        user.set_password('password')
        user.save()

        # user pk=2, без email
        user = User.objects.create(username="tester", email="", is_active=1, is_staff=1)
        user.set_password('password')
        user.save()

    def urltest(self, url, status_code):
        rs = self.c.get(url)
        self.failUnless(rs)
        print url
        self.assertEquals(rs.status_code, status_code, '%s returned %s, %s was expected' % (url, rs.status_code, status_code))

    """
        проверяем запросы GET
    """
    def test_user_urls(self):
        rs = self.c.post('/accounts/login/', {'username':'admin', 'password':'password'})
        self.failUnless(rs)

        urls = [
                    ("/", 302),
                    ("/tasks/new/", 200),
                    ("/tasks/1/comments/new/", 302),
                    ("/tasks/delete_comment/1/", 302),
                    ("/tasks/1/", 200),
                    ("/tasks/1/edit/", 200),
                    ("/tasks/1/to_accepted/", 302),
                    ("/tasks/1/to_done/", 302),
                    ("/tasks/1/to_checked/", 302),
                    ("/tasks/1/to_new/", 302),
                    ("/tasks/1/delete/", 302),
                    ("/projects/", 200),
                    ("/projects/new/", 200 ),
                    ("/projects/2/", 200),
                    ("/projects/2/edit/", 200),
                    ("/projects/2/delete/", 302),
               ]

        for url in urls:
            self.urltest(url[0], url[1])


    """
        добавление задачи
    """
    def test_add_task(self):
        rs = self.c.post('/accounts/login/', {'username':'admin', 'password':'password'})
        self.failUnless(rs)
        
        # правильные данные (ожидаем 302 - редирект на просмотр задачи)
        rs = self.c.post("/tasks/new/", {'project':'1', 'title':'New task', 'assigned_to':'1', 'deadline':'2008-12-12'})
        self.assertEquals(rs.status_code, 302)

        # правильные данные, ответственный - пользователь без email (ожидаем 302 - редирект на просмотр задачи)
        rs = self.c.post("/tasks/new/", {'project':'1', 'title':'One more', 'assigned_to':'2', 'deadline':'2008-12-12'})
        self.assertEquals(rs.status_code, 302)

        # правильные данные, ответственный не назначен (ожидаем 302 - редирект на просмотр задачи)
        rs = self.c.post("/tasks/new/", {'project':'1', 'title':'Not assigned task'})
        self.assertEquals(rs.status_code, 302)

        # неверный формат даты (ожидаем 200)
        rs = self.c.post("/tasks/new/", {'project':'1', 'title':'New task', 'deadline': 'invalid_date'})
        self.assertEquals(rs.status_code, 200)
        
        # не введена задача (ожидаем 200)
        rs = self.c.post("/tasks/new/", {'project':'1', 'title':''})
        self.assertEquals(rs.status_code, 200)

    """
        редактирование задачи
    """
    def test_edit_task(self):
        rs = self.c.post('/accounts/login/', {'username':'admin', 'password':'password'})
        self.failUnless(rs)
        
        # правильные данные (ожидаем 302 - редирект на просмотр задачи)
        rs = self.c.post("/tasks/1/edit/", {'project':'1', 'title':'Edited task', 'assigned_to':'1'})
        self.assertEquals(rs.status_code, 302)

    """
        добавление проекта
    """
    def test_add_project(self):
        rs = self.c.post('/accounts/login/', {'username':'admin', 'password':'password'})        
        self.failUnless(rs)

        # правильные данные (ожидаем 302)
        rs = self.c.post("/projects/new/", {'title':'New project'})
        self.assertEquals(rs.status_code, 302)

        # не введено название проекта
        rs = self.c.post("/projects/new/", {'title':''})
        self.assertEquals(rs.status_code, 200)