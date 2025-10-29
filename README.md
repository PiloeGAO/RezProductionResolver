# Rez Production Resolver

[![CI Tests](https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/ci-tests.yml)  
[![Docs Deploy](https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/docs-deploy.yml/badge.svg)](https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/docs-deploy.yml)
[![Tests coverage](https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/coverage.yml/badge.svg)](https://github.com/PiloeGAO/RezProductionResolver/actions/workflows/coverage.yml)  

A **Rez plugin** for managing production environments in animation/VFX workflows. It enables context-aware package management with staged validation, ensuring pipeline stability and preventing production breakage during testing.

---

## Key Features

- ✅ **SQLite-backed environment storage**
- 🧩 **Multi-level context hierarchy** (`studio → project → category → entity`)
- 🔄 **Automatic validation** of package combinations during install/uninstall
- 📦 **Staging/deployment workflow** with optional history backups
- 🧪 **Extensive test suite** with coverage tracking

---

## Installation

1. **Clone the repository**:
```shell script
git clone https://github.com/PiloeGAO/RezProductionResolver.git
   cd RezProductionResolver
```


2. **Install Rez** (see [Rez docs](https://rez.readthedocs.io/en/stable/installation.html)).

3. **Add the plugin to your `rezconfig.py`**:
```python
plugin_path = [
       "/path/to/RezProductionResolver/src",
   ]
```


4. **Initialize the database**:
```shell script
rez manage --initialize
```


---

## Usage

### Manage Commands

- **Install a package**:
```shell script
rez manage --install maya-2024 --software maya my_project assets character
```


- **Uninstall a package**:
```shell script
rez manage --uninstall houdini-19 --step lighting
```


- **List packages**:
```shell script
rez manage --list --step modeling --software blender my_game project
```


- **Deploy changes**:
```shell script
rez manage --deploy
```


### Resolve Commands

- **Launch software in a context**:
```shell script
rez resolve my_project assets character --software maya
```


- **Test staged changes**:
```shell script
rez resolve my_project assets character --software maya --staging
```


---

## Testing & Coverage

### Requirements
Install test dependencies:
```shell script
pip install -e .[tests]
```


### Run Tests
```shell script
pytest tests/
```


### Run Tests with Coverage
```shell script
coverage run -m pytest tests/ && coverage report
```


---

## Documentation

Build documentation using Sphinx:
```shell script
cd docs
pip install -e .[docs]
make html
```


Generated HTML will be in `docs/build/html/`.

---

## CI/CD Workflows

- **CI Tests**: Runs tests on every push/pull request.
- **Docs Deploy**: Deploys documentation to GitHub Pages automatically.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`.
3. Commit changes and push to your fork.
4. Submit a pull request with a clear description.
