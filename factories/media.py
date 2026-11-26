"""Render and verify an offline Arabic animated lesson."""

import argparse
from array import array
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from hashlib import file_digest
import json
import math
from pathlib import Path
from random import Random
import shutil
import subprocess
import sys
import tempfile
import wave


WIDTH = 768
HEIGHT = 432
FPS = 24
SAMPLE_RATE = 48_000
STAGE_SECONDS = 3
TITLE = "دورة الماء"
STAGES = (
    ("التبخّر", "تسخّن الشمس الماء، فيتحوّل بعضه إلى بخار."),
    ("التكاثف", "يبرد بخار الماء، فتتكوّن قطرات صغيرة في السحب."),
    ("الهطول", "تكبر القطرات، فتسقط مطرًا عندما تصبح ثقيلة."),
    ("التجمّع", "يتجمّع الماء في الأنهار والبحار، وتستمر الدورة."),
)
DURATION = len(STAGES) * STAGE_SECONDS
DEFAULT_FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
SHADOW_STAGE_SECONDS = 4
SHADOW_STAGES = (
    ("الصباح", "عندما تكون الشمس منخفضةً، يمتدّ الظل على الأرض."),
    ("قرب الظهر", "كلّما ارتفعت الشمس، قَصُرَ الظل."),
    ("بعد الظهر", "حين تنخفض الشمس من الجهة الأخرى، يطول الظل ويتغيّر اتجاهه."),
    ("جرّب وتوقّع", "كيف يتغيّر طول الظل إذا خفضتَ مصباحًا يضيء جسمًا ثابتًا؟"),
)


def span(frame, y, start, end, color):
    if 0 <= y < HEIGHT:
        start = max(0, start)
        end = min(WIDTH, end)
        if end > start:
            offset = (y * WIDTH + start) * 3
            frame[offset:offset + (end - start) * 3] = color * (end - start)


@lru_cache(maxsize=128)
def ellipse_rows(rx, ry):
    return tuple(
        (dy, round(rx * math.sqrt(1 - (dy / ry) ** 2)))
        for dy in range(-ry, ry + 1)
    )


def ellipse(frame, x, y, rx, ry, color):
    for dy, dx in ellipse_rows(rx, ry):
        span(frame, y + dy, x - dx, x + dx + 1, color)


def mountain(frame, x, peak, left, right, color):
    for y in range(peak, 260):
        progress = (y - peak) / (260 - peak)
        span(frame, y, round(x - left * progress), round(x + right * progress), color)


