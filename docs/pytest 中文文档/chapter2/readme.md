1. 使用python解释器执行测试：`python -m pytest [...]`，与`pytest [...]`的效果几乎一致
2. pytest执行结束时返回的状态码
   - 状态码信息
      - 0:(OK) 所有收集到的测试用例执行通过
      - 1:(TESTS_FAILED) 有用例执行失败
      - 2:(INTERRUPTED) 用户打断测试执行
      - 3:(INTERNAL_ERROR) 测试执行过程中，发生内部错误
      - 4:(USAGE_ERROR) pytest命令使用错误
      - 5:(NO_TESTS_COLLECTED) 没有收集到测试用例
   - 状态码导入：`from pytest import ExitCode`
3. 查看帮助信息：`pytest -h`
4. 最多允许失败的测试用例数，若不设置则遇到失败不退出
    - 遇到失败立即退出：`pytest -x`
    - 主动设置最大失败用例数：`pytest --maxfail=x`
5. 执行文件名、类名或者函数名中包含特定关键字的测试用例
    - 执行当前目录下名字包含`_class`但不包含`two`的测试用例：`pytest -k "_class and not two"`
        - 或：`or`
        - `-k`选项中不能出现python关键字，如`class`、`def`等
6. `pytest -s`表示不捕获输出，即无论用例执行成功与失败，都将`print()`输出在控制台上
7. 查看指定路径下的用例：`pytest --collect-only path`，若不指定`path`，则查看当前路径及其子目录
    - 输出结果类似xml
      - \<Dir chapter2\>: 表示目录结构
      - \<Module test_nodeid.py\>: 表示模块，即py文件
      - \<Class TestNodeId\>: 表示测试类
      - \<Function test_two\[1-1\]\>: 表示具体用例
8. 在引入`parametrize`注释下，执行某条测试用例：`pytest -q -s "pytest-chinese-doc/chapter2/test_nodeid.py::TestNodeId::test_two[1-1]"`
   - `[1-1]`表示`x`、`y`的入参，以`-`分隔，不同的入参均表示一个测试用例
   - MAC终端执行时需要注意字符转义，否则可能出现如下命令解析报错：`zsh: no matches found: xxx`
9. 执行包含特定标记的用例：`pytest -m mark`
    - 标记：`@pytest.mark.mark_name`
    - pytest内置了部分标记，也支持用户自定义
        - 内置标记即名称固定，具有特定行为
        - 自定义标记，强烈建议在`pytest.ini`中注册
          - 自定义标记不注册也可使用，但是会出现如下告警：`PytestUnknownMarkWarning: Unknown pytest.mark.mark_name`
    - `pytest --markers`可以查询已经注册的标记，包括自定义的标记
10. `pytest --pyargs pkg.testing`: 执行python包`pkg`中子包`testing`下的pytest要求的测试用例
    - 要求包`pkg.testing`能够被import导入
11. pytest中回溯信息的输出模式
    - 仅在失败用例中生效
      - `-l` or `--showlocals`: 输出本地变量
      - `--full-trace`: 输出最完整的调用栈信息
      - `--tb=`:
        - `auto`: 默认模式，失败时按照`long`输出
        - `long`: 尽可能详细的信息
        - `short`: 错误所在行及简短堆栈
        - `line`: 每个失败只显示一行
        - `native`: python标准格式的回溯信息
        - `no`: 只统计，不显示回溯信息
12. `pytest -r`后紧跟下列参数能够过滤并显示用例的执行结果
    - 参数列表
      - `f`: 失败的
      - `E`: 报错的
      - `s`: 跳过执行的
      - `x`: 跳过执行的，并标记为xfailed的
      - `X`: 跳过执行的，并标记为xpassed的
      - `p`: 测试通过的
      - `P`: 测试通过的，并且包含输出信息的，即用例中存在`print`等关键字的
      - `a`: 除了测试通过的，即不包含`p`和`P`的
      - `A`: 所有的
    - 代码示例: `pytest -rA`
    - 参数可以叠加使用，如期望过滤出失败和未执行的：`pytest -rfs`
