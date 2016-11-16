from ..base.handlers import BaseHandler


class IndexHandler(BaseHandler):
    def get(self):
        self.render('ptree/index.html')


handlers = [
    ('', IndexHandler),
]
