from unittest.mock import patch
import pytest

from venvops import *


@pytest.fixture
def venv(tmp_path):
    return Venv.create_in(tmp_path)


def test_find_in(temp_dir):
    venv_path = temp_dir / '.venv'
    venv_path.mkdir()
    (venv_path / 'pyvenv.cfg').write_text('home = /usr/bin\n')

    venv_obj = Venv.find_in(temp_dir)
    assert venv_obj is not None
    assert venv_obj.path == venv_path


def test_find_in__venv(temp_dir):
    venv_path = temp_dir / 'venv'
    venv_path.mkdir()
    (venv_path / 'pyvenv.cfg').write_text('home = C:\\Python\\')

    venv_obj = Venv.find_in(temp_dir)
    assert venv_obj is not None
    assert venv_obj.path == venv_path


def test_find_in_not_found(temp_dir):
    assert Venv.find_in(temp_dir) is None


def test_find_in__no_pyvenv_cfg(temp_dir):
    (temp_dir / '.venv').mkdir()
    assert Venv.find_in(temp_dir) is None


@patch('sys.platform', 'win32')
def test_scripts_dir__windows(venv):
    assert venv.scripts_dir == venv.path / 'Scripts'


@patch('sys.platform', 'linux')
def test_scripts_dir__linux(venv):
    assert venv.scripts_dir == venv.path / 'bin'


def test_run():
    result = Venv.run('python', '--version', check=True)
    assert result.returncode == 0
    assert isinstance(result, subprocess.CompletedProcess)


def test_run_for_output():
    output = Venv.run_for_output('python', '--version')
    assert 'Python' in output
    assert isinstance(output, str)


def test_run_for_output__failed():
    with pytest.raises(CommandError):
        Venv.run_for_output('python', '-c', 'import sys; sys.exit(1)')


def test_run_for_output__no_check():
    output = Venv.run_for_output('python', '-c', 'import sys; sys.exit(1)', check=False)
    assert isinstance(output, str)


def test_run_python(venv):
    result = venv.run_python('--version')
    assert isinstance(result, str)
    assert 'Python' in result


def test_run_pip(venv):
    result = venv.run_pip('--version')
    assert isinstance(result, str)
    assert 'pip' in result.lower()


def test_install(venv):
    venv.install('wheel')
    assert 'wheel' in venv.installed()


def test_install__specific_version(venv):
    venv.install('wheel==0.38.4')
    wheel = venv.installed().get('wheel')
    assert isinstance(wheel, PinnedPackage)
    assert wheel.version == '0.38.4'


def test_install__invalid_package(venv):
    with pytest.raises(InvalidPackageError):
        venv.install('invalid-package')


def test_install__invalid_version(venv):
    with pytest.raises(InvalidVersionError):
        venv.install('wheel==123.456.789')


def test_install__malformed_requirement(venv):
    with pytest.raises(MalformedRequirementError):
        venv.install('wheel==')


def test_uninstall(venv):
    venv.install('wheel')
    assert 'wheel' in venv.installed()

    venv.uninstall('wheel')
    assert 'wheel' not in venv.installed()


def test_install_file(venv, temp_dir):
    req_file = temp_dir / 'requirements.txt'
    req_file.write_text('wheel==0.43.0\n')

    venv.install_file(req_file)
    assert 'wheel' in venv.installed()


def test_uninstall_file(venv, temp_dir):
    venv.install('wheel')
    assert 'wheel' in venv.installed()

    req_file = temp_dir / 'requirements.txt'
    req_file.write_text('wheel\n')

    venv.uninstall_file(req_file)
    assert 'wheel' not in venv.installed()


def test_installed(venv):
    venv.install('wheel')

    packages = venv.installed()
    assert isinstance(packages, set)
    assert len(packages) > 0
    assert 'wheel' in packages
    assert all(isinstance(pkg, Package) for pkg in packages)


def test_installed__empty(venv):
    packages = venv.installed()
    assert isinstance(packages, set)
    assert all(isinstance(pkg, Package) for pkg in packages)


def test_installed__multiple_packages(venv):
    venv.install('wheel', 'setuptools')

    packages = venv.installed()
    assert 'wheel' in packages
    assert 'setuptools' in packages
    assert all(isinstance(pkg, Package) for pkg in packages)


def test_context_manager(tmp_path):
    venv_path = tmp_path / 'auto_venv'
    assert not venv_path.exists()

    with Venv(venv_path) as venv:
        assert venv.path == venv_path
        assert venv_path.exists()
        assert 'Python' in venv.run_python('--version')
        venv.install('wheel')
        assert 'wheel' in venv.installed()

    assert not venv_path.exists()


def test_context_manager__safety_check(tmp_path):
    existing_path = tmp_path / 'existing'
    existing_path.mkdir()
    with pytest.raises(ValueError):
        with Venv(existing_path) as venv:
            pass


def test_context_manager__exception_cleanup(tmp_path):
    venv_path = tmp_path / 'exception_venv'

    assert not venv_path.exists()

    try:
        with Venv(venv_path) as venv:
            assert venv.path.exists()
            raise RuntimeError("Test exception")
    except RuntimeError:
        pass

    assert not venv_path.exists()
