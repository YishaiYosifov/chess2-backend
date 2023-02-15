from enum import Enum

class DatabaseModel:
    _table : str = None

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

    @classmethod
    def select(cls, **params):
        from util import cursor

        cursor.execute(f"SELECT * FROM {cls._table} WHERE {' '.join([param + '=%s' for param in params.keys()])}", list(params.values()))
        return [cls.parse_obj(member) for member in cursor.fetchall()]

    def to_dict(self) -> dict[str:any]:
        variables = {}
        for key, value in self.__dict__.items():
            if not value or key.startswith("_") or callable(key): continue

            if isinstance(value, Enum): value = value.value
            variables[key] = value
        
        return variables