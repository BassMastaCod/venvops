import subprocess
import sys
import shutil
from venv import EnvBuilder
from pathlib import Path
from typing import Optional


class CommandError(Exception):
    """Base class for command execution errors."""


class InvalidPackageError(CommandError):
    """Raised when attempting to install an invalid package."""


class InvalidVersionError(CommandError):
    """Raised when attempting to install a package with an invalid version."""


class MalformedRequirementError(CommandError):
    """Raised when the requirement string is malformed."""


class ConflictingRequirementError(CommandError):
    """Raised when there are conflicting requirements during dependency resolution."""


class Package:
    """Represents a single package specification expressed in a standard requirement-line format.

    This can originate from sources such as `pip freeze`, a requirements
    file, or any other PEP 508–compatible specification. The `raw` field
    preserves the exact text of the requirement line, while subclasses
    may expose structured information when the format is recognized.
    """
    SUBCLASSES: list[type['Package']] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.SUBCLASSES = []

    def __init__(self, raw: str):
        self.raw = raw
        self.name = raw

    @property
    def kind(self) -> str:
        return self.__class__.__name__

    @classmethod
    def register_subclasses(cls, *subclasses: type['Package']) -> None:
        """Register subclasses to be considered during parsing."""
        cls.SUBCLASSES.extend(subclasses)

    @classmethod
    def parse(cls, raw: str) -> 'Package':
        raw = raw.strip()
        for sub in cls.SUBCLASSES:
            try:
                return sub.parse(raw)
            except ValueError:
                pass
        return cls(raw)

    def is_compatible(self, other: 'Package') -> bool:
        return self == other

    def __eq__(self, other):
        return getattr(other, 'name', str(other)) == self.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self) -> str:
        return self.raw


class PinnedPackage(Package):
    """A standard pinned package of the form:

        "requests==2.31.0"
        "numpy==1.26.4"
    """
    def __init__(self, raw: str):
        super().__init__(raw)
        if '==' not in raw:
            raise ValueError
        self.name, self.version = raw.split('==', 1)


class EditablePackage(Package):
    """An editable install (typically from a local source tree):

        "-e ../myproject"
        "-e /absolute/path/to/project"
    """
    def __init__(self, raw: str):
        super().__init__(raw)
        if not raw.startswith('-e '):
            raise ValueError
        self.path = Path(raw[3:])


class UrlPackage(Package):
    """A package installed directly from a URL:

        "mypkg @ https://example.com/mypkg-1.0.0.tar.gz"
        "lib @ file:///home/user/libs/lib-0.1.0.tar.gz"
    """
    def __init__(self, raw: str):
        super().__init__(raw)
        if ' @ ' not in raw:
            raise ValueError
        self.name, self.url = raw.split(' @ ', 1)


class VcsPackage(UrlPackage):
    """A specialized URL package installed from a version control system (VCS):

        "mypkg @ git+https://github.com/user/repo.git@abcdef"
        "tool @ hg+https://hg.example.com/tool@12345"
    """
    def __init__(self, raw: str):
        super().__init__(raw)
        if not self.url.startswith(('git+', 'hg+', 'svn+', 'bzr+')):
            raise ValueError
        self.vcs, rest = self.url.split('+', 1)
        self.repo, self.commit = rest.rsplit('@', 1)


UrlPackage.register_subclasses(VcsPackage)
Package.register_subclasses(PinnedPackage, EditablePackage, UrlPackage)


class Packages(set[Package]):
    def __contains__(self, item: str|Package) -> bool:
        return any(pkg == item for pkg in self)

    def get(self, name: str) -> 'Packages':
        return Packages([pkg for pkg in self if pkg.name == name])


