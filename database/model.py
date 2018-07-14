from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, Boolean


Base = declarative_base()
engine = create_engine("postgresql://localhost/test1", echo=False)


class Sentence(Base):
    __tablename__ = 'sentences'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    sentence = Column(String(1000), unique=False, nullable=False)
    conll_forest = Column(String(10000), unique=False, nullable=True)
    subcat_suggested = Column(String(100),unique=False, nullable=True)

    tree_correct = Column(String(1000), unique=False, nullable=True)
    subcat_correct = Column(String(100),unique=False, nullable=True)
    subcat_edited = Column(Boolean, unique=False, nullable=True, server_default="false")
    tree_annotated = Column(Boolean, unique=False, nullable=True, server_default="false")
    last_modified = Column(Boolean, unique=False, nullable=True, server_default="false")

    def __repr__(self):
        return '<Sentence %r>' % self.sentence

Base.metadata.create_all(engine)

