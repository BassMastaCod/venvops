from pathlib import Path

from venvops import Package, PinnedPackage, EditablePackage, UrlPackage, VcsPackage

import pytest


@pytest.mark.parametrize('line, expected_type', [
    ('requests==2.31.0', 'PinnedPackage'),
    ('numpy==1.26.4', 'PinnedPackage'),
    ('pandas==2.2.1', 'PinnedPackage'),
    ('uvicorn==0.29.0', 'PinnedPackage'),
    ('-e ../myproject', 'EditablePackage'),
    ('-e /absolute/path/to/project', 'EditablePackage'),
    ('-e src/myproj', 'EditablePackage'),
    ('-e ./relative/path', 'EditablePackage'),
    ('mypkg @ https://example.com/mypkg-1.0.0.tar.gz', 'UrlPackage'),
    ('lib @ file:///home/user/libs/lib-0.1.0.tar.gz', 'UrlPackage'),
    ('pkg @ https://domain.com/archive-0.0.1.zip', 'UrlPackage'),
    ('lib @ file:///C:/libs/lib-1.0.0.tar.gz', 'UrlPackage'),
    ('tool @ http://example.org/tool.whl', 'UrlPackage'),
    ('mypkg @ git+https://github.com/user/repo.git@abcdef', 'VcsPackage'),
    ('tool @ hg+https://hg.example.com/tool@12345', 'VcsPackage'),
    ('mypkg @ git+ssh://git@github.com/user/repo.git@deadbeef', 'VcsPackage'),
    ('mypkg @ svn+https://svn.example.com/repo@42', 'VcsPackage'),
    ('mypkg @ bzr+https://bzr.example.com/repo@rev123', 'VcsPackage'),
    ('unknown-format', 'Package'),
    ('just-a-name', 'Package'),
    ('something with spaces', 'Package')
])
def test_package_parsing(line: str, expected_type: str):
    assert Package.parse(line).kind == expected_type


def test_package_equality():
    pkg1 = Package.parse('requests==2.31.0')
    pkg2 = Package.parse('requests==2.32.5')
    pkg3 = Package.parse('numpy==1.26.4')
    assert pkg1 == pkg2
    assert pkg1 != pkg3
    assert hash(pkg1) == hash(pkg2)
    assert hash(pkg1) != hash(pkg3)


def test_package_set_operations():
    pkg1 = Package.parse('requests==2.31.0')
    pkg2 = Package.parse('requests==2.32.5')
    pkg3 = Package.parse('numpy==1.26.4')
    pkg_set = {pkg1, pkg2, pkg3}
    assert len(pkg_set) == 2
    assert pkg1 in pkg_set
    assert pkg2 in pkg_set
    assert pkg3 in pkg_set
    assert 'requests' in pkg_set
    assert 'numpy' in pkg_set
    assert 'pandas' not in pkg_set


def test_pinned_package_fields():
    pkg = Package.parse('requests==2.31.0')
    assert isinstance(pkg, PinnedPackage)
    assert pkg.name == 'requests'
    assert pkg.version == '2.31.0'
    assert str(pkg) == 'requests==2.31.0'


def test_editable_package_fields():
    pkg = Package.parse('-e ../myproject')
    assert isinstance(pkg, EditablePackage)
    assert pkg.path == Path('../myproject')
    assert pkg.name == '-e ../myproject'
    assert str(pkg) == '-e ../myproject'


def test_url_package_fields():
    pkg = Package.parse('mypkg @ https://example.com/pkg-1.0.0.tar.gz')
    assert isinstance(pkg, UrlPackage)
    assert pkg.name == 'mypkg'
    assert pkg.url == 'https://example.com/pkg-1.0.0.tar.gz'
    assert str(pkg) == 'mypkg @ https://example.com/pkg-1.0.0.tar.gz'


def test_vcs_package_fields():
    pkg = Package.parse('mypkg @ git+https://github.com/user/repo.git@abcdef')
    assert isinstance(pkg, VcsPackage)
    assert pkg.name == 'mypkg'
    assert pkg.vcs == 'git'
    assert pkg.repo == 'https://github.com/user/repo.git'
    assert pkg.commit == 'abcdef'
    assert pkg.url == 'git+https://github.com/user/repo.git@abcdef'
    assert str(pkg) == 'mypkg @ git+https://github.com/user/repo.git@abcdef'
