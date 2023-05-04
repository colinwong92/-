import os
import re
import time
import requests
from lxml import html


# 输出章节信息和下载进度
def display_progress(comic_name, chapter_name, current_page_idx, total_pages):
    """
    显示下载进度
    """
    chapter_name = chapter_name.strip()
    print(f"\n漫画名称：{comic_name}")
    print(f"章节名称：{chapter_name}")
    print(f"正在下载第 {current_page_idx}/{total_pages} 张漫画图片...")


# 创建漫画文件夹和章节文件夹
def create_folder(comic_name, chapter_names):
    """
    在当前目录下创建漫画文件夹及各章节子文件夹，返回漫画文件夹路径和章节文件夹名称列表
    """
    # 创建漫画文件夹
    comic_dir_name = comic_name.strip()
    comic_dir_name = re.sub(r'[\\/:*?"<>|.]', '', comic_dir_name)
    if not os.path.exists(comic_dir_name):
        os.mkdir(comic_dir_name)

    chapter_dir_names = []  # 存储各章节文件夹名称
    for chapter_name in chapter_names:
        # 创建各章节子文件夹
        chapter_dir_name = chapter_name.strip()
        chapter_dir_name = re.sub(r'[\\/:*?"<>|.]', '', chapter_dir_name)
        # chapter_dir_name = chapter_dir_name.replace(' ', '')  # 删除空格
        chapter_dir_name = os.path.join(comic_dir_name, chapter_dir_name)
        if not os.path.exists(chapter_dir_name):
            os.mkdir(chapter_dir_name)
        chapter_dir_names.append(chapter_dir_name)
    return comic_dir_name, chapter_dir_names


# 下载封面到漫画名文件夹中
def download_cover(cover_url, comic_dir_name):
    print(f"漫画封面链接为 {cover_url}")
    response = requests.get(cover_url)
    if response.status_code == 200:
        with open(os.path.join(comic_dir_name, 'cover.jpg'), 'wb') as f:
            f.write(response.content)
        print("漫画封面下载成功")
    else:
        print(f"漫画封面下载失败，状态码：{response.status_code}")


# 分析章节
def comic_chapter(comic_link):
    response = requests.get('https://www.sesemanhua.top' + comic_link)
    if response.status_code != 200:  # 判断是否请求成功
        print("请求失败")
        return [], "", "", []
    chapter_html_content = response.text
    etree = html.etree
    html_ = etree.HTML(chapter_html_content)
    # 漫画名
    comic_name = html_.xpath("//div[@class='de-info__cover']/img/@alt")
    if not comic_name:
        print("漫画名称获取失败")
        return [], "", "", []
    comic_name = comic_name[0]
    # 漫画封面
    cover_url = html_.xpath("//div[@class='de-info__cover']/img/@src")
    if not cover_url:
        print("漫画封面链接获取失败")
        return [], "", "", []
    cover_url = cover_url[0]
    # 章节名称
    chapter_names = html_.xpath("//div[@class='de-chapter']//a/text()")
    if not chapter_names:
        print("章节名称获取失败")
        return [], "", "", []
    # 章节连接
    chapter_links = html_.xpath("//div[@class='de-chapter']//a[@class='j-chapter-link']/@href")
    if not chapter_links:
        print("章节链接获取失败")
        return [], "", "", []
    result = []
    for url in chapter_links:
        # 组合出链接
        chapter_link = ('https://www.sesemanhua.top' + url)
        result.append(chapter_link)
    # 返回章节名称和章节链接列表
    return chapter_names, comic_name, cover_url, result


