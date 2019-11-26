from entangled.doctest import (Suite,Test, run_suite, read_config)

def test_suite():
    config = read_config()
    suite = Suite([Test("6*7", "42")], "python")
    result = run_suite(config, suite)
    assert len(result) == 1
    assert result[0].expected == result[0].repl_output

