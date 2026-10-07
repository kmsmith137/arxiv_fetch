#!/usr/bin/env python3
"""Download an arXiv paper's metadata, PDF, and source files.

Example: 'arxiv_fetch 2408.07699' creates:

  2408.07699/README.md        title, authors, abstract
  2408.07699/2408.07699.pdf
  2408.07699/src/...          source files
"""

import argparse
import gzip
import io
import pathlib
import sys
import tarfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ATOM = '{http://www.w3.org/2005/Atom}'


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'arxiv_fetch'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def get_metadata(arxiv_id):
    url = 'https://export.arxiv.org/api/query?' + urllib.parse.urlencode({'id_list': arxiv_id})
    entry = ET.fromstring(fetch(url)).find(ATOM + 'entry')
    if entry is None or 'api/errors' in entry.findtext(ATOM + 'id', ''):
        sys.exit(f'arxiv_fetch: paper {arxiv_id!r} not found')

    clean = lambda s: ' '.join(s.split())
    return {
        'title': clean(entry.findtext(ATOM + 'title')),
        'authors': [clean(a.findtext(ATOM + 'name')) for a in entry.findall(ATOM + 'author')],
        'abstract': clean(entry.findtext(ATOM + 'summary')),
    }


def write_readme(path, arxiv_id, meta):
    path.write_text(
        f"# {meta['title']}\n\n"
        f"**Authors:** {', '.join(meta['authors'])}\n\n"
        f"**arXiv:** [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})\n\n"
        f"## Abstract\n\n{meta['abstract']}\n",
        encoding='utf-8',
    )


def extract_source(data, src_dir, name):
    # arXiv source is usually a gzipped tarball, but can also be a single gzipped
    # .tex file, or just the PDF if the authors didn't submit source.
    if data.startswith(b'%PDF'):
        print('arxiv_fetch: no source available (arXiv only has the PDF)', file=sys.stderr)
        return

    src_dir.mkdir()
    try:
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            tar.extractall(src_dir, filter='data')   # 'data' filter blocks path traversal etc.
    except tarfile.ReadError:
        if data.startswith(b'\x1f\x8b'):
            data = gzip.decompress(data)
        (src_dir / f'{name}.tex').write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('arxiv_id', help='arXiv identifier, e.g. 2408.07699 or 2408.07699v2')
    arxiv_id = parser.parse_args().arxiv_id

    name = arxiv_id.replace('/', '_')   # old-style ids, e.g. hep-th/9711200
    outdir = pathlib.Path(name)
    if outdir.exists():
        sys.exit(f'arxiv_fetch: {outdir} already exists')

    try:
        meta = get_metadata(arxiv_id)
        print(meta['title'])
        outdir.mkdir()
        write_readme(outdir / 'README.md', arxiv_id, meta)
        (outdir / f'{name}.pdf').write_bytes(fetch(f'https://arxiv.org/pdf/{arxiv_id}'))
        extract_source(fetch(f'https://arxiv.org/e-print/{arxiv_id}'), outdir / 'src', name)
    except urllib.error.URLError as e:
        sys.exit(f'arxiv_fetch: {e}')

    print(f'Wrote {outdir}/')


if __name__ == '__main__':
    main()
