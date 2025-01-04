import os
import shutil
import re

def process_markdown_file(md_file_path, target_path, images_folder="images"):

    # 检查 Markdown 文件是否存在
    if not os.path.exists(md_file_path):
        print(f"Markdown 文件不存在: {md_file_path}")
        return

    # 创建目标目录
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    # 创建目标路径中的图片存放目录
    images_target_path = os.path.join(target_path, images_folder)
    if not os.path.exists(images_target_path):
        os.makedirs(images_target_path)

    # 读取 Markdown 文件内容
    with open(md_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配 Markdown 文件中的图片链接 (支持 `![描述](路径)` 格式)
    markdown_img_pattern = r"!\[.*?\]\((.*?)\)"  # 提取圆括号中的路径
    found_images = re.findall(markdown_img_pattern, content)

    # 迁移图片并更新路径
    for img_path in found_images:
        # 跳过远程图片（以 `http` 或 `https` 开头）
        if img_path.startswith("http://") or img_path.startswith("https://"):
            print(f"跳过远程图片: {img_path}")
            continue

        # 计算图片源文件的绝对路径
        img_source_path = os.path.join(os.path.dirname(md_file_path), img_path)
        if not os.path.exists(img_source_path):
            print(f"图片文件不存在，跳过: {img_source_path}")
            continue

        # 将图片复制到目标目录
        img_filename = os.path.basename(img_path)  # 提取图片文件名
        new_img_path = os.path.join(images_target_path, img_filename)  # 目标目录中的图片路径
        shutil.copy2(img_source_path, new_img_path)  # 复制图片
        print(f"图片迁移成功: {img_path} → {new_img_path}")

        # 构造相对于目标 Markdown 文件的路径，并确保以 `./images/` 开头
        new_relative_image_path = f"./{images_folder}/{img_filename}".replace("\\", "/")

        # 替换 Markdown 文件内容中的图片路径为相对路径
        content = content.replace(img_path, new_relative_image_path)

    # 修改后的 Markdown 文件路径
    new_md_file_path = os.path.join(target_path, os.path.basename(md_file_path))

    # 将更新后的 Markdown 文件保存到目标目录
    with open(new_md_file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Markdown 文件处理完成，保存到: {new_md_file_path}")


def process_markdown_directory(md_dir_path, target_path, images_folder="images"):

    if not os.path.exists(md_dir_path):
        print(f"目录不存在: {md_dir_path}")
        return

    # 遍历目录下的所有文件
    for root, _, files in os.walk(md_dir_path):
        for file in files:
            if file.lower().endswith(".md"):  # 只处理 .md 文件
                md_file_path = os.path.join(root, file)
                print(f"正在处理文件: {md_file_path}")
                process_markdown_file(md_file_path, target_path, images_folder)


if __name__ == "__main__":
    print("请选择操作模式(本版本赞不支持网络图片迁移)：")
    print("1 - 处理一个 Markdown 文件")
    print("2 - 批量处理一个目录下的所有 Markdown 文件")
    choice = input("请输入你的选择（1 或 2）：").strip()

    if choice == "1":
        # 单个 Markdown 文件处理模式
        md_file_path = input("请输入 Markdown 文件的绝对路径：").strip()
        while not os.path.isfile(md_file_path) or not md_file_path.lower().endswith(".md"):
            print("输入的路径无效或不是 Markdown 文件，请重新输入！")
            md_file_path = input("请输入 Markdown 文件的绝对路径：").strip()

        target_directory = input("请输入迁移后的目标文件夹路径：").strip()
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        # 调用单文件处理函数
        process_markdown_file(md_file_path, target_directory)

    elif choice == "2":
        # 批量 Markdown 文件处理模式
        md_dir_path = input("请输入包含 Markdown 文件的目录路径：").strip()
        while not os.path.isdir(md_dir_path):
            print("输入的路径无效或不是有效的目录，请重新输入！")
            md_dir_path = input("请输入包含 Markdown 文件的目录路径：").strip()

        target_directory = input("请输入迁移后的目标文件夹路径：").strip()
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        # 调用批量处理函数
        process_markdown_directory(md_dir_path, target_directory)

    else:
        print("输入无效，程序已退出。")
