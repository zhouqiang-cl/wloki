# -*- coding: utf-8 -*-
from os import path

# package 包名
PROJECT = 'loki'

# 本地语言，在国际化时有用，如果没有国际化，使用 en_US 即可
LOCALE = 'en_US'

# 时区
TIME_ZONE = 'Asia/Shanghai'

# tornado 进程数，若 > 1 则 tornado 会启动多进程模式，但不推荐
PROCESSES = 1

SERVE_TRACEBACK = True

# 绿色线程池大小
GREENLET_POOL_SIZE = 50

# 端口
PORT = 8000

# 地址
ADDRESS = '127.0.0.1'

# 是否开启 DEBUG 模式，如果开启，则程序会在侦测到修改后自动 reload，
# 并且会自动添加包路径到 sys.path。在生产环境最好关闭
DEBUG = True
# 显示 SQLALCHEMY 每条 SQL 执行时间
SQLDEBUG = False
# 开启 Python Exception Trace
EXCEPTION_TRACE = False


# 当 USE_BUILD 为 True 时，会使用上层的 build 目录作为静态文件和模板的根目录，
# 为 False 时，使用当前目录下的 static 和 template。生产环境使用 True，开发环境 False。
# USE_BUILD = False

# 静态文件目录
STATIC_PATH = 'static'

# 模板文件目录
TEMPLATE_PATH = 'template'

# 资产脚本配置目录
ASSET_SCRIPTS_PATH = '../scripts/asset/'
ASSET_HASH_KEY = 'asset_script_content_hash'
ASSET_SCRIPTS_CONTENT_KEY = 'asset_script_content'

