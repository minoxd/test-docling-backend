## Approaches
1. Best:
convert from chunk to dldoc then export as html (object-oriented document manipulation, but requires docling source code understanding)
2. Alternatives:
- find chunk by grouping html elements using chunk's headings (html formatting are kept, but chunk finding can be messed as headings can be repetitive)
- contextualize chunk and put in `<p></p>` (easy to implement but no html formatting)

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
1. table is chunked column-wise, meaning one column per chunk (i think this is a feature)