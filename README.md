# arxiv_fetch

Download an arXiv paper's PDF, source files, and metadata into a local directory.

```
pip install arxiv_fetch
arxiv_fetch 2408.xxxxx
```

creates:

```
2408.xxxxx/README.md        title, authors, abstract
2408.xxxxx/2408.xxxxx.pdf
2408.xxxxx/src/...          LaTeX source, figures, etc.
```

Versioned ids (`2408.xxxxxv2`) and old-style ids (`hep-th/9711xxx`, saved as `hep-th_9711xxx/`) also work.
No dependencies beyond the Python standard library.
