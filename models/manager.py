from models.person import Person

class Manager(Person):
    __mapper_args__ = {
        'polymorphic_identity': 'manager',
    }

    def __init__(self, infos):
        super().__init__(infos)

    def __repr__(self):
        return f"<Manager id={self.id}, name={self.name}>"