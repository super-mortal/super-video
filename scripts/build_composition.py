#!/usr/bin/env python3
"""Build index.html from timeline.json + scenes.json (data-driven; never
hand-write timings).

Design principle: **all visual timing comes from timeline.json** (i.e. the
whisper forced-alignment result). Humans only describe *what* each scene
shows (the ``html`` field in scenes.json); the script injects the timing.
This way audio and visuals can never drift, and captions can never fall out
of sync with the narration.

Usage:
    python build_composition.py timeline.json scenes.json -o index.html \
        --width 1920 --height 1080 [--theme theme.css]
    python build_composition.py .super-video/my-task/audio/timeline.json \
        .super-video/my-task/scenes.json --workdir .super-video/my-task

scenes.json format:
{
  "composition_id": "main",
  "scenes": [
    {"html": "<div class='cover'> ... </div>"},
    ...
  ]
}
  scenes[i].html is paired automatically with that scene's narration line as a
  static whole-sentence caption (no per-word highlight). Scenes with light or
  busy backgrounds should set ``"caption_bg": true`` to get a translucent dark
  box behind the caption; dark scenes (the default) render plain white text.
  Add class="reveal" to child elements for an automatic entrance; class="pop"
  for a pop-in emphasis.

With --workdir the default output becomes <workdir>/composition/index.html.

Dependencies: none beyond the standard library. Run `hyperframes lint`
after generating.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from task_paths import resolve_output


DEFAULT_CSS = r'''
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { margin: 0; overflow: hidden; }
body { background: #07090f; font-family: "Inter", "JetBrains Mono", sans-serif;
  color: #e6edf3; }
[data-composition-id="main"] { width: WIDTHpx; height: HEIGHTpx;
  position: relative; overflow: hidden; }

#bg { position: absolute; inset: 0; z-index: 0; }
#grid { position: absolute; inset: -60px;
  background-image:
    linear-gradient(rgba(88,166,255,0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(88,166,255,0.06) 1px, transparent 1px);
  background-size: 64px 64px; animation: drift 20s linear infinite; }
@keyframes drift { from { transform: translate(0,0);}
  to { transform: translate(64px,64px);} }
.glow { position: absolute; border-radius: 50%; filter: blur(130px); }
#g1 { width: 760px; height: 760px; left: -180px; top: -220px;
  background: radial-gradient(circle, rgba(38,108,255,0.34), transparent 70%); }
#g2 { width: 820px; height: 820px; right: -200px; bottom: -260px;
  background: radial-gradient(circle, rgba(63,185,80,0.22), transparent 70%); }
.particle { position: absolute; border-radius: 50%; background: rgba(88,166,255,0.55); }

.scene { position: absolute; inset: 0; opacity: 0; z-index: 5; }
.cols { position: absolute; top: 190px; left: 50%; transform: translateX(-50%);
  width: 92%; display: flex; justify-content: center; align-items: center;
  gap: 46px; flex-wrap: wrap; }

/* captions (static whole-sentence; no per-word highlight) */
.cap { position: absolute; left: 50%; transform: translateX(-50%); bottom: 74px;
  width: 92%; text-align: center; z-index: 60; }
.cap-box { display: inline-block; font-size: 44px; font-weight: 700; line-height: 1.5;
  color: #f2f6fb; letter-spacing: .02em; padding: 19px 42px; }
/* 浅色/彩色画面场景在 scenes.json 设 "caption_bg": true，字幕加浅黑透明方框；
   暗色场景（默认）不加底板，只留白字 */
.cap.is-boxed .cap-box { background: rgba(0,0,0,.25); backdrop-filter: blur(6px); }
'''

JS_TEMPLATE = r'''
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;
  var t=Math.imul(a^a>>>15,1|a);
  t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
const rand = mulberry32(42);
(function(){ const c=document.getElementById('particles');
  for(let i=0;i<46;i++){ const p=document.createElement('div'); p.className='particle';
    const s=2+Math.floor(rand()*4); p.style.width=s+'px'; p.style.height=s+'px';
    p.style.left=Math.floor(rand()*WIDTH)+'px';
    p.style.top=Math.floor(rand()*HEIGHT)+'px';
    p.style.opacity=(0.14+rand()*0.5).toFixed(2);
    p.dataset.dy=String(-14-Math.floor(rand()*26));
    c.appendChild(p);} })();

window.__timelines = window.__timelines || {};
const tl = gsap.timeline({paused:true});

gsap.utils.toArray('.particle').forEach((p,i)=>{
  tl.to(p,{y:parseFloat(p.dataset.dy)*7,duration:10,
    repeat:Math.max(0,Math.floor(TOTAL/9)-1),ease:'none'},(i%9)*0.7);
});

SCENES.forEach((sc,i)=>{
  tl.to('#scene-'+i,{opacity:1,duration:0.16,ease:'power1.out'},sc.s);
  tl.to('#scene-'+i,{opacity:0,duration:0.18,ease:'power1.in'},sc.e+0.02);
  const reveal_elements = gsap.utils.toArray('#scene-'+i+' .reveal');
  const avail = Math.max(0.8,(sc.e - sc.s) - 1.1);
  const stagger = Math.min(0.5,
    Math.max(0.1, avail/Math.max(1,reveal_elements.length)));
  if(reveal_elements.length) tl.from(reveal_elements,
    {y:46,opacity:0,duration:0.6,stagger:stagger,ease:'power2.out'},sc.s+0.12);
  const pop_elements = gsap.utils.toArray('#scene-'+i+' .pop');
  if(pop_elements.length) tl.from(pop_elements,
    {scale:0.55,opacity:0,duration:0.55,stagger:0.1,ease:'back.out(1.7)'},sc.s+0.5);
});

window.__timelines["main"] = tl;
'''


def build_html_document(
    timeline_data: dict,
    scene_data: dict,
    width: int,
    height: int,
    theme_css: str | None = None,
) -> str:
    """Compose the full index.html document from timeline and scene data.

    Pairs each timeline scene with its scene spec and renders the scene
    blocks plus CSS/JS. Each scene's narration line (timeline scenes[i].text)
    is shown as a static whole-sentence caption. Returns the HTML document.
    """
    composition_id = scene_data.get("composition_id", "main")
    # build_timeline already includes the tail padding; use total as-is.
    total = round(float(timeline_data["total"]), 3)
    timeline_scenes = timeline_data["scenes"]
    scene_specs = scene_data["scenes"]

    css = DEFAULT_CSS.replace("WIDTH", str(width)).replace("HEIGHT", str(height))
    if theme_css:
        css += "\n" + theme_css

    blocks, scenes_js = [], []
    for i, (timed_scene, scene_spec) in enumerate(zip(timeline_scenes, scene_specs)):
        start_sec = round(max(0.0, timed_scene["start"]), 3)
        end_sec = round(timed_scene["end"], 3)
        # 字幕：整句静态显示。浅色/彩色画面场景设 "caption_bg": true 加浅黑方框，
        # 暗色场景（默认）不加底板。
        cap_class = "cap is-boxed" if scene_spec.get("caption_bg", False) else "cap"
        blocks.append(
            f'  <div id="scene-{i}" class="scene clip" data-start="{start_sec}" '
            f'data-duration="{round(end_sec - start_sec, 3)}" data-track-index="1">\n'
            f'{scene_spec["html"]}\n'
            f'    <div class="{cap_class}" id="cap-{i}">'
            f'<div class="cap-box">{timed_scene["text"]}</div></div>\n'
            f'  </div>')
        scenes_js.append('  {s:%s, e:%s}' % (start_sec, end_sec))

    js = (JS_TEMPLATE.replace("WIDTH", str(width)).replace("HEIGHT", str(height))
          .replace("TOTAL", str(total)))
    scenes_js_block = ",\n".join(scenes_js)

    doc = f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
</head>
<body>
<div data-composition-id="{composition_id}" data-start="0" data-duration="{total}"
     data-width="{width}" data-height="{height}">

  <div id="bg">
    <div class="glow" id="g1"></div>
    <div class="glow" id="g2"></div>
    <div id="grid"></div>
    <div id="particles"></div>
  </div>

{chr(10).join(blocks)}

</div>
<style>{css}</style>
<script>
window.TOTAL = {total};
const SCENES = [
{scenes_js_block}
];
{js}
</script>
</body>
</html>
'''
    return doc


def main() -> int:
    """Parse CLI arguments, build the HTML document, and write it to disk."""
    parser = argparse.ArgumentParser(
        description="Build index.html from timeline.json + scenes.json")
    parser.add_argument("timeline", help="timeline.json produced by build_timeline.py")
    parser.add_argument("scenes", help="scenes.json with per-scene html specs")
    parser.add_argument("-o", "--output", default=None,
                        help="output HTML file path (default: "
                             "<workdir>/composition/index.html, or "
                             "./index.html when --workdir is omitted)")
    parser.add_argument("--workdir", default=None,
                        help="Task directory, e.g. .super-video/my-task; when "
                             "set, the default output lands in "
                             "<workdir>/composition/")
    parser.add_argument("--width", type=int, default=1920,
                        help="composition width in px (default: 1920)")
    parser.add_argument("--height", type=int, default=1080,
                        help="composition height in px (default: 1080)")
    parser.add_argument("--theme", default=None,
                        help="extra CSS file appended to the default styles "
                             "(e.g. assets/theme.css)")
    args = parser.parse_args()

    timeline_data = json.loads(Path(args.timeline).read_text(encoding="utf-8"))
    scene_data = json.loads(Path(args.scenes).read_text(encoding="utf-8"))
    timeline_scenes = timeline_data["scenes"]
    scene_specs = scene_data["scenes"]
    if len(timeline_scenes) != len(scene_specs):
        print(f"ERROR: timeline scenes={len(timeline_scenes)} does not match "
              f"scenes.json scenes={len(scene_specs)}", file=sys.stderr)
        return 2

    theme_css = Path(args.theme).read_text(encoding="utf-8") if args.theme else None
    doc = build_html_document(
        timeline_data, scene_data, args.width, args.height, theme_css)

    output_path = resolve_output(args.output, args.workdir, "composition",
                                 "index.html")
    output_path.write_text(doc, encoding="utf-8")
    total = round(float(timeline_data["total"]), 3)
    print(f"{output_path} written: {len(doc)} bytes, "
          f"scenes={len(timeline_scenes)}, total={total}s")
    for i, timed_scene in enumerate(timeline_scenes):
        print(f"  scene-{i}: {timed_scene['start']:.2f}-{timed_scene['end']:.2f}  "
              f"{timed_scene['text'][:24]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
