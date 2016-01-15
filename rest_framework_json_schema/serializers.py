from rest_framework import serializers


class ModelClassSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField()
    app_label = serializers.CharField(source='_meta.app_label')
    model_name = serializers.CharField(source='_meta.model_name')

    def restore_object(self, attrs, instance=None):
        return get_model(attrs['_meta.app_label'], attrs['_meta.model_name'])

    def get_name(self, obj):
        return "{}.{}".format(obj._meta.app_label, obj._meta.object_name)
