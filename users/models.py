# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ROLE_CHOICES = [(STUDENT, 'Студент'), (TEACHER, 'Преподаватель')]

    email = models.EmailField(unique=True)
    role  = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)

    groups = models.ManyToManyField(
        'auth.Group', related_name='lms_users', blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', related_name='lms_users', blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
