from rest_framework import serializers
from .models import Book, Comment


# 도서 목록 조회용 serializer
class BookListSerializer(serializers.ModelSerializer):
    num_of_comments = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = '__all__'

    def get_num_of_comments(self, obj):
        return Comment.objects.count()


# 도서 생성 / 수정용 serializer
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


# 도서 상세 조회용 serializer (댓글 목록 포함)
class BookDetailSerializer(serializers.ModelSerializer):
    class CommentDetailSerializer(serializers.ModelSerializer):
        class Meta:
            model = Comment
            fields = '__all__'

    comments = CommentDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = '__all__'


# 댓글 serializer
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
