import random

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from slugify import slugify

from apps.main.models import Post, Category

User = get_user_model()

CATEGORIES = [
    {"name": "Технологии", "description": "Статьи о технологиях, IT и разработке"},
    {"name": "Наука", "description": "Научные открытия и исследования"},
    {"name": "Спорт", "description": "Новости спорта и соревнований"},
    {"name": "Бизнес", "description": "Финансы, стартапы и экономика"},
    {"name": "Культура", "description": "Искусство, кино и музыка"},
    {"name": "Политика", "description": "Мировая политика"},
]

USERS = [
    {
        "username": "admin_user",
        "email": "admin@news.com",
        "password": "Admin1234!",
        "first_name": "Алексей",
        "last_name": "Смирнов",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "username": "editor_john",
        "email": "john@news.com",
        "password": "John1234!",
        "first_name": "Иван",
        "last_name": "Петров",
    },
    {
        "username": "writer_anna",
        "email": "anna@news.com",
        "password": "Anna1234!",
        "first_name": "Анна",
        "last_name": "Кузнецова",
    },
]

POSTS = [
    # Технологии
    {
        "title": "Python 4.0: что нас ждёт",
        "content": (
            "Python продолжает развиваться семимильными шагами. В новой версии ожидается "
            "значительное улучшение производительности за счёт JIT-компиляции, более строгая "
            "типизация и удобный синтаксис для асинхронного программирования. Сообщество уже "
            "активно обсуждает предложения PEP, которые войдут в релиз.\n\n"
            "Разработчики особо выделяют планы по ускорению интерпретатора в 5 раз по сравнению "
            "с Python 3.11. Это сделает его конкурентоспособным с компилируемыми языками в ряде "
            "задач. Ждём официального анонса!"
        ),
        "category": "Технологии",
        "status": "published",
        "views_count": 1540,
    },
    {
        "title": "Django REST Framework: лучшие практики 2026",
        "content": (
            "DRF остаётся стандартом де-факто для создания REST API на Python. В этой статье "
            "разбираем актуальные паттерны: версионирование API, throttling, кастомные permissions "
            "и оптимизация запросов через select_related и prefetch_related.\n\n"
            "Особое внимание уделим сериализаторам — как правильно разделять сериализаторы для "
            "чтения и записи, использовать SerializerMethodField и избегать N+1 проблем."
        ),
        "category": "Технологии",
        "status": "published",
        "views_count": 980,
    },
    {
        "title": "Как настроить CI/CD с GitHub Actions",
        "content": (
            "Continuous Integration и Continuous Deployment — основа современной разработки. "
            "GitHub Actions позволяет автоматизировать тесты, линтинг и деплой прямо в репозитории "
            "без сторонних сервисов.\n\n"
            "В этой статье настраиваем пайплайн: запуск pytest, проверка покрытия кода, "
            "автоматический деплой на сервер при пуше в main."
        ),
        "category": "Технологии",
        "status": "draft",
        "views_count": 0,
    },
    # Наука
    {
        "title": "Квантовые компьютеры: мифы и реальность",
        "content": (
            "Квантовые вычисления активно обсуждаются в прессе, но что за ними стоит на самом деле? "
            "Разбираем принципы суперпозиции и запутанности, текущее состояние квантового железа "
            "и реальные задачи, где квантовые компьютеры уже превосходят классические.\n\n"
            "Спойлер: для большинства задач обычный компьютер справится лучше ещё долгие годы."
        ),
        "category": "Наука",
        "status": "published",
        "views_count": 2300,
    },
    {
        "title": "Марс: итоги миссии Perseverance",
        "content": (
            "Марсоход Perseverance работает уже несколько лет и собрал уникальные данные о геологии "
            "Красной планеты. Найдены органические молекулы, засвидетельствованы следы древних рек. "
            "Вертолёт Ingenuity поставил рекорд по количеству полётов.\n\n"
            "В этой статье подводим итог открытий и смотрим на перспективы пилотируемой миссии."
        ),
        "category": "Наука",
        "status": "published",
        "views_count": 1870,
    },
    # Спорт
    {
        "title": "Чемпионат мира по футболу 2026: превью",
        "content": (
            "Турнир впервые пройдёт в трёх странах — США, Канаде и Мексике. Впервые участвуют "
            "48 команд. Разбираем группы, фаворитов и тёмных лошадок, а также расписание матчей "
            "для основных сборных.\n\n"
            "Бразилия, Франция и Англия считаются главными претендентами. Хотя история любит "
            "сюрпризы — никто не забыл Катар 2022."
        ),
        "category": "Спорт",
        "status": "published",
        "views_count": 3100,
    },
    {
        "title": "Бег для начинающих: с чего начать",
        "content": (
            "Бег — один из самых доступных видов спорта. Не нужен зал и дорогое оборудование — "
            "только кроссовки и желание. Но многие новички совершают одни и те же ошибки: "
            "слишком быстрый старт, неправильная техника, отсутствие плана.\n\n"
            "Рассказываем, как правильно начать: план на первые 8 недель, базовые упражнения "
            "для укрепления суставов и советы по питанию."
        ),
        "category": "Спорт",
        "status": "published",
        "views_count": 755,
    },
    # Бизнес
    {
        "title": "Как запустить стартап в 2026 году",
        "content": (
            "Экосистема стартапов изменилась. Инвесторы стали осторожнее, рынок насыщен. "
            "Но возможности никуда не делись — просто нужна другая стратегия.\n\n"
            "Говорим о lean-подходе, MVP без лишнего кода, поиске первых клиентов и "
            "bootstrapping vs привлечение инвестиций."
        ),
        "category": "Бизнес",
        "status": "published",
        "views_count": 1200,
    },
    {
        "title": "Криптовалюта в 2026: куда движется рынок",
        "content": (
            "После нескольких лет волатильности рынок криптовалют стабилизируется. Bitcoin "
            "получил институциональное признание, ETF одобрены. Разбираем текущий ландшафт, "
            "регуляторные изменения и перспективы DeFi.\n\n"
            "Стоит ли инвестировать? Какие риски? Отвечаем без хайпа."
        ),
        "category": "Бизнес",
        "status": "draft",
        "views_count": 0,
    },
    # Культура
    {
        "title": "Топ-10 сериалов 2025 года",
        "content": (
            "Прошедший год подарил нам несколько выдающихся сериалов. От психологических триллеров "
            "до масштабных исторических драм — индустрия не останавливается.\n\n"
            "Наш топ: The Last of Us Season 2, Severance Season 3, House of the Dragon Season 3 "
            "и ещё семь проектов, которые вы не должны пропустить."
        ),
        "category": "Культура",
        "status": "published",
        "views_count": 4500,
    },
    # Музыка
    {
        "title": "Почему vinyl возвращается",
        "content": (
            "Продажи виниловых пластинок растут восьмой год подряд. Молодёжь покупает проигрыватели "
            "и коллекционирует альбомы в эпоху стриминга. Почему?\n\n"
            "Разбираемся в феномене: физический объект, ритуал прослушивания, звук и ностальгия "
            "как антитеза бесконечного скролла."
        ),
        "category": "Культура",
        "status": "published",
        "views_count": 620,
    },
    {
        "title": "Выборы 2026: чего ожидать и как подготовиться",
        "content": (
            "В 2026 году мир ожидает несколько ключевых выборов, которые могут повлиять на глобальную политику. "
            "Эксперты анализируют прогнозы по партиям, кандидатам и возможным изменениям в законодательстве. "
            "Важно понимать, как различные события и международные отношения могут повлиять на результаты.\n\n"
            "В статье рассматриваем ключевые моменты: влияние социальных медиа на электорат, роль экономической "
            "ситуации и стратегические шаги партий для привлечения внимания граждан. Практические советы для "
            "наблюдателей и аналитиков помогут лучше понимать политический процесс и прогнозировать исход выборов."
        ),
        "category": "Политика",
        "status": "published",
        "views_count": 800,
    }
]


