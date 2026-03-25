from pathlib import Path

from venvops import Venv, Package


def test_end_to_end(tmp_path):
    # ------------------------------------------------------------
    # 0. Assert initial state: venv does not exist
    # ------------------------------------------------------------
    assert Venv.find_in(tmp_path) is None

    # ------------------------------------------------------------
    # 1. Create a venv
    # ------------------------------------------------------------
    v = Venv.create_in(tmp_path)
    assert v.path.exists()
    assert (v.path / 'pyvenv.cfg').exists()

    # ------------------------------------------------------------
    # 2. find_in should discover it
    # ------------------------------------------------------------
    found = Venv.find_in(tmp_path)
    assert found is not None
    assert found.path == v.path

    # ------------------------------------------------------------
    # 3. run_python should execute inside the venv
    # ------------------------------------------------------------
    out = v.run_python('-c', 'import sys; print(sys.prefix)')
    assert v.path.as_posix() in Path(out).as_posix()

    # ------------------------------------------------------------
    # 4. run_pip should work
    # ------------------------------------------------------------
    pip_version = v.run_pip('--version')
    assert 'pip' in pip_version.lower()

    # ------------------------------------------------------------
    # 5. install a real package
    # ------------------------------------------------------------
    assert 'wheel' not in v.installed()
    v.install('wheel')
    assert 'wheel' in v.installed()

    # ------------------------------------------------------------
    # 6. uninstall the package
    # ------------------------------------------------------------
    v.uninstall('wheel')
    assert 'wheel' not in v.installed()

    # ------------------------------------------------------------
    # 7. install from a requirements file
    # ------------------------------------------------------------
    req = tmp_path / 'requirements.txt'
    req.write_text('wheel==0.43.0\n')

    v.install_file(req)
    assert 'wheel' in v.installed()

    # ------------------------------------------------------------
    # 8. uninstall from a requirements file
    # ------------------------------------------------------------
    v.uninstall_file(req)
    assert 'wheel' not in v.installed()

    # ------------------------------------------------------------
    # 9. installed() returns parsed Package objects
    # ------------------------------------------------------------
    pkgs = v.installed()
    assert all(isinstance(p, Package) for p in pkgs)
