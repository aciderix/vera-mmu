"""Marker-based observation of a project's structure (§30).

The scanner answers one question: what does this tree look like from the outside? It recognises
names — directories, file names, extensions — and nothing else. It opens no file, follows no
symlink, starts no process and reaches no network, so an observation can never be mistaken for a
verdict: `pytest.ini` present means a file of that name exists, not that tests pass.

The detection lives in declarative tables rather than in branches, so a missing category is
visible by reading one table, and the conformance suite proves each one on its own fixture.

One row per recognised marker, not per file: a thousand Python modules make a single observation
about Python carrying its count. That keeps the report bounded, comparable between runs, and
usable as the input of a profile recommendation (§31).
"""
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from hashlib import sha256
from pathlib import Path
import json
import os

from .store import StoreError


SCAN_FORMAT = "vera-scan-report/v2"
MAX_SCAN_ENTRIES = 4096
MAX_SCAN_DEPTH = 5

# The categories §30 requires the scanner to observe. Extra categories are welcome; a missing one
# means the report no longer answers what the specification asks of it.
SPECIFIED_CATEGORIES = (
    "vcs", "language", "framework", "dependency-manager", "build-script", "tests",
    "linter", "ci", "container", "documentation", "dataset", "asset", "subproject", "configuration",
)

EXCLUDED_DIRECTORIES = frozenset({
    ".git", ".hg", ".svn", ".vera-mmu", ".venv", "venv", "node_modules", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build", "target", ".tox",
})

# A directory whose presence is itself an observation. Its own name is the evidence.
_DIRECTORY_MARKERS: dict[str, tuple[tuple[str, str], ...]] = {
    ".git": (("vcs", "git"),),
    ".hg": (("vcs", "mercurial"),),
    ".svn": (("vcs", "subversion"),),
    ".github": (),  # traversed for workflows/ below, never an observation on its own
    ".circleci": (("ci", "circleci"),),
    "docs": (("documentation", "docs-directory"),),
    "doc": (("documentation", "docs-directory"),),
    "data": (("dataset", "data-directory"),),
    "datasets": (("dataset", "data-directory"),),
    "fixtures": (("dataset", "fixtures-directory"),),
    "assets": (("asset", "assets-directory"),),
    "static": (("asset", "static-directory"),),
    "public": (("asset", "public-directory"),),
    "media": (("asset", "media-directory"),),
    "tests": (("tests", "tests-directory"),),
    "test": (("tests", "tests-directory"),),
    "spec": (("tests", "spec-directory"),),
    "__tests__": (("tests", "tests-directory"),),
    "config": (("configuration", "config-directory"),),
}

