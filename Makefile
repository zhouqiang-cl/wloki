.PHONY: build clean

ifneq (,$(VIRTUAL_ENV))
VIRTUAL = -H $(VIRTUAL_ENV)
else
VIRTUAL = 
endif

build:
	./node_modules/.bin/grunt build
	rm -rf build/
	mv _build build

update:
	git checkout .
	git fetch
	git checkout origin/release

update-privilege:
	git checkout .
	git fetch
	git checkout origin/release-privilege

restart:
	bash deploy/restart.sh

reload:
	echo "c" > /tmp/uwsgi.fifo

requirement:
	bash deploy/install_requirement.sh

jasmine:
	open loki/static/js/test/runner.html

grunt_clean:
	./node_modules/.bin/grunt clean

clean:
	rm -rf .tmp *.egg-info docs/_build build _build

pip-compile:
	pip-compile ./requirements.in

run_uwsgi:
	uwsgi $(VIRTUAL) --master --http :8000 --workers $$(python -c "import multiprocessing;print multiprocessing.cpu_count()") --gevent 100 --wsgi-file loki/get_wsgi.py --callable wsgi_app -L --worker-reload-mercy 10 --cache2 name=default,items=100 --lazy-apps --master-fifo /tmp/uwsgi.fifo  --stats :8001 --stats-http --cpu-affinity 1 --evil-reload-on-rss 768

run_uwsgi_dev:
	uwsgi $(VIRTUAL) --cache2 name=default,items=100 --master --http :8000 --workers 1 --gevent 100 --wsgi-file loki/get_wsgi.py --callable wsgi_app -L --py-autoreload 3 --lazy-apps --master-fifo /tmp/uwsgi.fifo --stats :8001 --stats-http --evil-reload-on-rss 768 --honour-stdin

run_privilege_uwsgi:
	uwsgi $(VIRTUAL) --master --http :8000 --workers $$(python -c "import multiprocessing;print multiprocessing.cpu_count()") --gevent 100 --wsgi-file loki/get_wsgi.py --callable privilege_wsgi_app -L --worker-reload-mercy 10 --cache2 name=default,items=100 --lazy-apps --master-fifo /tmp/uwsgi.fifo  --stats :8001 --stats-http --cpu-affinity 1

run_privilege_uwsgi_dev:
	uwsgi $(VIRTUAL) --cache2 name=default,items=100 --master --http :8000 --workers 1 --gevent 100 --wsgi-file loki/get_wsgi.py --callable privilege_wsgi_app -L --py-autoreload 3 --lazy-apps --master-fifo /tmp/uwsgi.fifo --stats :8001 --stats-http

release:
	git stash
	git checkout release
	git pull origin release
	git rebase master
	git tag $$(date "+release-%F_%H-%M-%S") HEAD
	git push origin release
	git push --tags origin && git fetch --tags
	git checkout master

release-privilege:
	git stash
	git checkout release-privilege
	git pull origin release-privilege
	git rebase master
	git tag $$(date "+release-privilege-%F_%H-%M-%S") HEAD
	git push origin release-privilege
	git push --tags origin && git fetch --tags
	git checkout master
