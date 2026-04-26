# supreme-garbanzo

Chess Scotland AI Agent - Query player grades and league standings using natural language.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) with Gemma 4 model installed
- `uv` package manager

## Setup

```bash
# Install dependencies
uv sync

# Pull Gemma 4 model
ollama pull gemma4
```

## Usage

Run the interactive agent:

```bash
uv run python agent.py
```

### Example Queries

- "Find player Michael Comerford" - Get grades for a player
- "Find player Stephen Maxwell grading" - Get grading info
- "What's John Smith's standard grade?"

### Programmatic Usage

```python
from scraper import ChessScotlandScraper

async def main():
    scraper = ChessScotlandScraper()
    result = await scraper.get_player_data("Michael Comerford")
    print(result)
    # {'name': 'Comerford, Michael', 'pnum': '29938', 
    #  'standard_grade': 904, 'standard_grade_live': 846,
    #  'allegro_grade': 940, 'allegro_grade_live': 905, 'club': ''}

asyncio.run(main())
```

## Output

Returns a dictionary with:
- `name` - Player full name
- `pnum` - Chess Scotland player number
- `standard_grade` - Published standard grade
- `standard_grade_live` - Live standard grade
- `allegro_grade` - Published allegro grade  
- `allegro_grade_live` - Live allegro grade
- `club` - Player's club

## Development

Run tests:
```bash
uv run pytest
```

Lint:
```bash
uv run ruff check
```