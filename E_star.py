import os
import shutil
import re
import logging
from tkinter import Tk, Label, Button, Entry, filedialog, messagebox, StringVar, IntVar, END, Checkbutton
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
from datetime import datetime

class Application(Tk):
    def __init__(self):
        super().__init__()
        self.title("E_starMarkdowntools")
        self.geometry("750x500")
        self.resizable(False, False)
        self.configure(bg="white")

        # 创建选项卡
        self.tab_control = ttk.Notebook(self)

        self.migration_tab = ttk.Frame(self.tab_control)  # Markdown迁移页
        self.path_processing_tab = ttk.Frame(self.tab_control)  # 路径处理工具页
        self.logs_tab = ttk.Frame(self.tab_control)  # 日志监控页

        self.tab_control.add(self.migration_tab, text="Markdown迁移")
        self.tab_control.add(self.path_processing_tab, text="路径处理工具")
        self.tab_control.add(self.logs_tab, text="日志监控")
        self.tab_control.pack(expand=1, fill="both")

        # 初始化共享变量
        self.path_var = StringVar()
        self.target_var = StringVar()
        self.merge_var = IntVar(value=0)
        self.subfolder_var = IntVar(value=0)

        # 构建用户界面
        self.build_migration_tab()  # Markdown迁移功能页面
        self.build_path_processing_tab()  # 路径处理工具页面
        self.build_logs_tab()  # 日志监控页面

        # 配置日志系统
        self.setup_logging()

    def build_migration_tab(self):
        """Markdown迁移功能页面"""
        Label(self.migration_tab, text="需迁移文件夹/文件：", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        Entry(self.migration_tab, textvariable=self.path_var, width=50).grid(row=0, column=1, pady=10, sticky="w")
        Button(self.migration_tab, text="选择", command=self.on_select_input).grid(row=0, column=2, padx=10)

        Label(self.migration_tab, text="目标文件夹：", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        Entry(self.migration_tab, textvariable=self.target_var, width=50).grid(row=1, column=1, pady=10, sticky="w")
        Button(self.migration_tab, text="选择", command=self.on_select_target_directory).grid(row=1, column=2, padx=10)

        Checkbutton(
            self.migration_tab,
            text="合并多个 Markdown 文件",
            variable=self.merge_var,
            font=("Arial", 10),
            bg="white",
        ).grid(row=2, column=1, sticky="w", padx=10, pady=5)

        Checkbutton(
            self.migration_tab,
            text="将图片迁移到以 Markdown 文件名为子文件夹",
            variable=self.subfolder_var,
            font=("Arial", 10),
            bg="white",
        ).grid(row=3, column=1, sticky="w", padx=10, pady=5)

        Button(self.migration_tab, text="开始迁移", command=self.on_process_migration, font=("Arial", 12), bg="#4CAF50", fg="white").grid(
            row=4, column=1, pady=20, columnspan=3
        )

    def build_path_processing_tab(self):
        """路径处理工具页面"""
        Label(self.path_processing_tab, text="请选择 Markdown 文件目录：", font=("Arial", 12)).pack(pady=10)
        Button(
            self.path_processing_tab,
            text="选择目录",
            command=self.on_select_md_directory,
            width=15,
            height=1,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12)
        ).pack(pady=10)

        Label(
            self.path_processing_tab,
            text="★ 将自动批量处理 Markdown 文件的图片路径\n★ 详细日志请查看日志监控页面\n★本操作将直接修改选中的markdown文件★",
            font=("Arial", 10),
            fg="gray",
            justify="center",
        ).pack(pady=5)

    def build_logs_tab(self):
        """日志监控页面"""
        Label(self.logs_tab, text="实时日志输出：", font=("Arial", 12)).pack(anchor="w", padx=10, pady=5)
        self.log_area = ScrolledText(self.logs_tab, wrap="word", font=("Courier New", 10), height=15)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_logging(self):
        """配置日志系统，将日志实时输出到日志框中"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler = TextHandler(self.log_area)
        logging.getLogger().addHandler(handler)

    def on_select_input(self):
        response = messagebox.askyesno("操作模式", "是否需要批量处理所有 Markdown 文件？\n选择“是”请选择文件夹，选择“否”请选择单个 Markdown 文件。")
        if response:
            selected_path = filedialog.askdirectory()
        else:
            selected_path = filedialog.askopenfilename(filetypes=[("Markdown files", "*.md")])
        if selected_path:
            self.path_var.set(selected_path)

    def on_select_target_directory(self):
        selected_path = filedialog.askdirectory()
        if selected_path:
            self.target_var.set(selected_path)

    def on_process_migration(self):
        source_path = self.path_var.get().strip()
        target_path = self.target_var.get().strip()
        merge = self.merge_var.get()
        use_subfolders = self.subfolder_var.get()

        if not source_path:
            messagebox.showerror("错误", "请选择文件或目录路径！")
            return
        if not target_path:
            messagebox.showerror("错误", "请选择目标目录！")
            return

        setup_logging(target_path)

        try:
            if os.path.isdir(source_path):
                process_markdown_directory(source_path, target_path, merge=merge, use_subfolders=use_subfolders)
                if merge:
                    messagebox.showinfo("完成", "批量处理完成，Markdown 文件已合并！")
                else:
                    messagebox.showinfo("完成", "批量处理完成！")
            elif os.path.isfile(source_path) and source_path.lower().endswith(".md"):
                process_markdown_file(source_path, target_path, use_subfolders=use_subfolders)
                messagebox.showinfo("完成", "Markdown 文件处理完成！")
            else:
                raise ValueError("无效的路径类型！")
        except Exception as e:
            logging.error(f"处理失败：{e}")
            messagebox.showerror("错误", f"处理失败：{e}")

    def on_select_md_directory(self):
        directory = filedialog.askdirectory(title="选择 Markdown 文件目录")
        if directory:
            self.process_all_md_files(directory)

    def process_all_md_files(self, md_dir):
        """批量处理 Markdown 文件目录"""
        if not os.path.isdir(md_dir):
            messagebox.showerror("错误", "提供的路径不是有效目录！")
            return

        md_files = [f for f in os.listdir(md_dir) if f.endswith(".md")]
        if not md_files:
            messagebox.showwarning("提示", "未找到任何 Markdown 文件！")
            return

        for file_name in md_files:
            md_file = os.path.join(md_dir, file_name)
            self.process_images_and_update_md(md_file)

        messagebox.showinfo("完成", f"处理完成！共处理 {len(md_files)} 个 Markdown 文件。")

    def process_images_and_update_md(self, md_file):
        md_folder = os.path.dirname(md_file)
        images_folder = os.path.join(md_folder, "images")
        prefix = os.path.splitext(os.path.basename(md_file))[0]

        os.makedirs(images_folder, exist_ok=True)
        logging.info(f"正在处理：{md_file}")
        image_paths, content = self.extract_image_paths(md_file)
        if not image_paths:
            logging.info(f"无图片引用：{md_file}")
            return

        for index, old_path in enumerate(image_paths):
            old_path = self.normalize_path(old_path.strip())
            old_abs_path = os.path.join(md_folder, old_path) if not os.path.isabs(old_path) else old_path
            if not os.path.exists(old_abs_path):
                logging.warning(f"图片文件不存在：{old_path}")
                continue

            old_filename = os.path.basename(old_abs_path)
            new_filename = f"{prefix}_{index + 1}{os.path.splitext(old_filename)[1].lower()}"
            new_abs_path = os.path.join(images_folder, new_filename)

            # 使用统一路径格式 "./images/"
            new_relative_path = f"./images/{new_filename}".replace("\\", "/")
            content = content.replace(old_path, new_relative_path)

            shutil.move(old_abs_path, new_abs_path)

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"完成：{md_file}")

    @staticmethod
    def normalize_path(path):
        """标准化路径"""
        return os.path.normpath(path).replace("\\", "/")

    @staticmethod
    def extract_image_paths(md_file):
        """提取 Markdown 文件中的图片路径"""
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        return re.findall(r'!\[.*?\]\((.*?)\)', content), content


class TextHandler(logging.Handler):
    """自定义日志处理器"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.after(0, self.text_widget.insert, END, msg + "\n")
        self.text_widget.after(0, self.text_widget.see, END)


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

    filename_without_ext = os.path.splitext(os.path.basename(md_file_path))[0]

    if use_subfolders:
        images_target_path = os.path.join(target_path, images_folder, filename_without_ext)
    else:
        images_target_path = os.path.join(target_path, images_folder)

    os.makedirs(images_target_path, exist_ok=True)

    with open(md_file_path, "r", encoding="utf-8") as f:
        content = f.read()

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

        content = content.replace(img_path, new_relative_image_path.replace("\\", "/"))

    new_md_file_path = os.path.join(target_path, os.path.basename(md_file_path))
    with open(new_md_file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logging.info(f"Markdown 文件处理完成，保存到: {new_md_file_path}")
    return content


def process_markdown_directory(md_dir_path, target_path, images_folder="images", merge=False, use_subfolders=False):
    """批量处理 Markdown 文件，支持合并到一个文件"""
    merged_content = ""

    for root, _, files in os.walk(md_dir_path):
        for file in files:
            if file.lower().endswith(".md"):
                md_file_path = os.path.join(root, file)
                processed_content = process_markdown_file(md_file_path, target_path, images_folder, use_subfolders)
                if merge:
                    header = f"\n\n# 来自文件: {os.path.basename(md_file_path)}\n\n"
                    merged_content += header + processed_content

    if merge:
        merged_file_path = os.path.join(target_path, "合并后的文档.md")
        with open(merged_file_path, "w", encoding="utf-8") as f:
            f.write(merged_content)
        logging.info(f"所有 Markdown 文件已合并并保存至: {merged_file_path}")


if __name__ == "__main__":
    app = Application()
    app.mainloop()
