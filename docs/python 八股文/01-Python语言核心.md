# Python 语言核心（面试出现率最高的部分）

> 使用方式：每节先看知识点，再把"陷阱代码"亲自跑一遍；末尾的「面试问法」要能脱口而出。

## 一、数据类型与内置结构

### 1. 可变与不可变（必考）

| 不可变 | 可变 |
|---|---|
| int / float / bool / str / tuple / frozenset / bytes | list / dict / set / bytearray |

**核心推论**：
- 不可变对象的"修改"实际是创建新对象并重新绑定
- 可变对象作为函数参数时，函数内的原地修改会影响外部

```python
def demo(lst, num, s):
    lst.append(1)      # 原地修改 -> 外部可见
    num += 1           # 不可变，重新绑定 -> 外部不可见
    s += '!'           # str 不可变，等同创建新对象 -> 外部不可见

lst, num, s = [], 10, 'hi'
demo(lst, num, s)
print(lst, num, s)     # [1] 10 hi
```

**面试问法**：Python 参数是值传递还是引用传递？
> 答：传对象引用（pass by object reference / shared reference）。函数拿到的是对象的引用副本：对可变对象原地修改影响外部；对不可变对象重新赋值只改变本地绑定，不影响外部。

### 2. 可变默认参数陷阱（必考）

```python
def add(item, items=[]):       # 默认值在【定义时】求值一次，之后所有调用共享同一个列表
    items.append(item)
    return items

add(1)      # [1]
add(2)      # [1, 2]  <-- 不是 [2]！
```

**正确写法**：

```python
def add(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

### 3. list vs tuple

| 维度 | list | tuple |
|---|---|---|
| 可变性 | 可变 | 不可变 |
| 作为字典键 | 不可 | 可（可哈希） |
| 内存/性能 | 较大 | 较小较快 |
| 适用 | 会变的数据 | 固定结构、返回多值 |

### 4. dict（哈希表）

- 键必须**可哈希**（不可变类型）；`hash()` 支持
- 查找/插入/删除平均 O(1)
- **3.7+ 保证插入有序**（3.6 是实现细节）
- 常用方法：`get(k, default)`（避免 KeyError）、`setdefault`、`update`、`pop`、`items/keys/values`
- 遍历时不能增删键（RuntimeError），需要先收集 `list(d.keys())`

### 5. set

- 自动去重、元素可哈希、无序
- 集合运算：`&` 交、`|` 并、`-` 差、`^` 对称差
- `frozenset`：不可变集合，可作为字典键
- 经典用途：列表去重 `list(set(lst))`（丢失顺序）、判重 O(1)

### 6. 深浅拷贝（必考）

```python
import copy

a = [[1, 2], [3, 4]]
b = copy.copy(a)        # 浅拷贝：只复制最外层，内层对象仍共享
c = copy.deepcopy(a)    # 深拷贝：递归复制所有层

b[0].append(99)
print(a)                # [[1, 2, 99], [3, 4]]  <-- a 被影响了
print(c)                # [[1, 2], [3, 4]]      <-- 深拷贝不受影响
```

**注意**：切片 `a[:]`、`list(a)`、`dict(d)`、`a.copy()` 都是**浅拷贝**。

**面试问法**：什么场景必须深拷贝？
> 答：嵌套结构（二维列表、字典套字典）且要对副本的内部元素做修改时；单层结构浅拷贝就够。

### 7. is vs ==

- `==` 比较**值**（调用 `__eq__`）；`is` 比较**身份**（是否同一对象，即 `id()` 相同）
- `is None` / `is not None` 是规范写法

```python
a = 256; b = 256
print(a is b)    # True  小整数缓存 [-5, 256]
a = 257; b = 257
print(a is b)    # 交互式解释器中通常 False（不同对象）
s1 = 'hello'; s2 = 'hello'
print(s1 is s2)  # True  字符串驻留（编译期常量合并）
```

### 8. 字符串

- 不可变；大量拼接用 `''.join(parts)`（`+` 循环拼接 O(n²)）
- 常用方法：`split / strip / replace / startswith / endswith / join / find / format`
- 格式化优先 f-string：`f'{name} 今年 {age} 岁'`、`f'{x:.2f}'`
- 编码：`'中'.encode('utf-8')` -> `b'\xe4\xb8\xad'`；`b.decode('utf-8')`
- 经典坑：utf-8 中文 3 字节，gbk 2 字节 -> 乱码问题先查编码

## 二、函数

### 1. 参数全解

```python
def func(a, b=1, /, c=2, *args, d, **kwargs):
    #  a      仅位置参数（3.8+，/ 之前）
    #  b=1    带默认值
    #  c=2    位置或关键字
    #  *args  可变位置参数（元组）
    #  d      仅关键字参数（* 之后的具名参数）
    #  **kwargs 可变关键字参数（字典）
    pass
