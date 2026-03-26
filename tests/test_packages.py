import pytest

from venvops import Package, Packages, PinnedPackage


def test_packages():
    pkg1 = Package.parse('requests==2.31.0')
    pkg2 = Package.parse('numpy==1.26.4')
    packages = Packages([pkg1, pkg2])

    assert len(packages) == 2
    assert pkg1 in packages
    assert pkg2 in packages


def test_contains():
    pkg1 = Package.parse('requests==2.31.0')
    pkg2 = Package.parse('numpy==1.26.4')
    pkg3 = Package.parse('requests==2.32.0')  # Different version, same name
    packages = Packages([pkg1, pkg2])

    assert pkg1 in packages
    assert pkg2 in packages
    assert pkg3 in packages  # Should be True because it checks by name only

    pkg4 = Package.parse('pandas==1.5.0')
    assert pkg4 not in packages


def test_contains__str():
    """Test __contains__ method with string package names."""
    pkg1 = Package.parse('requests==2.31.0')
    pkg2 = Package.parse('numpy==1.26.4')
    packages = Packages([pkg1, pkg2])

    assert 'requests' in packages
    assert 'numpy' in packages
    assert 'pandas' not in packages
    assert 'nonexistent' not in packages


def test_get():
    pkg1 = Package.parse('requests==2.31.0')
    pkg2 = Package.parse('numpy==1.26.4')
    packages = Packages([pkg1, pkg2])

    requests = packages.get('requests')
    assert isinstance(requests, PinnedPackage)
    assert requests.name == 'requests'
    assert requests.version == '2.31.0'

    numpy = packages.get('numpy')
    assert isinstance(numpy, PinnedPackage)
    assert numpy.name == 'numpy'
    assert numpy.version == '1.26.4'


def test_get__missing():
    with pytest.raises(KeyError):
        Packages().get('packagename')


def test_packages_empty():
    packages = Packages()

    assert len(packages) == 0
    assert 'anything' not in packages

    pkg = Package.parse('requests==2.31.0')
    assert pkg not in packages


def test_packages_with_different_package_types():
    pinned_pkg = Package.parse('requests==2.31.0')
    editable_pkg = Package.parse('-e ../myproject')
    url_pkg = Package.parse('mypkg @ https://example.com/pkg-1.0.0.tar.gz')

    packages = Packages([pinned_pkg, editable_pkg, url_pkg])

    assert 'requests' in packages
    assert '-e ../myproject' in packages
    assert 'mypkg' in packages

    assert pinned_pkg in packages
    assert editable_pkg in packages
    assert url_pkg in packages
