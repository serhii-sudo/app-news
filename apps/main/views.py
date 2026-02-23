from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters

from apps.main.models import Category, Post
from apps.main.serializers import CategorySerializer, PostListSerializer


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
        # select_related делает JOIN в SQL, чтобы не делать лишних запросов за автором и категорией (оптимизация)
        queryset = Post.objects.select_related('author', 'category')
        # Если пользователь не вошел в систему
        if not self.request.user.is_authenticated:
            # Показываем только опубликованные посты
            queryset = queryset.filter(status='published')
        else:
            # Если вошел - показываем опубликованные ИЛИ те, где он сам автор (даже черновики)
            # Q — это объект для сложных OR-условий в Django
            queryset = queryset.filter(
                Q(status='published') | Q(author=self.request.user)
            )
        return queryset
