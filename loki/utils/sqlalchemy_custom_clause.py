#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import ClauseElement, literal


class QueryMode(Enum):
    Boolean = "IN BOOLEAN MODE"
    Natural = "IN NATURAL LANGUAGE MODE"
    Query_Expansion = 'WITH QUERY EXPANSION'
    Default = ''


MYSQL = "mysql"
MYSQL_MATCH_AGAINST = u"""
                      MATCH ({0})
                      AGAINST ({1} {2})
                      """


class Match(ClauseElement):
    """
    Search FullText
    :param against: the search query
    :param table: the table needs to be query
    FullText support with in query, i.e.
        >>> session.query(Foo).filter(Match('Spam', Foo.Bar))
    """
    def __init__(self, against, mode=QueryMode.Default, *columns):
        self.columns = columns
        self.against = literal(against)
        self.mode = mode


@compiles(Match, "mysql")
def __mysql_fulltext_search(element, compiler, **kw):
    return MYSQL_MATCH_AGAINST.format(
        ", ".join([compiler.sql_compiler.process(expr, include_table=False,
                                                 literal_binds=True)
                   for expr in element.columns]),
        compiler.process(element.against),
        element.mode)