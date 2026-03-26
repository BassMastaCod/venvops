# venvops

A Python library for creating and managing virtual environments, including installing and managing packages.

## Overview

`venvops` provides a simple and intuitive API for working with Python virtual environments.
It allows you to create, discover, and manage virtual environments,
as well as perform pip operations like installing and uninstalling packages.

## Features

- **Virtual Environment Management**: Create new virtual environments or modify existing ones
- **Package Operations**: Install, uninstall, and manage packages within virtual environments
- **Package Parsing**: Handle different types of package specifications (pinned, editable, URL-based, VCS-based)
- **Cross-Platform Support**: Works on Windows, macOS, and Linux
- **Type Hints**: Full type hint support for better development experience

## Quick Start

### Requirements

- Python 3.10 or higher
- No external dependencies (uses only standard library)

### Installation

```bash
pip install venvops
```

### Import

```python
from venvops import Venv
```

## Usage

### Creating and Managing Virtual Environments

```python
from venvops import Venv

# Create a new virtual environment
venv = Venv.create_in('my_project')

# Or discover an existing one
venv = Venv.find_in('my_project')

# Install packages
venv.install('requests', 'numpy==1.26.4')

# Install from requirements file
venv.install_requirements('requirements.txt')

# Get installed packages
packages = venv.installed()
print(f'Installed packages: {len(packages)}')

# Check if a package is installed
if 'requests' in packages:
    print('requests is installed')

# Uninstall packages
venv.uninstall('requests')
```

### Running Commands

```python
# Run Python commands in the virtual environment
output = venv.run_python('-c', 'import sys; print(sys.version)')

# Run pip commands
output = venv.run_pip('list')

# Run arbitrary commands
result = Venv.run('uvicorn', '--version')
```

### Temporary Virtual Environments (Context Manager)

Use `Venv` as a context manager to create temporary virtual environments that are automatically cleaned up when done:

```python
from venvops import Venv
from pathlib import Path

# Create a temporary virtual environment that gets cleaned up automatically
with Venv(Path('temp_env')) as venv:
    # Install packages for temporary use
    venv.install('requests', 'beautifulsoup4')

    # Run some code
    output = venv.run_python('-c', 'import requests; print(requests.__version__)')
    print(f'Requests version: {output.strip()}')

    # Check installed packages
    packages = venv.installed()
    print(f'Temporary environment has {len(packages)} packages')

# The virtual environment is automatically deleted when exiting the context
print('Temporary environment has been cleaned up')
```

## API Reference

### Venv Class

The main class for virtual environment operations.

#### Class Methods

- `Venv.create_in(directory)`: Create a new virtual environment in the specified directory
- `Venv.find_in(directory)`: Find an existing virtual environment in the specified directory
- `Venv.run(executable, *args, **kwargs)`: Run a command and return the completed process
- `Venv.run_for_output(executable, *args, **kwargs)`: Run a command and return the output as a string

#### Instance Methods

- `run_python(*args)`: Run a Python command within the virtual environment
- `run_pip(*args)`: Run a pip command within the virtual environment
- `install(*packages)`: Install packages to the virtual environment
- `uninstall(*packages)`: Uninstall packages from the virtual environment
- `install_file(req_file)`: Install packages from a requirements file
- `uninstall_file(req_file)`: Uninstall packages from a requirements file
- `installed()`: Get the currently installed packages as a `Packages` object

#### Properties

- `path`: Path to the virtual environment directory
- `scripts_dir`: Path to the scripts directory (OS-dependent)
- `python`: Path to the Python executable
- `pip`: Path to the pip executable

### Package Class

Represents a Python package specification.

#### Class Methods

- `Package.parse(raw)`: Parse a package specification string and return the appropriate Package subclass

#### Properties

- `name`: The package name
- `kind`: The type of package (e.g., "PinnedPackage", "EditablePackage")

#### Subclasses

- `PinnedPackage`: For packages with specific versions (e.g., "requests==2.31.0")
- `EditablePackage`: For editable packages (e.g., "-e ../myproject")
- `UrlPackage`: For URL-based packages (e.g., "pkg @ https://example.com/pkg.tar.gz")
- `VcsPackage`: For VCS-based packages (e.g., "pkg @ git+https://github.com/user/repo.git")

### Packages Class

A collection class for managing multiple Package objects, inheriting from `list[Package]`.

#### Methods

- `__contains__(item)`: Check if a package (by name or Package object) is in the collection
- `get(name)`: Get all packages with the specified name

## Examples

### Setting up a Development Environment

```python
from venvops import Venv

# Create a new virtual environment for a project
venv = Venv.create_in('my_web_app')

# Install development dependencies
venv.install(
    'fastapi==0.104.1',
    'uvicorn[standard]==0.24.0',
    'pytest==7.4.3',
    'black==23.11.0'
)

# Install from requirements file
venv.install_requirements('requirements.txt')

# Check what's installed
packages = venv.installed()
print(f'Total packages installed: {len(packages)}')

# Check for specific packages
if 'fastapi' in packages:
    fastapi_packages = packages.get('fastapi')
    print(f'FastAPI version: {fastapi_packages[0]}')
```

### Managing Multiple Environments

```python
from venvops import Venv

projects = ['web_app', 'data_analysis', 'ml_project']

for project in projects:
    # Try to find existing environment, create if not found
    venv = Venv.find_in(project) or Venv.create_in(project)

    # Install common development tools
    venv.install('pytest', 'black', 'mypy')

    print(f'Environment ready for {project}')
```

### Testing with Temporary Environments

```python
from venvops import Venv
from pathlib import Path

def test_package_compatibility():
    """Test if different package versions work together."""
    test_combinations = [
        ['django==4.2.0', 'djangorestframework==3.14.0'],
        ['django==4.1.0', 'djangorestframework==3.13.0'],
    ]

    for i, packages in enumerate(test_combinations):
        print(f'Testing combination {i + 1}: {packages}')

        # Use context manager for automatic cleanup
        with Venv(Path(f'test_env_{i}')) as venv:
            try:
                # Install the package combination
                venv.install(*packages)

                # Run compatibility test
                result = venv.run_python('-c', '''
import django
import rest_framework
print(f"Django {django.VERSION}, DRF {rest_framework.VERSION}")
print("Compatibility test passed!")
                ''')
                print(result)

            except Exception as e:
                print(f'Test failed: {e}')

        # Environment is automatically cleaned up here
        print(f'Test environment {i + 1} cleaned up\n')

# Run the test
test_package_compatibility()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Feature requests are also a great form of contribution!
