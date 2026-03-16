# Image Manager

一个离线图片整理脚本：递归扫描目录中的图片，读取 EXIF GPS 信息，按中国省级行政区分类，并复制到新的输出目录。

## 功能

- 递归扫描指定根目录下的图片
- 读取 EXIF GPS 经纬度
- 按中国省份、直辖市、自治区分类
- 无 GPS 或无法归属的图片放入 `未知地区`
- 默认只预览，不复制
- 使用 `--apply` 后才真正复制文件
- 同名文件自动重命名，避免覆盖原文件

## 环境要求

- 建议在 `conda` 环境 `misc` 中运行
- Python 3.12+
- Pillow

安装依赖：

```bash
conda activate misc
pip install -r requirements.txt
```

## 使用方式

先预览：

```bash
conda activate misc
python3 organize_photos.py /path/to/photos
```

确认结果后再执行复制：

```bash
conda activate misc
python3 organize_photos.py /path/to/photos --apply
```

指定输出目录：

```bash
conda activate misc
python3 organize_photos.py /path/to/photos --apply --output /path/to/output
```

## 默认行为

- 默认输出目录：脚本所在目录下的 `output/`
- 默认执行模式：预览模式
- 默认归档目录结构：`output/<省份名>/`
- 无 GPS、GPS 损坏、坐标不在中国范围内：归入 `output/未知地区/`

## 支持格式

当前脚本会扫描以下常见扩展名：

- `.jpg`
- `.jpeg`
- `.png`
- `.heic`
- `.heif`
- `.tif`
- `.tiff`

## 测试

运行标准库测试：

```bash
conda activate misc
python3 -m unittest discover -s tests -v
```

## 注意事项

- 脚本采用复制，不会移动或删除原图
- 省份归属基于离线边界近似数据，适合日常整理，不适合高精度 GIS 场景
- 如果输出目录位于输入根目录内部，脚本会自动跳过输出目录，避免重复扫描
