"""
Encode the rendered PNG frames into an MP4 (H.264) with Blender's built-in FFmpeg.

CLI (recommended, run from the project folder):
  /Applications/Blender.app/Contents/MacOS/Blender -b -P encode_mp4.py
  /Applications/Blender.app/Contents/MacOS/Blender -b -P encode_mp4.py -- <frames_dir> <out.mp4> [fps]

Inside Blender: open this file in the Scripting tab and press Run Script.
"""
import bpy, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FRAMES_DIR = os.path.abspath(argv[0]) if len(argv) > 0 else os.path.join(HERE, "render", "frames")
OUT_FILE   = os.path.abspath(argv[1]) if len(argv) > 1 else os.path.join(HERE, "render", "aluminum_slab.mp4")
FPS        = int(argv[2]) if len(argv) > 2 else 30

frames = sorted(f for f in os.listdir(FRAMES_DIR) if f.lower().endswith(".png"))
frames = [f for f in frames if os.path.getsize(os.path.join(FRAMES_DIR, f)) > 0]  # skip placeholders
if not frames:
    raise SystemExit(f"No PNG frames found in {FRAMES_DIR}")

orig_scene = bpy.context.scene
scn = bpy.data.scenes.new("Encode_MP4")
if bpy.context.window is not None:
    bpy.context.window.scene = scn

# frames already carry the AgX look -> encode them as-is (no second view transform)
scn.view_settings.view_transform = 'Standard'
scn.view_settings.look = 'None'
scn.sequencer_colorspace_settings.name = 'sRGB'

first = bpy.data.images.load(os.path.join(FRAMES_DIR, frames[0]))
w, h = first.size
bpy.data.images.remove(first)

r = scn.render
r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
r.fps = FPS
scn.frame_start = 1
scn.frame_end = len(frames)

se = scn.sequence_editor_create()
strip = se.strips.new_image(name="frames", filepath=os.path.join(FRAMES_DIR, frames[0]),
                            channel=1, frame_start=1)
for f in frames[1:]:
    strip.elements.append(f)
strip.colorspace_settings.name = 'sRGB'

ims = r.image_settings
ims.media_type = 'VIDEO'
ims.file_format = 'FFMPEG'
ff = r.ffmpeg
ff.format = 'MPEG4'
ff.codec = 'H264'
ff.constant_rate_factor = 'PERC_LOSSLESS'
ff.ffmpeg_preset = 'BEST'
ff.gopsize = FPS
ff.audio_codec = 'NONE'
r.use_sequencer = True
r.use_compositing = False
r.filepath = OUT_FILE
r.use_file_extension = False

bpy.ops.render.render(animation=True, scene=scn.name)
print(f"[encode_mp4] {len(frames)} frames -> {OUT_FILE}")

if bpy.context.window is not None:   # GUI run: go back and clean up the helper scene
    bpy.context.window.scene = orig_scene
    bpy.data.scenes.remove(scn)
