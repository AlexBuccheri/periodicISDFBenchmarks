# Benchmarking for Periodic ISDF

## Installation

This project uses `uv` and installs the local packages
`periodic_isdf_benchmarks` and `qindependent` into the project environment.

From the repository root, install with `uv`:

```shell
uv sync
```

The equivalent editable `pip` install is:

```shell
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ../libraries/postopus
python -m pip install -e .
python -m pip install ruff pytest pytest-cov
```

The project expects `postopus` to be available at `../libraries/postopus`, as
configured in `pyproject.toml`. If your checkout is somewhere else, update the
`[tool.uv.sources]` entry before running `uv sync`, or adjust the `pip install`
path above.

To verify the installation:

```shell
uv run python -c "from periodic_isdf_benchmarks.parser.inp_gen import Quoted; print(Quoted('Si').render())"
```

Run lint checks with:

```shell
uv run ruff check qindependent periodic_isdf_benchmarks
```

Note, I took the parsing and job submission from:
`isdfBenchmarks`
Input generation is spread across:
```markdown
* octoprepy
* ocotopus-workflows
```
Should also generate a schema based on `oct_json_schema` and validate it with pydantic
