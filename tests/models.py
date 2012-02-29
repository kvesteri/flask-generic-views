from .extensions import db


class User(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.Unicode(255), index=True)
    age = db.Column(db.Integer, index=True)
    deleted_at = db.Column(db.DateTime)

    def as_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age
        }
