# -*- coding: utf-8 -*-
"""Differ module.

This module is inspired by difflib.Differ which creates human readable diff
output. Instead of text it outputs html which can be displayed by diff popup
well.
"""
import difflib
import html


def highlight_diff(old_lines, new_lines):
    """Generate the html string with highlighted diff."""
    return ''.join(_highlight_diff(old_lines, new_lines))


def _highlight_diff(a, b):
    # begin of mdpopups code view
    yield '<div class="highlight">'
    cruncher = difflib.SequenceMatcher(None, a, b, False)
    for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
        if tag == 'replace':
            g = _fancy_replace(a, alo, ahi, b, blo, bhi)
        elif tag == 'delete':
            g = _dump_lines('del', a, alo, ahi)
        elif tag == 'insert':
            g = _dump_lines('ins', b, blo, bhi)
        elif tag == 'equal':
            g = _dump_lines(None, a, alo, ahi)
        else:
            raise ValueError('unknown tag {0}'.format(tag))
        yield from g
    # end of mdpopups code view
    yield '</div>'


def _plain_replace(a, alo, ahi, b, blo, bhi):
    assert alo < ahi and blo < bhi
    # dump the shorter block first -- reduces the burden on short-term
    # memory if the blocks are of very different sizes
    if bhi - blo < ahi - alo:
        first = _dump_lines('chg-ins', b, blo, bhi)
        second = _dump_lines('chg-del', a, alo, ahi)
    else:
        first = _dump_lines('chg-del', a, alo, ahi)
        second = _dump_lines('chg-ins', b, blo, bhi)

    for g in first, second:
        yield from g


def _fancy_replace(a, alo, ahi, b, blo, bhi):
    """Generate comparison results for a same-tagged range."""

    # don't synch up unless the lines have a similarity score of at
    # least cutoff; best_ratio tracks the best score seen so far
    best_ratio, cutoff = 0.54, 0.55
    cruncher = difflib.SequenceMatcher()
    eqi, eqj = None, None   # 1st indices of equal lines (if any)

    # search for the pair that matches best without being identical
    # (identical lines must be junk lines, & we don't want to synch up
    # on junk -- unless we have to)
    for j in range(blo, bhi):
        bj = b[j]
        cruncher.set_seq2(bj)
        for i in range(alo, ahi):
            ai = a[i]
            if ai == bj:
                if eqi is None:
                    eqi, eqj = i, j
                continue
            cruncher.set_seq1(ai)
            # computing similarity is expensive, so use the quick
            # upper bounds first -- have seen this speed up messy
            # compares by a factor of 3.
            # note that ratio() is only expensive to compute the first
            # time it's called on a sequence pair; the expensive part
            # of the computation is cached by cruncher
            if cruncher.real_quick_ratio() > best_ratio and \
                    cruncher.quick_ratio() > best_ratio and \
                    cruncher.ratio() > best_ratio:
                best_ratio, best_i, best_j = cruncher.ratio(), i, j
    if best_ratio < cutoff:
        # no non-identical "pretty close" pair
        if eqi is None:
            # no identical pair either -- treat it as a straight replace
            yield from _plain_replace(a, alo, ahi, b, blo, bhi)
            return
        # no close pair, but an identical pair -- synch up on that
        best_i, best_j, best_ratio = eqi, eqj, 1.0
    else:
        # there's a close pair, so forget the identical pair (if any)
        eqi = None

    # a[best_i] very similar to b[best_j]; eqi is None if they're not
    # identical

    # pump out diffs from before the synch point
    yield from _fancy_helper(a, alo, best_i, b, blo, best_j)

    # pump out the synch point
    yield '<p>'
    if eqi is None:
        aelt, belt = a[best_i], b[best_j]
        cruncher.set_seqs(aelt, belt)
        for tag, ai1, ai2, bj1, bj2 in cruncher.get_opcodes():
            if tag == 'replace':
                yield from _dump_chunk('chg-del', aelt[ai1:ai2])
                yield from _dump_chunk('chg-ins', belt[bj1:bj2])
            elif tag == 'delete':
                yield from _dump_chunk('del', aelt[ai1:ai2])
            elif tag == 'insert':
                yield from _dump_chunk('ins', belt[bj1:bj2])
            elif tag == 'equal':
                yield from _dump_chunk(None, belt[bj1:bj2])
            else:
                raise ValueError('unknown tag {0}'.format(tag))
    else:
        yield from _dump_chunk(None, a[best_i])
    yield '</p>'

    # pump out diffs from after the synch point
    yield from _fancy_helper(a, best_i+1, ahi, b, best_j+1, bhi)


def _fancy_helper(a, alo, ahi, b, blo, bhi):
    if alo < ahi:
        if blo < bhi:
            g = _fancy_replace(a, alo, ahi, b, blo, bhi)
        else:
            g = _dump_lines('del', a, alo, ahi)
    elif blo < bhi:
        g = _dump_lines('ins', b, blo, bhi)
    else:
        g = []

    yield from g


def _dump_lines(tag, x, lo, hi):
    """Generate comparison results for a same-tagged range."""
    for l in x[lo:hi]:
        yield from _dump_line(tag, l)


def _dump_line(tag, x):
    """Generate comparison results for a same-tagged range."""
    yield '<p>'
    yield from _dump_chunk(tag, x)
    yield '<p>'


def _dump_chunk(tag, x):
    """Generate comparison results for a same-tagged range."""
    if tag:
        yield ''.join(('<span class="hi-', tag, '">'))
    yield from _to_html(x)
    if tag:
        yield '</span>'


def _to_html(text):
    yield html.escape(text, quote=False).replace('  ', '&nbsp;&nbsp;') or '↵'