```

- 传参顺序：位置参数 -> `*args` -> 关键字参数 -> `**kwargs`
- 解包调用：`func(*list, **dict)`

### 2. lambda 与高阶函数

```python
sorted(users, key=lambda u: u['age'], reverse=True)
list(map(str.upper, ['a', 'b']))
list(filter(lambda x: x > 0, [-1, 2, 3]))
```

测开场景：按响应时间排序接口、过滤失败用例。

### 3. 闭包（必考）

**定义**：内层函数引用了外层函数作用域中的变量，并且内层函数被返回/传出，这些变量被"封闭"保留。

```python
def make_multiplier(n):
    def multiply(x):
        return x * n        # 引用外层变量 n
    return multiply

double = make_multiplier(2)
double(5)   # 10
```

**经典陷阱——延迟绑定**（面试原题）：

```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])     # [2, 2, 2]  循环结束后才调用，i 已是 2

funcs = [lambda i=i: i for i in range(3)]   # 默认参数在定义时求值
print([f() for f in funcs])     # [0, 1, 2]
```

### 4. 装饰器（必考中的必考）

**原理**：`@deco` 是语法糖，等价于 `func = deco(func)`。装饰器接收函数返回函数。

```python
import functools
import time

def timer(func):
    @functools.wraps(func)                 # 保留原函数 __name__/__doc__
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f'{func.__name__} 耗时 {time.time() - start:.3f}s')
        return result
    return wrapper

@timer
def slow_add(a, b):
    time.sleep(0.5)
    return a + b
```

**带参数的装饰器（三层）**：

```python
def retry(times=3, delay=1):               # 第一层：接收装饰器参数
    def decorator(func):                   # 第二层：接收被装饰函数
        @functools.wraps(func)
        def wrapper(*args, **kwargs):      # 第三层：实际执行逻辑
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == times:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(times=3, delay=2)
def flaky_api_call(): ...
```

**面试问法**：
- 装饰器原理？`@` 等价于什么？
- `functools.wraps` 不加会怎样？（原函数的 `__name__`、`__doc__` 被 wrapper 覆盖，影响调试与反射）
- 带参装饰器为什么要三层？
- 测开里装饰器用来干什么？（重试、计时、缓存、登录态校验、失败截图）

### 5. 迭代器与生成器（必考）

**两个协议**：
- 可迭代对象：实现 `__iter__`（list/str/dict/file...）
- 迭代器：实现 `__iter__` + `__next__`，用 `iter()` 从可迭代对象获取，`next()` 取下一个，耗尽抛 `StopIteration`

**生成器是创建迭代器的便捷方式**：

```python
def read_large_file(path):
    with open(path, encoding='utf-8') as f:
        for line in f:          # 惰性逐行，不会把整个文件读进内存
            yield line

g = read_large_file('big.log')
next(g)                          # 执行到 yield 暂停并返回值
```

- `yield`：暂停函数并保存现场，下次从暂停处继续；函数一旦含 yield 就是生成器函数，调用不执行只返回生成器
- 生成器表达式 `(x*x for x in range(10))` 惰性求值；列表推导式 `[...]` 立即求值
- `range` 不是生成器，是惰性 range 对象（可重复迭代，生成器只能消费一次）
- `send()` 可向生成器内传值、`yield from` 委托子生成器（了解）

**面试问法**：生成器和列表的区别？什么场景用？
> 答：惰性求值、边生成边消费、内存 O(1)；场景：读大日志文件、无限序列、流水线处理。生成器只能遍历一次。

### 6. 推导式

```python
squares = [x*x for x in range(10) if x % 2 == 0]
mapping = {k: v for k, v in pairs}
unique = {x for x in items}
```

嵌套可读性差，超过两层建议展开为普通循环。

## 三、面向对象

### 1. 属性查找顺序

实例 `__dict__` -> 类属性 -> 父类（沿 MRO）。类属性被所有实例共享，实例属性互不影响。

### 2. __new__ vs __init__（必考）

- `__new__`：**创建**实例（静态方法，返回实例），先执行
- `__init__`：**初始化**实例（不返回值），后执行

```python
class Singleton:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

a, b = Singleton(), Singleton()
print(a is b)     # True
```

### 3. 三种方法（必考）

| 方法 | 装饰器 | 首参 | 能访问实例属性 | 能访问类属性 | 场景 |
|---|---|---|---|---|---|
| 实例方法 | 无 | self | 能 | 能（self.x / cls.x） | 绝大多数业务逻辑 |
| 类方法 | `@classmethod` | cls | 不能 | 能 | 工厂方法（备选构造器） |
| 静态方法 | `@staticmethod` | 无 | 不能 | 不能（可硬引用） | 工具函数，逻辑上归属该类 |

### 4. 继承、MRO 与 super（必考）

- MRO：Method Resolution Order，C3 线性化算法，`Cls.__mro__` 可查
- **super() 不是"调用父类"，而是"调用 MRO 中的下一个类"**

```python
class A:
    def who(self): print('A')