class Venv:
    """An API for creating and managing virtual environments."""
    def __init__(self, path: Path):
        self.path = Path(path)

    def _create(self) -> None:
        """Builds the new virtual environment."""
        self.path.mkdir()
        EnvBuilder(with_pip=True).create(self.path)

    @classmethod
    def create_in(cls, directory: str|Path) -> 'Venv':
        """Creates a new virtual environment within the given directory e.g., directory/.venv/"""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        venv = cls(directory / '.venv')
        venv._create()
        return venv

    @classmethod
    def find_in(cls, directory: str|Path) -> Optional['Venv']:
        """Discovers a pre-existing venv within the given directory e.g., directory/.venv/ or directory/venv/"""
        directory = Path(directory)
        for candidate in [directory / '.venv', directory / 'venv']:
            if (candidate / 'pyvenv.cfg').exists():
                return cls(candidate)
        return None

    @property
    def scripts_dir(self) -> Path:
        """The directory containing the venv's scripts depending on the OS."""
        return self.path / ('Scripts' if sys.platform.startswith('win') else 'bin')

    @property
    def python(self) -> Path:
        """The path to the python executable within the venv."""
        return self.scripts_dir / 'python'

    @property
    def pip(self) -> Path:
        """The path to the pip executable within the venv."""
        return self.scripts_dir / 'pip'

    @classmethod
    def run(cls, executable: str|Path, *args, **kwargs) -> subprocess.CompletedProcess:
        """Runs a command.

        :param executable: The executable to run
        :param args: The arguments to pass to the executable
        :param kwargs: The keyword arguments to pass to the subprocess.run function
        :return: The completed process having the returncode, stdout, and stderr attributes, etc
        """
        return subprocess.run([str(executable), *args], **kwargs)

    @classmethod
    def run_for_output(cls, executable: str|Path, *args, check: bool = True, **kwargs) -> str:
        """Runs a command and returns the output as a string.

        :param executable: The executable to run
        :param args: The arguments to pass to the executable
        :param check: False to not raise an exception if the command returns a non-zero exit code
        :param kwargs: The keyword arguments to pass to the subprocess.run function
        :return: The output of the command as a string (includes both stdout and stderr)
        :raises: CommandError if the command fails (assuming check=True)
        """
        try:
            return cls.run(
                executable,
                *args,
                check=check,
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE,
                text=True,
                **kwargs
            ).stdout
        except subprocess.CalledProcessError as e:
            raise CommandError(
                f'Command failed:\n'
                f'  Executable: {executable}\n'
                f'  Arguments: {" ".join(args)}\n'
                f'  Exit code: {e.returncode}\n'
                f'  Output:\n{e.stdout}'
            ) from e

    def run_python(self, *args) -> str:
        """Runs a python command within the venv."""
        return self.run_for_output(self.python, *args)

    def run_pip(self, *args) -> str:
        """Runs a pip command within the venv."""
        try:
            return self.run_for_output(self.pip, *args)
        except CommandError as e:
            if isinstance(e.__cause__, subprocess.CalledProcessError):
                output = e.__cause__.stdout
                if 'No matching distribution found' in output:
                    if 'from versions: none' in output:
                        raise InvalidPackageError(
                            f'Invalid package specified:\n'
                            f'{output}'
                        ) from e
                    else:
                        raise InvalidVersionError(
                            f'Invalid version specified:\n'
                            f'{output}'
                        ) from e
                elif 'Invalid requirement' in output:
                    raise MalformedRequirementError(
                        f'Malformed requirement string:\n'
                        f'{output}'
                    ) from e
                elif 'ResolutionImpossible' in output:
                    raise ConflictingRequirementError(
                        f'Conflicting requirements detected:\n'
                        f'{output}'
                    )
            raise

    def install(self, *packages) -> str:
        """Installs the given packages to the venv."""
        return self.run_pip('install', *packages)

    def uninstall(self, *packages) -> str:
        """Uninstalls the given packages from the venv."""
        return self.run_pip('uninstall', '-y', *packages)

    def install_file(self, req_file: str|Path) -> str:
        """Installs the packages in the specified requirements file to the venv."""
        return self.install('-r', str(req_file))

    def uninstall_file(self, req_file: str|Path) -> str:
        """Uninstalls the packages in the specified requirements file from the venv."""
        return self.uninstall('-r', str(req_file))

    def installed(self) -> Packages:
        """Returns the current packages installed in the venv."""
        freeze_output = self.run_pip('freeze').splitlines()
        return Packages(Package.parse(line) for line in freeze_output if line.strip())

    def __enter__(self) -> 'Venv':
        if self.path.exists():
            raise ValueError(f'Path {self.path} already exists. Cannot auto-create venv over existing path.')
        self._create()
        return self

    def __exit__(self, exc_type, exc, tb):
        shutil.rmtree(self.path)
