# Release Checklist

## 导入或更新新版素材

```bash
python3 scripts/import-350.py "/path/to/350张瑞士平面图片"
```

脚本会核对 001–350 连续编号、复制高清图、生成轻量缩略图，并重建 CSV、JSON 和 8 个分类画廊。重复执行是安全的；未变化的图片不会重复处理。

## 发布 GitHub Release

1. 确认 `python3 scripts/verify-collection.py` 通过。
2. 将 `v2/images/` 打包为 `dist/350-layout-compositions-images.zip`。
3. 提交并推送代码和图片。
4. 创建新版本 Release，并上传新版与经典版两个 ZIP：
   - `350-layout-compositions-images.zip`
   - `100-layout-compositions-images.zip`
5. 检查 README 分类入口、图片链接和两个下载附件。

ZIP 只作为 GitHub Release 附件发布，不提交到 Git 历史。
