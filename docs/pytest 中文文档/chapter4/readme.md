1. `pytest --fixtures [testpath]`能够显示`testpath`中所有可用的`fixture`
     - 对于以`_`开头的`fixture`需要添加`-v`选项
2. `fixture`的查找顺序：测试类、测试模块、`conftest.py`、内置和第三方插件，通过`conftest.py`可以实现自定义`fixture`共享
3. 共享测试数据的实现方式
    - 把需要共享的数据加载至`fixture`中，测试中再使用这些`fixture`
      - 把需要共享的数据放入`tests`路径下，某些第三方插件，如`pytest-datadir`和`pytest-datafiles`，能够帮助管理这方面的测试
4. `fixture`支持通过`scope`选项设置作用域`function(default)`、`class`、`module`、`package`和`session`
5. 注意测试用例的执行路径，相同的配置，在不同的路径下执行可能会有不一样的结果
6. `fixture`的实例化顺序
   - 高级别作用域(例如: `session`)先于低级别作用域(例如: `function`)实例化
   - 相同级别作用域，实例化顺序遵循**在测试用例中被声明的顺序(即形参的顺序)**，或者`fixture`之间的相互调用关系
   - 使能`autouse`的`fixture`，先于其同级别的其他`fixture`实例化
   - 除了`autouse`声明的`fixture`需要测试用例显示声明(形参)，不声明则不会被实例化
   - 多个相同作用域的`autouse fixture`实例化顺序遵循`fixture`函数名排序
7. `fixture`支持三种清理操作
   - 将`return`关键字替换成`yield`，`yield`之后可以添加清理代码
      - 支持`with`写法的对象可以执行隐式清理操作
   - `fixture`能够接收一个`request`参数，表示**测试请求的上下文**，可以使用`request.addfinalizer`为`fixture`添加清理操作