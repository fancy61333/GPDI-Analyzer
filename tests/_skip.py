# -*- coding: utf-8 -*-
"""Shared guard for the tests that need assets this repository does not carry.

The graded character inventory and the 82-poem reference figures are not
distributed (see the README section "What is not included"). A checkout that
has neither should report "skipped" rather than crash with FileNotFoundError,
so the same suite runs in a private working copy and in a public clone.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))


def require(*rel_paths, **kwargs):
    """Exit 0 with a skip notice if any required asset is missing."""
    missing = [p for p in rel_paths if not os.path.exists(os.path.join(ROOT, p))]

    if kwargs.get('inventory', True):
        sys.path.insert(0, os.path.join(ROOT, 'core'))
        import gpdi
        if gpdi.find_inventory() is None:
            missing.append('the graded character inventory')

    if missing:
        print('SKIPPED - not available here: %s' % ', '.join(missing))
        print('This test needs assets the repository does not distribute; '
              'see the README section "What is not included".')
        sys.exit(0)
