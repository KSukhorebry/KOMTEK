from rest_framework import serializers

from .models import RefBook, RefBookElement


class RefBookQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False, input_formats=['%Y-%m-%d'])


class VersionQuerySerializer(serializers.Serializer):
    version = serializers.CharField(required=False, allow_blank=False, max_length=50)


class CheckElementQuerySerializer(VersionQuerySerializer):
    code = serializers.CharField(required=True, allow_blank=False, max_length=100)
    value = serializers.CharField(required=True, allow_blank=False, max_length=300)


class RefBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefBook
        fields = ('id', 'code', 'name')


class RefBookListResponseSerializer(serializers.Serializer):
    refbooks = RefBookSerializer(many=True)


class RefBookElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefBookElement
        fields = ('code', 'value')


class ElementsResponseSerializer(serializers.Serializer):
    elements = RefBookElementSerializer(many=True)


class ElementCheckResponseSerializer(serializers.Serializer):
    is_valid = serializers.BooleanField()