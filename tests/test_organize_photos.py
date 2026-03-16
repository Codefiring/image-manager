from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import organize_photos


class OrganizePhotosTests(unittest.TestCase):
    def test_scan_images_recurses_and_skips_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "nested"
            output = root / "output"
            nested.mkdir()
            output.mkdir()

            keep = nested / "photo.jpg"
            ignored = output / "copied.jpg"
            text = root / "note.txt"
            keep.write_bytes(b"jpg")
            ignored.write_bytes(b"jpg")
            text.write_text("skip", encoding="utf-8")

            image_paths = organize_photos.scan_images(root, excluded_dirs=[output])

            self.assertEqual(image_paths, [keep])

    def test_resolve_province_matches_known_coordinates(self) -> None:
        self.assertEqual(organize_photos.resolve_province(39.9042, 116.4074), "北京市")
        self.assertEqual(organize_photos.resolve_province(23.1291, 113.2644), "广东省")
        self.assertIsNone(organize_photos.resolve_province(35.6764, 139.6500))

    def test_build_target_path_adds_suffix_on_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            province_dir = output / "北京市"
            province_dir.mkdir()
            first = province_dir / "photo.jpg"
            first.write_bytes(b"original")

            candidate = organize_photos.build_target_path(output, "北京市", Path("photo.jpg"))

            self.assertEqual(candidate.name, "photo (1).jpg")

    def test_preview_mode_does_not_copy_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "input"
            output = Path(temp_dir) / "output"
            root.mkdir()
            source = root / "beijing.jpg"
            source.write_bytes(b"image")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                with mock.patch("organize_photos.extract_gps", return_value=(39.9042, 116.4074)):
                    exit_code = organize_photos.main([str(root), "--output", str(output)])

            self.assertEqual(exit_code, 0)
            self.assertFalse((output / "北京市" / "beijing.jpg").exists())
            self.assertIn("当前为预览模式", stdout.getvalue())

    def test_apply_mode_copies_and_renames_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "input"
            output = Path(temp_dir) / "output"
            a_dir = root / "a"
            b_dir = root / "b"
            a_dir.mkdir(parents=True)
            b_dir.mkdir(parents=True)

            first = a_dir / "same.jpg"
            second = b_dir / "same.jpg"
            first.write_bytes(b"first")
            second.write_bytes(b"second")

            with mock.patch("organize_photos.extract_gps", return_value=(39.9042, 116.4074)):
                exit_code = organize_photos.main([str(root), "--output", str(output), "--apply"])

            self.assertEqual(exit_code, 0)
            self.assertEqual((output / "北京市" / "same.jpg").read_bytes(), b"first")
            self.assertEqual((output / "北京市" / "same (1).jpg").read_bytes(), b"second")


if __name__ == "__main__":
    unittest.main()
