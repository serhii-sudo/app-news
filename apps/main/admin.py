from django.contrib import admin

from .models import Category, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)

    def post_count(self, obj):
        return obj.posts.count()

    post_count.short_description = 'Posts Count'


@admin.register(Post)
class PostsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'views_count', 'comments_count', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at', 'category')
    search_fields = ('title', 'content', 'author__username')  # Поиск + по username автора
    prepopulated_fields = {'slug': ('title',)}  # Slug автозаполнение из title
    readonly_fields = ('created_at', 'updated_at', 'views_count')
    raw_id_fields = ('author',)  # Автора выбираем через ID (удобно при большой БД)

    fieldsets = (  # Разбиваем форму редактирования на секции
        (None, {  # Секция без названия (основная)
            'fields': ('title', 'slug', 'content', 'img')  # Основные поля поста
        }),
        ('Meta', {  # Секция "Meta"
            'fields': ('category', 'author', 'status')  # Категория, автор, статус
        }),
        ('Statistics', {  # Секция "Statistics"
            'fields': ('views_count', 'created_at', 'updated_at'),  # Статистика
            'classes': ('collapse',)  # Секция свёрнута по умолчанию
        }),
    )

    def comments_count(self, obj):  # Кастомная колонка — считает комментарии поста
        return obj.comments.count()  # Возвращает кол-во связанных комментариев

    comments_count.short_description = 'Comments' # Название колонки в админке

    def get_queryset(self, request): # Переопределяем базовый queryset
        # select_related подгружает автора и категорию одним SQL запросом (оптимизация)
        return super().get_queryset(request).select_related('author', 'category')

