from array import array
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
import wave

from factories import media


class MediaFactoryTests(unittest.TestCase):
    def test_lesson_script_and_animation_cover_each_stage(self):
        base = media.background()
        for index, (heading, _) in enumerate(media.STAGES):
            with self.subTest(heading=heading):
                frame = index * media.STAGE_SECONDS * media.FPS
                self.assertNotEqual(media.render_frame(base, frame), media.render_frame(base, frame + 12))

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe") and media.DEFAULT_FONT.is_file(),
        "FFmpeg, ffprobe and the default Arabic-capable font are required",
    )
    def test_render_decodes_with_audio_and_preserves_verified_output(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            narration = root / "fixture.wav"
            with wave.open(str(narration), "wb") as audio:
                audio.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
                cycle = b"\x00\x08" * 4 + b"\x00\xf8" * 4
                audio.writeframes(cycle * 1000)

            output = root / "lesson"
            subprocess.run(
                [
                    sys.executable, "-m", "factories.media", "--output-dir", str(output),
                    "--narration", str(narration),
                ],
                cwd=Path(__file__).resolve().parents[1],
                check=True, capture_output=True, text=True,
            )
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["language"], "ar")
            self.assertEqual(manifest["narration"], "local_wav")
            self.assertEqual(manifest["duration_seconds"], 12)
            self.assertEqual(
                manifest["sha256"],
                {name: media.digest(output / name) for name in ("water-cycle.mp4", "captions.vtt")},
            )
            captions = (output / "captions.vtt").read_text(encoding="utf-8")
            self.assertTrue(captions.startswith("WEBVTT\n"))
            for heading, body in media.STAGES:
                self.assertIn(f"{heading}\n{body}", captions)
            video = output / "water-cycle.mp4"
            self.assertEqual(media.verify(shutil.which("ffprobe"), video), manifest["probe"])
            decoded = subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(video), "-t", "0.1", "-f", "s16le", "-"],
                check=True, capture_output=True,
            )
            samples = array("h", decoded.stdout)
            if sys.byteorder != "little":
                samples.byteswap()
            self.assertGreater(max(abs(sample) for sample in samples), 400)

            with self.assertRaises(FileExistsError):
                media.render_lesson(output)
            self.assertEqual(media.digest(video), manifest["sha256"][video.name])

    def test_rejects_an_invalid_narration_before_rendering(self):
        with TemporaryDirectory() as temporary:
            malformed = Path(temporary) / "recording.wav"
            malformed.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "PCM WAV"):
                media.validate_narration(malformed)


if __name__ == "__main__":
    unittest.main()
