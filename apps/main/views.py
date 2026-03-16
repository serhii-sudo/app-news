from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from django.db.models import Case, When, Value, DateTimeField, BooleanField
from django.utils import timezone
from datetime import timedelta

from apps.main.models import Category, Post
from apps.main.permissions import IsAuthorOrReadOnly
from apps.main.serializers import CategorySerializer, PostListSerializer, PostCreateUpdateSerializer, \
    PostDetailSerializer


class CategoryListCreateView(generics.ListCreateAPIView):
    # Указываем, какие данные брать из базы (все объекты модели Category)
    queryset = Category.objects.all()
    # Указываем сериализатор, который превратит объекты базы в JSON и наоборот
    serializer_class = CategorySerializer
    # Права доступа (чтение всем, создание авторизованным)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # Бекенды: фильтрация по полям, поиск и сортировка
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    # Поиск по заголовку и контенту (?search=...)
    search_fields = ['name', 'description']
    # Поля, по которым можно кликнуть для сортировки
    ordering_fields = ['name', 'created_at']
    # Сортировка по умолчанию (по имени)
    ordering = ['name']


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author', 'status']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'views_count', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        """Возвращает посты с учетом прав доступа"""

        queryset = Post.objects.select_related('author', 'category')

        # фильрация по правам доступа
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published')
        else:
            queryset = queryset.filter(
                Q(status='published') | Q(author=self.request.user)
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateUpdateSerializer
        return PostListSerializer


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.select_related('author', 'category')
    serializer_class = PostDetailSerializer
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PostCreateUpdateSerializer
        return PostDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MyPostsView(generics.ListAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'views_count', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return Post.objects.filter(
            author=self.request.user
        ).select_related('author', 'category')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def post_by_category(request, category_slug):
    """Посты определенной категории"""
    category = get_object_or_404(Category, slug=category_slug)

    # Получаем посты с учетом закрепления
    # Используем менеджер модели для получения with_subscription_info
    posts = Post.objects.filter(
        category=category,
        status='published'
    ).select_related('author', 'category').order_by('-created_at')

    # Сортируем с учетом закрепленных постов
    # Используем сложную аннотацию для правильной сортировки

    serializer = PostListSerializer(posts, many=True, context={'request': request})

    return Response({
        'category': CategorySerializer(category).data,
        'posts': serializer.data,
    })


# Получаем 10 самых популярных(просматриваемых) постов - первые
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def popular_posts(request):
    """10 самых популярных постов"""
    posts = Post.objects.filter(
        status='published'
    ).select_related('author', 'category').order_by('-views_count')[:10]

    serializer = PostListSerializer(
        posts,
        many=True,
        context={'request': request}
    )
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recent_posts(request):
    """10 последних опубликованных постов"""
    posts = Post.objects.filter(
        status='published'
    ).select_related('author', 'category').order_by('-created_at')[:10]

    serializer = PostListSerializer(
        posts,
        many=True,
        context={'request': request}
    )
    return Response(serializer.data)
