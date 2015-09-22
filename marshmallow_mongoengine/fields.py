import bson
from marshmallow import ValidationError, fields, missing
from mongoengine import ValidationError as MongoValidationError, NotRegistered
from mongoengine.base import get_document


# Default marshmallow fields consider None and empty list/tuple as a valid
class SkipEmptyClass(object):
    def __init__(self, *args, **kwargs):
        skip_empty = kwargs.pop('skip_empty', True)
        super(SkipEmptyClass, self).__init__(*args, **kwargs)
        self.skip_empty = skip_empty

    def _serialize(self, value, attr, obj):
        value = super(SkipEmptyClass, self)._serialize(value, attr, obj)
        if (self.skip_empty and
                (value is None or isinstance(value, (list, tuple)) and not value)):
            return missing
        return value


class Field(SkipEmptyClass, fields.Field):
    pass


class Raw(SkipEmptyClass, fields.Raw):
    pass


class Nested(SkipEmptyClass, fields.Nested):
    pass


class List(SkipEmptyClass, fields.List):
    pass


class String(SkipEmptyClass, fields.String):
    pass


class UUID(SkipEmptyClass, fields.UUID):
    pass


class Number(SkipEmptyClass, fields.Number):
    pass


class Integer(SkipEmptyClass, fields.Integer):
    pass


class Decimal(SkipEmptyClass, fields.Decimal):
    pass


class Boolean(SkipEmptyClass, fields.Boolean):
    pass


class FormattedString(SkipEmptyClass, fields.FormattedString):
    pass


class Float(SkipEmptyClass, fields.Float):
    pass


class Arbitrary(SkipEmptyClass, fields.Arbitrary):
    pass


class DateTime(SkipEmptyClass, fields.DateTime):
    pass


class LocalDateTime(SkipEmptyClass, fields.LocalDateTime):
    pass


class Time(SkipEmptyClass, fields.Time):
    pass


class Date(SkipEmptyClass, fields.Date):
    pass


class TimeDelta(SkipEmptyClass, fields.TimeDelta):
    pass


class Fixed(SkipEmptyClass, fields.Fixed):
    pass


class Price(SkipEmptyClass, fields.Price):
    pass


class Url(SkipEmptyClass, fields.Url):
    pass


class Email(SkipEmptyClass, fields.Email):
    pass


class Select(SkipEmptyClass, fields.Select):
    pass


class QuerySelect(SkipEmptyClass, fields.QuerySelect):
    pass


class QuerySelectList(SkipEmptyClass, fields.QuerySelectList):
    pass


class Constant(SkipEmptyClass, fields.Constant):
    pass


# Verbatim republish for those ones
Method = fields.Method
Function = fields.Function


# Aliases
URL = Url
Enum = Select
Str = String
Bool = Boolean
Int = Integer


# ...and add custom ones for mongoengine
class ObjectId(fields.Field):

    def _deserialize(self, value, attr, data):
        try:
            return bson.ObjectId(value)
        except:
            raise ValidationError('invalid ObjectId `%s`' % value)

    def _serialize(self, value, attr, obj):
        if value is None:
            return missing
        return str(value)


class Reference(fields.Field):
    """
    Marshmallow custom field to map with :class Mongoengine.ReferenceField:
    """

    def __init__(self, document_type_obj, *args, **kwargs):
        self.document_type_obj = document_type_obj
        super(Reference, self).__init__(*args, **kwargs)

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, str):
            self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    def _deserialize(self, value, attr, data):
        document_type = self.document_type
        try:
            return document_type.objects.get(pk=value)
        except (document_type.DoesNotExist, MongoValidationError, ValueError, TypeError):
            raise ValidationError('unknown document %s `%s`' %
                                  (document_type._class_name, value))
        return value

    def _serialize(self, value, attr, obj):
        # Only return the id of the document for serialization
        if value is None:
            return missing
        return value.id


class GenericReference(fields.Field):
    """
    Marshmallow custom field to map with :class Mongoengine.GenericReferenceField:

    :param choices: List of Mongoengine document class (or class name) allowed

    .. note:: Without `choices` param, this field allow to reference to
        any document in the application which can be a security issue.
    """
    def __init__(self, *args, **kwargs):
        self.document_class_choices = []
        choices = kwargs.pop('choices', None)
        if choices:
            # Temporary fix for https://github.com/MongoEngine/mongoengine/pull/1060
            for choice in choices:
                if hasattr(choice, '_class_name'):
                    self.document_class_choices.append(choice._class_name)
                else:
                    self.document_class_choices.append(choice)
        super(GenericReference, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data):
        # To deserialize a generic reference, we need a _cls field in addition
        # with the id field
        if not isinstance(value, dict) or not value.get('id') or not value.get('_cls'):
            raise ValidationError("Need a dict with 'id' and '_cls' fields")
        doc_id = value['id']
        doc_cls_name = value['_cls']
        if self.document_class_choices and doc_cls_name not in self.document_class_choices:
            raise ValidationError("Invalid _cls field `%s`, must be one of %s" %
                                  (doc_cls_name, self.document_class_choices))
        try:
            doc_cls = get_document(doc_cls_name)
        except NotRegistered:
            raise ValidationError("Invalid _cls field `%s`" % doc_cls_name)
        try:
            doc = doc_cls.objects.get(pk=doc_id)
        except (doc_cls.DoesNotExist, MongoValidationError, ValueError, TypeError):
            raise ValidationError('unknown document %s `%s`' %
                                  (doc_cls_name, value))
        return doc

    def _serialize(self, value, attr, obj):
        # Only return the id of the document for serialization
        if value is None:
            return missing
        return value.id


class GenericEmbeddedDocument(fields.Field):
    """
    Dynamic embedded document
    """

    def _deserialize(self, value, attr, data):
        # Cannot deserialize given we have no way knowing wich kind of
        # document is given...
        return missing

    def _serialize(self, value, attr, obj):
        # Create the schema at serialize time to be dynamic
        from marshmallow_mongoengine.schema import ModelSchema

        class NestedSchema(ModelSchema):
            class Meta:
                model = type(value)
        data, errors = NestedSchema().dump(value)
        if errors:
            raise ValidationError(errors)
        return data


class Map(fields.Field):
    """
    Marshmallow custom field to map with :class Mongoengine.Map:
    """

    def __init__(self, mapped, **kwargs):
        self.mapped = mapped
        self.schema = getattr(mapped, "schema", None)
        super(Map, self).__init__(**kwargs)

    def _schema_process(self, action, value):
        func = getattr(self.schema, action)
        total = {}
        for k, v in value.items():
            data, errors = func(v)
            if errors:
                raise ValidationError(errors)
            total[k] = data
        return total

    def _serialize(self, value, attr, obj):
        if self.schema:
            return self._schema_process('dump', value)
        else:
            return value

    def _deserialize(self, value, attr, data):
        if self.schema:
            return self._schema_process('load', value)
        else:
            return value


class Skip(fields.Field):
    """
    Marshmallow custom field that just ignore the current field
    """

    def _deserialize(self, value, attr, data):
        return missing

    def _serialize(self, value, attr, obj):
        return missing
