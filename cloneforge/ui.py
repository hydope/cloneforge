"""Optional Gradio UI — a thin shell over the CLI paths.

Kept deliberately small: route explanation, DSP-baseline synth, and a bench
runner. All honesty labels from the CLI are preserved in the UI text.
"""

from __future__ import annotations

import tempfile
from pathlib import Path


def launch() -> None:
    import gradio as gr

    from .audio import dsp_clone
    from .router import route

    def do_route(lang, sample, priority, commercial):
        recs, warnings = route(language=lang, sample_seconds=float(sample),
                               priority=priority, commercial=bool(commercial))
        out = [f"⚠ {w}" for w in warnings]
        for i, r in enumerate(recs, start=1):
            out.append(f"{i}. {r.backend.name} (score {r.score:.1f})")
            out += [f"   + {x}" for x in r.reasons]
            out += [f"   ! {x}" for x in r.warnings]
        return "\n".join(out) or "No backend fits."

    def do_synth(text, reference_audio, reference_text):
        if reference_audio is None:
            return None, "Upload a reference WAV first."
        out = Path(tempfile.mkdtemp()) / "clone.wav"
        info = dsp_clone(text, reference_audio, out,
                         reference_text=reference_text or None)
        return str(out), str(info)

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
            gr.Button("Route").click(do_route,
                                     [lang, sample, priority, commercial],
                                     route_out)
        with gr.Tab("Synth (DSP CONTROL — not a voice clone)"):
            text = gr.Textbox(label="Text to speak")
            ref = gr.Audio(type="filepath", label="Reference WAV")
            ref_text = gr.Textbox(label="Reference transcript (enables pace matching)")
            synth_audio = gr.Audio(label="Output")
            synth_info = gr.Textbox(lines=8, label="Measurements")
            gr.Button("Synthesise").click(do_synth, [text, ref, ref_text],
                                          [synth_audio, synth_info])
    demo.launch()
