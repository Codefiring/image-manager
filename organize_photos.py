from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from PIL import Image

GPS_INFO_TAG = 34853
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff"}
UNKNOWN_REGION = "未知地区"


@dataclass(slots=True)
class ProvinceBounds:
    name: str
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    @property
    def area(self) -> float:
        return (self.max_lon - self.min_lon) * (self.max_lat - self.min_lat)

    def contains(self, lat: float, lon: float) -> bool:
        return self.min_lon <= lon <= self.max_lon and self.min_lat <= lat <= self.max_lat


@dataclass(slots=True)
class ProcessSummary:
    total_files: int = 0
    copied_files: int = 0
    gps_matched: int = 0
    unknown_region: int = 0
    failed_files: int = 0


@lru_cache(maxsize=1)
def load_province_bounds() -> list[ProvinceBounds]:
    data_path = Path(__file__).with_name("china_province_bounds.json")
    data = json.loads(data_path.read_text(encoding="utf-8"))
    provinces = [
        ProvinceBounds(
            name=item["name"],
            min_lon=item["bbox"][0],
            min_lat=item["bbox"][1],
            max_lon=item["bbox"][2],
            max_lat=item["bbox"][3],
        )
        for item in data
    ]
    return sorted(provinces, key=lambda item: item.area)


def scan_images(root_path: Path, excluded_dirs: Iterable[Path] | None = None) -> list[Path]:
    root_path = root_path.resolve()
    excluded = {path.resolve() for path in (excluded_dirs or [])}
    image_paths: list[Path] = []

    for path in root_path.rglob("*"):
        if path.is_dir():
            continue
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if any(path.is_relative_to(directory) for directory in excluded):
            continue
        image_paths.append(path)

    return sorted(image_paths)


def _rational_to_float(value: object) -> float:
    if isinstance(value, tuple) and len(value) == 2:
        numerator, denominator = value
        return float(numerator) / float(denominator)
    return float(value)


def _dms_to_decimal(values: object, ref: str) -> float:
    degrees, minutes, seconds = values
    decimal = _rational_to_float(degrees) + _rational_to_float(minutes) / 60 + _rational_to_float(seconds) / 3600
    if ref in {"S", "W"}:
        return -decimal
    return decimal


def extract_gps(path: Path) -> tuple[float, float] | None:
    try:
        with Image.open(path) as image:
            exif = image.getexif()
    except Exception:
        return None

    if not exif:
        return None

    gps_info = exif.get_ifd(GPS_INFO_TAG)
    if not gps_info:
        return None

    latitude = gps_info.get(2)
    latitude_ref = gps_info.get(1)
    longitude = gps_info.get(4)
    longitude_ref = gps_info.get(3)

    if not latitude or not latitude_ref or not longitude or not longitude_ref:
        return None

    try:
        lat = _dms_to_decimal(latitude, str(latitude_ref))
        lon = _dms_to_decimal(longitude, str(longitude_ref))
    except Exception:
        return None

    return lat, lon


def resolve_province(lat: float, lon: float) -> str | None:
    best_match: ProvinceBounds | None = None
    for province in load_province_bounds():
        if province.contains(lat, lon):
            best_match = province
            break
    return best_match.name if best_match else None


def build_target_path(output_dir: Path, province_name: str, source_path: Path) -> Path:
    destination_dir = output_dir / province_name
    destination_dir.mkdir(parents=True, exist_ok=True)

    candidate = destination_dir / source_path.name
    if not candidate.exists():
        return candidate

    stem = source_path.stem
    suffix = source_path.suffix
    index = 1
    while True:
        candidate = destination_dir / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def copy_file(source_path: Path, destination_path: Path) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination_path)


def process_images(image_paths: list[Path], output_dir: Path, apply_changes: bool) -> tuple[ProcessSummary, Counter[str], list[str]]:
    summary = ProcessSummary(total_files=len(image_paths))
    province_counter: Counter[str] = Counter()
    errors: list[str] = []

    for image_path in image_paths:
        gps = extract_gps(image_path)
        province = resolve_province(*gps) if gps else None
        region_name = province or UNKNOWN_REGION
        province_counter[region_name] += 1

        if province:
            summary.gps_matched += 1
        else:
            summary.unknown_region += 1

        if not apply_changes:
            continue

        try:
            destination = build_target_path(output_dir, region_name, image_path)
            copy_file(image_path, destination)
            summary.copied_files += 1
        except Exception as exc:
            summary.failed_files += 1
            errors.append(f"{image_path}: {exc}")

    return summary, province_counter, errors


def print_summary(summary: ProcessSummary, province_counter: Counter[str], errors: list[str], output_dir: Path, apply_changes: bool) -> None:
    action_text = "复制完成" if apply_changes else "预览完成"
    print(action_text)
    print(f"输出目录: {output_dir}")
    print(f"图片总数: {summary.total_files}")
    print(f"可识别省份: {summary.gps_matched}")
    print(f"未知地区: {summary.unknown_region}")
    print(f"复制成功: {summary.copied_files}")
    print(f"处理失败: {summary.failed_files}")

    if province_counter:
        print("分类统计:")
        for province_name, count in sorted(province_counter.items()):
            print(f"  {province_name}: {count}")

    if errors:
        print("错误详情:", file=sys.stderr)
        for message in errors:
            print(f"  {message}", file=sys.stderr)

    if not apply_changes:
        print("当前为预览模式，添加 --apply 才会执行复制。")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按 EXIF GPS 归属省份整理图片到新目录。")
    parser.add_argument("root_path", help="要递归扫描的图片根目录")
    parser.add_argument("--apply", action="store_true", help="执行复制；默认仅预览")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "output",
        help="输出目录，默认是脚本所在目录下的 output",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root_path = Path(args.root_path).expanduser().resolve()
    output_dir = args.output.expanduser().resolve()

    if not root_path.exists() or not root_path.is_dir():
        print(f"根目录不存在或不是目录: {root_path}", file=sys.stderr)
        return 1

    excluded_dirs: list[Path] = []
    if output_dir.is_relative_to(root_path):
        excluded_dirs.append(output_dir)

    image_paths = scan_images(root_path, excluded_dirs=excluded_dirs)
    summary, province_counter, errors = process_images(image_paths, output_dir, apply_changes=args.apply)
    print_summary(summary, province_counter, errors, output_dir, apply_changes=args.apply)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
