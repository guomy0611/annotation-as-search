ß

class User(db.Model):
    __tablename__ = 'user_'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)


    def __repr__(self):
        return '<User %r>' % self.username

class Sentence(db.Model):
    __tablename__ = 'sentences'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    sentence = db.Column(db.String(1000), unique=False, nullable=False)
    conll_forest = db.Column(db.String(10000), unique=False, nullable=True)
    subcat_suggested = db.Column(db.String(100),unique=False, nullable=True)
    tree_suggested = db.Column(db.String(1000), unique=False, nullable=True)
    subcat_corrected = db.Column(db.String(100),unique=False, nullable=True)

    def __repr__(self):
        return '<Sentence %r>' % self.sentence

#db.create_all()