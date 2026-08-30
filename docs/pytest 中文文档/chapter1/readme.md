1. 安装命令: `pip install pytest`
2. 查看版本: `pytest --version`
3. 命名规范:
   - 文件命名规范: `test_*.py`或`*_test.py`
   - 测试类命名规范: `Test*`
4. 其他约束:
   - 测试类中不能有`__init()__`方法
5. 执行:
   - `pytest`: 执行当前及其子目录中所有满足命名规范的文件
   - `pytest path`: 执行指定文件或目录
   - `pytest -q`: 输出精简版本的测试报告
   - `pytest -o`: 设置临时参数并执行
   - `pytest path::class`: 执行指定的测试类
   - `pytest path::class::method`: 执行指定的测试类方法
   - `pytest path::method`: 执行指定的方法
6. 查看所有可用的fixtures: `pytest --fixtures`
7. `tmp_path`是**pytest**内置的fixture之一，其作用是: 自动创建一个临时目录并在测试结束后清理

```python
# 可以通过如下代码查看tmp_path创建临时目录的保留策略和数量
# 可以在项目根目录下创建pytest.ini（已确认有效）或pyproject.toml进行更改
# 也可以通过pytest -o key=val指定值修改，优先级高于pytest.ini（已确认有效）

# 优先级：pytest -o > pytest.ini > pyproject.toml

# pytestconfig也是一个fixture，返回pytest的配置对象
def test_show_tmp_path_config(pytestconfig):
    # 获取保留的数量限制（默认 3）
    retention_count = pytestconfig.getini("tmp_path_retention_count")
    # 获取保留策略（默认 all: 全部保留; failed: 仅失败保留）
    retention_policy = pytestconfig.getini("tmp_path_retention_policy")

    print(f"\n[配置信息] 默认保存目录数量: {retention_count}")
    print(f"\n[配置信息] 默认目录保留策略: {retention_policy}")
```