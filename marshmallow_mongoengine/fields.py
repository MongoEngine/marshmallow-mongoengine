from marshmallow import ValidationError
from marshmallow.fields import Field
from mongoengine import ValidationError as MongoValidationError
# Republishing the default fields...
from marshmallow.fields import *  # flake8: noqa


# ...and add custom ones for mongoengine
class Reference(Field):
    """
    Marshmallow custom field to map with :class Mongoengine.DocumentReference:
    """

    def __init__(self, document_cls, *args, **kwargs):
        self.document_cls = document_cls
        super(Reference, self).__init__(*args, **kwargs)

    def _deserialize(self, value):
        try:
            return self.document_cls.objects.get(pk=value)
        except self.document_cls.DoesNotExist:
            raise ValidationError('unknown `%s` document with id `%s`' %
                                  (self.document_cls.__name__, value))
        except MongoValidationError:
            raise ValidationError('invalid ObjectId `%s`' % value)
        return value

    def _serialize(self, value, attr, obj):
        """
        Only return the pk of the document for serialization
        """
        if value is None:
            return None
        return str(value.pk)
