from __future__ import annotations

import time

import pytest

from spotify_tools import perf


def test_timing_result_init():
    result = perf.TimingResult("test_operation", 0.123)

    assert result.name == "test_operation"
    assert result.elapsed == 0.123
    assert result.ms == 123.0


def test_timing_result_str():
    result = perf.TimingResult("test_operation", 0.123456)

    assert str(result) == "test_operation: 123.46ms"


def test_timing_result_ms_conversion():
    result = perf.TimingResult("fast_op", 0.001)

    assert result.ms == 1.0


def test_measure_time_context_manager():
    with perf.measure_time("test_operation"):
        time.sleep(0.01)


def test_measure_time_default_name():
    with perf.measure_time():
        pass


def test_measure_time_with_exception():
    with pytest.raises(ValueError):
        with perf.measure_time("failing_operation"):
            raise ValueError("Test error")


def test_silent_timer_no_output(capsys):
    with perf.silent_timer("silent_operation"):
        time.sleep(0.01)

    captured = capsys.readouterr()
    assert captured.out == ""


def test_silent_timer_with_exception():
    with pytest.raises(ValueError):
        with perf.silent_timer("failing_silent"):
            raise ValueError("Test error")


def test_timed_decorator(capsys):
    @perf.timed
    def sample_function(x):
        time.sleep(0.01)
        return x * 2

    result = sample_function(5)

    assert result == 10

    captured = capsys.readouterr()
    assert "TIMING: sample_function:" in captured.out
    assert "ms" in captured.out


def test_timed_decorator_with_exception(capsys):
    @perf.timed
    def failing_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        failing_function()

    captured = capsys.readouterr()
    assert "TIMING: failing_function:" in captured.out


def test_timed_decorator_preserves_function_name():
    @perf.timed
    def my_function():
        pass

    assert my_function.__name__ == "my_function"


def test_timed_decorator_with_args_and_kwargs(capsys):
    @perf.timed
    def complex_function(a, b, c=3, d=4):
        return a + b + c + d

    result = complex_function(1, 2, c=5, d=6)

    assert result == 14

    captured = capsys.readouterr()
    assert "TIMING: complex_function:" in captured.out


def test_multiple_timing_results():
    results = [
        perf.TimingResult("op1", 0.1),
        perf.TimingResult("op2", 0.05),
        perf.TimingResult("op3", 0.025),
    ]

    assert results[0].ms == 100.0
    assert results[1].ms == 50.0
    assert results[2].ms == 25.0


def test_measure_time_accuracy():
    with perf.measure_time("sleep_test"):
        time.sleep(0.05)
