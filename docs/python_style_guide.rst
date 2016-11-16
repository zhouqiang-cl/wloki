Python 代码规范
===============

命名
----

- 尽量简单明了。

- 不需要在各种模块、类、函数名前面加标识项目名称的前缀，因为已经处于项目的 package 之下，没必要重复声明。

  如以下模块， ``WD`` ， ``DB`` 的前缀都可以去掉，然后改成首字母小写:

  ``WDDBService.py`` -> ``service.py``

  ``WDDBNames.py`` -> ``const.py`` ("const" 常量比 "names" 更合适)

- **模块名(文件名)**, **函数名**, **变量名** 使用小写、下划线命名法:

  + 模块:

    ``Radix`` -> ``radix``, ``Utils`` -> ``utils``

  + 函数:

    ``addUrlTopicIndex`` -> ``add_url_topic_index``

- **类名** 使用首字母大写的驼峰命名法:

  ``class zookeeper_client(object):`` -> ``class ZookeeperClient(object):``

- 可以缩写，但不要更改单词本身:

  ``midware`` -> ``middleware``


导入方式
--------

- 每个导入应该独占一行

  **Yes**

  .. code:: python

    import os
    import sys

  *No*

  .. code:: python

    import os, sys

- 导入总应该放在文件顶部, 位于模块注释和文档字符串之后, 模块全局变量和常量之前(之间空两行).

  导入应该按照从最通用到最不通用的顺序分组:

  1. 标准库导入

  2. 第三方库导入

  3. 应用程序指定导入

- 不要使用 ``import *``, 一个从别的模块导入过来的变量应该能在代码的头部找到明确的导入语句。

  对于包含很多常量的模块，最好的导入方法是 ``from xx import const`` 之后可以 ``const.SOME_VARIABLE``,
  如果 ``const`` 与其他模块冲突，可以 ``from xx import const as xx_const``, ``from oo import const as oo_const``

- 项目包内所有模块之间一律使用相对导入( `relative import <http://www.python.org/dev/peps/pep-0328/>`_)

  .. code:: python

    # Structure:
    # myproject
    # ├── app1
    # │   ├── __init__.py
    # │   ├── models.py
    # │   └── api.py
    # ├── errors.py
    # └── utils.py
    #
    # file `myproject/app1/api.py`

    from .models import User
    from ..utils import truncate
    from ..errors import DoesNotExist


引号
----

正常情况下，所有字符串以及文档字符串都应该使用双引号。单引号用于语义上不变的字符串标记

.. code:: python

    def get_messages():
        """This is a function for getting messages"""
        return {
            'double_quote': "By default used for a strings",
            'single_quote': "used for small symbol-like strings"
        }


空格&空行
---------

#. 函数、类之间空 2 行，类的方法之间空 1 行，类的第一个方法上面空 1 行。

#. 不要在行尾留空格或在文件末尾留多余的空行

#. 括号内不要有空格.

   **Yes**

   .. code:: python

    spam(ham[1], {eggs: 2}, [])

   *No*:

   .. code:: python

    spam( ham[ 1 ], { eggs: 2 }, [ ] )

#. 不要在逗号, 分号, 冒号前面加空格, 但应该在它们后面加(除了在行尾).

   **Yes**

   .. code:: python

    if x == 4:
        print x, y
    x, y = y, x

   *No*

   .. code:: python

    if x == 4 :
        print x , y
    x , y = y , x

#. 参数列表, 索引或切片的左括号前不应加空格.

   **Yes**

   .. code:: python

    spam(1)
    dict['key'] = list[index]

   *No*

   .. code:: python

    spam (1)
    dict ['key'] = list [index]

#. 在二元运算符两边都加上一个空格, 比如赋值( ``=`` ),
   比较 ( ``==, <, >, !=, <>, <=, >=, in, not in, is, is not`` ),
   布尔 ( ``and, or, not`` ). 至于算术操作符两边的空格该如何使用,
   需要根据情况判断. 不过两侧务必要保持一致.

   **Yes**

   .. code:: python

    x == 1
    i = i + 1
    submitted += 1
    x = x*2 - 1
    hypot2 = x*x + y*y
    c = (a + b) * (a - b)

   *No*

   .. code:: python

    x<1
    i=i+1
    submitted +=1
    c = (a+b) * (a-b)

