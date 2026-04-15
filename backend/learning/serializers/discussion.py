from rest_framework import serializers
from ..models import DiscussionThread, DiscussionComment

class DiscussionCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = DiscussionComment
        fields = ['id', 'thread', 'author', 'author_name', 'content', 'parent', 'created_at', 'replies']

    def get_replies(self, obj):
        if obj.replies.exists():
            return DiscussionCommentSerializer(obj.replies.all(), many=True).data
        return []

class DiscussionThreadSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    
    class Meta:
        model = DiscussionThread
        fields = ['id', 'course', 'title', 'author', 'author_name', 'created_at', 'comments_count']
