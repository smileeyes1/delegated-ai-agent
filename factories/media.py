"""Render and verify the offline Arabic water-cycle lesson."""

import argparse
from array import array
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


def timestamp(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"00:{minutes:02}:{seconds:02}.000"


def caption_filters(work):
    caption_file = ["WEBVTT", ""]
    (work / "title.txt").write_text(TITLE, encoding="utf-8")
    style = "fontfile=arabic.ttf:expansion=none:text_shaping=1:x=(w-tw)/2"
    filters = [f"drawtext={style}:textfile=title.txt:fontcolor=white:fontsize=38:y=17"]
    for index, (heading, body) in enumerate(STAGES):
        start = index * STAGE_SECONDS
        end = start + STAGE_SECONDS
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


def write_effects(path):
    samples = array("h", [0]) * (DURATION * SAMPLE_RATE)
    random = Random(42)
    for stage, (frequency, sweep, length) in enumerate(
        ((260, 510, 0.8), (660, -170, 0.65), (560, -310, 1.85), (360, -230, 1.0))
    ):
        start = round((stage * STAGE_SECONDS + 0.15) * SAMPLE_RATE)
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


def encode(ffmpeg, work, video_filters, narration):
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
        "-c:a", "aac", "-ar", str(SAMPLE_RATE), "-t", str(DURATION), "-map_metadata", "-1",
        "-movflags", "+faststart", "water-cycle.mp4",
    ))
    with tempfile.TemporaryFile() as diagnostics:
        with subprocess.Popen(command, cwd=work, stdin=subprocess.PIPE, stderr=diagnostics) as job:
            try:
                with job.stdin as frames:
                    base = background()
                    for index in range(DURATION * FPS):
                        frames.write(render_frame(base, index))
            except BrokenPipeError:
                pass
            if job.wait():
                diagnostics.seek(0)
                raise RuntimeError(f"FFmpeg encode failed: {diagnostics.read().decode().strip()}")


def verify(ffprobe, video):
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
        or visual.get("nb_read_frames") != str(DURATION * FPS)
        or (audio.get("codec_name"), audio.get("sample_rate"), audio.get("channels"))
        != ("aac", str(SAMPLE_RATE), 1)
        or not audio.get("nb_read_frames", "").isdigit()
        or int(audio["nb_read_frames"]) < 1
        or abs(float(proof["format"]["duration"]) - DURATION) > 1 / FPS
    ):
        raise RuntimeError("Rendered media does not match the lesson's video and audio contract")
    return proof


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def validate_narration(path):
    try:
        with wave.open(str(path), "rb") as recording:
            seconds = recording.getnframes() / recording.getframerate()
            if not 0 < seconds <= DURATION:
                raise ValueError(f"Narration must run for at most {DURATION} seconds")
    except (EOFError, wave.Error) as error:
        raise ValueError("Narration must be a readable PCM WAV file") from error


def render_lesson(output, font=DEFAULT_FONT, narration=None):
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
        validate_narration(narration)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".media-", dir=output.parent) as temporary:
        work = Path(temporary)
        package = work / "lesson"
        package.mkdir()
        shutil.copyfile(font, work / "arabic.ttf")
        filters = caption_filters(work)
        write_effects(work / "effects.wav")
        encode(ffmpeg, work, filters, narration)
        video = work / "water-cycle.mp4"
        proof = verify(ffprobe, video)
        video.rename(package / video.name)
        captions = work / "captions.vtt"
        captions.rename(package / captions.name)
        manifest = {
            "schema_version": 1,
            "lesson": "water-cycle",
            "language": "ar",
            "title": TITLE,
            "duration_seconds": DURATION,
            "narration": "local_wav" if narration else "absent",
            "stages": [
                {"heading": heading, "start_seconds": index * STAGE_SECONDS}
                for index, (heading, _) in enumerate(STAGES)
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
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT)
    parser.add_argument("--narration", type=Path, help="Optional local PCM WAV up to 12 seconds")
    args = parser.parse_args()
    try:
        render_lesson(args.output_dir, args.font, args.narration)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")
    print(args.output_dir / "water-cycle.mp4")


if __name__ == "__main__":
    main()