def background():
    frame = bytearray()
    for y in range(HEIGHT):
        if y < 260:
            color = bytes((42 + y // 10, 94 + y // 6, 143 + y // 7))
        elif y < 318:
            color = bytes((14, 103 - (y - 260) // 2, 134 - (y - 260) // 3))
        else:
            color = b"#\x35\x4c"
        frame.extend(color * WIDTH)
    mountain(frame, 493, 137, 184, 190, b"\x51\x7b\x91")
    mountain(frame, 657, 127, 188, 151, b"\x60\x89\xa0")
    mountain(frame, 721, 182, 210, 120, b"\x38\x68\x79")
    for x, y, rx in ((86, 264, 75), (291, 270, 90), (492, 264, 42), (727, 266, 61)):
        ellipse(frame, x, y, rx, 2, b"\x24\x9c\xab")
    return frame


def drop(frame, x, y, color):
    for dy in range(-10, 0):
        width = (dy + 11) // 2
        span(frame, y + dy, x - width, x + width + 1, color)
    ellipse(frame, x, y, 6, 6, color)


def render_frame(base, index):
    frame = bytearray(base)
    stage, step = divmod(index, STAGE_SECONDS * FPS)
    progress = step / (STAGE_SECONDS * FPS)
    sun_size = round(37 + 3 * math.sin(math.tau * progress)) if stage == 0 else 37
    ellipse(frame, 129, 129, 55, 55, b"\x71\x99\xa5")
    ellipse(frame, 129, 129, 45, 45, b"\xd8\xbc\x80")
    ellipse(frame, 129, 129, sun_size, sun_size, b"\xff\xd3\x70")

    cloud_scale = (0.65, 0.65 + 0.35 * progress, 1.0, 0.85)[stage]
    cloud_color = b"\xb8\xd2\xdc" if stage == 2 else b"\xec\xf6\xf5"
    for x, y, rx, ry in ((550, 158, 75, 23), (507, 147, 35, 29), (551, 132, 45, 42),
                         (597, 148, 39, 31)):
        ellipse(frame, x, y, round(rx * cloud_scale), round(ry * cloud_scale), cloud_color)

    if stage < 2:
        for particle in range(7):
            rise = (progress + particle / 7) % 1
            start_x = 275 + (particle % 3) * 29
            x = start_x + round((495 - start_x) * rise)
            y = 250 - round(102 * rise) + (particle % 3) * 4
            size = 4 + round(5 * rise)
            ellipse(frame, x, y, size, size, b"\xbd\xe6\xe8")
    if stage == 2:
        for particle in range(8):
            fall = (progress * 2 + particle / 8) % 1
            drop(frame, 470 + particle * 22 - round(12 * fall), 183 + round(68 * fall),
                 b"\x77\xe2\xf8")
    if stage >= 2:
        for ripple in range(4):
            radius = 8 + round(38 * ((progress * 2 + ripple / 4) % 1))
            x = 450 + 69 * ripple
            y = 280 + (ripple % 2) * 13
            ellipse(frame, x, y, radius, 4, b"\x69\xca\xd5")
            ellipse(frame, x, y, radius - 3, 2, b"\x0e\x50\x72")
    span(frame, 318, 0, WIDTH, b"\x49\xac\xb9")
    for step in range(len(STAGES)):
        color = b"\x7c\xde\xe4" if step == stage else b"\x5a\x71\x85"
        ellipse(frame, 411 - step * 18, 410, 4, 4, color)
    return frame


def shadow_background():
    frame = bytearray()
    for y in range(HEIGHT):
        if y < 233:
            color = bytes((81 + y // 6, 101 + y // 8, 147 + y // 9))
        elif y < 319:
            color = bytes((69 + (y - 233) // 3, 80 + (y - 233) // 6, 98))
        else:
            color = b"\x20\x2c\x40"
        frame.extend(color * WIDTH)
    for x, y, rx, ry in ((49, 236, 139, 29), (201, 235, 155, 24), (629, 240, 163, 37),
                         (736, 246, 112, 30)):
        ellipse(frame, x, y, rx, ry, b"\x50\x5d\x73")
    for y in (267, 287, 311):
        span(frame, y, 0, WIDTH, b"\x61\x68\x78")
    for x in range(72, WIDTH, 48):
        span(frame, 290, x, x + 5, b"\xa6\x9d\x99")
    span(frame, 318, 0, WIDTH, b"\xe1\xac\x70")
    return frame


def shadow_geometry(daylight):
    """Project a vertical stick's shadow onto an oblique ground plane."""
    azimuth = math.pi * daylight
    elevation = math.radians(24 + 52 * math.sin(azimuth))
    length = 102 / math.tan(elevation)
    sun = (384 - round(267 * math.cos(azimuth)), 226 - round(138 * math.sin(elevation)))
    tip = (384 + round(length * math.cos(azimuth)), 274 + round(0.44 * length * math.sin(azimuth)))
    return sun, tip, length


def dotted_line(frame, start, end, count, color):
    x, y = start
    dx, dy = end[0] - x, end[1] - y
    for dot in range(1, count):
        ellipse(frame, x + round(dx * dot / count), y + round(dy * dot / count), 2, 2, color)


def render_shadows(base, index):
    frame = bytearray(base)
    stage, step = divmod(index, SHADOW_STAGE_SECONDS * FPS)
    progress = step / (SHADOW_STAGE_SECONDS * FPS)
    # Keep the sun moving through the shot boundaries, and hold the exercise for reading.
    start, end = ((0.0, 0.11), (0.11, 0.5), (0.5, 0.98), (0.98, 0.98))[stage]
    sun, tip, length = shadow_geometry(start + (end - start) * progress)
    x, y = sun
    ellipse(frame, x, y, 41, 41, b"\xc1\x91\x74")
    ellipse(frame, x, y, 34, 34, b"\xf4\xb3\x63")
    ellipse(frame, x, y, 28, 28, b"\xff\xd8\x85")

    anchor = (384, 274)
    tx, ty = tip
    # Ground stroke tapers from the stick to the projected tip.
    for point in range(41):
        along = point / 40
        radius = round(6 - 3 * along)
        ellipse(frame, round(anchor[0] + (tx - anchor[0]) * along),
                round(anchor[1] + (ty - anchor[1]) * along), radius, 4, b"\x1b\x22\x32")
    dotted_line(frame, (384, 172), tip, max(7, round(length / 17)), b"\xf0\xc5\x80")
    for y in range(172, 275):
        span(frame, y, 378, 390, b"\xe9\xee\xd9")
        span(frame, y, 386, 390, b"\xb0\x83\x64")
    ellipse(frame, 384, 171, 9, 9, b"\xff\xb3\x60")
    radius = 6 + round(2 * math.sin(progress * math.tau))
    ellipse(frame, tx, ty, radius, 3, b"\x8c\xc2\xc8")
    for marker in range(len(SHADOW_STAGES)):
        color = b"\xf5\xb6\x6e" if marker == stage else b"\x68\x76\x8a"
        ellipse(frame, 411 - marker * 18, 410, 4, 4, color)
    return frame


@dataclass(frozen=True)
class Lesson:
    slug: str
    title: str
    stages: tuple[tuple[str, str], ...]
    stage_seconds: int
    background: Callable[[], bytearray]
    frame: Callable[[bytearray, int], bytearray]
    effects: tuple[tuple[int, int, float], ...]

    @property
    def duration(self):
        return len(self.stages) * self.stage_seconds


WATER_CYCLE = Lesson(
    "water-cycle", TITLE, STAGES, STAGE_SECONDS, background, render_frame,
    ((260, 510, 0.8), (660, -170, 0.65), (560, -310, 1.85), (360, -230, 1.0)),
)
MOVING_SHADOWS = Lesson(
    "moving-shadows", "كيف يتغيّر طول الظل؟", SHADOW_STAGES, SHADOW_STAGE_SECONDS,
    shadow_background, render_shadows,
    ((156, 186, 0.55), (370, 255, 0.7), (310, -208, 0.75), (523, 70, 0.45)),
)
LESSONS = {lesson.slug: lesson for lesson in (WATER_CYCLE, MOVING_SHADOWS)}


def timestamp(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"00:{minutes:02}:{seconds:02}.000"


def caption_filters(work, lesson):
    caption_file = ["WEBVTT", ""]
    (work / "title.txt").write_text(f"\u200f{lesson.title}\u200f", encoding="utf-8")
    style = "fontfile=arabic.ttf:expansion=none:text_shaping=1:x=(w-tw)/2"
    filters = [f"drawtext={style}:textfile=title.txt:fontcolor=white:fontsize=38:y=17"]
    for index, (heading, body) in enumerate(lesson.stages):
        start = index * lesson.stage_seconds
        end = start + lesson.stage_seconds
        caption_file.extend((f"{timestamp(start)} --> {timestamp(end)}", heading, body, ""))
        enabled = f"'gte(t,{start})*lt(t,{end})'"
        for label, content, size, y, color in (
            ("heading", heading, 25, 328, "0x9ae5e9"),
            ("body", body, 23, 373, "0xf4f8fb"),
        ):
            name = f"{label}-{index}.txt"
            # Right-to-left marks keep neutral punctuation at the end of the Arabic line.
            (work / name).write_text(f"\u200f{content}\u200f", encoding="utf-8")
            filters.append(
                f"drawtext={style}:textfile={name}:fontcolor={color}:fontsize={size}"
                f":y={y}:enable={enabled}"
            )
    (work / "captions.vtt").write_text("\n".join(caption_file), encoding="utf-8")
    return ",".join(filters)


def write_effects(path, lesson):
    samples = array("h", [0]) * (lesson.duration * SAMPLE_RATE)
    random = Random(42)
    for stage, (frequency, sweep, length) in enumerate(lesson.effects):
        start = round((stage * lesson.stage_seconds + 0.15) * SAMPLE_RATE)
        for index in range(round(length * SAMPLE_RATE)):
            time = index / SAMPLE_RATE
            envelope = min(1, time * 30) * (1 - time / length) ** 2
            oscillation = math.sin(math.tau * (frequency * time + sweep * time * time / 2))
            noise = random.uniform(-1, 1)
            samples[start + index] = round(4_000 * envelope * (0.7 * oscillation + 0.3 * noise))
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
        output.writeframes(samples.tobytes())


def encode(ffmpeg, work, video_filters, narration, lesson):
    command = [
        ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}",
        "-framerate", str(FPS), "-i", "pipe:0", "-i", "effects.wav",
        "-filter_threads", "1",
    ]
    if narration:
        command.extend((
            "-f", "wav", "-i", str(narration),
            "-filter_complex",
            "[2:a]aresample=48000,aformat=channel_layouts=mono,apad[narration];"
            "[1:a]volume=0.25[effects];"
            "[effects][narration]amix=inputs=2:duration=first:normalize=0,"
            "alimiter=limit=0.95:level=0[mixed]",
            "-map", "0:v", "-map", "[mixed]",
        ))
    else:
        command.extend(("-map", "0:v", "-map", "1:a"))
    command.extend((
        "-vf", video_filters, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-threads:v", "2",
        "-c:a", "aac", "-ar", str(SAMPLE_RATE), "-t", str(lesson.duration), "-map_metadata", "-1",
        "-movflags", "+faststart", f"{lesson.slug}.mp4",
    ))
    with tempfile.TemporaryFile() as diagnostics:
        with subprocess.Popen(command, cwd=work, stdin=subprocess.PIPE, stderr=diagnostics) as job:
            try:
                with job.stdin as frames:
                    base = lesson.background()
                    for index in range(lesson.duration * FPS):
                        frames.write(lesson.frame(base, index))
            except BrokenPipeError:
                pass
            if job.wait():
                diagnostics.seek(0)
                raise RuntimeError(f"FFmpeg encode failed: {diagnostics.read().decode().strip()}")


def verify(ffprobe, video, duration=DURATION):
    result = subprocess.run(
        [
            ffprobe, "-v", "error", "-count_frames",
            "-show_entries", "stream=codec_type,codec_name,width,height,nb_read_frames"
            ",sample_rate,channels:format=duration",
            "-of", "json", str(video),
        ],
        check=True, capture_output=True, text=True,
    )
    proof = json.loads(result.stdout)
    streams = {stream["codec_type"]: stream for stream in proof["streams"]}
    visual = streams.get("video", {})
    audio = streams.get("audio", {})
    if (
        set(streams) != {"video", "audio"}
        or len(proof["streams"]) != 2
        or (visual.get("codec_name"), visual.get("width"), visual.get("height"))
        != ("h264", WIDTH, HEIGHT)
        or visual.get("nb_read_frames") != str(duration * FPS)
        or (audio.get("codec_name"), audio.get("sample_rate"), audio.get("channels"))
        != ("aac", str(SAMPLE_RATE), 1)
        or not audio.get("nb_read_frames", "").isdigit()
        or int(audio["nb_read_frames"]) < 1
        or abs(float(proof["format"]["duration"]) - duration) > 1 / FPS
    ):
        raise RuntimeError("Rendered media does not match the lesson's video and audio contract")
    return proof


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def validate_narration(path, duration=DURATION):
    try:
        with wave.open(str(path), "rb") as recording:
            seconds = recording.getnframes() / recording.getframerate()
            if not 0 < seconds <= duration:
                raise ValueError(f"Narration must run for at most {duration} seconds")
    except (EOFError, wave.Error) as error:
        raise ValueError("Narration must be a readable PCM WAV file") from error


def render_lesson(output, font=DEFAULT_FONT, narration=None, *, lesson=WATER_CYCLE):
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("Install FFmpeg with ffprobe, Arabic text shaping, and libx264")
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Lesson output already exists: {output}")
    font = Path(font)
    if not font.is_file():
        raise FileNotFoundError("Provide an Arabic-capable font with --font")
    if narration:
        narration = Path(narration).resolve(strict=True)
        validate_narration(narration, lesson.duration)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".media-", dir=output.parent) as temporary:
        work = Path(temporary)
        package = work / "lesson"
        package.mkdir()
        shutil.copyfile(font, work / "arabic.ttf")
        filters = caption_filters(work, lesson)
        write_effects(work / "effects.wav", lesson)
        encode(ffmpeg, work, filters, narration, lesson)
        video = work / f"{lesson.slug}.mp4"
        proof = verify(ffprobe, video, lesson.duration)
        video.rename(package / video.name)
        captions = work / "captions.vtt"
        captions.rename(package / captions.name)
        manifest = {
            "schema_version": 1,
            "lesson": lesson.slug,
            "language": "ar",
            "title": lesson.title,
            "duration_seconds": lesson.duration,
            "narration": "local_wav" if narration else "absent",
            "stages": [
                {"heading": heading, "start_seconds": index * lesson.stage_seconds}
                for index, (heading, _) in enumerate(lesson.stages)
            ],
            "probe": proof,
            "sha256": {path.name: digest(path) for path in sorted(package.iterdir())},
        }
        (package / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Lesson output already exists: {output}")
        package.rename(output)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--lesson", choices=LESSONS, default=WATER_CYCLE.slug)
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT)
    parser.add_argument("--narration", type=Path, help="Optional local PCM WAV up to the lesson's duration")
    args = parser.parse_args()
    lesson = LESSONS[args.lesson]
    try:
        render_lesson(args.output_dir, args.font, args.narration, lesson=lesson)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")
    print(args.output_dir / f"{lesson.slug}.mp4")


if __name__ == "__main__":
    main()
