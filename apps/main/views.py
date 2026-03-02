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
        # Получаем параметр сортировки из query string (например: ?ordering=-created_at)
        ordering = self.request.query_params.get('ordering', '')

        # Закреплённые посты показываем первыми только при сортировке по дате
        # (или если сортировка не задана вообще)
        show_pinned_first = not ordering or ordering in ['-created_at', 'created_at']

        if show_pinned_first:
            # get_posts_for_feed() — метод модели, который сортирует: сначала закреплённые, потом остальные
            return Post.get_posts_for_feed().filter(
                Q(status='published') |  # опубликованные посты для всех
                (
                    Q(author=self.request.user)  # свои посты — только если авторизован
                    if self.request.user.is_authenticated
                    else Q()  # пустой Q() — ничего не добавляет к фильтру
                )
            )

        # Если задана нестандартная сортировка — возвращаем обычный queryset без учёта закреплённых
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateUpdateSerializer
        return PostListSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        if hasattr(response, 'data') and 'results' in response.data:
            # Считаем количество закреплённых постов среди возвращённых результатов
            # sum() + генератор — компактная замена цикла со счётчиком
            # post.get('is_pinned', False) — безопасно достаём поле, если его нет — считаем False
            pinned_count = sum(1 for post in response.data['results'] if post.get('is_pinned', False))

            # Добавляем кастомное поле в ответ рядом с results, count, next, previous
            response.data['pinned_posts_count'] = pinned_count

        return response


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
    category = get_object_or_404(Category, slug=category_slug)
    posts = Post.objects.with_subscription_info().filter(category=category, status='published')

    posts = posts.annotate(
        # effective_date — вычисляемое поле для сортировки:
        # если пост закреплён и у автора активная подписка — берём дату закрепления (pin_info__pinned_at)
        # иначе — берём обычную дату создания поста (created_at)
        effective_date=Case(
            When(
                pin_info__isnull=False,  # есть запись о закреплении
                pin_info__user__subscription__status='active',  # подписка активна
                pin_info__user__subscription__end_date__gt=timezone.now(),  # подписка не истекла
                then='pin_info__pinned_at'  # берём дату закрепления
            ),
            default='created_at',  # в начале берём дату создания
            output_field=DateTimeField()
        ),

        # is_pinned_flag — булево поле: True если пост закреплён с активной подпиской
        # используется для того чтобы закреплённые посты шли первыми
        is_pinned_flag=Case(
            When(
                pin_info__isnull=False,
                pin_info__user__subscription__status='active',
                pin_info__user__subscription__end_date__gt=timezone.now(),
                then=Value(True)  # закреплённый
            ),
            default=Value(False),  # обычный
            output_field=BooleanField()
        )
    ).order_by(
        '-is_pinned_flag',  # 1. Сначала закреплённые (True > False)
        'effective_date',  # 2. Потом по дате (закреплённые - по дате закрепления, остальные - по дате создания)
        '-created_at'  # 3. Среди одинаковых дат - новые первыми
    )

    # Сериализуем посты, передаём request для построения абсолютных URL
    serializer = PostListSerializer(posts, many=True, context={'request': request})

    return Response({
        'category': CategorySerializer(category).data,  # Данные категории
        'posts': serializer.data,  # Список постов
        # считаем количество закреплённых постов в ответе
        'pinned_posts_count': sum(1 for post in serializer.data if post.get('is_pinned', False))
    })


# Получаем 10 самых популярных(просматриваемых) постов - первые
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def popular_posts(request):
    posts = Post.objects.with_subscription_info().filter(status='published').order_by('-views_count')[:10]
    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)


# Получаем первые 10 постов, по свежей дате публикации
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recent_posts(request):
    posts = Post.objects.with_subscription_info().filter(status='published').order_by('-created_at')[:10]
    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)


# Получаем закрепленные посты
@api_view
@permission_classes([permissions.AllowAny])
def pinned_posts_only(request):
    posts = Post.objects.pinned_posts()
    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response({
        'count': posts.count(),
        'results': serializer.data
    })


# Работа с постами через ORM
@api_view
@permission_classes([permissions.AllowAny])
def featured_posts(request):
    # Получаем первые 3 закрепленных поста автора
    pinned_posts = Post.objects.pinned_posts()[:3]
    # берем посты за последние 7 дней
    week_ago = timezone.now() - timedelta(days=7)
    # делаем ORM запись
    popular_posts = Post.objects.with_subscription_info().filter(
        status='published',
        created_at__gte=week_ago
    ).exclude(id__in=[post.id for post in pinned_posts]).order_by('-views_count')[:6]

    pinned_serializer = PostListSerializer(pinned_posts, many=True, context={'request': request})
    popular_serializer = PostListSerializer(popular_posts, many=True, context={'request': request})

    return Response({
        'pinned_posts': pinned_serializer.data,
        'popular_posts': popular_serializer.data,
        'total_pinned': Post.objects.pinned_posts().count()
    })
