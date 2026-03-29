"""Deprecation warning 체계 테스트."""

import warnings

import pytest

from dartlab.core.deprecation import DartlabDeprecationWarning, deprecated, warnDeprecated

pytestmark = pytest.mark.unit


class TestWarnDeprecated:
    def test_emitsWarning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnDeprecated("oldFunc", "0.9.0")
            assert len(w) == 1
            assert issubclass(w[0].category, DartlabDeprecationWarning)
            assert "0.9.0" in str(w[0].message)

    def test_includesAlternative(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnDeprecated("oldFunc", "0.9.0", alternative="newFunc()")
            assert "newFunc()" in str(w[0].message)


class TestDeprecatedDecorator:
    def test_decoratedFunctionStillWorks(self):
        @deprecated("0.9.0", alternative="newFunc()")
        def oldFunc(x):
            return x * 2

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = oldFunc(5)
            assert result == 10
            assert len(w) == 1
            assert issubclass(w[0].category, DartlabDeprecationWarning)

    def test_preservesFunctionMetadata(self):
        @deprecated("0.9.0")
        def myFunc():
            """원본 독스트링."""

        assert myFunc.__name__ == "myFunc"
        assert myFunc.__doc__ == "원본 독스트링."

    def test_isFutureWarningSubclass(self):
        """FutureWarning 하위라서 기본적으로 사용자에게 표시."""
        assert issubclass(DartlabDeprecationWarning, FutureWarning)
