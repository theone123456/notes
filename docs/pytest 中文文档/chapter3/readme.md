1. `assert`表达式后可以指定一条说明信息，用例执行失败时会输出
2. `with python.raise(Exception) as excinfo`中`pytest.raise()`是一个上下文管理器，可以用于编写触发期望异常的断言
    - 由`with`进行断言
    - `excinfo`是`ExceptionInfo`的一个实例，其中封装了异常信息，包括`.type`、`.value`、`.traceback`等
    - 在`pytest.raise()`作用域中，`raise`代码，即抛出异常的代码必须是最后一行，否则后续代码不会执行
    - 支持传入`match`关键字参数测试异常字符串`str(excinfo.value)`表示是否匹配给定的正则表达式
    - 支持匹配多个异常，由元组的形式传入
    - 支持传入一个可调用对象，检查该对象执行后是否会触发指定的异常，此时不支持传入`match`，否则会出现`TypeErro`异常
3. `pytest.mark.xfail(raises=Error)`支持传入一个异常，若触发异常则用例执行结果标记为`xfailed`，用例执行成功则标记为`xpassed`
   - `pytest.mark.xfail(raises=Error)`更适合用于记录一些未修复的bug，并不常用于测试异常
4. 类方法的说明
   - `def __eq__()`的作用是当使用相等运算符`==`比较时被调用，通常返回True或False
   - `def __repr__()`的作用时当使用`repr(obj)`或在交互式终端直接输出对象名时被调用，通常返回一个能表示该对象的字符串，偏向于开发调试使用
   - `def __str__()`若未被定义，会回退使用`def __repr__()`，通常返回一个简易字符串，偏向于用户使用
5. 类对象的比较有两种方式实现
    - 重写`def __repr__()`，基于重写返回值进行比较
    - `conftest.py`中定义钩子函数`def pytest_assertrepr_compare(op, left, right)`
6. python在导入模块时，默认会将源码编译成字节码并保存为`.pyc`文件存放在`__pycache__`路径下，以加速后续导入
    - `conftest.py`中可添加`import sys; sys.dont_write_bytecode = True;`禁止python生成缓存字节码文件
      - 测试代码变动频繁，缓存无意义，反而可能导致旧字节码文件被误用
      - 禁止缓存后不影响使用
7. 测试用例执行时去断言自省: `pytest --assert=plain`
   - 不建议使用，使用后几乎看不出任何有用的调试信息