# A file name that is recognised exactly. One file may evidence several categories: a manifest
# declares a dependency manager and is itself a configuration file.
_FILE_MARKERS: dict[str, tuple[tuple[str, str], ...]] = {
    # dependency managers
    "pyproject.toml": (("dependency-manager", "python"), ("configuration", "pyproject")),
    "requirements.txt": (("dependency-manager", "python"),),
    "Pipfile": (("dependency-manager", "python"),),
    "poetry.lock": (("dependency-manager", "python"),),
    "uv.lock": (("dependency-manager", "python"),),
    "setup.py": (("dependency-manager", "python"),),
    "setup.cfg": (("dependency-manager", "python"), ("configuration", "setup-cfg")),
    "package.json": (("dependency-manager", "node"),),
    "package-lock.json": (("dependency-manager", "npm"),),
    "pnpm-lock.yaml": (("dependency-manager", "pnpm"),),
    "yarn.lock": (("dependency-manager", "yarn"),),
    "Cargo.toml": (("dependency-manager", "cargo"),),
    "Cargo.lock": (("dependency-manager", "cargo"),),
    "go.mod": (("dependency-manager", "go-modules"),),
    "go.sum": (("dependency-manager", "go-modules"),),
    "Gemfile": (("dependency-manager", "bundler"),),
    "Gemfile.lock": (("dependency-manager", "bundler"),),
    "composer.json": (("dependency-manager", "composer"),),
    "composer.lock": (("dependency-manager", "composer"),),
    "pom.xml": (("dependency-manager", "maven"), ("build-script", "maven")),
    "build.gradle": (("dependency-manager", "gradle"), ("build-script", "gradle")),
    "build.gradle.kts": (("dependency-manager", "gradle"), ("build-script", "gradle")),
    "mix.exs": (("dependency-manager", "mix"),),
    # build scripts
    "Makefile": (("build-script", "make"),),
    "makefile": (("build-script", "make"),),
    "GNUmakefile": (("build-script", "make"),),
    "justfile": (("build-script", "just"),),
    "Justfile": (("build-script", "just"),),
    "Taskfile.yml": (("build-script", "task"),),
    "Taskfile.yaml": (("build-script", "task"),),
    "CMakeLists.txt": (("build-script", "cmake"),),
    "meson.build": (("build-script", "meson"),),
    "SConstruct": (("build-script", "scons"),),
    "Rakefile": (("build-script", "rake"),),
    "gulpfile.js": (("build-script", "gulp"),),
    "settings.gradle": (("build-script", "gradle"),),
    # frameworks
    "manage.py": (("framework", "django"),),
    "angular.json": (("framework", "angular"),),
    "platformio.ini": (("framework", "platformio"),),
    "project.godot": (("framework", "godot"),),
    "tsconfig.json": (("configuration", "tsconfig"),),
    "config.ru": (("framework", "rack"),),
    "artisan": (("framework", "laravel"),),
    "Procfile": (("configuration", "procfile"),),
    # tests
    "pytest.ini": (("tests", "pytest"),),
    "tox.ini": (("tests", "tox"), ("configuration", "tox")),
    "phpunit.xml": (("tests", "phpunit"),),
    "karma.conf.js": (("tests", "karma"),),
    # linters
    ".editorconfig": (("linter", "editorconfig"),),
    ".flake8": (("linter", "flake8"),),
    ".pylintrc": (("linter", "pylint"),),
    "ruff.toml": (("linter", "ruff"),),
    ".ruff.toml": (("linter", "ruff"),),
    "mypy.ini": (("linter", "mypy"),),
    ".rubocop.yml": (("linter", "rubocop"),),
    "clippy.toml": (("linter", "clippy"),),
    ".pre-commit-config.yaml": (("linter", "pre-commit"),),
    # continuous integration
    ".gitlab-ci.yml": (("ci", "gitlab"),),
    "azure-pipelines.yml": (("ci", "azure-pipelines"),),
    "Jenkinsfile": (("ci", "jenkins"),),
    ".travis.yml": (("ci", "travis"),),
    ".drone.yml": (("ci", "drone"),),
    "bitbucket-pipelines.yml": (("ci", "bitbucket"),),
    # containers
    "Dockerfile": (("container", "docker"),),
    "Containerfile": (("container", "podman"),),
    ".dockerignore": (("container", "docker"),),
    "docker-compose.yml": (("container", "docker-compose"),),
    "docker-compose.yaml": (("container", "docker-compose"),),
    "compose.yml": (("container", "docker-compose"),),
    "compose.yaml": (("container", "docker-compose"),),
    "Chart.yaml": (("container", "helm"),),
    # documentation and repository metadata
    "README.md": (("documentation", "readme"),),
    "README.rst": (("documentation", "readme"),),
    "README": (("documentation", "readme"),),
    ".gitmodules": (("subproject", "git-submodules"),),
}

# A file name recognised by shape, because its variants are open-ended.
_FILE_PATTERNS: tuple[tuple[str, tuple[str, str]], ...] = (
    ("Dockerfile.*", ("container", "docker")),
    ("CHANGELOG*", ("documentation", "changelog")),
    ("CONTRIBUTING*", ("documentation", "contributing")),
    ("next.config.*", ("framework", "next")),
    ("nuxt.config.*", ("framework", "nuxt")),
    ("vue.config.*", ("framework", "vue")),
    ("svelte.config.*", ("framework", "svelte")),
    ("vite.config.*", ("framework", "vite")),
    ("tailwind.config.*", ("framework", "tailwind")),
    ("astro.config.*", ("framework", "astro")),
    ("remix.config.*", ("framework", "remix")),
    ("webpack.config.*", ("build-script", "webpack")),
    ("rollup.config.*", ("build-script", "rollup")),
    ("esbuild.config.*", ("build-script", "esbuild")),
    ("jest.config.*", ("tests", "jest")),
    ("vitest.config.*", ("tests", "vitest")),
    ("playwright.config.*", ("tests", "playwright")),
    ("cypress.config.*", ("tests", "cypress")),
    (".eslintrc*", ("linter", "eslint")),
    ("eslint.config.*", ("linter", "eslint")),
    (".prettierrc*", ("linter", "prettier")),
    ("prettier.config.*", ("linter", "prettier")),
    (".stylelintrc*", ("linter", "stylelint")),
    (".golangci.*", ("linter", "golangci")),
    (".env", ("configuration", "dotenv")),
    (".env.*", ("configuration", "dotenv")),
)