#. 当 ``=`` 用于指示关键字参数或默认参数值时, 不要在其两侧使用空格.

   **Yes**

   .. code:: python

    def complex(real, imag=0.0): return magic(r=real, i=imag)

   *No*

   .. code:: python

    def complex(real, imag = 0.0): return magic(r = real, i = imag)

#. 不要用空格来垂直对齐多行间的标记, 因为这会成为维护的负担
   (适用于 ``:``, ``#``, ``=`` 等):

   **Yes**

   .. code:: python

    foo = 1000  # comment
    long_name = 2  # comment that should not be aligned

    dictionary = {
        "foo": 1,
        "long_name": 2,
    }

   *No*

   .. code:: python

    foo       = 1000  # comment
    long_name = 2     # comment that should not be aligned

    dictionary = {
        "foo"      : 1,
        "long_name": 2,
    }


合并语句
--------

不要在行尾加分号, 也不要用分号将两条命令放在同一行

**Yes**

.. code:: python

    if foo:
      print foo

*No*

.. code:: python

    if foo: print foo

**Yes**

.. code:: python

    x = foo
    print x

*No*

.. code:: python

    x = foo; print x


文档字符串
----------

文档字符串是包, 模块, 类或函数里的第一个语句, 这些字符串可以通过对象的
``__doc__`` 属性被自动提取, 并且被 pydoc 或 sphinx 所用, 生成格式漂亮的文档.
文档字符串的惯例是使用三重双引号 ``"""``.

如果不是既显然又简短, 任何函数或方法都应该有一个文档字符串. 而且,
任何外部可访问的函数或方法, 都需要文档字符串. 文档字符串应该包含函数做什么,
以及输入和输出的详细描述.  通常, 不应该描述「怎么做」, 除非是一些复杂的算法.
对于技巧性的代码, 块注释或者行内注释是最重要的. 文档字符串应该提供足够的信息,
当别人编写代码调用该函数时, 只要看文档字符串就可以对它做了什么、
如何调用获得清晰的印象和理解.

文档字符串中定义参数 (param)，返回值 (returns)，异常 (raises) 等字段时
需要使用符合 rst 格式的标记，
参考: http://sphinx-doc.org/domains.html#the-python-domain

一个文档字符串应该这样组织:

#. 紧接着 ``"""`` 后面的的概述,可以段行

#. 空格

#. 对参数、返回值、可能产生的异常的详细描述和定义

**Source code**

.. code:: python

    def get_users(user_ids, remove_delete=False, detail=False):
        """Get user objects by user ids

        This function is the standard API for any equivalent or upper layer
        (eg. :mod:`models.topic` or :mod:`web.user`)

        :param list user_ids: A list of key of rows in :class:`User` ColumnFamily
        :param bool detail: Whether to get detail data of user object.

        :rtype: list of user objects

        The user object contained in return list could be represented like this::

            {
                - nick
                - status
                - ctime
                - counters: {
                    - like_count
                    - new_reply_count
                }
            }

        :raises: KeyError
        """
        ...

.. 类示例


注释
----

最需要写注释的是代码中那些技巧性的部分。如果你在下次代码走查的时候必须解释一下，
那么你应该现在就给它写注释。对于复杂的操作，应该在其操作开始前写上若干行注释。
对于不是一目了然的代码, 应在其行尾添加注释。 为保证格式，注释在井号之后要空 1 格。

.. code:: python

    # We use a weighted dictionary search to find out where i is in
    # the array.  We extrapolate position based on the largest num
    # in the array and the array size and then do binary search to
    # get the exact number.

为了提高可读性, 行内注释应该至少离开代码2个空格

.. code:: python

    if i & (i-1) == 0:  # True if i is a power of 2

有时需要为临时代码使用 TODO 注释，TODO 注释应该在所有开头处包含 "TODO" 字符串，
紧跟着是用括号括起来的你的名字，email 地址或其它标识符，然后是一个可选的冒号，
接着必须有一行注释，解释要做什么。这样做的主要目的是为了有一个统一的 TODO 格式，
这样添加注释的人就可以搜索到 (并可以按需提供更多细节) 。
写了 TODO 注释并不保证写的人会亲自解决问题。

.. code:: python

    # TODO(mengxiao): Drop the use of "has_key".

如果你的TODO是 "将来做某事" 的形式, 那么请确保你包含了一个指定的日期，eg.
``("2013年9月解决")``
或者一个特定的事件，eg.
``("等到所有的函数都可以处理 JSON 就移除这些代码")`` 。


面向对象编程
------------

如果一个类不继承自其它类，就显式的从 object 继承，嵌套类也一样。

继承自 object 是为了使属性(properties)正常工作，并且这样可以保护你的代码，使其不受 Python 潜在不兼容性影响。
这样做也定义了一些特殊的方法，这些方法实现了对象的默认语义，包括

    ``__new__``, ``__init__``, ``__delattr__``, ``__getattribute__``,
    ``__setattr__``, ``__hash__``, ``__repr__``, ``__str__``

等，详细的用法可以参考 http://www.rafekettler.com/magicmethods.html
这个非常好的教程。


字符串
------

字符串

用 ``%`` 操作符格式化字符串, 即使参数都是字符串. 不过也不能一概而论,
你需要在 ``+`` 和 ``%`` 之间好好判定.

**Yes**

.. code:: python

    x = a + b
    x = '%s, %s!' % (imperative, expletive)
    x = 'name: %s; score: %d' % (name, n)

*No*

.. code:: python

    x = '%s%s' % (a, b)  # use + in this case
    x = imperative + ', ' + expletive + '!'  # inconvenient
    x = 'name: ' + name + '; score: ' + str(n)  # `str` is called

避免在循环中用 ``+`` 和 ``+=`` 操作符来累加字符串. 由于字符串是不可变的,
这样做会创建不必要的临时对象, 并且导致二次方而不是线性的运行时间.
作为替代方案, 你可以将每个子串加入列表, 然后在循环结束后用 ``.join`` 连接列表
(也可以将每个子串写入一个 ``cStringIO.StringIO`` 缓存中).

**Yes**

.. code:: python

    items = ['<table>']
    for last_name, first_name in employee_list:
        items.append('<tr><td>%s, %s</td></tr>' % (last_name, first_name))
    items.append('</table>')
    employee_table = ''.join(items)

*No*

.. code:: python

    employee_table = '<table>'
    for last_name, first_name in employee_list:
        employee_table += '<tr><td>%s, %s</td></tr>' % (last_name, first_name)
    employee_table += '</table>'

为多行字符串使用三重双引号而非三重单引号. 不过要注意, 通常用隐式行连接更清晰,
因为多行字符串与程序其他部分的缩进方式不一致.

**Yes**

.. code:: python

    def pri():
        print ("This is much nicer.\n"
               "Do it this way.\n")

*No*

.. code:: python

    def pri():
        print """This is pretty ugly.
        Don't do this.
        """


括号
----

宁缺毋滥地使用括号。

除非是用于实现行连接, 否则不要在返回语句或条件语句中使用括号.
不过在元组两边使用括号是可以的.

**Yes**

.. code:: python

    if foo:
        pass

    while x:
        pass

    if x and y:
        pass

    if not x:
        pass

    return foo

    for (x, y) in dict.items(): ...

*No*

.. code:: python

    if (x):
        pass

    if (x and y):
        pass

    return (foo)


缩进
----

用 4 个空格来缩进代码

如果第一行写了参数，第二行的参数与上一行的括号对齐

.. code:: python

    foo = long_function_name(var_one, var_two,
                             var_three, var_four)

定义函数时，如果第一行未写参数，第二行要多一级缩进，为与函数主题区分开，
调用时则只需缩进一级

.. code:: python

    def long_function_name(
            var_one, var_two, var_three,
            var_four):
        print(var_one)

    result = long_function_name(
                var_one, var_two, var_three,
                var_four)


其他规范
--------

- 文件头部要声明编码类型，默认使用 utf8

  .. code:: python

    # -*- coding:utf-8 -*-

  可以使用以上的兼容写法，也可以直接 ``# coding: utf-8`` ，见 http://legacy.python.org/dev/peps/pep-0263/

- 对于需要执行的 Python 文件，头部可以声明所使用的 Python 解释器的路径，
  放在编码类型声明之后

  推荐使用 env 的声明方式，这样可以根据运行环境选择当前的 Python:

  .. code:: python

    #!/usr/bin/env python

  如果要使用特定的执行路径的话，也可以直接写:

  .. code:: python

    #!/usr/bin/python

- 一行尽量控制在 79 个字符内，若超过则可考虑断行

  .. code:: python

    with open('/path/to/some/file/you/want/to/read') as file_1, \
            open('/path/to/some/file/being/written', 'w') as file_2:
        file_2.write(file_1.read())

    # 条件语句和字符串格式化不需要使用反斜杠
    if (width == 0 and height == 0 and
            color == 'red' and emphasis == 'strong' or
            highlight > 100):
        raise ValueError("sorry, you lose")
    if width == 0 and height == 0 and (color == 'red' or
                                       emphasis is None):
        raise ValueError("I don't think so -- values are %s, %s" %
                         (width, height))


Bonus: 一些常见错误纠正
-----------------------

#. 不要做不必要的模块导入

   **Yes**

   .. code:: python

    from ..utils.tools import time_now_as_long, decode_json

   *No*

   .. code:: python

    from ..utils import tools

   一般情况下，使用到什么函数或类，就应该明确地将其导入进来
   (*Explicit is better than implicit*)，除非有不得不整个导入模块的需求，
   此原则不可违背。

#. 字典格式问题

   **Yes**

   .. code:: python

    audit_option_default = {
        'insert_new': True,
        'insert_hot': True,
        'use_bao10jie': True,
        'use_filter': True
    }

   *No*

   .. code:: python

    audit_option_default = {
                    'insert_new':True,
                    'insert_hot':True,
                    'use_bao10jie':True,
                    'use_filter':True}

   使用正确的 **四空格** 缩进; 冒号后面要 **空一格**; 最后一个花括号 **另起一行**

#. 列表格式问题

   **逗号后面要空一格!**

#. 代码块间的空行问题

   全局的函数、类，调用语句之间要 **空2行** ，类方法之间 **空1行**

   函数或方法内语句之间可根据逻辑或可读性进行适当空行，但 **不能超过2行**

#. 配置编辑器检查行尾空格和空白行

   - Vim

     在 ``.vimrc`` 中加上::

        autocmd ColorScheme * highlight TrailWhitespace ctermbg=red guibg=red
        highlight TrailWhitespace ctermbg=red guibg=red
        match TrailWhitespace /\s\+$/

   - Eclipse

     `How to auto-remove trailing whitespace in Eclipse? <http://stackoverflow.com/q/1043433/596206>`_

     `How does one show trailing whitespace in eclipse? <http://stackoverflow.com/q/11596194/596206>`_


#. 给编辑器配置静态语法检查工具

   - Vim

     使用 `syntastic` 插件 + `flake8` 包

..

    注: 以上规范只说到了项目代码中涉及到的，其他一些 PEP8 中比较细节的规范，
    如类的继承、异常语句的使用大家可以去参考原文看一看。

    注: 本文档使用 rst - reStructuredText 标记语言撰写。rst 在 Python
    体系中占有很重要的地位，所有 Python 文档都是用 rst 撰写，Pocoo 小组开发的
    Sphinx 文档系统也是基于 rst，大家有兴趣也可以去了解下


开发工具
--------

virtualenv
~~~~~~~~~~

virtualenv 是一个用于创建和管理 Python 虚拟环境的工具。所谓的 Python 虚拟环境
即在同一个大 Python 环境下（同一个 Python 解释器下）共存的互相之间不受影响、
隔离开来的 shell 运行环境。 比如 A 环境安装 tornado==2.3，
B 环境安装 tornado==3.0，他们都基于同一个 Python 解释器，
但可以安装同一个包的不同版本而不发生冲突。virtualenv 在开发多个项目，
以及一个项目的多种环境的测试时非常有用，是 Python 开发者的必备工具。


nose
~~~~

nose 是方便编写和执行单元测试的工具。在项目文件夹中运行 ``nosetests`` ，
nose 就会自动检索与特定的命名规则匹配的文件以及其中的函数和类，
自动执行这些测试。使用 nose 写单元测试会变得很方便，不用非要写成 TestCase
的类的形式， 也不用在文件末尾写 ``if '__main__' == __name__:`` 的运行代码了。


References
----------

    - https://github.com/brantyoung/zh-google-styleguide/blob/master/google-python-styleguide/python_style_rules.rst#%E8%AE%BF%E9%97%AE%E6%8E%A7%E5%88%B6

    - http://google-styleguide.googlecode.com/svn/trunk/pyguide.html

    - http://www.python.org/dev/peps/pep-0008/

    - http://zh-google-styleguide.readthedocs.org/en/latest/google-python-styleguide/

    - http://cdnzz.github.io/python-style-guide/

    - http://blog.csdn.net/gzlaiyonghao/article/details/6601123

    - http://blog.csdn.net/gzlaiyonghao/article/details/2834883
