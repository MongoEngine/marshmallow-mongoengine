import inspect
import functools

import marshmallow as ma
import mongoengine as me

from marshmallow_mongoengine import fields as ma_fields
from marshmallow_mongoengine.conversion import params
from marshmallow_mongoengine.exceptions import ModelConversionError


class MetaFieldBuilder(object):
    BASE_AVAILABLE_PARAMS = (params.DescriptionParam, params.AllowNoneParam, params.ChoiceParam)
    AVAILABLE_PARAMS = ()
    MARSHMALLOW_FIELD_CLS = None

    def __init__(self, field):
        self.AVAILABLE_PARAMS += self.BASE_AVAILABLE_PARAMS
        self.mongoengine_field = field
        self.params = [paramCls(field) for paramCls in self.AVAILABLE_PARAMS]

    def build_marshmallow_field(self, **kwargs):
        field_kwargs = None
        for param in self.params:
            field_kwargs = param.apply(field_kwargs)
        field_kwargs.update(kwargs)
        return self.marshmallow_field_cls(**field_kwargs)

    def _get_marshmallow_field_cls(self):
        return self.MARSHMALLOW_FIELD_CLS

    @property
    def marshmallow_field_cls(self):
        return self._get_marshmallow_field_cls()


class IntegerBuilder(MetaFieldBuilder):
    AVAILABLE_PARAMS = (params.SizeParam,)
    MARSHMALLOW_FIELD_CLS = ma_fields.Integer


class FloatBuilder(MetaFieldBuilder):
    AVAILABLE_PARAMS = (params.SizeParam,)
    MARSHMALLOW_FIELD_CLS = ma_fields.Float


class DecimalBuilder(MetaFieldBuilder):
    AVAILABLE_PARAMS = (params.SizeParam,)
    MARSHMALLOW_FIELD_CLS = ma_fields.Decimal


class StringBuilder(MetaFieldBuilder):
    AVAILABLE_PARAMS = (params.LenghtParam,)
    MARSHMALLOW_FIELD_CLS = ma_fields.String


class ListBuilder(MetaFieldBuilder):
    AVAILABLE_PARAMS = (params.LenghtParam,)
    MARSHMALLOW_FIELD_CLS = ma_fields.List

    def _get_marshmallow_field_cls(self):
        sub_field = get_field_builder_for_data_type(self.mongoengine_field.field)
        return functools.partial(
            self.MARSHMALLOW_FIELD_CLS,
            sub_field.build_marshmallow_field()
        )


class ReferenceBuilder(MetaFieldBuilder):
    AVAILABLE_PARAMS = ()
    MARSHMALLOW_FIELD_CLS = ma_fields.Reference

    def _get_marshmallow_field_cls(self):
        return functools.partial(
            self.MARSHMALLOW_FIELD_CLS,
            self.mongoengine_field.document_type
        )


class DateTimeBuilder(MetaFieldBuilder):
    AVAILABLE_PARAMS = ()
    MARSHMALLOW_FIELD_CLS = ma_fields.DateTime


class BooleanBuilder(MetaFieldBuilder):
    AVAILABLE_PARAMS = ()
    MARSHMALLOW_FIELD_CLS = ma_fields.Boolean


FIELD_MAPPING = {
    me.fields.BinaryField: IntegerBuilder,
    me.fields.BooleanField: BooleanBuilder,
    me.fields.ComplexDateTimeField: DateTimeBuilder,
    me.fields.DateTimeField: DateTimeBuilder,
    me.fields.DecimalField: DecimalBuilder,
    # # me.fields.DictField: ma_fields.Dict,
    # # me.fields.DynamicField: ma_fields.Dynamic,
    # # me.fields.EmailField: ma_fields.Email,
    # # me.fields.EmbeddedDocumentField: ma_fields.EmbeddedDocument,
    # # me.fields.FileField: ma_fields.File,
    me.fields.FloatField: FloatBuilder,
    # # me.fields.GenericEmbeddedDocumentField: ma_fields.GenericEmbeddedDocument,
    # # me.fields.GenericReferenceField: ma_fields.GenericReference,
    # # me.fields.GeoPointField: ma_fields.GeoPoint,
    # # me.fields.ImageField: ma_fields.Image,
    me.fields.IntField: IntegerBuilder,
    me.fields.ListField: ListBuilder,
    # # me.fields.MapField: ma_fields.Map,
    me.fields.ObjectIdField: StringBuilder,
    me.fields.ReferenceField: ReferenceBuilder,
    me.fields.SequenceField: IntegerBuilder,  # TODO: handle value_decorator
    me.fields.SortedListField: ListBuilder,
    me.fields.StringField: StringBuilder,
    # # me.fields.URLField: ma_fields.URL,
    # me.fields.UUIDField: ma_fields.UUID,
    # # me.fields.PointField: ma_fields.Point,
    # # me.fields.LineStringField: ma_fields.LineString,
    # # me.fields.PolygonField: ma_fields.Polygon,
    # # me.fields.MultiPointField: ma_fields.MultiPoint,
    # # me.fields.MultiLineStringField: ma_fields.MultiLineString,
    # # me.fields.MultiPolygonField: ma_fields.MultiPolygon,
}


def get_field_builder_for_data_type(field_me):
    field_cls = None
    field_me_types = inspect.getmro(type(field_me))
    for field_me_type in field_me_types:
        if field_me_type in FIELD_MAPPING:
            field_ma_cls = FIELD_MAPPING[field_me_type]
            break
    else:
        raise ModelConversionError(
            'Could not find field column of type {0}.'.format(field_me))
        # # Try to find a field class based on the column's python_type
        # if field_me.python_type in me.Schema.TYPE_MAPPING:
        #     field_cls = ma.Schema.TYPE_MAPPING[field_me.python_type]
        # else:
        #     raise ModelConversionError(
        #         'Could not find field column of type {0}.'.format(types[0]))
    return field_ma_cls(field_me)
