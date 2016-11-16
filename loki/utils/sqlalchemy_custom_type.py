#!/usr/bin/env python
# -*- coding: utf-8 -*-
import binascii
import simplejson as json
import msgpack
import sqlalchemy
from sqlalchemy import String, schema
from sqlalchemy.dialects.mssql import VARBINARY
from sqlalchemy.ext.compiler import compiles
from torext.sql_helper import MutationObj


class JSONEncodedObj(sqlalchemy.types.TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


def JSONObject(sqltype):
    """A type to encode/decode JSON on the fly

    sqltype is the string type for the underlying DB column.

    You can use it like:
    Column(JSONObject(Text(600)))
    """
    class _JSONEncodedObj(JSONEncodedObj):
        impl = sqltype
    return MutationObj.as_mutable(_JSONEncodedObj)


def BinaryObject(length=None, encoder=None, decoder=None):
    """A type to encode/decode Msgpack on the fly

    sqltype is the string type for the underlying DB column.

    You can use it like:
    Column(PickleObject(600))
    """
    class BinaryEncodeObj(sqlalchemy.types.TypeDecorator):
        """Represents an immutable structure as a json-encoded string."""

        impl = VARBINARY(length)

        def process_bind_param(self, value, dialect):
            if value is not None:
                value = msgpack.packb(value, default=encoder)
            return binascii.hexlify(value)

        def process_result_value(self, value, dialect):
            if value is not None:
                value = msgpack.unpackb(value, ext_hook=decoder)
            return value

        def bind_expression(self, bindvalue):
            return sqlalchemy.func.unhex(bindvalue, type_=self)


    return MutationObj.as_mutable(BinaryEncodeObj)


class FullTextSearch(schema.ColumnCollectionConstraint):
    pass


@compiles(FullTextSearch, "mysql")
def compile_full_text_search(element, compiler, **kw):
    index = element

    columns = [compiler.sql_compiler.process(expr, include_table=False,
                                             literal_binds=True)
               for expr in index.columns]

    name = element.name or 'full_text_idx_%s' % ('_'.join(index.columns))

    text = "FULLTEXT %s " % name

    columns = ', '.join(columns)
    text += '(%s)' % columns

    return text