# A source extension is what tells a language apart from the manifest that builds it.
_LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "python", ".pyi": "python", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".rs": "rust", ".go": "go", ".java": "java", ".kt": "kotlin", ".kts": "kotlin",
    ".rb": "ruby", ".php": "php", ".cs": "csharp", ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".swift": "swift",
    ".scala": "scala", ".ex": "elixir", ".exs": "elixir", ".sh": "shell", ".bash": "shell",
    ".lua": "lua", ".r": "r", ".m": "objective-c", ".dart": "dart", ".sql": "sql",
    ".ino": "arduino",
}

_OTHER_EXTENSIONS: dict[str, tuple[str, str]] = {
    ".md": ("documentation", "markdown"), ".rst": ("documentation", "restructuredtext"),
    ".adoc": ("documentation", "asciidoc"),
    ".ipynb": ("framework", "jupyter"), ".kicad_pcb": ("framework", "kicad"),
    ".csv": ("dataset", "csv"), ".tsv": ("dataset", "tsv"), ".parquet": ("dataset", "parquet"),
    ".jsonl": ("dataset", "jsonl"), ".ndjson": ("dataset", "ndjson"), ".arrow": ("dataset", "arrow"),
    ".feather": ("dataset", "feather"), ".h5": ("dataset", "hdf5"), ".hdf5": ("dataset", "hdf5"),
    ".npz": ("dataset", "npz"), ".npy": ("dataset", "npy"),
    ".png": ("asset", "image"), ".jpg": ("asset", "image"), ".jpeg": ("asset", "image"),
    ".gif": ("asset", "image"), ".svg": ("asset", "image"), ".webp": ("asset", "image"),
    ".ico": ("asset", "icon"), ".woff": ("asset", "font"), ".woff2": ("asset", "font"),
    ".ttf": ("asset", "font"), ".otf": ("asset", "font"), ".mp4": ("asset", "video"),
    ".mp3": ("asset", "audio"), ".wav": ("asset", "audio"),
    ".ini": ("configuration", "ini"), ".cfg": ("configuration", "cfg"),
    ".conf": ("configuration", "conf"), ".toml": ("configuration", "toml"),
    ".yaml": ("configuration", "yaml"), ".yml": ("configuration", "yaml"),
}

# A nested manifest is a sub-project; the same file at the root is just the project.
_SUBPROJECT_MANIFESTS = frozenset({
    "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml",
    "build.gradle", "build.gradle.kts", "composer.json", "Gemfile", "mix.exs",
})

# Test-like paths, recognised by shape rather than by a configuration file.
_TEST_FILE_PATTERNS = ("test_*.py", "*_test.py", "*_test.go", "*.test.ts", "*.test.js", "*.spec.ts", "*.spec.js", "*Test.java")


class ProjectScanError(StoreError):
    """Raised when a scan root cannot be observed unambiguously."""


@dataclass(frozen=True)
class ScanObservation:
    """One recognised marker: what category, which marker, where it was first seen."""

    kind: str
    marker: str
    path: str
    detail: str
    occurrences: int = 1
    status: str = "OBSERVED"

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "marker": self.marker,
            "path": self.path,
            "detail": self.detail,
            "occurrences": self.occurrences,
            "status": self.status,
        }


@dataclass(frozen=True)
class ScanReport:
    """A deterministic, read-only observation of one project tree."""

    format: str
    root: str
    observations: tuple[ScanObservation, ...]
    categories: tuple[str, ...]
    status: str
    report_hash: str
    json_text: str

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "root": self.root,
            "observations": [item.as_dict() for item in self.observations],
            "categories": list(self.categories),
            "status": self.status,
            "report_hash": self.report_hash,
        }


