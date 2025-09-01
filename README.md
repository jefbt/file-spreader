# file-spreader

## Overview

**file-spreader** is a Python tool designed to efficiently distribute or organize files across directories according to user-defined rules or patterns. It can be used for tasks such as sorting, copying, or moving files in bulk.

## Installation

It is recommended to use a virtual environment to manage dependencies.

### Using `venv`

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Using [`uv`](https://github.com/astral-sh/uv)

If you have [uv](https://github.com/astral-sh/uv) installed:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

## Usage

After installing the dependencies, run the program with:

```bash
python main.py
```

or, if using uv:

```bash
uv pip run main.py
```

Refer to the documentation or help command for available options.

## Pysintaller
To use pyinstaller, run
```bash
pyinstaller --name "File Spreader" --noconfirm --noconsole --hidden-import=PySide6.QtCore --hidden-import=PySide6.QtWidgets --hidden-import=PySide6.QtGui main.py
```

## License

This project is licensed under the [MIT License](LICENSE).