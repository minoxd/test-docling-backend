
3 approach
- DocumentConverter -> HybridChunker -> json
```
{
    "chunks": [
        "<p>chunk 1</p>",
        "<p>chunk 2</p>"
    ]
}
```
- DocumentConverter export to HTML -> LangChain HTMLHeaderTextSplitter