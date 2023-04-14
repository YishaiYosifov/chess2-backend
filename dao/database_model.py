from enum import Enum

class DatabaseModel:
    _table : str = None
    _primary : str = None

    def insert(self):
        from util import cursor, database

        params = self.to_dict()
        cursor.execute(f"INSERT INTO {self._table} ({', '.join(params.keys())}) VALUES ({', '.join(['%s'] * len(params))})", list(params.values()))
        database.commit()

    def update(self):
        from util import cursor, database

        params = self.to_dict()
        cursor.execute(f"UPDATE {self._table} SET {', '.join([param + '=%s' for param in params.keys()])} WHERE member_id=%s", list(params.values()) + [self.member_id])
        database.commit()
    
    def delete(self):
        from util import cursor, database
        cursor.execute(f"DELETE FROM {self._table} WHERE {self._primary}=%s", (getattr(self, self._primary),))
        database.commit()

    @classmethod
    def select(cls, **params):
        """
        Select the object from the database using the given attributes

        :param params: the attributes
        """

        from util import cursor

        cursor.execute(f"SELECT * FROM {cls._table} WHERE {' '.join([param + '=%s' for param in params.keys()])}", list(params.values()))
        return [cls.parse_obj(member) for member in cursor.fetchall()]

    def to_dict(self) -> dict[str:any]:
        """
        Convert the object to a dictionary
        """
        attributes = [attribute for attribute, value in self.__dict__.items() if value != None and not attribute.startswith("_") and not callable(attribute)]
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
            results[attribute] = value
        return results