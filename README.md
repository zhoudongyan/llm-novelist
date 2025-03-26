# LLM Novelist

An AI-powered novel generation tool that creates complete novels from simple prompts.

## Features

- Generate complete novels with multiple chapters
- Support for various writing styles (Fantasy, Romance, Science Fiction, etc.)
- Automatic cover image generation
- EPUB and Markdown format output
- Smart chapter and style determination based on prompts
- Command-line interface and API support

## Prerequisites

- Python 3.8 or higher
- Poetry (Python package manager)

## Installation

### Install Poetry

First, install Poetry if you haven't already:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Regular Installation

```bash
poetry add llm-novelist
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-novelist.git
cd llm-novelist

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

## Configuration

Create a `.env` file in your project root with the following variables:

```env
# OpenAI Configuration
OPENAI_BASE_URL=your_openai_base_url
OPENAI_API_KEY=your_openai_api_key
LLM_MODEL=gpt-3.5-turbo  # Optional, defaults to GPT-3.5

# Stability AI Configuration
STABILITY_API_KEY=your_stability_api_key
```

## Usage

### Command Line Interface

You can run the tool in two ways:

1. Using the `-m` flag (recommended):
```bash
poetry run python -m llm_novelist --prompt "Your story prompt" [options]
```

2. Direct package execution:
```bash
poetry run llm_novelist --prompt "Your story prompt" [options]
```

Options:
  --chapters NUMBER    Number of chapters (optional)
  --style STYLE       Writing style (optional)
  --output-dir DIR    Output directory (default: output)
  --author NAME       Author name (default: AI)

Example:
```bash
poetry run python -m llm_novelist --prompt "A story about AI and justice" --style "scifi" --chapters 10
```

### Python API

```python
from llm_novelist import generate_novel

result = generate_novel(
    prompt="Your story prompt",
    num_chapters=10,  # Optional
    style="fantasy",  # Optional
    output_dir="output",
    author="AI"
)

if result["status"] == "success":
    print(f"Novel generated: {result['title']}")
    print(f"Output directory: {result['output_dir']}")
    print(f"Files: {result['files']}")
```

## Development

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Activate the virtual environment:
   ```bash
   poetry shell
   ```
4. Run tests:
   ```bash
   poetry run pytest
   ```
5. Format code:
   ```bash
   poetry run black .
   poetry run isort .
   ```
6. Type checking:
   ```bash
   poetry run mypy .
   ```
7. Linting:
   ```bash
   poetry run ruff check .
   ```

## License

MIT License 