import pytest

from nocturne import __version__, cli, config


def test_parser_defaults():
    args = cli.build_parser().parse_args([])
    assert args.host == "127.0.0.1"
    assert args.port == config.DEFAULT_PORT
    assert args.data_dir is None and not args.no_browser


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.build_parser().parse_args(["--version"])
    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_probe_finds_nothing_on_a_closed_port():
    assert cli.probe("127.0.0.1", 1, timeout=0.2) is False


def test_probe_recognises_a_running_codex(server):
    host, port = server.server_address[:2]
    assert cli.probe(host, port) is True


def test_main_summons_an_open_codex_instead_of_starting_another(server, capsys):
    host, port = server.server_address[:2]
    assert cli.main(["--host", host, "--port", str(port), "--no-browser"]) == 0
    assert "already open" in capsys.readouterr().out


def test_data_dir_honours_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("NOCTURNE_HOME", str(tmp_path / "grimoire"))
    assert config.default_data_dir() == tmp_path / "grimoire"


def test_data_dir_defaults_per_platform(monkeypatch, tmp_path):
    monkeypatch.delenv("NOCTURNE_HOME", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(config.sys, "platform", "linux")
    assert config.default_data_dir() == tmp_path / "NocturneCodex"
    monkeypatch.setattr(config.sys, "platform", "darwin")
    assert config.default_data_dir().parts[-2:] == ("Application Support", "NocturneCodex")
    monkeypatch.setattr(config.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    assert config.default_data_dir() == tmp_path / "Roaming" / "NocturneCodex"


def test_make_server_skips_taken_ports(codex):
    from nocturne.server import make_server

    first = make_server(codex, "127.0.0.1", 0)
    taken = first.server_address[1]
    second = make_server(codex, "127.0.0.1", taken, attempts=5)
    try:
        assert second.server_address[1] != taken
        assert second.url.startswith("http://127.0.0.1:")
    finally:
        first.server_close()
        second.server_close()
