# Loki - 自动化运维平台

## 功能介绍

Loki 是专为豌豆荚服务体系打造的自动化运维平台，有一个非常恰当的英文单词来描述它:
[Orchestration](http://en.wikipedia.org/wiki/Orchestration_(computing)) Platform
(which is better than automation :).

Loki 的主要用途:

1. Monitoring -- 监控展示
2. Deploying -- 部署

### 监控展示

> 注: 以下各种服务器相关的指标，均刨除了在资源池中的服务器

* **Loki 首页的图表示什么**

    * cpu 使用率，是整个公司的平均使用率

    * 资源使用总览，是每个产品线的资源使用率

    * Domain Bandwidth/Availability 域名所使用的带宽、可用率

        可用率计算方式：(20X+30X) / (all requests - 40X)

    * 产品线可用率、响应时间，这是根据绑定到产品线节点上的 url(s) 的可用率综合计算出来的，
    如果没有看到你所在的产品线，说明在你的产品线节点上没有绑定任何 url

    * n 天平均可用率、响应时间。表示 n 天内，各个产品线的这两个指标的所有监测点的平均值

* **如何查看服务器性能指标**

    在这[系统展示](http://loki.nosa.me/draw)里找到你所在的产品线，点进去就可以看到各种指标

* 如何查看域名的各个指标，如 qps，响应时间，使用带宽，可用率等

    在[域名展示](http://loki.nosa.me/domain)可以查到域名的四个指标：

    * queries per second
    * response time (ms)
    * bandwidth (byte)
    * availability

* 怎样监控某一个域名的某个 path

    默认情况下，你所要查的 url，可能不存在，因为太具体了；所以得找 sre 将要监控的 url 绑定到你所在的产品线即可

### 部署

请参考[文档](https://docs.google.com/a/nosa.me/document/d/1Rz5oBQjWa5FeLiErzaBGGbWtiBQiJ8c1Uj5jc4Wl8b4)


## 开发

### 各组件负责人

* 监控展示

    * 数据存储

        * 使用 [opentsdb](http://opentsdb.net/) @wateer
        * opentsdb 使用 hbase @wateer

    * 数据收集

        * pandora-client, (yum search pandora-client) @wateer
        * 还有一些离线计算的程序，比如计算一个域名的、一个产品线的各项指标，参见[文档](https://docs.google.com/a/nosa.me/document/d/1YCYudXcnuzG0ih7gN7q0VtjmvZWb_PDWbBjxbMpat00/edit) @wateer

    * 数据展示

        * it's loki's job

* 部署

    * [job tracker](https://git.nosa.me/#/admin/projects/gangr)

    * [agent](https://git.nosa.me/#/admin/projects/vali)

### 环境搭建

    $ python --version
    Python 2.7.6
    $ node --version
    v0.10.35
    $ npm --version
    1.4.28

本地开发环境搭建步骤如下:

1. 安装 Python >= 2.7.9, 并安装 pip, virtualenv
2. 创建并进入虚拟环境:
   
        virtualenv LOKI
        source LOKI/bin/activate
        pip install -U pip

3. 安装依赖:

        pip install -r requirements.txt

4. 添加本地配置，在 loki/ 目录下创建 local_settings.py 文件，并在其中加入如下条目的适当配置:

        SQLALCHEMY = {
           "uri": "mysql+mysqlconnector://<user>:<password>@<ip>/loki",
        }

        SQLALCHEMY_CDN_SYSTEM = {
           "uri": "mysql+mysqlconnector://<user>:<password>@<ip>/cdn_system",
        } 

5. 测试 loki 打包，这一步也会使 loki 所在目录在运行时被添加到 sys.path 中
   (会在 `site-packages/easy-install.pth` 中添加 loki 所在目录的路径)

   `python setup.py develop`

6. 运行:

        make run_uwsgi_dev

***

由于线上环境使用编译后的 HTML 模板和静态文件，因此在真正上线前，需在本地编译静态文件，
并模拟线上对编译后文件进行使用:

1. 在 `local_settings.py` 中加入以下配置:

        STATIC_PATH = '../build/static'

        TEMPLATE_PATH = '../build/template'

2. 编译静态文件:

        make build

3. 运行:

        make run_uwsgi_dev

***

线上环境搭建步骤如下:

1. 安装 Python >= 2.7.9, 并安装 pip, virtualenv

2. 创建并进入虚拟环境 (同 _本地开发环境搭建步骤_)

3. 更新代码，指向 release 版本

        make update

4. 安装依赖:

   由于线上环境一般不允许外网访问，因此需要使用内部提供的 pypi 源进行安装:

        easy_install -i http://pypi.hy01.internal.nosa.me/simple/ protobuf
        pip install --trusted-host pypi.hy01.internal.nosa.me -i http://pypi.hy01.internal.nosa.me/simple/ -r requirements.txt

   > 注: 由于 protobuf 库有 `setup_requires` 项不受 pip 指定 index-url 的控制，因此需先使用 `easy_install` 单独安装

5. 添加本地配置 (同 _本地开发环境搭建步骤_)

6. 编译静态文件:

        make build

7. 运行:

        make run_uwsgi

***

`make` 支持的命令说明:

- `make build`

  编译静态文件

- `make clean`

  清理 build 文件

- `make pip-compile`

  生成 requirements.txt, 这个命令依赖 `pip-tools`，需按照如下方法安装:

  `pip install pip-tools`

- `make run_uwsgi`

  生产环境运行 loki uwsgi 进程

- `make run_uwsgi_dev`

  开发环境运行 loki uwsgi 进程

- `make reload`

  重载 uwsgi workers

- `make restart`

  重启 supervisor

- `make release`

  发布 release 版本

- `make update`
  
  更新到最新的 release 版本


### 基础组件

* opentsdb(based on hbase): 存储时序数据

* redis: rambo, alert.py, monitor.py 都会用到

* mysql: 存储任务信息，包信息，服务器和节点之间的关系等

* zookeeper: 存储服务树，任务信息等


### 前端

- requirejs

  requirejs 用于模块化 js 代码，大大增加了代码的规范性和可维护性

- grunt

  grunt 用于执行预置的 build 任务，由于使用了 requirejs，为避免线上代码需要
  加载过多的 js 文件，因此使用 grunt 进行 js 打包和压缩工作，使线上代码只需要
  加载 2 个 js 文件，增加了加载和运行的效率

### 代码结构

#### 目录

整个项目的目录结构如下:

    loki
    ├── loki/
    ├── docs/
    ├── scripts/
    ├── site-packages/
    ├── README.md
    ├── manage.py
    ├── requirements.txt
    ├── dev-requirements.txt
    └── setup.py

各文件和目录的意义为:

* `loki/` 核心代码 Python 包

* `docs/` 文档目录

* `scripts/` 可执行脚本

* `site-packages/` loki 所依赖的 Python 库，为方便修改特意放在项目中

* `README.md` 本说明文件

* `requirements.in` loki 依赖库管理文件

* `requirements.txt` pip-compile 生成的依赖信息

* `dev-requirements.txt` 开发 loki 所依赖的 Python 库

* `manage.py` 用于控制 loki 运行的脚本，同样可以添加其他自定义的任务

* `setup.py` 打包脚本

包 `loki` 的目录结构如下:

    loki
    ├── base
    │   ├── __init__.py
    │   ├── models.py
    │   ├── api.py
    │   └── handlers.py
    ├── user
    │   ├── __init__.py
    │   ├── models.py
    │   ├── api.py
    │   └── handlers.py
    | ... (部分省略)
    ├── static/
    ├── template/
    ├── __init__.py
    ├── utils.py
    ├── const.py
    ├── errors.py
    ├── redis.py
    ├── zookeeper.py
    ├── settings.py
    └── app.py

其中各模块的详细解释见「模块划分」


#### 模块

按照用途划分模块，如，用于异常类的定义的是一个模块，用于工具函数的是一个模块
，用于某个业务功能的是一个模块等等。

所有的模块结构扁平，不需要 `lib/`, `conf/` 的层级划分。

整体结构中，由下至上，可以分为两类模块:

1. 基础模块

2. 业务功能模块


##### 基础模块

基础模块被其他更上层的模块调用，可以互相依赖

* `base`

    包含 `handlers` 和 `models`，定义了被功能模块使用的 request handler
    类和实体数据模型的基类

* `const`

    定义内部使用，并且可能被多个模块引用的常量。专由某个模块使用的常量
    放在那个模块中就可以，不需要放在这里

* `utils`

    定义各种工具函数。工具函数不包含业务逻辑。

* `errors`

    定义专属于 loki 的异常类。

* `settings`

    与服务运行有关的配置。区别于 const，settings 可能根据运行环境不同而变化
    ，而 const 固定不变，只与业务和功能有关。

* `redis`, `zookeeper`

    这两个模块放置与 redis、zookeeper 两个基础设施有关的代码，如客户端类
    的定义，连接池的定义，客户端实例的初始化等。

* `app`

    服务的运行入口，初始化了 app 实例，并声明了第一层的 url 映射关系，通过它
    运行服务时会自动加载所有涉及到的模块


##### 业务功能模块

一个业务功能模块一般包含 3 个子模块:

* `models` 定义数据模型和基本的 CRUD 方法

* `api` 定义操作业务逻辑的函数，被 `handlers` 或其他功能模块的 `api` 调用

* `handlers` 定义 HTTP 服务层的处理方式，调用 `api` 完成对数据层的操作

现有业务功能模块列出如下:

* `user` 与用户有关的部分

* `monitor` 监控和报警的配置部分

* `alarm` 报警消息的展示部分，未来可能包含 issue tracker 的功能

* `draw` 监控数据画图

* `ptree` 服务树描述管理

* `audit` 服务树节点更改审核

* `job` 任务管理

* `tpl` 模板管理


## Note

- 若需要增改项目依赖库，首先编辑 `requirements.in` 文件，再执行 `pip-compile requirements.in` 生成依赖信息
- 代码规范见 `docs/python_style_guide.rst`
- 有关 Git **请使用 `git pull --rebase` 以避免和消除不必要的 merge**
- kazoo replacement: [https://pypi.python.org/pypi/zc.zk/2.0.1](https://pypi.python.org/pypi/zc.zk/2.0.1)
- gevent VS tornado.http.AsyncHTTPClient VS kazoo conflicts.
- grant privileges


## SOP

* Fix OpenTSDB

    `tsdb fsck --fix 20d-ago avg domain.availability --config /etc/opentsdb/opentsdb.conf`


## 独立模块

### Poseidon

> by wzyboy

#### Etymology

Poseidon is one of the twelve Olympian deities of the pantheon in Greek
mythology. His main domain is the ocean, and he is called the "God of the
Sea".

#### Usage
    python -m poseidon

### torext

> by mengxiao


## 维护人

| name | email |
| ---- | ----- |
| wateer | wateer@nosa.me |