class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми данными: пользователи, категории, посты"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Удалить все существующие посты и категории перед созданием",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Удаляем существующие данные..."))
            Post.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Данные удалены."))

        # 1. Создаём пользователей
        self.stdout.write("\n👤 Создаём пользователей...")
        created_users = []
        for user_data in USERS:
            is_staff = user_data.pop("is_staff", False)
            is_superuser = user_data.pop("is_superuser", False)
            password = user_data.pop("password")
            email = user_data["email"]

            user, created = User.objects.get_or_create(
                email=email,
                defaults=user_data,
            )
            if created:
                user.set_password(password)
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Создан: {user.email} / пароль: {password}")
                )
            else:
                self.stdout.write(f"  — Уже существует: {user.email}")
            created_users.append(user)

        # 2. Создаём категории
        self.stdout.write("\n📁 Создаём категории...")
        category_map = {}
        for cat_data in CATEGORIES:
            slug = slugify(cat_data["name"])
            try:
                cat = Category.objects.get(slug=slug)
                self.stdout.write(f"  — Уже существует: {cat.name}")
            except Category.DoesNotExist:
                cat, created = Category.objects.get_or_create(
                    name=cat_data["name"],
                    defaults={
                        "slug": slug,
                        "description": cat_data["description"],
                    },
                )
                self.stdout.write(self.style.SUCCESS(f"  ✅ {cat.name}"))
            created = getattr(cat, '_state', None) and cat._state.adding  # удалить, так как не используем?!
            category_map[cat_data["name"]] = cat

        # 3. Создаём посты
        self.stdout.write("\n📝 Создаём посты...")
        writers = [u for u in created_users]  # все пользователи могут быть авторами

        posts_created = 0
        for post_data in POSTS:
            cat_name = post_data.pop("category")
            category = category_map.get(cat_name)
            author = random.choice(writers)
            views = post_data.pop("views_count", 0)
            title = post_data["title"]

            # Генерируем уникальный slug
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            post, created = Post.objects.get_or_create(
                slug=slug,
                defaults={
                    **post_data,
                    "category": category,
                    "author": author,
                },
            )

            if created:
                # Обновляем views_count напрямую (без вызова increment_views)
                Post.objects.filter(pk=post.pk).update(views_count=views)
                status_label = "📄 черновик" if post.status == "draft" else "🌐 published"
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ [{status_label}] {post.title} (автор: {author.email})")
                )
                posts_created += 1
            else:
                self.stdout.write(f"  — Уже существует: {post.title}")

        # Итог
        self.stdout.write("\n" + "─" * 50)
        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Готово!\n"
            f"   Пользователей: {len(created_users)}\n"
            f"   Категорий:     {len(category_map)}\n"
            f"   Постов:        {posts_created} создано\n"
        ))
        self.stdout.write("─" * 50)
        self.stdout.write("\n📋 Учётные данные:\n")
        for ud in USERS:
            # ud уже модифицирован pop-ами, берём из оригинала
            pass

        creds = [
            ("admin@news.com", "Admin1234!", "Superuser / admin панель"),
            ("john@news.com", "John1234!", "Редактор"),
            ("anna@news.com", "Anna1234!", "Автор"),
        ]
        for email, password, role in creds:
            self.stdout.write(f"   {role:30s} → {email} / {password}")
        self.stdout.write("")
