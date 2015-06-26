# -*- coding: utf-8 -*-
import inspect
import functools

import marshmallow as ma
import mongoengine as me
# from marshmallow import validate
from marshmallow.compat import text_type

from marshmallow_mongoengine.exceptions import ModelConversionError
from marshmallow_mongoengine.conversion import fields


def get_pk_from_identity(obj):
    """Get primary key for `obj`. If `obj` has a compound primary key,
    return a string of keys separated by ``":"``. This is the default keygetter for
    used by `ModelSchema <marshmallow_mongoengine.ModelSchema>`.
    """
    _, key = identity_key(instance=obj)
    if len(key) == 1:
        return key[0]
    else:  # Compund primary key
        return ':'.join(text_type(x) for x in key)


def _is_field(value):
    return (
        isinstance(value, type) and
        issubclass(value, fields.Field)
    )


def _list_field_factory(converter, data_type):
    return functools.partial(
        fields.List,
        converter._get_field_class_for_data_type(data_type.field),
    )

def _reference_field_factory(converter, data_type):
    return fields.String


def _recursive_build_wrapper(wrapper_cls):
    def recursive_build(field):

        return wrapper_cls()
    return recursive_build
    return d

class ModelConverter(object):
    """Class that converts a mongoengine Document into a dictionary of
    corresponding marshmallow `Fields <marshmallow.fields.Field>`.
    """

    TYPE_MAPPING = {
        me.fields.BinaryField: ma.fields.Integer,
        me.fields.BooleanField: ma.fields.Boolean,
        me.fields.ComplexDateTimeField: ma.fields.DateTime,
        me.fields.DateTimeField: ma.fields.DateTime,
        me.fields.DecimalField: ma.fields.Decimal,
        # me.fields.DictField: ma.fields.Dict,
        # me.fields.DynamicField: ma.fields.Dynamic,
        # me.fields.EmailField: ma.fields.Email,
        # me.fields.EmbeddedDocumentField: ma.fields.EmbeddedDocument,
        # me.fields.FileField: ma.fields.File,
        me.fields.FloatField: ma.fields.Float,
        # me.fields.GenericEmbeddedDocumentField: ma.fields.GenericEmbeddedDocument,
        # me.fields.GenericReferenceField: ma.fields.GenericReference,
        # me.fields.GeoPointField: ma.fields.GeoPoint,
        # me.fields.ImageField: ma.fields.Image,
        me.fields.IntField: ma.fields.Integer,
        me.fields.ListField: _list_field_factory,
        # me.fields.MapField: ma.fields.Map,
        me.fields.ObjectIdField: ma.fields.String,
        me.fields.ReferenceField: _reference_field_factory,
        me.fields.SequenceField: ma.fields.Integer,  # TODO: handle value_decorator
        me.fields.SortedListField: _list_field_factory,
        me.fields.StringField: ma.fields.String,
        # me.fields.URLField: ma.fields.URL,
        me.fields.UUIDField: ma.fields.UUID,
        # me.fields.PointField: ma.fields.Point,
        # me.fields.LineStringField: ma.fields.LineString,
        # me.fields.PolygonField: ma.fields.Polygon,
        # me.fields.MultiPointField: ma.fields.MultiPoint,
        # me.fields.MultiLineStringField: ma.fields.MultiLineString,
        # me.fields.MultiPolygonField: ma.fields.MultiPolygon,
    }

    def fields_for_model(self, model, keygetter=None, fields=None):
        result = {}
        for field_name, field_me in model._fields.items():
            if fields and field_name not in fields:
                continue
            field_ma_cls = self.convert_field(field_me)
            if field_ma_cls:
                result[field_name] = field_ma_cls
        return result

    def convert_field(self, field_me, keygetter=None, instance=True, **kwargs):
        field_builder = fields.get_field_builder_for_data_type(field_me)
        if not instance:
            return field_builder.marshmallow_field_cls
        return field_builder.build_marshmallow_field(**kwargs)

    def field_for(self, model, property_name, **kwargs):
        field_me = getattr(model, property_name)
        field_builder = fields.get_field_builder_for_data_type(field_me)
        return field_builder.build_marshmallow_field(**kwargs)

    def _get_field_class_for_data_type(self, field_me):
        field_ma_cls = None
        field_me_types = inspect.getmro(type(field_me))
        for field_me_type in field_me_types:
            if field_me_type in self.TYPE_MAPPING:
                field_ma_cls = self.TYPE_MAPPING[field_me_type]
                if callable(field_ma_cls) and not _is_field(field_ma_cls):
                    field_ma_cls = field_ma_cls(self, field_me)
                break
        else:
            # Try to find a field class based on the column's python_type
            if field_me.python_type in me.Schema.TYPE_MAPPING:
                field_cls = ma.Schema.TYPE_MAPPING[field_me.python_type]
            else:
                raise ModelConversionError(
                    'Could not find field column of type {0}.'.format(types[0]))
        return field_ma_cls

    # def _get_field_kwargs_from_mongo(self, field_me, keygetter=None):
    #     kwargs = self.get_base_kwargs()
    #     # import pdb; pdb.set_trace()
    #     # if column.nullable:
    #     #     kwargs['allow_none'] = True

    #     # if hasattr(column.type, 'enums'):
    #     if getattr(field_me, 'choices', None):
    #         kwargs['validate'].append(validate.OneOf(choices=field_me.choices))

    #     # Add a length validator for max_length/min_length
    #     maxmin_args = {}
    #     if hasattr(field_me, 'max_length'):
    #         maxmin_args['max'] = field_me.max_length
    #     if hasattr(field_me, 'min_length'):
    #         maxmin_args['min'] = field_me.min_length
    #     if maxmin_args:
    #         kwargs['validate'].append(validate.Length(**maxmin_args))
    #     if hasattr(field_me, 'null'):
    #         kwargs['allow_none'] = True

    #     # if hasattr(column.type, 'scale'):
    #     #     kwargs['places'] = getattr(column.type, 'scale', None)

    #     # Primary keys are dump_only ("read-only")
    #     if getattr(field_me, 'primary_key', False):
    #         kwargs['dump_only'] = True

    #     # if hasattr(prop, 'columns'):
    #     #     column = prop.columns[0]
    #     #     self._add_column_kwargs(kwargs, column)
    #     # if hasattr(prop, 'direction'):  # Relationship property
    #     #     self._add_relationship_kwargs(kwargs, prop, session=session, keygetter=keygetter)
    #     if getattr(field_me, 'help_text', None):  # Useful for documentation generation
    #         kwargs['description'] = field_me.help_text
    #     return kwargs

    # def get_base_kwargs(self):
    #     return {
    #         'validate': []
    #     }

default_converter = ModelConverter()

fields_for_model = default_converter.fields_for_model
"""Generate a dict of field_name: `marshmallow.fields.Field` pairs for the
given model.

:param model: The Mongoengine Document model
:return: dict of field_name: Field instance pairs
"""

convert_field = default_converter.convert_field
"""Convert a Mongoengine `Filed` to a field instance or class.

:param Property field_me: Mongoengine Field Property.
:param keygetter: See `marshmallow.fields.QuerySelect` for documenation on the
    keygetter parameter.
:param bool instance: If `True`, return  `Field` instance, computing relevant kwargs
    from the given property. If `False`, return the `Field` class.
:param kwargs: Additional keyword arguments to pass to the field constructor.
:return: A `marshmallow.fields.Field` class or instance.
"""

field_for = default_converter.field_for
"""Convert a property for a mapped Mongoengine Document class to a marshmallow `Field`.
Example: ::

    date_created = field_for(Author, 'date_created', dump_only=True)
    author = field_for(Book, 'author')

:param type ,: A Mongoengine Document mapped class.
:param str property_name: The name of the property to convert.
:param kwargs: Extra keyword arguments to pass to `property2field`
:return: A `marshmallow.fields.Field` class or instance.
"""
