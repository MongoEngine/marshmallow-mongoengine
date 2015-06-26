# Marshmallow-Mongoengine

## Introduction

Mongoengine integration with the marshmallow (de)serialization library.

Heavilly ~~ripped~~ inspired by [marshmallow-sqlalchemy](http://marshmallow-sqlalchemy.rtfd.org/)

## Declare your models

```
import mongoengine as me

class Author(me.Document):
    id = me.IntField(primary_key=True, default=1)
    name = me.StringField()
    books = me.ListField(me.ReferenceField('Book'))

    def __repr__(self):
        return '<Author(name={self.name!r})>'.format(self=self)


class Book(me.Document):
    title = me.StringField()
```

## Generate marshmallow schemas

```
from marshmallow_mongoengine import ModelSchema

class AuthorSchema(ModelSchema):
    class Meta:
        model = Author

class BookSchema(ModelSchema):
    class Meta:
        model = Book

author_schema = AuthorSchema()
```

## (De)serialize your data

```
author = Author(name='Chuck Paluhniuk').save()
book = Book(title='Fight Club', author=author).save()

dump_data = author_schema.dump(author).data
# {'id': 1, 'name': 'Chuck Paluhniuk', 'books': ['5578726b7a58012298a5a7e2']}

author_schema.load(dump_data).data
# <Author(name='Chuck Paluhniuk')>
```
