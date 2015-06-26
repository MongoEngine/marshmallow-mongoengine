import inspect

from marshmallow_mongoengine.conversion import params


class MetaField(object):
    AVAILABLE_PARAMS = (,)
    MONGO_FIELD_CLS = None
    MARSHMALLOW_FIELD_CLS = None

    def __init__(self, field):
        self.params = [paramCls(field) for paramCls in self.AVAILABLE_PARAMS]

    def build_field(self):
        kwargs = {}
        for param in self.params:
            param.apply(kwargs)
        return self.MONGO_FIELD_CLS(**kwargs)

    def _get_field(self):
        return self.MARSHMALLOW_FIELD_CLS

    @property
    def field(self):
        return self._get_field()


class Integer(MetaField):
    AVAILABLE_PARAMS = (params.MaxMinParam,)
    MONGO_FIELD_CLS = me.fields.IntField
    MARSHMALLOW_FIELD_CLS = ma.fields.Integer


FIELD_MAPPING = {
    me.fields.BinaryField: Integer,
    # me.fields.BooleanField: ma.fields.Boolean,
    # me.fields.ComplexDateTimeField: ma.fields.DateTime,
    # me.fields.DateTimeField: ma.fields.DateTime,
    # me.fields.DecimalField: ma.fields.Decimal,
    # # me.fields.DictField: ma.fields.Dict,
    # # me.fields.DynamicField: ma.fields.Dynamic,
    # # me.fields.EmailField: ma.fields.Email,
    # # me.fields.EmbeddedDocumentField: ma.fields.EmbeddedDocument,
    # # me.fields.FileField: ma.fields.File,
    # me.fields.FloatField: ma.fields.Float,
    # # me.fields.GenericEmbeddedDocumentField: ma.fields.GenericEmbeddedDocument,
    # # me.fields.GenericReferenceField: ma.fields.GenericReference,
    # # me.fields.GeoPointField: ma.fields.GeoPoint,
    # # me.fields.ImageField: ma.fields.Image,
    # me.fields.IntField: ma.fields.Integer,
    # me.fields.ListField: _list_field_factory,
    # # me.fields.MapField: ma.fields.Map,
    # me.fields.ObjectIdField: ma.fields.String,
    # me.fields.ReferenceField: _reference_field_factory,
    # me.fields.SequenceField: ma.fields.Integer,  # TODO: handle value_decorator
    # me.fields.SortedListField: _list_field_factory,
    # me.fields.StringField: ma.fields.String,
    # # me.fields.URLField: ma.fields.URL,
    # me.fields.UUIDField: ma.fields.UUID,
    # # me.fields.PointField: ma.fields.Point,
    # # me.fields.LineStringField: ma.fields.LineString,
    # # me.fields.PolygonField: ma.fields.Polygon,
    # # me.fields.MultiPointField: ma.fields.MultiPoint,
    # # me.fields.MultiLineStringField: ma.fields.MultiLineString,
    # # me.fields.MultiPolygonField: ma.fields.MultiPolygon,
}


def get_field_class_for_data_type(self, field_me):
    field_cls = None
    field_me_types = inspect.getmro(type(field_me))
    for field_me_type in field_me_types:
        if field_me_type in FIELD_MAPPING:
            field_ma_cls = FIELD_MAPPING[field_me_type]
            break
    else:
        raise ModelConversionError(
            'Could not find field column of type {0}.'.format(types[0]))
        # # Try to find a field class based on the column's python_type
        # if field_me.python_type in me.Schema.TYPE_MAPPING:
        #     field_cls = ma.Schema.TYPE_MAPPING[field_me.python_type]
        # else:
        #     raise ModelConversionError(
        #         'Could not find field column of type {0}.'.format(types[0]))
    return field_ma_cls
