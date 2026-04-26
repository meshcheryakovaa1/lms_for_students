from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lessons.models import LessonEntry
from users.models import User

from .filters import LessonEntryFilter
from .permissions import IsOwnerOrTeacher, IsStudent, IsTeacher
from .serializers import GradeSerializer, LessonEntrySerializer


class LessonEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LessonEntrySerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    filter_backends  = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class  = LessonEntryFilter
    search_fields    = ['comment']
    ordering_fields  = ['date', 'created_at', 'grade']
    ordering         = ['-date']

    def get_queryset(self):
        user = self.request.user
        qs = LessonEntry.objects.select_related('student', 'graded_by')
        if user.role == User.TEACHER:
            return qs.all()
        return qs.filter(student=user)

    def get_permissions(self):
        if self.action == 'grade':
            return [IsAuthenticated(), IsTeacher()]
        if self.action == 'create':
            return [IsAuthenticated(), IsStudent()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrTeacher()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    @action(detail=True, methods=['patch'], url_path='grade')
    def grade(self, request, pk=None):
        entry = self.get_object()
        serializer = GradeSerializer(
            entry,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            LessonEntrySerializer(entry, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


class UserViewSet(DjoserUserViewSet):
    pass
