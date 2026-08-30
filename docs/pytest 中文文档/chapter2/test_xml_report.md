# test_xml_report.py

> 源文件：`chapter2/test_xml_report.py`

```python
import pytest

def test_record_property1(record_property):
    record_property("test_id", 10010)
    assert True

def test_record_property2(record_testsuite_property):
    record_testsuite_property("test_id", 10011)

@pytest.fixture(scope="session")
def log_global_env_facts(record_testsuite_property):
    record_testsuite_property("EXECUTOR", "luizyao")
    record_testsuite_property("LOCATION", "NJ")

def test_record_property3(log_global_env_facts):
    assert True
```
