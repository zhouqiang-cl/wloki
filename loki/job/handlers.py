#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..base.handlers import BaseHandler
from .privileges import JobPrivilege
from .models import Package


class IndexHandler(BaseHandler):
    def get(self):
        self.render('job/index.html')


class PackagesHandler(BaseHandler):
    def get(self):
        packages = Package.query.group_by(Package.name).all()
        self.render('job/packages.html', packages=packages)


class PackageItemHandler(BaseHandler):
    def get(self, name):
        packages = Package.query.group_by(Package.name).all()
        package_items = Package.query.filter(
            Package.name == name).order_by(Package.ctime.desc())
        self.render('job/packages.html', name=name, packages=packages, package_items=package_items)


class ImagesHandler(BaseHandler):
    def get(self):
        import requests
        url = "http://docker.internal.nosa.me/image/services"
        images = requests.get(url).json()
        self.render('job/images.html', images=images)


class ImagesItemHandler(BaseHandler):
    def get(self, name):
        import requests

        url = "http://docker.internal.nosa.me/image/services"
        images = requests.get(url).json()

        url = "http://docker.internal.nosa.me/image/builders/" + name
        image_items = requests.get(url).json()

        self.render('job/images.html', name=name, images=images, image_items=image_items)


handlers = [
    ('', IndexHandler),
    ('/packages', PackagesHandler),
    ('/packages/(.+)', PackageItemHandler),
    ('/images', ImagesHandler),
    ('/images/(.+)', ImagesItemHandler),
]
