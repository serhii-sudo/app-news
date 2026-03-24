from rest_framework import serializers

from apps.comments.models import Comment
from apps.main.models import Post


class CommentSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для комментариев"""
    author_info = serializers.SerializerMethodField()
    # ReadOnlyField — берёт значение напрямую из @property модели, только для чтения
    replies_count = serializers.ReadOnlyField()
    is_reply = serializers.ReadOnlyField()

    class Meta:
        model = Comment
        fields = [
            'id', 'content',
            'author', 'author_info',
            'parent', 'is_active',
            'replies_count', 'is_reply',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['author', 'is_active']

    def get_author_info(self, obj):
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'full_name': obj.author.full_name,
            'avatar': obj.author.avatar.url if obj.author.avatar else None
        }


class CommentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания комментариев"""

    class Meta:
        model = Comment
        fields = ['post', 'parent', 'content']  # только эти поля принимаем от юзера

    def validate_post(self, value):
        # Проверяем что пост существует и опубликован
        # validate_<field> — вызывается автоматически при валидации поля
        if not Post.objects.filter(id=value.id, status='published').exists():
            raise serializers.ValidationError('Post not found')
        return value

    def validate_parent(self, value):
        if value:
            # Получаем пост из валидированных данных или из initial_data
            post_data = self.initial_data.get('post')
            if post_data:
                # Сравниваем ID поста родительского комментария с переданным ID поста
                if value.post.id != int(post_data):
                    raise serializers.ValidationError(
                        'Parent comment must belong to the same post'
                    )
        return value

    def create(self, validated_data):
        # Автора берём из request.user, а не из данных юзера — чтобы нельзя было подделать запрос
        #  context['request'] передаётся из ViewSet автоматически
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class CommentUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления комментариев"""

    class Meta:
        model = Comment
        fields = ['content']  # при обновлении можно менять только текст


class CommentDetailSerializer(CommentSerializer):
    """Детальный сериализатор комментария с ответами"""
    replies = serializers.SerializerMethodField()

    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ['replies']

    def get_replies(self, obj):
        # Показываем ответы только для корневых комментариев (у которых нет parent)
        # Если это сам ответ — возвращаем пустой список (без вложенности)
        if obj.parent is None:
            replies = obj.replies.filter(is_active=True).order_by('created_at')
            # Сериализуем ответы через базовый CommentSerializer
            # many=True — говорит что передаём список объектов
            # context=self.context — передаём request дальше (нужен для get_author_info)
            return CommentSerializer(replies, many=True, context=self.context).data
        return []

