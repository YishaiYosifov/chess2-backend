from __future__ import annotations

from datetime import datetime
from enum import Enum

import logging
import time

from mysql.connector.errors import PoolError
from pydantic import BaseModel
from flask import request

from extensions import BaseType, cnx_pool, CONFIG

class DatabaseModel(BaseModel):
    def dynamic_db(function):
        def wrapper(self, pool_conn : PoolConn = None, *args, **kwargs):
            if not pool_conn: pool_conn = request.pool_conn

            return function(self, pool_conn=pool_conn, *args, **kwargs)
        return wrapper

    __tablename__ : str = None
    __primary__ : str = None

    @dynamic_db
    def insert(self, pool_conn : PoolConn):
        params = self.to_dict()

        pool_conn.cursor.execute(f"INSERT INTO {self.__tablename__} ({', '.join(params.keys())}) VALUES ({', '.join(['%s'] * len(params))})", list(params.values()))
        setattr(self, self.__primary__, pool_conn.cursor.lastrowid)

    @dynamic_db
    def update(self, pool_conn : PoolConn):
        params = self.to_dict()
        pool_conn.cursor.execute(f"UPDATE {self.__tablename__} SET {', '.join([param + '=%s' for param in params.keys()])} WHERE {self.__primary__}=%s", list(params.values()) + [getattr(self, self.__primary__)])

    @dynamic_db
    def delete(self, pool_conn : PoolConn):
        pool_conn.cursor.execute(f"DELETE FROM {self.__tablename__} WHERE {self.__primary__}=%s", (getattr(self, self.__primary__),))

    @classmethod
    @dynamic_db
    def delete_all(cls, pool_conn : PoolConn, **params):
        statement = ", ".join(
            [
                param + (value._sign if hasattr(value, "_sign") else "=") + '%s'
                for param, value in params.items()
            ]
        )

        params = list(map(lambda i: i._value if hasattr(i, "_value") else i, params.values()))
        pool_conn.cursor.execute(f"DELETE FROM {cls.__tablename__} WHERE {statement}", params)

    @classmethod
    @dynamic_db
    def select(cls, pool_conn : PoolConn, **params) -> "Select":
        """
        Select the object from the database using the given attributes

        :param params: the attributes
        """
        
        return Select(cls, pool_conn=pool_conn, params=params)

    def to_dict(self, exclude = []) -> dict[str:any]:
        """
        Convert the object to a dictionary
        """
        attributes = [attribute for attribute, value in self.__dict__.items()
            if value != None and \
            not attribute in exclude and \
            not attribute.startswith("_") and \
            not callable(attribute)
        ]
        return self.get(attributes)
    
    def get(self, attributes : list) -> dict[str:any]:
        """
        Get attributes from the object

        :param attributes: the attribute to get
        """
        results = {}
        for attribute in attributes:
            value = getattr(self, attribute)
            if isinstance(value, Enum): value = value.value
            elif value == "CURRENT_TIMESTAMP": value = datetime.now()
            results[attribute] = value
        return results

class Select:
    def __init__(self, model : DatabaseModel, pool_conn : PoolConn, params : dict):
        i = 0
        statement = f"SELECT * FROM {model.__tablename__} "
        for param, value in params.items():
            if i: statement += " OR " if isinstance(value, Or) else " AND "
            else: statement += "WHERE "
            statement += param + "=%s"

            i += 1

        self._statement = statement
        self.params = params
        self.model = model

        self.pool_conn = pool_conn

        self.clauses = {
            "ORDER BY": None,
            "LIMIT": None
        }

    def _execute(self):
        processed_statement = self._statement
        for clause, value in self.clauses.items():
            if value: processed_statement += f" {clause} {value} "

        params = list(map(lambda i: i._value if hasattr(i, "_value") else i, self.params.values()))
        self.pool_conn.cursor.execute(processed_statement, params)

    def first(self):
        self._execute()
        fetched = self.pool_conn.cursor.fetchone()
        return self.model.parse_obj(fetched) if fetched else None
    
    def all(self) -> list:
        self._execute()

        return [self.model.parse_obj(member) for member in self.pool_conn.cursor.fetchall()]
    
    def limit(self, to : int) -> Select:
        self.clauses["LIMIT"] = to
        return self
    
    def order_by(self, by) -> Select:
        self.clauses["ORDER BY"] = by
        return self

class Or(BaseType): pass

class LessThan(BaseType): _sign = "<"
class LargerThan(BaseType): _sign = ">"

class PoolConn:
    def __init__(self):
        timeout = 0.1
        while True:
            try: self.conn = cnx_pool.get_connection()
            except PoolError:
                logging.error(f"MySQL pool exhausted: timing out for {timeout}s")
                time.sleep(timeout)

                timeout *= 2
                if timeout > CONFIG["max_mysql_pool_timeout"]: timeout = CONFIG["max_mysql_pool_timeout"]
                continue
            break
        self.cursor = self.conn.cursor(dictionary=True)

        self._closed = False
    
    def close(self):
        self._closed = True

        self.conn.commit()
        
        self.cursor.close()
        self.conn.close()