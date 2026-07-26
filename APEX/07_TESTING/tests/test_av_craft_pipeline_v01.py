#!/usr/bin/env python3
"""Smoke tests for APEX Audiovisual Craft Analysis Pipeline v0.1.

Frame extraction and audio analysis are exercised for real (offline,
against a locally ffmpeg-synthesized test clip -- no network needed).
The vision LLM and yt-dlp download are stubbed/injected since those need
a real API key / network access this test suite doesn't have.
"""
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "03_APPLICATION" / "consoles" / "youtube-principles" / "v0.1" / "backend"


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, BACKEND_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


avc = load_module("av_craft_pipeline", "av_craft_pipeline.py")
pipeline = avc.pipeline


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


HAVE_FFMPEG = shutil.which("ffmpeg") is not None


def make_synthetic_clip(path: Path, duration: int = 12) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"testsrc=duration={duration}:size=320x240:rate=10",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
            "-c:v", "libx264", "-c:a", "aac", "-shortest", str(path),
        ],
        capture_output=True, check=True,
    )


class FakeVisionClient:
    def analyze_frame_batch(self, frames, video_title):
        return [{
            "name": "High-contrast color grading",
            "category": "color_grading",
            "domains": ["Color Grading", "music-video-production"],
            "description": "Deep blacks and punchy saturated colors throughout.",
            "application": "Creates a moody, stylized aesthetic.",
            "evidence": "Strong contrast and saturated hues visible in the frame.",
        }]

    def summarize(self, craft_elements, audio, video_title):
        return "A visually stylized clip with strong color grading and steady tempo."


def test_check_dependencies_reports_missing_ffmpeg_and_libs():
    missing = avc.check_dependencies()
    assert_true(isinstance(missing, list), "check_dependencies should return a list")


def test_frame_extraction_and_audio_analysis_against_a_real_synthetic_clip():
    if not HAVE_FFMPEG:
        print("SKIP: ffmpeg not available in this environment")
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        clip_path = tmp_path / "synthetic.mp4"
        make_synthetic_clip(clip_path, duration=12)

        duration = avc.probe_duration_seconds(clip_path)
        assert_true(abs(duration - 12.0) < 1.0, f"probed duration should be ~12s, got {duration}")

        frames = avc.extract_frames(clip_path, tmp_path, interval_seconds=3, max_frames=10)
        assert_true(len(frames) == 4, f"expected 4 frames at 3s intervals over 12s, got {len(frames)}")
        assert_true(frames[0][0] == 0.0, "first frame should be at t=0")
        assert_true(all(p.exists() and p.stat().st_size > 0 for _, p in frames), "frame files should exist and be non-empty")

        audio_path = avc.extract_audio(clip_path, tmp_path)
        assert_true(audio_path.exists() and audio_path.stat().st_size > 0, "extracted audio file should exist and be non-empty")

        audio = avc.analyze_audio(audio_path)
        assert_true(audio.status == "ok", "audio analysis should succeed on a valid wav file")
        assert_true(abs(audio.duration_seconds - 12.0) < 1.0, "measured duration should match the clip")
        assert_true(audio.avg_rms_energy > 0, "a non-silent sine tone should have positive RMS energy")


def test_build_report_assembles_measured_and_inferred_sections():
    video = pipeline.VideoMeta(video_id="abc123XYZ_9", url="https://youtu.be/abc123XYZ_9", title="Test Music Video", channel="Test Channel")
    audio = avc.AudioAnalysis(status="ok", duration_seconds=180.0, tempo_bpm=128.0, beat_count=384, avg_rms_energy=0.12)
    items = [{"name": "High-contrast color grading", "category": "color_grading", "domains": ["Color Grading"], "evidence_timestamp": "0.0s-15.0s"}]

    report = avc.build_report("https://youtu.be/abc123XYZ_9", video, "ok", "", audio, 30, items, FakeVisionClient())

    assert_true(report["source_type"] == "music_video_craft", "report should be labeled as a music_video_craft source")
    assert_true(report["craft_element_count"] == 1, "expected exactly one craft element")
    assert_true(report["craft_elements"][0]["domains"] == ["color-grading"], "domains should be normalized")
    assert_true(report["audio_analysis"]["tempo_bpm"] == 128.0, "measured audio data should pass through unchanged")
    assert_true(
        "measured via real audio signal analysis" in report["truth_status"]["VERIFIED"][0],
        "VERIFIED truth status should distinguish measured audio data from LLM inference",
    )
    assert_true(report["qa_gates"]["release_status"] == "PROTOTYPE_OK", "clean report should pass QA")
    assert_true(report["manifest_hash_sha256"], "manifest hash must be generated")


def test_build_report_flags_failed_media_download():
    video = pipeline.VideoMeta(video_id="zzz999ZZZ_1", url="https://youtu.be/zzz999ZZZ_1")
    audio = avc.AudioAnalysis(status="error", error="not attempted")
    report = avc.build_report("https://youtu.be/zzz999ZZZ_1", video, "download_failed", "video unavailable", audio, 0, [], FakeVisionClient())
    assert_true(report["craft_element_count"] == 0, "a failed download should yield zero craft elements")
    assert_true(report["qa_gates"]["release_status"] == "HOLD_FOR_REVIEW", "failed download should hold for review")
    assert_true("media_download_failed" in report["qa_gates"]["issues"], "issues should reflect the download failure")


def test_analyze_url_rejects_non_youtube_url():
    report = avc.analyze_url("not a youtube url", FakeVisionClient())
    assert_true(report["craft_element_count"] == 0, "invalid URL should yield zero craft elements")
    assert_true("invalid_url" in report["risk_flags"], "invalid URL should be flagged")


if __name__ == "__main__":
    test_check_dependencies_reports_missing_ffmpeg_and_libs()
    test_frame_extraction_and_audio_analysis_against_a_real_synthetic_clip()
    test_build_report_assembles_measured_and_inferred_sections()
    test_build_report_flags_failed_media_download()
    test_analyze_url_rejects_non_youtube_url()
    print("PASS: APEX Audiovisual Craft Analysis Pipeline v0.1 smoke tests")