def scan_project(root: str | Path) -> ScanReport:
    """Observe one project tree by name only, never opening a file it finds."""
    source = Path(root).expanduser()
    if source.is_symlink():
        raise ProjectScanError("Racine de scan symlinkée refusée.")
    try:
        resolved = source.resolve(strict=True)
    except OSError as exc:
        raise ProjectScanError("Racine de scan introuvable.") from exc
    if not resolved.is_dir():
        raise ProjectScanError("Racine de scan non répertoire.")

    found: dict[tuple[str, str], list] = {}
    count = 0
    truncated = False
    for current, directories, files in os.walk(resolved, followlinks=False):
        here = Path(current)
        relative = here.relative_to(resolved)
        depth = 0 if relative == Path(".") else len(relative.parts)
        for name in sorted(directories):
            child = here / name
            if child.is_symlink():
                continue
            _record_directory(found, name, (relative / name).as_posix() if depth else name)
        if depth == 0 and (resolved / ".github" / "workflows").is_dir():
            _record(found, "ci", "github-actions", ".github/workflows", "répertoire de workflows présent")
        directories[:] = sorted(
            name for name in directories
            if name not in EXCLUDED_DIRECTORIES and not (here / name).is_symlink() and depth < MAX_SCAN_DEPTH
        )
        for name in sorted(files):
            path = here / name
            if path.is_symlink() or not path.is_file():
                continue
            count += 1
            if count > MAX_SCAN_ENTRIES:
                truncated = True
                break
            _record_file(found, name, (relative / name).as_posix() if depth else name, depth)
        if truncated:
            break
    if truncated:
        _record(found, "scan-limit", "entries", ".", f"observation bornée à {MAX_SCAN_ENTRIES} fichiers réguliers")

    observations = tuple(
        ScanObservation(kind, marker, path, detail, occurrences)
        for (kind, marker), (path, detail, occurrences) in sorted(
            ((key, (value[0], value[1], value[2])) for key, value in found.items()), key=lambda item: item[0]
        )
    )
    categories = tuple(sorted({item.kind for item in observations}))
    body = {
        "format": SCAN_FORMAT,
        "root": str(resolved),
        "observations": [item.as_dict() for item in observations],
        "categories": list(categories),
        "status": "OBSERVED",
    }
    text = json.dumps(body, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return ScanReport(SCAN_FORMAT, str(resolved), observations, categories, "OBSERVED", sha256(text.encode()).hexdigest(), text)


def _record(found: dict[tuple[str, str], list], kind: str, marker: str, path: str, detail: str) -> None:
    """Keep one row per recognised marker: the first path seen, and how many times."""
    key = (kind, marker)
    existing = found.get(key)
    if existing is None:
        found[key] = [path, detail, 1]
        return
    existing[2] += 1
    if path < existing[0]:
        existing[0], existing[1] = path, detail


def _record_directory(found: dict[tuple[str, str], list], name: str, path: str) -> None:
    for kind, marker in _DIRECTORY_MARKERS.get(name, ()):
        _record(found, kind, marker, path, f"répertoire `{name}` présent")


def _record_file(found: dict[tuple[str, str], list], name: str, path: str, depth: int) -> None:
    for kind, marker in _FILE_MARKERS.get(name, ()):
        _record(found, kind, marker, path, f"marqueur `{name}` présent")
    for pattern, (kind, marker) in _FILE_PATTERNS:
        if fnmatch(name, pattern):
            _record(found, kind, marker, path, f"marqueur `{name}` présent")
    suffix = Path(name).suffix.lower()
    language = _LANGUAGE_EXTENSIONS.get(suffix)
    if language is not None:
        _record(found, "language", language, path, f"extension `{suffix}` présente")
    other = _OTHER_EXTENSIONS.get(suffix)
    if other is not None:
        _record(found, other[0], other[1], path, f"extension `{suffix}` présente")
    if depth > 0 and name in _SUBPROJECT_MANIFESTS:
        parent = path.rsplit("/", 1)[0]
        _record(found, "subproject", parent, parent, f"manifeste `{name}` imbriqué")
    if any(fnmatch(name, pattern) for pattern in _TEST_FILE_PATTERNS):
        _record(found, "tests", "test-file", path, "nom de fichier de test présent")
