# Tests

## Automated Tests
In this directory we write our tests, especially those that should be run automatically so future commits don't break functionality.

### Pytest
For testing pytest will be run in this directory. Pytest searches through files `"*_test.py"` for functions named `'test_*'` that can be Grouped by a `'Test*'`class.
Here are two examples:
#### Function
```python
def reverse_text(text):
    return text[::-1]

def test_reverse_text():
    assert reverse_text('python') == 'nohtyp'

```

#### Class
```python
class TestGroup:
    def getNumber(self):
        return 2
    def test_numbers(self):
        assert self.getNumber()==3, "Wrong numbers"
```

#### See also
There are many more functionalities, such as fixtures, marking and parametrization
https://docs.pytest.de/en/stable/how-to/usage.html