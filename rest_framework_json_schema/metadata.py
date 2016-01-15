from collections import OrderedDict

from django.utils.text import force_text
from rest_framework import metadata, serializers
from rest_framework.utils.field_mapping import ClassLookupDict

from .serializers import ModelClassSerializer


class JSONSchemaMetadataMixin(object):
    label_lookup = ClassLookupDict({
        serializers.Field: 'object',
        serializers.BooleanField: 'boolean',
        serializers.CharField: 'string',
        serializers.URLField: 'string',
        serializers.EmailField: 'string',
        serializers.RegexField: 'string',
        serializers.SlugField: 'string',
        serializers.IntegerField: 'integer',
        serializers.FloatField: 'number',
        serializers.DecimalField: 'number',
        serializers.DateField: 'string',
        serializers.DateTimeField: 'string',
        serializers.ChoiceField: 'enum',
        serializers.FileField: 'string',
        serializers.PrimaryKeyRelatedField: 'integer',
        serializers.SlugRelatedField: 'enum',
        serializers.HyperlinkedRelatedField: 'string',
        serializers.HyperlinkedIdentityField: 'string',
    })

    def __init__(self, *args, **kwargs):
        super(JSONSchemaMetadataMixin, self).__init__(*args, **kwargs)

    def get_serializer_info(self, serializer):
        opts = serializer.Meta.model._meta
        schema = {
            'rels': {},
            'links': [],
            'properties': OrderedDict(),
            'required': [],
        }

        for field_name, field in serializer.fields.items():
            if getattr(field, 'read_only', False):
                continue

            schema['properties'][field_name] = self.get_field_info(field)

            if getattr(field, 'required', False):
                schema['required'].append(field_name)

            if isinstance(field, serializers.RelatedField):
                field__name = field_name
                link = {
                    'rel': field__name,
                }

                if isinstance(field, serializers.HyperlinkedRelatedField):
                    link['href'] = "{{{}}}".format(field_rel)

                schema['links'].append(link)
                schema['rels'][field_name] = ModelClassSerializer(field.queryset.model).data,

            if isinstance(field, serializers.Serializer):
                related_schema = self.get_serializer_info(field)
                field_info = {
                    'type': 'object',
                    'properties': related_schema['properties'],
                }

                if isinstance(field, serializers.ListSerializer):
                    field_info = {
                        'items': field_info,
                        'type': 'array',
                    }

                schema['properties'][field_name] = field_info

        return schema

    def get_field_info(self, field):
        """
        Given an instance of a serializer field, return a dictionary
        of metadata about it.
        """
        field_info = OrderedDict()
        field_info['type'] = self.label_lookup[field]

        attribute_map = {
            'label': 'title',
            'help_text': 'description',
        }

        format_map = ClassLookupDict({
            serializers.Field: None,
            serializers.URLField: 'uri',
            serializers.EmailField: 'email',
            serializers.DateTimeField: 'date-time',
            serializers.DateField: 'date-time',
            serializers.FileField: 'file',
            serializers.HyperlinkedRelatedField: 'uri',
            serializers.HyperlinkedIdentityField: 'uri',
        })

        for attr in ['min_length', 'max_length', 'label', 'help_text']:
            dest = attribute_map.get(attr, attr)
            value = getattr(field, attr, None)
            if value is not None and value != '':
                field_info[dest] = force_text(value, strings_only=True)

        format = format_map[field]
        if format:
            field_info['format'] = format

        if hasattr(field, 'choices') and not isinstance(field, serializers.RelatedField):
            field_info['enum'] = field.choices.keys()
            field_info['choices'] = [
                {'value': value, 'display_name': display_name}
                for value, display_name in field.choices.iteritems()
            ]

        if isinstance(field, serializers.RelatedField):
            if isinstance(field, serializers.ListSerializer):
               field_info['items'] = {'type': field_info['type']}
               if 'format' in field_info:
                   field_info['items']['format'] = field_info.pop('format')
               field_info['type'] = 'array'

        return field_info


class JSONSchemaMetadata(JSONSchemaMetadataMixin, metadata.SimpleMetadata):
    pass
