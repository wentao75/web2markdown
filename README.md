# Web2Markdown

一个将网页转换为 Markdown 格式文件的命令行工具。

## 功能特点

- 支持将网页内容转换为 Markdown 格式
- 自动下载和保存网页中的图片
- 保持原网页的基本格式结构
- 支持知乎专栏文章的特殊处理
- 图片文件使用唯一文件名，避免重名覆盖
- 支持多种图片格式（JPG、PNG、GIF、WebP）
- 自动处理相对路径和绝对路径的图片链接
- 智能处理标题和段落格式
- 提供图片下载失败重试机制

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

基本用法：
```bash
python web2md.py <网页URL> <输出文件名>
```

指定图片存储目录：
```bash
python web2md.py <网页URL> <输出文件名> -i <图片目录名>
```

例如：
```bash
python web2md.py https://example.com/article output.md
python web2md.py https://example.com/article output.md -i images
```

## 输出说明

- Markdown 文件将保存为指定的输出文件名
- 图片文件将保存在与 Markdown 文件同目录下的指定目录中（默认为 'i'）
- 图片文件名格式：`image_序号_哈希值.扩展名`（例如：`image_1_a8b7c6d5.jpg`）
- 如果发生文件名冲突，会自动添加序号（例如：`image_1_a8b7c6d5_1.jpg`）

## 特殊网站支持

### 知乎专栏
- 自动处理知乎的反爬虫机制
- 使用知乎 API 获取文章内容
- 正确处理知乎文章中的图片

## 系统要求

- Python 3.6 或更高版本
- 安装所有 requirements.txt 中列出的依赖包

## 注意事项

1. 部分网站可能有访问限制或反爬虫机制，可能需要特殊处理
2. 图片下载可能受网络状况影响，工具会自动重试失败的下载
3. 对于大型网页或包含大量图片的页面，转换过程可能需要较长时间
4. 确保有足够的磁盘空间存储下载的图片
5. 建议在使用前检查网页是否允许内容转换和图片下载

## 依赖包说明

- beautifulsoup4：HTML解析
- requests：网络请求
- markdownify：HTML到Markdown转换
- Pillow：图片处理
- urllib3：URL处理

## 错误处理

工具会在运行过程中提供详细的日志信息，包括：
- 网页访问状态
- 图片下载进度
- 错误信息和重试状态
- 转换完成状态

如果遇到问题，请检查：
1. 网络连接是否正常
2. URL是否正确
3. 是否有足够的磁盘空间
4. 是否有写入权限
5. 依赖包是否正确安装 