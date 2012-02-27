class MockForm(object):
    def __init__(self, params, obj=None):
        self.params = params
        self.obj = obj

    def validate(self):
        return len(self.params) > 0

    def populate_obj(self, obj):
        for param, value in self.params.items():
            setattr(obj, param, value)