13. `pytest --pdb`允许在用例执行失败或是`ctrl+c`退出时进入调试模式
    - 可以在调试模式中访问测试用例变量
    - 可以导入`sys`模块，查看用例的失败信息，常见的失败信息有：
      - `sys.last_value`: 最近一次**未捕获异常**的实例
      - `sys.last_type`: 最近一次**未捕获异常**的类型
      - `sys.last_traceback`: 最近一次**未捕获异常**的调用栈
      - 若`ctrl+c`退出，则不存在未捕获异常，因此无法访问`sys.last_*`信息
14. `pytest --trace`能使**每个**测试用例运行即进入调试模式
15. 测试用例中添加`import pdb; pdb.set_trace()`可以在运行到该测试用例初进入调试模式，且不会影响其他测试用例，即其他测试用例不会进入调测模式
16. pytest可以结合`breakpoint()`方法一起使用，同`pdb.set_trace()`一样，仅在运行时生效
    - 结合`breakpoint()`默认使用系统内置的pdb，可以切换成更好的调试器，如`ipdb`、`pudb`等
        - 设置方法
          - 环境变量：`export PYTHONBREAKPOINT=ipdb.set_trace`
          - 代码设置：`os.environ["PYTHONBREAKPOINT"] = "ipdb.set_trace"`
    - CI运行时需要避免因`breakpoint()`未删除而卡住，因此建议临时禁用：`PYTHONBREAKPOINT=0 pytest test.py`
17. `pytest --pdbcls=模块路径:类名`可以使用其他或自定义的pdb，如`pytest --pdbcls=IPython.terminal.debugger:Pdb --pdb`或`pytest --pdbcls=pudb.debugger:Debugger`
    - 仅对pytest生效
      - 结合`breakpoint()`使用时，需要设置`PYTHONBREAKPOINT`环境变量，如`PYTHONBREAKPOINT=ipdb.set_trace pytest --pdbcls=IPython.terminal.debugger:Pdb`
    - `PYTHONBREAKPOINT=0 pytest --pdbcls=pdb:Pdb -p no:debugging`表示同时禁用`breakpoint()`和pytest的调试功能
18. `pytest --duration=10`可以显示执行最慢的10歌用例
    - 执行时间小于0.005s的用例不会显示，可以通过`-vv`选项查看
19. 在测试用例发生段错误或超时的情况下，`faulthandler`模块可以转储python的回溯信息
    - 默认使能，可以通过`-p no:faulthandler`关闭
    - 可以在`pytest.ini`中添加`faulthandler_timeout=x`配置项，使测试用例完成时间超过x秒时，转储所有线程的python回溯信息
20. `pytest --junitxml=/path/to/test_xxx.xml`能够在指定路径下生成xml格式的测试报告
    - 可以在`pytest.ini`中添加`junit_suite_name=x`配置项，使xml测试报告中`<testsuite name=x>`
    - 可以在`pytest.ini`中添加`junit_duration_report=call`配置项，使xml测试报告中`<testsuite time=x>`只记录测试用例执行时间，过滤`setup`和`teardown`阶段中的耗时（默认包含）
21. 当前pytest生成测试报告时使用的`JUnit XML`格式版本默认为`xunit2`，该版本约束：**<properties>只能放在`<testsuite>`下，不能放在`<testcase>`下**
    - 使用`record_property`fixture添加额外子节点信息时，能够添加成功，但是会产生告警，如果一定要使用此方案则采用屏蔽告警的策略
    - 或者使用`record_testsuite_property`fixture将额外的子节点信息放在`<testsuite>`以兼容`xunit2`约束
22. 部分fixture，如`record_xml_attribute`等由于`JUnit XML`默认格式版本变更为`xunit2`存在兼容问题或已不支持，学习优先级降低
23. `pytest --pastebin=`可以为用例创建一个URL，便于他人查看（需要安装插件和证书）
    - `--pastebin=failed`: 为每一个失败用例创建一个URL 
    - `--pastebin=all`: 为所有的测试用例创建一个URL
24. pytest的插件操作
    - `pytest -p plugin_name`: 引入插件
    - `pytest -p no:plugin_name`: 禁用插件
25. python代码中支持直接调用pytest: `pytest.main(["e1", "e2", ...])`
    - 不建议在一个程序中多次调用`pytest.main()`，因为全局状态（模块、插件、配置、缓存等）不会清理，非要使用可以采用多进程方式进行隔离