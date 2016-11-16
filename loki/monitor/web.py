from ..base.handlers import BaseHandler


class RelativesIndexHandler(BaseHandler):
    def get(self):
        self.render('monitor/index.html')


class TemplatesIndexHandler(BaseHandler):
    def get(self):
        self.redirect("http://falcon-portal.nosa.me/templates")


class ExpressionsIndexHandler(BaseHandler):
    def get(self):
        self.redirect("http://falcon-portal.nosa.me/expressions")


class NodatasIndexHandler(BaseHandler):
    def get(self):
        self.redirect("http://falcon-portal.nosa.me/nodatas")


handlers = [
    ('/relatives', RelativesIndexHandler),
    ('/templates', TemplatesIndexHandler),
    ('/expressions', ExpressionsIndexHandler),
    ('/nodatas', NodatasIndexHandler)
]
