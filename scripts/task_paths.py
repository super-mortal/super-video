"""Shared helper: resolve pipeline outputs inside a task directory.

Convention
----------
Every artefact of one video job lives under a single task directory::

    .super-video/<task>/
        script.txt      input  narration script (one sentence per line)
        scenes.json     input  per-scene visual spec
        audio/          narration audio, whisper words, timeline.json, bgm
        composition/    generated index.html
        render/         silent visual renders (semi-finished)
        deliver/        finished videos (with audio)

Every pipeline script accepts ``--workdir <task dir>``. When it is given the
script's default output lands in the matching sub-directory, created on
demand. An explicit ``-o/--output`` always wins and is used verbatim. Without
``--workdir`` the legacy behaviour is kept: the output is written relative to
the current working directory.
"""
from __future__ import annotations

from pathlib import Path


def resolve_output(explicit, workdir, subdir, name) -> Path:
    """Resolve an output path and create its parent directory.

    Args:
        explicit: Value of ``-o/--output``, or None when not supplied.
        workdir: Value of ``--workdir`` (a task directory), or None.
        subdir: Sub-directory below *workdir* that owns this artefact.
        name: Default file name used when only *workdir* is supplied.

    Returns:
        The output :class:`Path`. When *explicit* is given it is returned
        unchanged; otherwise ``<workdir>/<subdir>/<name>`` is returned;
        with neither, a plain relative ``<name>`` is returned.
    """
    if explicit:
        target = Path(explicit)
    elif workdir:
        target = Path(workdir) / subdir / name
    else:
        return Path(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def task_topic(workdir) -> str:
    """Return the topic label of a task directory, i.e. its base name."""
    return Path(workdir).name