# 下载漫画图片并保存在对应文件夹
def download_comic_img(comic_name, chapter_name, chapter_link, comic_dir_name, chapter_dir_name):
    chapter_name = chapter_name.strip()
    comic_name = re.sub(r'[\\/:*?"<>|.]', ' ', comic_name)
    chapter_name = re.sub(r'[\\/:*?"<>|.]', ' ', chapter_name)
    response = requests.get(chapter_link)
    if response.status_code != 200:  # 判断是否请求成功
        print(f"请求失败，状态码：{response.status_code}")
        return

    comic_html_image_content = response.text
    etree = html.etree
    html_ = etree.HTML(comic_html_image_content)
    img_src_list = html_.xpath("//div[@class='rd-article-wr clearfix']//img/@data-original")
    num_pages = len(img_src_list)

    # 判断该章节是否已经下载完成，如果已经下载完成，则跳过该章节，进行下一个章节的下载
    if len(os.listdir(chapter_dir_name)) == num_pages:
        print(f"\n{chapter_name} 已下载完成！")
        return

    print(f"\n共获取到{num_pages}张图片，当前已下载{len(os.listdir(chapter_dir_name))}张图片")
    # 判断是否下载中断，如果是，则跳过已下载的部分，从中断的位置开始下载
    start_idx = len(os.listdir(chapter_dir_name))
    if start_idx > 0:
        img_src_list = img_src_list[start_idx:]

    for index, img_src in enumerate(img_src_list):
        display_progress(comic_name, chapter_name, index + 1 + start_idx, num_pages)
        img_name = str(index + 1 + start_idx).zfill(3) + '.jpg'
        # 如果该文件已经存在于本地文件夹中，则跳过该文件的下载
        if os.path.exists(os.path.join(chapter_dir_name, img_name)):
            print(f"第{index + 1 + start_idx}张图片已存在，跳过下载")
            continue

        # 保存到目录中
        response = requests.get(img_src)
        if response.status_code == 200:
            content = response.content
            with open(os.path.join(chapter_dir_name, img_name), 'wb') as f:
                f.write(content)
            print(f"第{index + 1 + start_idx}张图片下载完成")
            time.sleep(5)
        else:
            print(f"第{index + 1 + start_idx}张图片下载失败，状态码：{response.status_code}")

        # 下载过程中若出现中断，则尝试重新下载该章节的图片
        if index + 1 + start_idx < num_pages:
            if len(os.listdir(os.path.join(chapter_dir_name))) < index + 2 + start_idx:
                print(f"第{index + 1 + start_idx + 1}张图片下载失败，尝试重新下载...")
                download_comic_img(comic_name, chapter_name, chapter_link, comic_dir_name, chapter_dir_name)
                break

    print()


# 请求漫画链接页面
def page():
    for page in range(1, 21):
        # 请求网页内容
        url = f'https://www.sesemanhua.top/index.php/category/order/addtime/page/{page}'
        response = requests.get(url)
        if response.status_code != 200:  # 判断是否请求成功
            print("请求失败")
            return []
        page_html_content = response.text
        # 使用XPath解析漫画链接
        etree = html.etree
        html_ = etree.HTML(page_html_content)
        # 漫画链接
        comic_links = html_.xpath("//div[@class='cate-comic-list clearfix']//p[@class='comic__title']/a/@href")
        # 打印当前页面的漫画链接和状态
        print(f"正在爬取第{page}页...")
        for link in comic_links:
            if 'javascript:void' in link:
                continue  # 跳过无效链接
            print('https://www.sesemanhua.top' + link)  # 漫画链接
        return comic_links


if __name__ == '__main__':
    # 获取漫画链接、名称和封面图片链接
    comic_links = page()
    if not comic_links:
        exit()
    _, comic_name, cover_url, _ = comic_chapter(comic_links[0])  # 修改此处，取第一话的漫画名称和封面链接
    # 创建漫画文件夹和章节文件夹
    _, chapter_dir_names = create_folder(comic_name, [])
    # 下载漫画封面
    download_cover(cover_url, comic_name)
    # 遍历漫画链接并下载漫画
    for comic_link in comic_links:
        # 获取章节名称和链接
        chapter_names, comic_name, _, chapter_links = comic_chapter(comic_link)
        if not chapter_links:
            continue
        # 创建章节文件夹
        _, chapter_dir_names = create_folder(comic_name, chapter_names)
        # 下载漫画图片
        for i in range(len(chapter_links)):
            download_comic_img(comic_name, chapter_names[i], chapter_links[i], comic_name, chapter_dir_names[i])