# 配置 loggers。空字符串 '' 表示 root logger，即直接调用 logging.info
# 所使用的 logger。
LOGGERS = {
    '': {
        'level': 'INFO',
        'fmt': '%(color)s[%(fixed_levelname)s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s',  # NOQA
        # 'fmt': '%(color)s[%(name)s %(pathname)s][%(fixed_levelname)s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s',  # NOQA
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
    'loki': {
        'level': 'INFO',
        'fmt': '%(color)s[%(fixed_levelname)s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s',  # NOQA
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'propagate': 0
    },
    'sqlalchemy.pool': {
        'level': 'INFO',
        'fmt': '%(color)s[%(fixed_levelname)s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s',  # NOQA
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'propagate': 0
    },
    'sqlalchemy.engine': {
        'level': 'INFO',
        'fmt': '%(color)s[%(fixed_levelname)s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s',  # NOQA
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'propagate': 0
    },
    'raven': {
        'level': 'INFO',
        'fmt': '%(color)s[%(fixed_levelname)s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s',  # NOQA
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'propagate': 0
    },
    'mail': {
        'level': 'WARN',
        'fmt': '%(color)s[%(fixed_levelname)s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s',  # NOQA
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'propagate': 0
    },
    'kazoo.client': {
        'level': 'INFO',
        'propagate': 0
    }
}

# 是否在 log 中显示 request 的详细信息 (包括 header 和 body)
LOG_REQUEST = False

# 是否在 log 中显示 response 的详细信息 (包括 header 和 body)
LOG_RESPONSE = False

# 在 log 中忽略哪些 url
LOGGING_IGNORE_URLS = [
    '/favicon.ico',
]


# 页面渲染所使用的模板引擎，默认为 tornado，可以使用 jinja2
TEMPLATE_ENGINE = 'jinja2'

# Cookie 密钥
COOKIE_SECRET = 'J23Yc606TDG2Pc5J816OYnfYOgHd2kQIvxwmXqNskIE='

# Cookie 过期时间
COOKIE_EXPIRE_DAY = 7

# Cookie 作用域名
COOKIE_DOMAIN = 'loki.nosa.me'

# 用于验证身份的 Cookie 键
AUTH_COOKIE = 'loki_session'

# 用于验证身份的 Token HTTP Header
AUTH_TOKEN_HEADER = 'X-Loki-Token'
AUTH_TOKEN_PREFIX = 'token:'
AUTH_AES_KEY = COOKIE_SECRET[:16]
AUTH_AES_IV = '\xd6\xd9F_ux\x93\x18R\x9a#\xac\x1e\xdb\x01\xe1'

# zookeeper 服务器IP
ZK_ADDR = "10.19.26.31:2181,10.19.27.225:2181,10.19.29.180:2181"
ZK_JOB_PATH = "/loki/job"
ZK_LOCK_PATH = "/loki/lock"
ZK_NEW_JOB_PATH = path.join(ZK_JOB_PATH, "new_job")
ZK_JOB_STATUS_PATH = path.join(ZK_JOB_PATH, "job_status")
ZK_GANGR_PATH = path.join(ZK_LOCK_PATH, "GangrOnline")

# MySQL
SQLALCHEMY = {
    # "uri": "mysql+mysqlconnector://testdb:testdb@10.0.69.62/testdb",
    "uri": "sqlite:////tmp/myfile.db",
}
SQLALCHEMY_CDN_SYSTEM = {
    "uri": "mysql+mysqlconnector://user:password@domain.invalid/foobar",
}

# LDAP
LDAP_HOST = "ldap.nosa.me"

# Redis
REDIS_ADDR = '10.19.25.63'
REDIS_PORT = 6384
REDIS_DB_FOR_CACHE = 1

# Sentry
# SENTRY_SERVER_URL='http://b49c355be66346bf8d87d1f35c0d7209:b4e762b6449440c5b0c4646155f1deb4@sentry.hy01.internal.nosa.me/3'
SENTRY_SERVER_URL = 'http://67a4ffba14c4433f808dbded9c72378d:91be2c8be78f40d584f96ecd8d1d3306@sentry2.hy01.internal.nosa.me/5'

# OpenTSDB
# OPENTSDB_URL = 'http://10.0.12.235:4242'
OPENTSDB_URL = 'http://loki.hy01.internal.nosa.me/tsdbproxy'
OPENTSDB_CACHE_KEY_PREFIX = 'tsdbcache:'
OPENTSDB_CACHE_TTL = 60 * 3  # 3 min
OPENTSDB_TIMEOUT = 60  # 60 sec

# MAIL
SMTP_HOST = 'mx.hy01.nosa.me'
SMTP_PORT = 25

# FOR MAIL MODULE
MAIL_SERVER = 'mx.hy01.nosa.me'
MAIL_PORT = 25
#MAIL_USE_TLS = False
#MAIL_USE_SSL = False
#MAIL_DEBUG = False
#MAIL_USERNAME = None
#MAIL_PASSWORD = None
#DEFAULT_MAIL_SENDER = None

# SMS
SMS_GATEWAY_URL = 'http://sms-gateway.nosa.me/api/send'
SMS_SRE_ACCOUNT = 'sre'
SMS_SRE_TOKEN = 'MYNqvSOEfsrbPChJ'

# jstree
TREE_ROOT_ID = 1

# Users
DEBUG_USER = '_dev'

ADMIN_USERS = [
    # SRE
    'aaa',
    'bbb',

    # EP
    'xxx',

    # Others
    'yyy',

    # For debug mode
    DEBUG_USER
]

GROUPS = {
    'ti': ['aaa'],
    'gv': ['aaa'],
    'apps_0': [
        'bbb',
        'ccc',
        'aaa'
    ],
    'muce': [
        'ddd'
        'ccc',
    ],
    'lock_screen': [
        'fff',
        'ggg',
    ],
    'ads': [
        'aaa',
        'bbb',
        'ddd'
    ],
    'baobab': [
        'aaa',
        'bbb'
    ]
}

GROUP_NODE_ACCESS = {
    'ti': [3223, 2509],
    'gv': [3221, 2408],
    'apps_0': [
        2356,
        2509,  # java8
        2408,  # java7
        2485,  # java6
        2357,
        2369
    ],
    'muce': [
        3006,
        3007,
        2408,
        2509,
        3463,
        2677
    ],
    'lock_screen': [
        3123,
        3262,
        2988
    ],
    'ads': [
        2485,
        2408,
        2509,
        2382,
        2638,
        2211,
        3459
    ],
    'baobab': [
        2408,
        2903
    ]
}


SSO_ADDR = 'https://sso.nosa.me'

WHO_PERSON_LIST_ADDR = 'http://who.hy01.internal.nosa.me/api/v1/list/person/'
WHO_PERSON_ADDR = 'http://who.hy01.internal.nosa.me/api/v1/person/'

PACKAGE_HOST = 'monitor11.hy01'
DOWNLOAD_URL = 'http://download.hy01.nosa.me/download'

HEALTHY_FILE = '/home/work/lighttpd/nginx_check/index.html'
PUBLIC_DOMAIN = "http://loki.nosa.me/"

try:
    from .local_settings import *
except Exception as e:
    print 'Import local_settings error: %s' % e
