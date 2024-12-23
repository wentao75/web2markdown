#!/usr/bin/env python3
import os
import sys
import requests
import hashlib
import time
import re
import argparse
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Comment
from markdownify import markdownify
from PIL import Image
from io import BytesIO

class Web2Markdown:
    def __init__(self, url, output_file, image_dir='i'):
        self.url = url
        self.output_file = output_file
        self.image_dir = image_dir
        self.image_count = 0
        self.session = requests.Session()
        
        # 基础请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        # 根据URL设置特定的请求头
        if 'zhihu.com' in url:
            self.headers.update({
                'x-requested-with': 'fetch',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
            })
            
            # 设置知乎图片请求头
            self.image_headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://zhuanlan.zhihu.com/',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'image',
                'sec-fetch-mode': 'no-cors',
                'sec-fetch-site': 'cross-site',
            }
        elif 'segmentfault.com' in url:
            # SegmentFault 需要特定的请求头来模拟浏览器行为
            self.headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',  # 支持压缩内容
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',  # 语言偏好
                'Cache-Control': 'max-age=0',  # 禁用缓存
                'Connection': 'keep-alive',  # 保持连接
                'Host': 'segmentfault.com',  # 指定主机名
                'Referer': 'https://segmentfault.com/',  # 来源页面
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',  # 浏览器标识
                'sec-ch-ua-mobile': '?0',  # 非移动设备
                'sec-ch-ua-platform': '"macOS"',  # 操作系统平台
                'Sec-Fetch-Dest': 'document',  # 请求目标类型
                'Sec-Fetch-Mode': 'navigate',  # 导航模式
                'Sec-Fetch-Site': 'same-origin',  # 同源请求
                'Sec-Fetch-User': '?1',  # 用户触发的请求
                'Upgrade-Insecure-Requests': '1',  # 升级不安全请求
            })
            
            # SegmentFault 图片请求头设置
            self.image_headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',  # 支持多种图片格式
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://segmentfault.com/',  # 防盗链处理
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'image',  # 图片资源
                'sec-fetch-mode': 'no-cors',  # 无CORS请求
                'sec-fetch-site': 'cross-site',  # 跨站请求
            }
        else:
            self.image_headers = self.headers

    def get_zhihu_content(self, url):
        """获取知乎文章内容"""
        # 从URL中提取文章ID
        article_id = url.split('/')[-1]
        if 'p/' in url:
            article_id = article_id.split('p/')[-1]
        
        # 构建API URL
        api_url = f'https://www.zhihu.com/api/v4/articles/{article_id}'
        
        try:
            response = self.session.get(api_url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # 提取文章内容
            title = data.get('title', '')
            content = data.get('content', '')
            
            # 构建完整的HTML
            html = f'<h1>{title}</h1>{content}'
            return html
            
        except Exception as e:
            print(f"获取知乎文章内容失败: {str(e)}")
            return None

    def get_segmentfault_content(self, url):
        """获取 SegmentFault 文章内容
        
        Args:
            url (str): SegmentFault 文章的URL
            
        Returns:
            str: 处理后的HTML内容，包含文章标题和正文
            None: 如果获取失败
            
        处理步骤：
        1. 发送GET请求获取页面内容
        2. 使用BeautifulSoup解析HTML
        3. 提取文章标题和正文内容
        4. 组合成新的HTML字符串返回
        """
        try:
            # 发送请求获取页面内容
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # 使用BeautifulSoup解析页面
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取文章标题（h1标签带class='h1'）
            title = soup.find('h1', class_='h1')
            if title:
                title = title.get_text(strip=True)
            
            # 获取文章内容（article标签带class='article-content'）
            content = soup.find('article', class_='article-content')
            
            if not content:
                raise Exception("无法找到文章内容，可能是页面结构已变化")
            
            # 构建完整的HTML，确保标题和内容之间有适当的间隔
            html = f'<h1>{title}</h1>\n{str(content)}'
            return html
            
        except Exception as e:
            print(f"获取 SegmentFault 文章内容失败: {str(e)}")
            return None

    def download_image(self, img_url):
        """下载图片并保存到本地"""
        try:
            # 处理相对URL
            if not img_url.startswith(('http://', 'https://')):
                img_url = urljoin(self.url, img_url)
            
            # 处理特殊的图片URL（例如数据URL）
            if img_url.startswith('data:'):
                print(f"跳过数据URL: {img_url[:50]}...")
                return None
            
            # 添加重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"尝试下载图片 (尝试 {attempt + 1}/{max_retries}): {img_url}")
                    
                    # 使用特定的图片请求头
                    response = self.session.get(img_url, headers=self.image_headers, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    if response.status_code == 200:
                        try:
                            # 确保资源目录存在
                            os.makedirs(self.image_dir, exist_ok=True)
                            
                            # 获取内容类型
                            content_type = response.headers.get('content-type', '').lower()
                            print(f"图片内容类型: {content_type}")
                            
                            # 根据内容类型确定扩展名
                            ext = None
                            if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                                ext = '.jpg'
                            elif 'image/png' in content_type:
                                ext = '.png'
                            elif 'image/gif' in content_type:
                                ext = '.gif'
                            elif 'image/webp' in content_type:
                                ext = '.png'  # 将webp转换为png
                            
                            # 如果无法从内容类型确定扩展名，从URL获取
                            if not ext:
                                ext = os.path.splitext(urlparse(img_url).path)[1].lower()
                                if not ext:
                                    ext = '.jpg'  # 默认使用jpg
                            
                            # 生成唯一的图片文件名
                            self.image_count += 1
                            # 使用URL的MD5哈希值和序号组合生成文件名
                            url_hash = hashlib.md5(img_url.encode()).hexdigest()[:8]
                            local_filename = f'image_{self.image_count}_{url_hash}{ext}'
                            local_path = os.path.join(self.image_dir, local_filename)
                            
                            # 如果文件已存在，添加额外的序号
                            counter = 1
                            while os.path.exists(local_path):
                                local_filename = f'image_{self.image_count}_{url_hash}_{counter}{ext}'
                                local_path = os.path.join(self.image_dir, local_filename)
                                counter += 1
                            
                            # 保存图片
                            img_data = response.content
                            try:
                                # 尝试打开图片以验证其有效性
                                img = Image.open(BytesIO(img_data))
                                
                                # 如果是webp格式，转换为PNG
                                if 'image/webp' in content_type:
                                    img = img.convert('RGBA')
                                
                                # 保存图片
                                img.save(local_path)
                                print(f"图片保存成功: {local_path}")
                                
                                relative_path = os.path.join(self.image_dir, local_filename)
                                return relative_path
                                
                            except Exception as e:
                                print(f"图片处理失败: {str(e)}")
                                # 尝试直接保存原始数据
                                with open(local_path, 'wb') as f:
                                    f.write(img_data)
                                print(f"使用原始数据保存图片: {local_path}")
                                relative_path = os.path.join(self.image_dir, local_filename)
                                return relative_path
                                
                        except Exception as e:
                            print(f"保存图片失败: {str(e)}")
                            if attempt < max_retries - 1:
                                continue
                            
                    elif response.status_code == 429:  # Too Many Requests
                        print(f"请求过于频繁，等待后重试...")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # 指数退避
                            continue
                    else:
                        print(f"HTTP错误: {response.status_code}")
                    break
                    
                except requests.exceptions.Timeout:
                    print("请求超时，重试...")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                except requests.exceptions.RequestException as e:
                    print(f"请求异常: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    break
            
            print(f"图片下载失败，已尝试 {max_retries} 次")
            return None
            
        except Exception as e:
            print(f"下载图片时发生错误: {str(e)}")
            return None

    def clean_html(self, soup):
        """清理HTML，移除不需要的元素"""
        # 移除script标签
        for script in soup.find_all('script'):
            script.decompose()
        
        # 移除style标签
        for style in soup.find_all('style'):
            style.decompose()
            
        # 移除link标签
        for link in soup.find_all('link'):
            link.decompose()
            
        # 移除meta标签
        for meta in soup.find_all('meta'):
            meta.decompose()
            
        # 移除注释
        for comment in soup.find_all(string=lambda string: isinstance(string, Comment)):
            comment.extract()
            
        # 处理figure和figcaption
        for figure in soup.find_all('figure'):
            # 找到figcaption
            figcaption = figure.find('figcaption')
            if figcaption:
                # 在figcaption后添加换行
                br = soup.new_tag('br')
                figcaption.insert_after(br)
                # 检查figcaption后是否有标题
                next_element = figcaption.next_sibling
                while next_element and isinstance(next_element, str) and not next_element.strip():
                    next_element = next_element.next_sibling
                if next_element and next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    br2 = soup.new_tag('br')
                    figcaption.insert_after(br2)
            
        # 移除空白标签，但保留可能影响布局的标签
        for tag in soup.find_all():
            # 跳过可能影响布局的标签
            if tag.name in ['figure', 'img', 'br', 'hr', 'div', 'p', 'figcaption']:
                continue
            # 跳过标题标签
            if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                continue
            # 跳过包含图片的标签
            if tag.find_all(['img', 'video', 'iframe'], recursive=False):
                continue
            # 跳过标题前后的标签
            if (tag.find_next(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or 
                tag.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
                continue
            # 检查标签是否为空
            if len(tag.get_text(strip=True)) == 0:
                # 将空标签替换为换行符
                tag.replace_with(soup.new_string('\n'))

        # 标准化标题标签
        for i, tag in enumerate(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            for heading in soup.find_all(tag):
                # 确保标题前后有换行
                if heading.previous_sibling and isinstance(heading.previous_sibling, str):
                    heading.insert_before(soup.new_string('\n\n'))
                if heading.next_sibling and isinstance(heading.next_sibling, str):
                    heading.insert_after(soup.new_string('\n\n'))
        
        return soup

    def process_html(self, html_content):
        """处理HTML内容，载图片并更新图片链接"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("\n原始HTML内容中的图片标签:")
        for img in soup.find_all('img'):
            print(f"发现原始图片标签: {img}")
        
        # 清理HTML
        soup = self.clean_html(soup)
        
        print("\n清理后HTML内容中的图片标签:")
        for img in soup.find_all('img'):
            print(f"清理后的图片标签: {img}")
        
        def process_image(img):
            """处理单个图片标签"""
            print(f"\n处理图片标签: {img}")
            # 获取所有可能的图片URL属性
            src = None
            for attr in ['src', 'data-src', 'data-original', 'data-actualsrc', 'data-original-src', 'data-src-retina']:
                src = img.get(attr)
                if src:
                    print(f"从属性 {attr} 找到图片URL: {src}")
                    break
            
            if src:
                print(f"找到图片URL: {src}")
                # 转换为绝对URL
                abs_url = urljoin(self.url, src)
                print(f"转换为绝对URL: {abs_url}")
                # 下载图片并获取本地路径
                local_path = self.download_image(abs_url)
                if local_path:
                    print(f"图片已下载到: {local_path}")
                    img['src'] = local_path
                    # 移除其他可能的图片属性
                    for attr in ['data-src', 'srcset', 'data-srcset', 'data-original', 'data-actualsrc', 'data-original-src', 'data-src-retina']:
                        if img.has_attr(attr):
                            del img[attr]
                else:
                    print(f"图片下载失败: {abs_url}")
        
        # 递归查找所有图片标签
        print("\n开始查找所有图片标签...")
        all_images = soup.find_all('img', recursive=True)
        print(f"找到 {len(all_images)} 个图片标签")
        
        # 处理每个图片
        for img in all_images:
            process_image(img)
        
        # 检查是否有遗漏的图片（通过其他属性隐藏的图片）
        print("\n检查可能遗漏的图片...")
        for tag in soup.find_all(recursive=True):
            for attr in ['data-src', 'data-original', 'data-actualsrc', 'data-original-src', 'data-src-retina']:
                if tag.has_attr(attr):
                    src = tag.get(attr)
                    if src and src.startswith(('http://', 'https://')):
                        print(f"发现额外的图片URL在标签 {tag.name}: {src}")
                        # 创建新的img标签
                        new_img = soup.new_tag('img')
                        new_img['src'] = src
                        tag.append(new_img)
                        process_image(new_img)
        
        return str(soup)

    def post_process_markdown(self, content):
        """后处理Markdown内容，只处理图片下载"""
        print("\n开始处理Markdown内容中的图片...")
        
        # 下载markdown的图片
        def download_md_image(match):
            img_url = match.group(1)
            print(f"\n发现Markdown图片链接: {img_url}")
            # 如果不是本地路径，则下载图片
            if img_url.startswith(('http://', 'https://')):
                print(f"处理远程图片URL: {img_url}")
                local_path = self.download_image(img_url)
                if local_path:
                    print(f"图片已下载到: {local_path}")
                    return f'![]({local_path})'
                else:
                    print(f"图片下载失败: {img_url}")
            return match.group(0)
        
        # 处理所有图片链接，包括带查询参数的URL
        content = re.sub(r'!\[([^\]]*)\]\((https?://[^\s\)]+(?:\?[^\s\)]+)?)\)', 
                        lambda m: f'![{m.group(1)}]({download_md_image(m)})', content)
        
        # 检查是否还有未处理的图片链接
        remaining_images = re.findall(r'!\[.*?\]\((https?://[^\s\)]+)(?:\?[^\s\)]+)?\)', content)
        if remaining_images:
            print("\n发现未处理的图片链接:")
            for img_url in remaining_images:
                print(f"- {img_url}")
                local_path = self.download_image(img_url)
                if local_path:
                    content = content.replace(img_url, local_path)
        
        return content.strip() + '\n'

    def convert(self):
        """将网页转换为Markdown"""
        try:
            print(f"\n开始处理网页: {self.url}")
            
            # 获取网页内容
            if 'zhihu.com' in self.url:
                html_content = self.get_zhihu_content(self.url)
                if not html_content:
                    raise Exception("无法获取知乎文章内容")
            elif 'segmentfault.com' in self.url:
                html_content = self.get_segmentfault_content(self.url)
                if not html_content:
                    raise Exception("无法获取 SegmentFault 文章内容")
            else:
                response = self.session.get(self.url, headers=self.headers, timeout=30)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                html_content = response.text
            
            print("\n开始处理HTML内容...")
            # 处理HTML内容
            processed_html = self.process_html(html_content)
            
            # 在转换前处理HTML中的标题，确保标题前有换行
            soup = BeautifulSoup(processed_html, 'html.parser')
            
            # 处理所有标题，确保它们是独立的行
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                # 如果标题前面有文本节点，将其分割
                prev_element = heading.previous_sibling
                if prev_element and isinstance(prev_element, str):
                    text = prev_element.strip()
                    if text:
                        # 创建新的p标签包含文本
                        p = soup.new_tag('p')
                        p.string = text
                        prev_element.replace_with(p)
                        # 添加换行
                        br = soup.new_tag('br')
                        p.insert_after(br)
                
                # 如果标题后面有文本节点，将其分割
                next_element = heading.next_sibling
                if next_element and isinstance(next_element, str):
                    text = next_element.strip()
                    if text:
                        # 创建新的p标签包含文本
                        p = soup.new_tag('p')
                        p.string = text
                        next_element.replace_with(p)
                        # 添加换行
                        br = soup.new_tag('br')
                        heading.insert_after(br)
            
            # 处理图片后面的标题
            for img in soup.find_all('img'):
                next_element = img.next_sibling
                while next_element and isinstance(next_element, str) and not next_element.strip():
                    next_element = next_element.next_sibling
                if next_element and next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    br = soup.new_tag('br')
                    img.insert_after(br)
            
            print("\n开始转换为Markdown...")
            # 转换为Markdown
            markdown_content = markdownify(
                str(soup),
                heading_style="ATX",
                bullets="-",
                strip=['script', 'style', 'meta', 'link', 'xml']
            )
            
            # 保存Markdown文件
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
                
            print(f"\n转换完成！文件已保存为: {self.output_file}")
            if self.image_count > 0:
                print(f"共下载了 {self.image_count} 张图片，保存在目录: {self.image_dir}")
            else:
                print("警告：未发现任何图片需要下载！")
                
        except Exception as e:
            print(f"转换失败: {str(e)}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='将网页转换为Markdown格式文件')
    parser.add_argument('url', help='网页URL')
    parser.add_argument('output', help='输出文件名')
    parser.add_argument('-i', '--image-dir', default='i', help='图片存储目录名 (默认: i)')
    
    args = parser.parse_args()
    
    converter = Web2Markdown(args.url, args.output, args.image_dir)
    converter.convert()

if __name__ == "__main__":
    main() 