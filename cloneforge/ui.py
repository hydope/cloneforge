"""Optional Gradio UI — a thin shell over the CLI paths.

The two operations live at module level (route_text, synth_dsp) so tests
can exercise the UI's own function layer without a browser; launch()
only wires them into Gradio widgets. All honesty labels from the CLI
are preserved in the UI text.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _sanitize_proxy_env() -> None:
    """Make NO_PROXY safe for httpx before gradio imports it.

    Measured failure (v0.3 round, this VM): gradio 6.x creates an
    httpx.Client at import time; httpx parses NO_PROXY, and bracketed
    IPv6 entries such as `[::1]` crash it with
    `httpx.InvalidURL: Invalid port: ':1]'` — gradio cannot even be
    imported. Dropping bracketed IPv6 literals from NO_PROXY/no_proxy
    (localhost names stay) fixes the import without touching the proxy
    itself. Only this process's environment is modified.
    """
    for var in ("NO_PROXY", "no_proxy"):
        value = os.environ.get(var)
        if not value:
            continue
        kept = [p for p in value.split(",")
                if p.strip() and not p.strip().startswith("[")]
        os.environ[var] = ",".join(kept)


def gradio_available() -> tuple[bool, str]:
    """(available, reason) — sanitises the env, then probes the import."""
    _sanitize_proxy_env()
    try:
        import gradio  # noqa: F401

        return True, "gradio importable"
    except ImportError:
        return False, "gradio not installed (pip install 'cloneforge[ui]')"



def route_text(lang, sample, priority, commercial) -> str:
    """The Route tab's logic: ranked backends with reasons and warnings."""
    from .router import route

    recs, warnings = route(language=lang, sample_seconds=float(sample),
                           priority=priority, commercial=bool(commercial))
    out = [f"⚠ {w}" for w in warnings]
    for i, r in enumerate(recs, start=1):
        out.append(f"{i}. {r.backend.name} (score {r.score:.1f})")
        out += [f"   + {x}" for x in r.reasons]
        out += [f"   ! {x}" for x in r.warnings]
    return "\n".join(out) or "No backend fits."


def synth_dsp(text, reference_audio, reference_text):
    """The Synth tab's logic: DSP CONTROL synth (not a voice clone)."""
    from .audio import dsp_clone

    if reference_audio is None:
        return None, "Upload a reference WAV first."
    out = Path(tempfile.mkdtemp()) / "clone.wav"
    info = dsp_clone(text, reference_audio, out,
                     reference_text=reference_text or None)
    return str(out), str(info)


def launch(server_port: int = 7860, share: bool = False) -> None:
    _sanitize_proxy_env()
    import gradio as gr

    with gr.Blocks(title="CloneForge") as demo:
        gr.Markdown(
            "# CloneForge\nA meta-engine, not a model. It routes to the best "
            "free local backend and benchmarks them honestly — no 100% "
            "claims, no invented numbers. Urdu and other unverified "
            "languages are flagged, not faked.")
        with gr.Tab("Route"):
            lang = gr.Textbox(value="en", label="Language (ISO code)")
            sample = gr.Number(value=10, label="Reference seconds")
            priority = gr.Dropdown(
                ["accuracy", "emotion", "speed", "short-sample", "pace"],
                value="accuracy", label="Priority")
            commercial = gr.Checkbox(label="Commercial use")
            route_out = gr.Textbox(lines=14, label="Recommendation")
            gr.Button("Route").click(route_text,
                                     [lang, sample, priority, commercial],
                                     route_out)
        with gr.Tab("Synth (DSP CONTROL — not a voice clone)"):
            text = gr.Textbox(label="Text to speak")
            ref = gr.Audio(type="filepath", label="Reference WAV")
            ref_text = gr.Textbox(label="Reference transcript (enables pace matching)")
            synth_audio = gr.Audio(label="Output")
            synth_info = gr.Textbox(lines=8, label="Measurements")
            gr.Button("Synthesise").click(synth_dsp, [text, ref, ref_text],
                                          [synth_audio, synth_info])
    demo.launch(server_port=server_port, share=share)
