## Approaches
1. Best:
convert from chunk to dldoc then export as HTML (object-oriented document manipulation, but requires docling source code understanding)
2. Alternatives:
- find chunk by grouping HTML elements using chunk's headings (HTML formatting is kept, but chunk finding can be messed as headings can be repetitive)
- contextualize chunk and put in `<p></p>` (easy to implement but no HTML formatting)

## Output format example
```
{
    "chunks": [
        "<!-- HTML snippet 01 -->",
        "<!-- HTML snippet 02 -->"
    ]
}
```

## Notes
1. tables are chunked column-wise, meaning one column per chunk (I think this is a feature)

## Install 
1. jupiter
- automatically install jupiter in pycharm by creating a new ipynb file and run a simple cell (e.g. `print("hello world")`). After that:
```
pip install ipywidgets
```
2. pytorch
```
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu129
```
3. docling
```
pip install docling
```
4. fastapi
```
pip install starlette uvicorn
pip install pydantic
pip install "fastapi[standard]"
```