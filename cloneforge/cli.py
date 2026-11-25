"""CloneForge command line.

    cloneforge doctor                      what's installed, what isn't, why
    cloneforge backends [--installed]      the adapter registry
    cloneforge route --lang en --sample 8 --priority accuracy [--commercial]
    cloneforge reference --text "..." --out ref.wav   synthetic test speaker
    cloneforge synth --text "..." --reference ref.wav --out clone.wav
                                   (default backend is the DSP CONTROL —
                                   a prosody-matched baseline, not a clone)
    cloneforge bench --text "..." --reference ref.wav --out-dir bench-out
    cloneforge ui                          optional Gradio UI (pip install .[ui])
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .backends import BACKENDS
from .router import route


def doctor_lines() -> list[str]:
    """Doctor output as lines — shared by the CLI and the regression test.

    Detection goes through Backend.status(), the same probes the bench
    runners use (including the coqui-tts / voxcpm side venvs), so what
    doctor calls INSTALLED is exactly what the bench can run.
    """
    from .bench import CONTROL, category_for
    from .similarity import ecapa_status, embedder_status

    lines = [f"CloneForge {__version__} — backend status"]
    ok, method = embedder_status()
    lines.append(f"- speaker embedder GE2E (similarity) — "
                 f"{'INSTALLED' if ok else 'not installed'}: {method}")
    ok_ec, method_ec = ecapa_status()
    lines.append(f"- speaker embedder ECAPA (similarity) — "
                 f"{'INSTALLED' if ok_ec else 'not installed'}: {method_ec}")
    for b in BACKENDS:
        installed, via = b.status()
        state = "INSTALLED" if installed else "not installed"
        tag = " [CONTROL — not a voice clone]" if category_for(b.id) == CONTROL else ""
        via_txt = f" (via {via})" if installed and via else ""
        lines.append(f"- {b.name} [{b.kind}]{tag} — {state}{via_txt}")
        if not installed and b.install_hint:
            lines.append(f"    install: {b.install_hint}")
        if not b.commercial_ok:
            lines.append(f"    licence warning: weights = {b.licence_weights}")
    return lines


def _cmd_doctor(_args) -> int:
    for line in doctor_lines():
        print(line)
    return 0


def _cmd_backends(args) -> int:
    for b in BACKENDS:
        if args.installed and not b.installed():
            continue
        sim = f"SIM {b.sim_en}" if b.sim_en is not None else "SIM n/a"
        wer = f"WER {b.wer_en}%" if b.wer_en is not None else "WER n/a"
        print(f"{b.id:12s} {b.name:38s} {b.kind:16s} "
              f"min {b.min_sample_s:>4.0f}s  {sim:9s} {wer:10s} "
              f"commercial={'yes' if b.commercial_ok else 'NO'}")
    return 0


def _cmd_route(args) -> int:
    recs, warnings = route(language=args.lang, sample_seconds=args.sample,
                           priority=args.priority, commercial=args.commercial)
    for w in warnings:
        print(f"⚠ {w}")
    if args.commercial:
        print("(commercial filter ON — non-commercial weights excluded)")
    for i, r in enumerate(recs, start=1):
        print(f"{i}. {r.backend.name}  (score {r.score:.1f})")
        for reason in r.reasons:
            print(f"     + {reason}")
        for w in r.warnings:
            print(f"     ! {w}")
    if not recs:
        print("No backend fits. Record a longer reference or relax the filters.")
    return 0


def _cmd_reference(args) -> int:
    from .audio import make_reference

    out = make_reference(args.text, args.out, model_name=args.voice)
    print(f"Synthetic reference written: {out}")
    Path(str(out) + ".txt").write_text(args.text, encoding="utf-8")
    print("Transcript sidecar written (used for pace matching).")
    return 0


def _cmd_synth(args) -> int:
    if args.backend == "voxcpm":
        from .voxcpm import voxcpm_clone

        result = voxcpm_clone(args.text, args.reference, args.out,
                              reference_text=args.reference_text)
        for key, value in result.items():
            print(f"{key}: {value}")
        print("Note: VoxCPM2 is a TTS cloner — it invents timing. Only "
              "voice conversion preserves a real performance's pace.")
        return 0
    if args.backend == "dotstts":
        from .dotstts import dotstts_clone

        result = dotstts_clone(args.text, args.reference, args.out)
        for key, value in result.items():
            print(f"{key}: {value}")
        return 0
    if args.backend == "xtts":
        from .neural import xtts_clone

        result = xtts_clone(args.text, args.reference, args.out,
                            language=args.lang)
        for key, value in result.items():
            print(f"{key}: {value}")
        print("Note: XTTS-v2 is a TTS cloner — it invents timing. Only "
              "voice conversion preserves a real performance's pace. Its "
              "weights are non-commercial (Coqui Public Model Licence).")
        return 0
    if args.backend == "yourtts":
        from .neural import yourtts_clone

        result = yourtts_clone(args.text, args.reference, args.out,
                               language=args.lang)
        for key, value in result.items():
            print(f"{key}: {value}")
        print("Note: YourTTS is a TTS cloner — it invents timing. Only "
              "voice conversion preserves a real performance's pace.")
        return 0
    from .audio import dsp_clone

    result = dsp_clone(args.text, args.reference, args.out,
                       reference_text=args.reference_text)
    for key, value in result.items():
        print(f"{key}: {value}")
    print("Note: this is a CONTROL — not a voice clone (prosody-matched "
          "baseline). For neural cloning, route first "
          "(`cloneforge route`) and run the picked backend; TTS backends "
          "invent timing — only voice conversion preserves real pace.")
    return 0


def _cmd_bench(args) -> int:
    from .bench import report_markdown, run_bench, save_report

    report = run_bench(args.text, args.reference, args.out_dir)
    paths = save_report(report, args.out_dir)
    print(report_markdown(report))
    print(f"Reports saved: {paths}")
    return 0


def _cmd_blindtest(args) -> int:
    from .blindtest import Pair, build_pack, score_pack

    if args.blind_action == "score":
        result = score_pack(args.pack_dir)
        if result["accuracy"] is None:
            print("No answered pairs in the sheet — nothing to score. "
                  "A human listener must fill in the sheet first.")
            return 0
        print(f"Answered {result['answered']}/{result['pairs']} pairs · "
              f"correct {result['correct']} · "
              f"accuracy {result['accuracy']:.1%}")
        for d in result["detail"]:
            mark = "✓" if d["correct"] else ("—" if d["correct"] is None else "✗")
            print(f"  {mark} {d['pair']} ({d['backend']}): clone was "
                  f"{d['clone_side']}, guess {d['guess']}")
        return 0
    pairs = []
    for spec in args.pair:
        parts = spec.split(":", 2)
        if len(parts) != 3:
            print(f"Bad --pair spec {spec!r}: expected backend:reference.wav:clone.wav",
                  file=sys.stderr)
            return 2
        backend, reference, clone = parts
        pairs.append(Pair(pair_id="", reference=reference, clone=clone,
                          backend=backend))
    build_pack(pairs, args.out_dir, seed=args.seed)
    print(f"Blind pack written to {args.out_dir}: sheet.md for the listener, "
          "answer-key.json to keep hidden until scoring.")
    print("No human has scored this pack yet — there is no result until "
          "someone listens and fills in the sheet.")
    return 0


def _cmd_ui(_args) -> int:
    try:
        import gradio  # noqa: F401
    except ImportError:
        print("Gradio is not installed. Run: pip install 'cloneforge[ui]'",
              file=sys.stderr)
        return 2
    from .ui import launch

    launch()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cloneforge", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="show backend install status").set_defaults(
        fn=_cmd_doctor)
    bp = sub.add_parser("backends", help="list the adapter registry")
    bp.add_argument("--installed", action="store_true")
    bp.set_defaults(fn=_cmd_backends)

    rp = sub.add_parser("route", help="pick the best backend, with reasons")
    rp.add_argument("--lang", default="en")
    rp.add_argument("--sample", type=float, default=10.0,
                    help="reference length in seconds")
    rp.add_argument("--priority", default="accuracy",
                    choices=["accuracy", "emotion", "speed", "short-sample", "pace"])
    rp.add_argument("--commercial", action="store_true")
    rp.set_defaults(fn=_cmd_route)

    fp = sub.add_parser("reference", help="generate a synthetic test reference")
    fp.add_argument("--text", required=True)
    fp.add_argument("--out", required=True)
    fp.add_argument("--voice", default="en_US-lessac-medium")
    fp.set_defaults(fn=_cmd_reference)

    sp = sub.add_parser(
        "synth", help="clone a voice (DSP CONTROL baseline, YourTTS, or XTTS-v2)")
    sp.add_argument("--backend", default="dsp",
                    choices=["dsp", "yourtts", "xtts", "voxcpm", "dotstts"])
    sp.add_argument("--lang", default="en")
    sp.add_argument("--text", required=True)
    sp.add_argument("--reference", required=True)
    sp.add_argument("--reference-text", default=None,
                    help="transcript of the reference (enables pace matching)")
    sp.add_argument("--out", required=True)
    sp.set_defaults(fn=_cmd_synth)

    np_ = sub.add_parser("bench", help="benchmark all runnable backends")
    np_.add_argument("--text", required=True)
    np_.add_argument("--reference", required=True)
    np_.add_argument("--out-dir", default="bench-out")
    np_.set_defaults(fn=_cmd_bench)

    bt = sub.add_parser("blindtest", help="build or score a blind listening test")
    bt_sub = bt.add_subparsers(dest="blind_action", required=True)
    bt_build = bt_sub.add_parser("build", help="build a shuffled A/B pack")
    bt_build.add_argument("--pair", action="append", required=True,
                          metavar="BACKEND:REF.wav:CLONE.wav",
                          help="one reference/clone pair (repeatable)")
    bt_build.add_argument("--out-dir", required=True)
    bt_build.add_argument("--seed", type=int, default=None,
                          help="shuffle seed (omit for a random shuffle)")
    bt_score = bt_sub.add_parser("score", help="unblind and score a filled pack")
    bt_score.add_argument("pack_dir")
    bt.set_defaults(fn=_cmd_blindtest)

    sub.add_parser("ui", help="launch the optional Gradio UI").set_defaults(fn=_cmd_ui)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