class B(A):
    def who(self): print('B'); super().who()
class C(A):
    def who(self): print('C'); super().who()
class D(B, C):
    def who(self): print('D'); super().who()

D().who()        # D B C A（菱形继承，A 只执行一次，由 MRO 保证）
```

### 5. 封装（伪私有）

- `_name`：约定私有（外界仍可访问）
- `__name`：触发名称改写 -> `_ClassName__name`，用于避免子类覆盖
- Python 没有真正的 private，一切靠约定

### 6. 多态与鸭子类型（必考）

> "走起来像鸭子、叫起来像鸭子，那它就是鸭子。"

Python 的多态不依赖继承体系：只要对象实现了同名方法，就可以在运行时替换，无需统一父类。

```python
class JsonReporter:  def report(self): return 'json'
class HtmlReporter:  def report(self): return 'html'

def run(reporter):            # 不检查类型，只依赖 report 方法存在
    print(reporter.report())
```

### 7. 魔法方法速查（高频）

| 方法 | 触发时机 | 备注 |
|---|---|---|
| `__init__` / `__new__` | 构造 | new 创建、init 初始化 |
| `__str__` | `print()` / `str()` | 面向用户 |
| `__repr__` | 交互式回显 / `repr()` | 面向开发者，没定义 __str__ 时兜底 |
| `__len__` | `len(obj)` | 配合 `if obj:` 真值判断 |
| `__eq__` / `__hash__` | `==` / `hash()` | 同时定义；可变对象不应可哈希 |
| `__lt__` 等 | 比较运算 | 配合 sorted |
| `__call__` | `obj()` | 让实例像函数一样调用 |
| `__getitem__` / `__setitem__` | `obj[k]` | 支持下标与切片 |
| `__getattr__` | **常规查找失败后**触发 | 常用于代理/链式调用 |
| `__getattribute__` | **每次属性访问都触发** | 小心递归，需 super() |
| `__enter__` / `__exit__` | `with` 语句 | 上下文管理器，exit 接收异常信息 |
| `__iter__` / `__next__` | for 循环 | 迭代器协议 |
| `__del__` | 引用归零时 | 不保证及时执行，别放关键清理逻辑 |

### 8. property（受控属性）

```python
class Account:
    def __init__(self):
        self._balance = 0

    @property
    def balance(self):              # 读：acc.balance
        return self._balance

    @balance.setter
    def balance(self, value):       # 写：acc.balance = v
        if value < 0:
            raise ValueError('余额不能为负')
        self._balance = value
```

### 9. 其他必知

- `__slots__ = ('a', 'b')`：限定实例属性、省内存（失去动态添加属性与 `__dict__`）
- 抽象基类：`class Base(abc.ABC)` + `@abstractmethod`，子类必须实现才能实例化
- `@dataclass`：自动生成 `__init__/__repr__/__eq__`，适合配置与数据载体
- 元类一句话：类的类是 type，metaclass 控制类的创建过程（ORM、单例的实现手段之一），面试能说出这句话即可

## 四、作用域 LEGB

查找顺序：**L**ocal -> **E**nclosing（闭包外层）-> **G**lobal（模块）-> **B**uilt-in

```python
x = 'global'

def outer():
    x = 'enclosing'
    def inner():
        x = 'local'
        print(x)          # local
    inner()

inner 中用 global x 可改全局；用 nonlocal x 可改闭包层变量
```

**类作用域陷阱**：类体内不是闭包，类体中的推导式/生成器表达式访问不到类属性：

```python
class C:
    n = 10
    a = [n for _ in range(3)]     # NameError！推导式有独立作用域，看不到类命名空间
```

## 五、本模块高频面试问法清单

1. Python 的可变/不可变类型有哪些？函数传参时表现有什么不同？
2. 可变默认参数的坑？怎么修？
3. 深拷贝和浅拷贝的区别？切片是哪种？
4. is 和 == 的区别？小整数缓存是什么？
5. 闭包是什么？延迟绑定问题怎么解决？
6. 装饰器的原理？带参装饰器为什么要三层？wraps 的作用？
7. 生成器和列表的区别？生成器能遍历几次？
8. __new__ 和 __init__ 的区别？
9. 类方法/静态方法/实例方法的区别？
10. super() 的真正含义？菱形继承下 A 为什么只执行一次？
11. Python 的多态怎么理解（鸭子类型）？
12. __getattr__ 和 __getattribute__ 的区别？
13. LEGB 是什么？global 和 nonlocal 的区别？
