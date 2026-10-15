"""DOM text serialization: preserve inline adjacency, separate structural blocks."""
import re

from bs4.element import Comment, Declaration, Doctype, NavigableString, ProcessingInstruction, Tag

_SKIP = {'script', 'style', 'noscript', 'svg', 'template', 'head'}
_BLOCKS = {'address', 'article', 'blockquote', 'dd', 'div', 'dl', 'dt', 'fieldset',
    'figcaption', 'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'li', 'main',
    'ol', 'p', 'pre', 'section', 'table', 'tr', 'ul'}


def render_dom_text(node: Tag) -> str:
    """Serialize without mutating the DOM, rewriting punctuation or guessing spaces.

    This is not browser layout/CSS evaluation. Source whitespace in text nodes is
    collapsed; inline tag boundaries introduce no separator. Blocks use blank
    lines, br a single newline, and table cells an explicit space.
    """
    chunks = []

    def visit(current):
        if isinstance(current, (Comment, Declaration, Doctype, ProcessingInstruction)):
            return
        if isinstance(current, NavigableString):
            chunks.append(re.sub(r'\s+', ' ', str(current)))
            return
        if not isinstance(current, Tag) or current.name in _SKIP:
            return
        if current.name == 'br':
            chunks.append('\n')
            return
        boundary = '\n\n' if current.name in _BLOCKS else ' ' if current.name in {'td', 'th'} else ''
        chunks.append(boundary)
        for child in current.children:
            visit(child)
        chunks.append(boundary)

    visit(node)
    lines = [re.sub(r'[^\S\n]+', ' ', line).strip() for line in ''.join(chunks).split('\n')]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()
