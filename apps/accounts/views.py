from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes

# Импортируем из Django REST Framework три важных модуля:
# - status: содержит HTTP-статусы (например, HTTP_201_CREATED, HTTP_200_OK и т.д.).
#   Используем их, чтобы возвращать правильные коды ответа клиенту.
# - generics: набор готовых классов-представлений (views), которые сильно упрощают написание API
#   (CreateAPIView, RetrieveUpdateAPIView и т.д.).
# - permissions: классы для контроля доступа (IsAuthenticated, AllowAny и др.).

# Импортируем декораторы:
# - @api_view: используется для функций-представлений (function-based views), указывает допустимые HTTP-методы.
# - @permission_classes: позволяет задавать разрешения для конкретного представления.

from rest_framework.response import Response
# Класс Response — это объект, который DRF возвращает клиенту.
# Он автоматически сериализует данные в JSON и устанавливает правильный Content-Type.

from rest_framework_simplejwt.tokens import RefreshToken
# Из библиотеки SimpleJWT импортируем класс RefreshToken.
# Он используется для генерации пары токенов (refresh и access) и для их черного списка (blacklist).


from django.contrib.auth import login
# Функция login из стандартной аутентификации Django.
# Устанавливает сессию пользователя в request (полезно, если одновременно используется сессионная аутентификация).

from .models import User

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer
)


# Импортируем все сериализаторы, которые будут преобразовывать модели в JSON и валидировать входящие данные.
# Каждый сериализатор отвечает за свою задачу (регистрация, логин, профиль и т.д.).

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    # Обязательное поле для всех generic views. Указывает, какие объекты может обрабатывать view.
    # В данном случае не используется напрямую (мы создаём нового пользователя), но DRF требует его наличия.

    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # Переопределяем метод create, чтобы добавить выдачу JWT-токенов сразу после регистрации.
        # Стандартный create просто сохранил бы пользователя и вернул его данные.

        serializer = self.get_serializer(data=request.data)
        # Создаём экземпляр сериализатора с данными из запроса (request.data — это JSON из тела POST-запроса).

        serializer.is_valid(raise_exception=True)
        # Проверяем валидность данных. Если невалидно — автоматически возвращается 400 с ошибками.

        user = serializer.save()
        # Если данные валидны, вызываем save() у сериализатора.
        # В UserRegistrationSerializer должен быть переопределён метод create(),
        # который создаёт и возвращает пользователя.

        refresh = RefreshToken.for_user(user)
        # Генерируем refresh-токен для только что созданного пользователя.
        # Внутри создаётся и access-токен (доступен как refresh.access_token).

        return Response({
            'user': UserProfileSerializer(user).data,
            # Сериализуем данные пользователя для ответа (обычно email, username и т.д.).
            'refresh': str(refresh),
            # Преобразуем refresh-токен в строку (иначе будет объект).
            'access': str(refresh.access_token),
            # Аналогично выдаём access-токен.
            'message': 'User registered successfully'
            # Сообщение для фронтенда (обратите внимание на опечатку: regirstered -> registered).
        }, status=status.HTTP_201_CREATED)
        # 201 Created — правильный статус для успешного создания ресурса.


class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # сериализатор с данными тела запроса

        serializer.is_valid(raise_exception=True)
        # Валидация. В UserLoginSerializer должен быть переопределён validate()
        # который проверяет пароль и возвращает объект пользователя в validated_data.

        user = serializer.validated_data['user']
        # Извлекаем аутентифицированного пользователя (сериализатор сам его нашёл и проверил).

        login(request, user)
        # Устанавливаем сессию Django (request.user станет этим пользователем).
        # Полезно, если у вас смешанная аутентификация (JWT + сессии).

        refresh = RefreshToken.for_user(user)
        # Генерируем пару JWT-токенов.

        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User login successfully'
        }, status=status.HTTP_200_OK
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Переопределяем, чтобы возвращать текущего пользователя (request.user),
        # а не искать по pk в URL.
        return self.request.user

    def get_serializer_class(self):
        # Динамически выбираем сериализатор в зависимости от метода.
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            # Для обновления используем другой сериализатор (возможно, с другими полями или валидацией).
            return UserUpdateSerializer
        # Для GET — просто выводим профиль.
        return UserProfileSerializer


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Password changed successfully',

        }, status=status.HTTP_200_OK)


@api_view(['POST'])
def logout_view(request):
    @permission_classes([permissions.IsAuthenticated])
    # Вложенный декоратор — доступ только авторизованным (проверяется access-токен).
    def inner_function(*args, **kwargs):
        try:
            refresh_token = request.data.get('refresh_token')
            # Клиент должен прислать refresh-токен в теле запроса (обычно в JSON: {"refresh_token": "..."})

            if refresh_token:
                token = RefreshToken(refresh_token)
                # Создаём объект RefreshToken из строки.

                token.blacklist()
                # Добавляем токен в черный список (в базе появится запись в BlacklistedToken).
                # После этого этот refresh-токен и все последующие access-токены от него станут недействительными.

            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
