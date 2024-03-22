from sqlalchemy.orm import scoped_session, sessionmaker

TestScopedSession = scoped_session(sessionmaker())
