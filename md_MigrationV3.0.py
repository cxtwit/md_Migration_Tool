import os
import shutil
import re
import logging
from tkinter import Tk, Label, Button, Entry, filedialog, messagebox, StringVar, IntVar, Frame, Checkbutton
from datetime import datetime



def setup_logging(target_path):
    """配置日志系统：输出日志到目标文件夹"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_filename = os.path.join(target_path, f"{current_date}_迁移日志.log")
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info(f"日志文件路径：{log_filename}")
def process_markdown_file(md_file_path, target_path, images_folder="images", use_subfolders=False):
    """迁移单个 Markdown 文件及其关联的本地图片"""
    if not os.path.exists(md_file_path):
        logging.error(f"Markdown 文件不存在: {md_file_path}")
        return ""

    filename_without_ext = os.path.splitext(os.path.basename(md_file_path))[0]  # 获取 Markdown 文件名（去掉扩展名）

  
    if use_subfolders:
        images_target_path = os.path.join(target_path, images_folder, filename_without_ext)
    else:
        images_target_path = os.path.join(target_path, images_folder)

   
    os.makedirs(images_target_path, exist_ok=True)

    with open(md_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配 Markdown 文件中的图片路径
    markdown_img_pattern = r"!\[.*?\]\((.*?)\)"
    found_images = re.findall(markdown_img_pattern, content)

    for img_path in found_images:
        if img_path.startswith("http://") or img_path.startswith("https://"):
            logging.info(f"跳过远程图片: {img_path}")
            continue

        img_source_path = os.path.abspath(os.path.join(os.path.dirname(md_file_path), img_path))
        if not os.path.exists(img_source_path):
            logging.warning(f"图片文件不存在，跳过: {img_source_path}")
            continue

        img_filename = os.path.basename(img_source_path)
        new_img_path = os.path.join(images_target_path, img_filename)

        # 处理重名
        if os.path.exists(new_img_path):
            base, ext = os.path.splitext(img_filename)
            counter = 1
            while os.path.exists(new_img_path):
                new_img_path = os.path.join(images_target_path, f"{base}_{counter}{ext}")
                counter += 1

        
        shutil.copy2(img_source_path, new_img_path)
        logging.info(f"图片迁移成功: {img_path} → {new_img_path}")

        
        if use_subfolders:
            new_relative_image_path = f"./{images_folder}/{filename_without_ext}/{os.path.basename(new_img_path)}"
        else:
            new_relative_image_path = f"./{images_folder}/{os.path.basename(new_img_path)}"

        content = content.replace(img_path, new_relative_image_path)

   
    new_md_file_path = os.path.join(target_path, os.path.basename(md_file_path))
    with open(new_md_file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logging.info(f"Markdown 文件处理完成，保存到: {new_md_file_path}")
    return content


def process_markdown_directory(md_dir_path, target_path, images_folder="images", merge=False, use_subfolders=False):
    """批量处理 Markdown 文件，支持合并到一个文件"""
    merged_content = ""  # 合并所有内容的变量

    for root, _, files in os.walk(md_dir_path):
        for file in files:
            if file.lower().endswith(".md"):
                md_file_path = os.path.join(root, file)
                processed_content = process_markdown_file(md_file_path, target_path, images_folder, use_subfolders)
                if merge:
                    # 合并内容时加文件标题分隔
                    header = f"\n\n# 来自文件: {os.path.basename(md_file_path)}\n\n"
                    merged_content += header + processed_content

    # 如果启用了合并功能，则保存合并后的 Markdown 文件
    if merge:
        merged_file_path = os.path.join(target_path, "合并后的文档.md")
        with open(merged_file_path, "w", encoding="utf-8") as f:
            f.write(merged_content)
        logging.info(f"所有 Markdown 文件已合并并保存至: {merged_file_path}")


# ---------------- GUI 功能实现 ----------------
def on_select_input():
    """选择文件或文件夹"""
    response = messagebox.askyesno("是否启用批量处理", "选择“是”请选择md文件所在文件夹；\n选择“否”请选择单个 Markdown 文件。")
    if response:  # 用户选择文件夹模式
        selected_path = filedialog.askdirectory()
    else:  # 用户选择单文件模式
        selected_path = filedialog.askopenfilename(filetypes=[("Markdown files", "*.md")])
    if selected_path:  # 判断用户是否取消选择
        path_var.set(selected_path)


def on_select_target_directory():
    """选择目标文件夹"""
    directory = filedialog.askdirectory()
    if directory:
        target_var.set(directory)


def on_process():
    """执行 Markdown 文件或目录处理"""
    path = path_var.get().strip()
    target_path = target_var.get().strip()
    merge = merge_var.get()  # 获取是否合并选项
    use_subfolders = subfolder_var.get()  # 获取是否启用子文件夹功能

    if not path:
        messagebox.showerror("错误", "请选择文件或目录路径！")
        return
    if not target_path:
        messagebox.showerror("错误", "请选择目标目录！")
        return

    setup_logging(target_path)

    if os.path.isdir(path):  # 如果是文件夹则批量处理
        process_markdown_directory(path, target_path, merge=merge, use_subfolders=use_subfolders)
        if merge:
            messagebox.showinfo("完成", "批量处理完成，Markdown 文件已合并！")
        else:
            messagebox.showinfo("完成", "批量处理完成！")
    elif os.path.isfile(path) and path.lower().endswith(".md"):  # 如果是单文件
        content = process_markdown_file(path, target_path, use_subfolders=use_subfolders)
        new_md_file_path = os.path.join(target_path, os.path.basename(path))
        with open(new_md_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("完成", "Markdown 文件处理完成！")
    else:
        messagebox.showerror("错误", "无效路径，请重新选择！")


# ---------------- 主窗口 GUI ----------------
root = Tk()
root.title("MD_Migration BY tw1t")
root.geometry("600x350")
root.configure(bg="#F7F7F7")

title_label = Label(
    root, text="Markdown工具", font=("Arial", 18, "bold"), bg="#F7F7F7", fg="#4CAF50"
)
title_label.pack(pady=20)

content_frame = Frame(root, bg="#F7F7F7")
content_frame.pack(fill="both", expand=True, padx=20, pady=10)

path_var = StringVar()
Label(content_frame, text="需迁移文件：", font=("Arial", 12), bg="#F7F7F7").grid(
    row=0, column=0, pady=10, sticky="w"
)
path_entry = Entry(content_frame, textvariable=path_var, font=("Arial", 12), width=40)
path_entry.grid(row=0, column=1, pady=10)
Button(content_frame, text="选择", command=on_select_input, font=("Arial", 10), bg="#E0E0E0").grid(
    row=0, column=2, padx=10
)

target_var = StringVar()
Label(content_frame, text="目标文件夹：", font=("Arial", 12), bg="#F7F7F7").grid(
    row=1, column=0, pady=10, sticky="w"
)
target_entry = Entry(content_frame, textvariable=target_var, font=("Arial", 12), width=40)
target_entry.grid(row=1, column=1, pady=10)
Button(content_frame, text="选择", command=on_select_target_directory, font=("Arial", 10), bg="#E0E0E0").grid(
    row=1, column=2, padx=10
)

merge_var = IntVar() 
merge_checkbox = Checkbutton(
    root, text="合并多个 Markdown 文件", variable=merge_var, font=("Arial", 12), bg="#F7F7F7"
)
merge_checkbox.pack(pady=10)

# 图片迁移到文件命名的文件夹
subfolder_var = IntVar()  
subfolder_checkbox = Checkbutton(
    root, text="将图片迁移到以 Markdown 文件名为子文件夹的路径中", variable=subfolder_var, font=("Arial", 12), bg="#F7F7F7"
)
subfolder_checkbox.pack(pady=10)

# 开始处理按钮
process_button = Button(
    root, text="开始处理", command=on_process, font=("Arial", 14, "bold"), bg="#4CAF50", fg="white"
)
process_button.pack(pady=20)

# 运行主窗口
root.mainloop()
