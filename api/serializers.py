from django.conf import settings
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from lessons.models import LessonEntry
from lessons.yadisk import upload_to_yadisk
from users.models import User


# ── Пользователи ─────────────────────────────────────────────────────────────

class UserReadSerializer(DjoserUserSerializer):
    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role')


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password', 'role')


# ── Записи занятий ────────────────────────────────────────────────────────────

class LessonEntrySerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        write_only=True, required=False, allow_null=True,
        help_text='Файл загружается на Яндекс Диск',
    )
    file_name = serializers.CharField(read_only=True)
    file_url = serializers.URLField(read_only=True)
    grade = serializers.IntegerField(read_only=True)
    graded_by = serializers.StringRelatedField(read_only=True)
    student = UserReadSerializer(read_only=True)

    class Meta:
        model = LessonEntry
        fields = [
            'id', 'student', 'date', 'comment',
            'file', 'file_name', 'file_url',
            'grade', 'graded_by',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['student', 'grade', 'graded_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        file = validated_data.pop('file', None)
        entry = LessonEntry(**validated_data)
        if file is not None:
            self._upload(entry, file)
        entry.save()
        return entry

    def update(self, instance, validated_data):
        file = validated_data.pop('file', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if file is not None:
            self._upload(instance, file)
        instance.save()
        return instance

    @staticmethod
    def _upload(entry, file_obj):
        token = settings.DISK_TOKEN
        _, url = upload_to_yadisk(file_obj.name, file_obj.read(), token)
        entry.file_name = file_obj.name
        entry.file_url = url


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonEntry
        fields = ['grade']

    def validate_grade(self, value):
        if value is not None and not (1 <= value <= 10):
            raise serializers.ValidationError('Оценка должна быть от 1 до 10.')
        return value

    def update(self, instance, validated_data):
        instance.grade = validated_data['grade']
        instance.graded_by = self.context['request'].user
        instance.save()
        return instance
