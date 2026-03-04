from django.conf import settings
from django.db import models
from django.db.models import Case, When, Value, BooleanField
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class PostsQuerySet(models.QuerySet):
    """
       Кастомный QuerySet для модели Post.
       Содержит методы для работы с закреплёнными постами и подпиской.
       """

    def with_subscription_info(self):
        """
        Аннотирует queryset флагом is_pinned_flag:
        True — если у поста есть активная подписка автора и пост закреплён.
        """
        return self.annotate(  # добавляем вычисляемое поле к каждому объекту QuerySet
            is_pinned_flag=Case(  # is_pinned_flag — название нового поля; Case — аналог IF/ELSE в SQL
                When(  # условие: когда выполняются все параметры ниже — возвращаем True
                    pin_info__isnull=False,  # у поста есть связанный объект PinInfo (пост закреплён)
                    pin_info__user__subscription__status='active',  # подписка автора активна
                    pin_info__user__subscription__end_date__gt=timezone.now(),  # подписка ещё не истекла
                    then=Value(True)  # если все условия выполнены — присваиваем True
                ),
                default=Value(False),  # во всех остальных случаях — False
                output_field=BooleanField()  # указываем Django тип возвращаемого поля
            )
        )

    def pinned_posts(self):
        """
        Возвращает только закреплённые посты (с активной подпиской),
        отсортированные по дате закрепления.
        """
        return self.with_subscription_info().filter(  # сначала аннотируем, затем фильтруем
            status='published',  # берём только опубликованные посты
            is_pinned_flag=True  # берём только те, где is_pinned_flag = True
        ).order_by('-pin_info__pinned_at')  # сортируем по дате закрепления (новые первые)


class PostManager(models.Manager):
    """Менеджер для модели Post, использует PostQuerySet."""

    def get_queryset(self):
        return PostsQuerySet(self.model, using=self._db)

    def with_subscription_info(self):
        return self.get_queryset().with_subscription_info()

    def pinned_posts(self):
        return self.get_queryset().pinned_posts()


class Category(models.Model):
    """модель категорий для постов блога"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)


class Post(models.Model):
    """модель постов для блога"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published')
    ]
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    img = models.ImageField(upload_to='posts/', blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='published'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    objects = PostManager()

    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']
        # Индексы для ускорения запросов к базе данных
        indexes = [
            # Индекс для быстрой сортировки по дате создания
            models.Index(fields=['-created_at']),

            # Индекс для фильтрации по статусу и дате (например, опубликованные посты)
            models.Index(fields=['status', '-created_at']),

            # Индекс для фильтрации по категории и дате
            models.Index(fields=['category', '-created_at']),

            # Индекс для фильтрации по автору и дате
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'slug': self.slug})

    @property
    def comments_count(self):
        return self.comments.filter(is_active=True).count()

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])
