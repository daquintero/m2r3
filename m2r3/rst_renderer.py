import os
from urllib.parse import urlparse

from docutils.utils import column_width
from mistune.renderers import BaseRenderer

_is_sphinx = False


class RestRenderer(BaseRenderer):
    _include_raw_html = False
    # list_indent_re = re.compile(r"^(\s*(#\.|\*)\s)")
    indent = " " * 3
    list_marker = "{#__rest_list_mark__#}"
    hmarks = {
        1: "=",
        2: "-",
        3: "^",
        4: "~",
        5: '"',
        6: "#",
    }

    def __init__(self, *args, **kwargs):
        self.parse_relative_links = kwargs.pop("parse_relative_links", False)
        self.anonymous_references = kwargs.pop("anonymous_references", False)
        self.use_mermaid = kwargs.pop("use_mermaid", False)
        super(RestRenderer, self).__init__(*args, **kwargs)
        # if not _is_sphinx:
        #    parse_options()
        #    if getattr(options, "parse_relative_links", False):
        #        self.parse_relative_links = options.parse_relative_links
        #    if getattr(options, "anonymous_references", False):
        #       self.anonymous_references = options.anonymous_references

    def finalize(self, data):
        return "".join(filter(lambda x: x is not None, data))

    def _indent_block(self, block):
        return "\n".join(
            self.indent + line if line else "" for line in block.splitlines()
        )

    def _raw_html(self, html):
        self._include_raw_html = True
        return r"\ :raw-html-m2r:`{}`\ ".format(html)

    def block_code(self, code, lang=None):
        if lang == "math":
            first_line = "\n.. math::\n\n"
        elif lang == "mermaid" and self.use_mermaid:
            first_line = "\n.. mermaid::\n\n"
        elif lang:
            first_line = "\n.. code-block:: {}\n\n".format(lang)
        elif _is_sphinx:
            first_line = "\n::\n\n"
        else:
            first_line = "\n.. code-block::\n\n"
        return first_line + self._indent_block(code) + "\n"

    def block_quote(self, text):
        # text includes some empty line
        return "\n..\n\n{}\n\n".format(self._indent_block(text.strip("\n")))

    def block_text(self, text):
        return text

    def block_html(self, html):
        """Rendering block level pure html content.

        :param html: text content of the html snippet.
        """
        return "\n\n.. raw:: html\n\n" + self._indent_block(html) + "\n\n"

    def header(self, text, level, raw=None):
        """Rendering header/heading tags like ``<h1>`` ``<h2>``.

        :param text: rendered text content for the header.
        :param level: a number for the header level, for example: 1.
        :param raw: raw text content of the header.
        """
        return "\n{0}\n{1}\n".format(text, self.hmarks[level] * column_width(text))

    def heading(self, text, level, raw=None):
        """Rendering header/heading tags like ``<h1>`` ``<h2>``.
        :param text: rendered text content for the header.
        :param level: a number for the header level, for example: 1.
        :param raw: raw text content of the header.
        """
        return "\n{0}\n{1}\n".format(text, self.hmarks[level] * column_width(text))

    def thematic_break(self):
        """Rendering method for ``<hr>`` tag."""
        return "\n----\n"

    def list(self, body, ordered, level, start):
        """Rendering list tags like ``<ul>`` and ``<ol>``.

        :param body: body contents of the list.
        :param ordered: whether this list is ordered or not.
        """
        mark = "#. " if ordered else "* "
        lines = body.splitlines()
        for i, line in enumerate(lines):
            if line and not line.startswith(self.list_marker):
                lines[i] = " " * len(mark) + line
        return "\n{}\n".format("\n".join(lines)).replace(self.list_marker, mark)

    def list_item(self, text, level):
        """Rendering list item snippet. Like ``<li>``."""
        return "\n" + self.list_marker + text

    def paragraph(self, text):
        """Rendering paragraph tags. Like ``<p>``."""
        return "\n" + text + "\n"

    def table(self, header, body):
        """Rendering table element. Wrap header and body in it.

        :param header: header part of the table.
        :param body: body part of the table.
        """
        table = "\n.. list-table::\n"
        if header and not header.isspace():
            table = (
                table
                + self.indent
                + ":header-rows: 1\n\n"
                + self._indent_block(header)
                + "\n"
            )
        else:
            table = table + "\n"
        table = table + self._indent_block(body) + "\n\n"
        return table

    def table_row(self, content):
        """Rendering a table row. Like ``<tr>``.

        :param content: content of current table row.
        """
        contents = content.splitlines()
        if not contents:
            return ""
        clist = ["* " + contents[0]]
        if len(contents) > 1:
            for c in contents[1:]:
                clist.append("  " + c)
        return "\n".join(clist) + "\n"

    def table_cell(self, content, **flags):
        """Rendering a table cell. Like ``<th>`` ``<td>``.

        :param content: content of current table cell.
        :param header: whether this is header or not.
        :param align: align of current table cell.
        """
        return "- " + content + "\n"

    def double_emphasis(self, text):
        """Rendering **strong** text.

        :param text: text content for emphasis.
        """
        return r"\ **{}**\ ".format(text)

    def emphasis(self, text):
        """Rendering *emphasis* text.

        :param text: text content for emphasis.
        """
        return r"\ *{}*\ ".format(text)

    def strong(self, text):
        return r"**{}**".format(text)

    def codespan(self, text):
        """Rendering inline `code` text.

        :param text: text content for inline code.
        """
        if "``" not in text:
            return r"\ ``{}``\ ".format(text)
        else:
            # actually, docutils split spaces in literal
            return self._raw_html(
                '<code class="docutils literal">'
                '<span class="pre">{}</span>'
                "</code>".format(text.replace("`", "&#96;"))
            )

    def linebreak(self):
        """Rendering line break like ``<br>``."""
        if self.options.get("use_xhtml"):
            return self._raw_html("<br />") + "\n"
        return self._raw_html("<br>") + "\n"

    def strikethrough(self, text):
        """Rendering ~~strikethrough~~ text.

        :param text: text content for strikethrough.
        """
        return self._raw_html("<del>{}</del>".format(text))

    def text(self, text):
        """Rendering unformatted text.

        :param text: text content.
        """
        return text

    def autolink(self, link, is_email=False):
        """Rendering a given link or email address.

        :param link: link content or email address.
        :param is_email: whether this is an email or not.
        """
        return link

    def link(self, link, title, text):
        """Rendering a given link with content and title.

        :param link: href link for ``<a>`` tag.
        :param title: title content for `title` attribute.
        :param text: text content for description.
        """
        if self.anonymous_references:
            underscore = "__"
        else:
            underscore = "_"
        if title:
            return self._raw_html(
                '<a href="{link}" title="{title}">{title}</a>'.format(
                    link=link, title=title, text=text
                )
            )
        if not self.parse_relative_links:
            return r"\ `{text} <{target}>`{underscore}\ ".format(
                target=link, text=text, underscore=underscore
            )
        else:
            url_info = urlparse(link)
            if url_info.scheme:
                return r"\ `{text} <{target}>`{underscore}\ ".format(
                    target=link, text=text, underscore=underscore
                )
            else:
                link_type = "doc"
                anchor = url_info.fragment
                if url_info.fragment:
                    if url_info.path:
                        # Can't link to anchors via doc directive.
                        anchor = ""
                    else:
                        # Example: [text](#anchor)
                        link_type = "ref"
                doc_link = "{doc_name}{anchor}".format(
                    # splittext approach works whether or not path is set. It
                    # will return an empty string if unset, which leads to
                    # anchor only ref.
                    doc_name=os.path.splitext(url_info.path)[0],
                    anchor=anchor,
                )
                return r"\ :{link_type}:`{text} <{doc_link}>`\ ".format(
                    link_type=link_type, doc_link=doc_link, text=text
                )

    def image(self, src, title, text):
        """Rendering a image with title and text.

        :param src: source link of the image.
        :param title: title text of the image.
        :param text: alt text of the image.
        """
        # rst does not support title option
        # and I couldn't find title attribute in HTML standard
        return "\n".join(
            [
                "",
                ".. image:: {}".format(src),
                "   :target: {}".format(src),
                "   :alt: {}".format(text),
                "",
            ]
        )

    def inline_html(self, html):
        """Rendering span level pure html content.

        :param html: text content of the html snippet.
        """
        return self._raw_html(html)

    def newline(self):
        """Rendering newline element."""
        return ""

    def footnote_ref(self, key, index):
        """Rendering the ref anchor of a footnote.

        :param key: identity key for the footnote.
        :param index: the index count of current footnote.
        """
        return r"\ [#fn-{}]_\ ".format(key)

    def footnote_item(self, key, text):
        """Rendering a footnote item.

        :param key: identity key for the footnote.
        :param text: text content of the footnote.
        """
        return ".. [#fn-{0}] {1}\n".format(key, text.strip())

    def footnotes(self, text):
        """Wrapper for all footnotes.

        :param text: contents of all footnotes.
        """
        if text:
            return "\n\n" + text
        else:
            return ""

    """Below outputs are for rst."""

    def image_link(self, url, target, alt):
        return "\n".join(
            [
                "",
                ".. image:: {}".format(url),
                "   :target: {}".format(target),
                "   :alt: {}".format(alt),
                "",
            ]
        )

    def rest_role(self, text):
        return text

    def rest_link(self, text):
        return text

    def inline_math(self, math):
        """Extension of recommonmark."""
        return r":math:`{}`".format(math)

    def eol_literal_marker(self, marker):
        """Extension of recommonmark."""
        return marker

    def directive(self, text):
        return "\n" + text

    def rest_code_block(self, text):
        return "\n\n"
