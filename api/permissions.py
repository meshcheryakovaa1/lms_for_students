from rest_framework.permissions import BasePermission

from users.models import User


class IsTeacher(BasePermission):
    """Доступ только для преподавателей."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.TEACHER)


class IsStudent(BasePermission):
    """Доступ только для студентов."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.STUDENT)


class IsOwnerOrTeacher(BasePermission):
    """Студент — только свои записи. Преподаватель — любые."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.TEACHER:
            return True
        return obj.student == request.user
