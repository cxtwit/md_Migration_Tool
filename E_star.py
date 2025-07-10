import os
import shutil
import re
import logging
import time
import customtkinter as ctk
import threading
from tkinter import filedialog, messagebox, PhotoImage
from datetime import datetime
from urllib.parse import urlparse

# 检查并导入拖拽功能库
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    TkinterDnD = None # 如果库不存在，则设置为None

# 检查依赖库是否存在
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

class App(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # --- 主体布局 (图标侧边栏 + 主内容区) ---
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 初始化变量
        self.path_var = ctk.StringVar()
        self.target_var = ctk.StringVar()
        self.merge_var = ctk.BooleanVar(value=False)
        self.subfolder_var = ctk.BooleanVar(value=False)
        self.download_remote_var = ctk.BooleanVar(value=True)

        # 为重命名工具初始化变量
        self.rename_folder_var = ctk.StringVar()
        self.rename_pattern_var = ctk.StringVar(value="{original}_{num}")
        self.rename_start_num_var = ctk.StringVar(value="1")
        self.rename_padding_var = ctk.StringVar(value="3")
        self.rename_folder_var.trace_add('write', self.on_preview_rename)
        self.rename_pattern_var.trace_add('write', self.on_preview_rename)
        self.rename_start_num_var.trace_add('write', self.on_preview_rename)
        self.rename_padding_var.trace_add('write', self.on_preview_rename)

        # 加载图标
        self.load_icons()
        
        # 构建UI
        self.build_sidebar()
        self.build_main_content_area()

        # 默认显示主页
        self.select_frame_by_name("home")
        
        # 配置日志
        self.setup_logging()
        self.check_dependencies()

    def load_icons(self):
        """为亮色和暗色模式分别加载或创建程序中使用的图标"""
        self.icons = {}
        if not PILLOW_AVAILABLE:
            return

        light_mode_icon_color = "#2B2B2B"
        dark_mode_icon_color = "#DCE4EE"

        def create_dual_mode_icon(draw_func):
            light_img = Image.new("RGBA", (28, 28), (0, 0, 0, 0))
            draw_func(ImageDraw.Draw(light_img), light_mode_icon_color)
            dark_img = Image.new("RGBA", (28, 28), (0, 0, 0, 0))
            draw_func(ImageDraw.Draw(dark_img), dark_mode_icon_color)
            return ctk.CTkImage(light_image=light_img, dark_image=dark_img)

        self.icons["home"] = create_dual_mode_icon(
            lambda draw, color: draw.polygon([(14, 4), (4, 14), (8, 14), (8, 24), (20, 24), (20, 14), (24, 14)], fill=color)
        )
        
        self.icons["migration"] = create_dual_mode_icon(
            lambda draw, color: (
                draw.polygon([(6, 8), (14, 2), (22, 8)], fill=color),
                draw.polygon([(6, 20), (14, 26), (22, 20)], fill=color),
                draw.line([(14, 3), (14, 18)], fill=color, width=2)
            )
        )
        
        self.icons["rename"] = create_dual_mode_icon(
            lambda draw, color: (
                draw.polygon([(4, 10), (14, 4), (24, 10), (24, 24), (4, 24)], fill=color),
                draw.ellipse((8, 8, 12, 12), fill="#242424" if color == dark_mode_icon_color else "#EBEBEB")
            )
        )

        self.icons["inplace"] = create_dual_mode_icon(
            lambda draw, color: (
                draw.rectangle((4, 4, 20, 24), fill=color),
                draw.polygon([(16, 6), (24, 14), (22, 16), (14, 8)], fill=color)
            )
        )

        self.icons["log"] = create_dual_mode_icon(
            lambda draw, color: (
                draw.line([(6, 8), (22, 8)], fill=color, width=2),
                draw.line([(6, 14), (22, 14)], fill=color, width=2),
                draw.line([(6, 20), (22, 20)], fill=color, width=2)
            )
        )

    def build_sidebar(self):
        """构建左侧的图标导航栏"""
        self.sidebar_frame = ctk.CTkFrame(self, width=80, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="E*", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=20)

        self.sidebar_buttons = {}
        button_config = {
            "home": {"icon": self.icons.get("home")},
            "migration": {"icon": self.icons.get("migration")},
            "rename": {"icon": self.icons.get("rename")},
            "inplace": {"icon": self.icons.get("inplace")},
            "log": {"icon": self.icons.get("log")},
        }

        for i, (name, config) in enumerate(button_config.items(), start=1):
            btn = ctk.CTkButton(self.sidebar_frame, image=config["icon"], text="",
                                width=50, height=50, fg_color="transparent",
                                hover_color=("#E5E5E5", "#2B2B2B"),
                                command=lambda n=name: self.select_frame_by_name(n))
            btn.grid(row=i, column=0, padx=15, pady=15)
            self.sidebar_buttons[name] = btn

    def build_main_content_area(self):
        """构建右侧的主内容区域和各个功能Frame"""
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)

        self.home_frame = self.create_home_frame()
        self.migration_frame = self.create_migration_frame()
        self.rename_frame = self.create_rename_frame()
        self.inplace_frame = self.create_inplace_frame()
        self.log_frame = self.create_log_frame()
    
    def select_frame_by_name(self, name):
        """根据名称显示对应的Frame"""
        for btn_name, button in self.sidebar_buttons.items():
            button.configure(fg_color=("#DCE4EE", "#1F6AA5") if btn_name == name else "transparent")

        for frame in [self.home_frame, self.migration_frame, self.rename_frame, self.inplace_frame, self.log_frame]:
            frame.grid_forget()

        frame_map = {
            "home": self.home_frame,
            "migration": self.migration_frame,
            "rename": self.rename_frame,
            "inplace": self.inplace_frame,
            "log": self.log_frame,
        }
        selected_frame = frame_map.get(name)
        if selected_frame:
            selected_frame.grid(row=0, column=0, sticky="nsew")

    def create_home_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        
        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.grid(row=0, column=0)

        ctk.CTkLabel(container, text="E_Star Markdown", font=ctk.CTkFont(size=40, weight="bold")).pack(pady=(0, 10))
        ctk.CTkLabel(container, text="by cxtwit", font=ctk.CTkFont(size=16)).pack(pady=(0, 40))
        ctk.CTkLabel(container, text="某pj论坛发个东西处处找事,发不明白，不知道哪来的优越感。", font=ctk.CTkFont(size=12)).pack(pady=(0, 60))
        ctk.CTkButton(container, text="开始文件迁移", height=50, font=ctk.CTkFont(size=16), command=lambda: self.select_frame_by_name("migration")).pack(pady=10, ipadx=10)
        
        theme_frame = ctk.CTkFrame(frame, fg_color="transparent")
        theme_frame.grid(row=1, column=0, pady=20, sticky="s")
        self.theme_switch = ctk.CTkSwitch(theme_frame, text="暗色模式", command=self.toggle_theme)
        self.theme_switch.pack()
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()

        return frame

    def create_migration_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text="文件迁移", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 25))
        ctk.CTkLabel(frame, text="源文件/文件夹 (可拖拽)", font=ctk.CTkFont(size=14)).grid(row=1, column=0, sticky="w")
        source_frame = ctk.CTkFrame(frame, fg_color="transparent")
        source_frame.grid(row=2, column=0, sticky="ew", pady=(5, 15))
        source_frame.grid_columnconfigure(0, weight=1)
        source_entry = ctk.CTkEntry(source_frame, textvariable=self.path_var, height=40)
        source_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(source_frame, text="选择", width=100, height=40, command=self.on_select_input).grid(row=0, column=1, padx=(15, 0))
        
        ctk.CTkLabel(frame, text="目标文件夹 (可拖拽)", font=ctk.CTkFont(size=14)).grid(row=3, column=0, sticky="w")
        target_frame = ctk.CTkFrame(frame, fg_color="transparent")
        target_frame.grid(row=4, column=0, sticky="ew", pady=(5, 25))
        target_frame.grid_columnconfigure(0, weight=1)
        target_entry = ctk.CTkEntry(target_frame, textvariable=self.target_var, height=40)
        target_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(target_frame, text="选择", width=100, height=40, command=self.on_select_target_directory).grid(row=0, column=1, padx=(15, 0))
        
        # 启用拖拽
        if TkinterDnD:
            source_entry.drop_target_register(DND_FILES)
            source_entry.dnd_bind('<<Drop>>', lambda e: self.handle_drop(e, self.path_var))
            target_entry.drop_target_register(DND_FILES)
            target_entry.dnd_bind('<<Drop>>', lambda e: self.handle_drop(e, self.target_var))

        ctk.CTkLabel(frame, text="处理选项", font=ctk.CTkFont(size=14)).grid(row=5, column=0, sticky="w")
        options_frame = ctk.CTkFrame(frame, fg_color="transparent")
        options_frame.grid(row=6, column=0, sticky="ew", pady=(5, 25))
        ctk.CTkCheckBox(options_frame, text="合并多个 Markdown 文件为一个", variable=self.merge_var).pack(anchor="w", pady=8)
        ctk.CTkCheckBox(options_frame, text="图片按 Markdown 文件名存入子文件夹", variable=self.subfolder_var).pack(anchor="w", pady=8)
        self.download_cb_migration = ctk.CTkCheckBox(options_frame, text="下载远程图片到本地", variable=self.download_remote_var)
        self.download_cb_migration.pack(anchor="w", pady=8)
        ctk.CTkButton(frame, text="开始迁移", height=50, font=ctk.CTkFont(size=18, weight="bold"), command=self.start_processing_thread).grid(row=7, column=0, sticky="ew", pady=20)
        return frame

    def create_rename_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(4, weight=1) 

        ctk.CTkLabel(frame, text="批量重命名", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 25))

        folder_frame = ctk.CTkFrame(frame, fg_color="transparent")
        folder_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        folder_frame.grid_columnconfigure(0, weight=1)
        rename_entry = ctk.CTkEntry(folder_frame, textvariable=self.rename_folder_var, placeholder_text="请选择或拖拽包含 .md 文件的文件夹...", height=40)
        rename_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(folder_frame, text="选择文件夹", width=120, height=40, command=self.on_select_rename_folder).grid(row=0, column=1, padx=(15, 0))
        
        if TkinterDnD:
            rename_entry.drop_target_register(DND_FILES)
            rename_entry.dnd_bind('<<Drop>>', lambda e: self.handle_drop(e, self.rename_folder_var))

        rules_frame = ctk.CTkFrame(frame)
        rules_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        rules_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(rules_frame, text="新文件名范式:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        ctk.CTkEntry(rules_frame, textvariable=self.rename_pattern_var).grid(row=1, column=0, columnspan=4, padx=20, pady=(0, 5), sticky="ew")
        ctk.CTkLabel(rules_frame, text="可用占位符: {original} (原文件名), {num} (序号), {date} (日期)", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray").grid(row=2, column=0, columnspan=4, padx=20, pady=(0,15), sticky="w")

        ctk.CTkLabel(rules_frame, text="序号格式:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")
        num_frame = ctk.CTkFrame(rules_frame, fg_color="transparent")
        num_frame.grid(row=4, column=0, columnspan=4, padx=20, pady=(0, 15), sticky="w")
        ctk.CTkLabel(num_frame, text="起始数字:").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(num_frame, textvariable=self.rename_start_num_var, width=80).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(num_frame, text="数字位数 (补零):").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(num_frame, textvariable=self.rename_padding_var, width=80).pack(side="left")

        ctk.CTkLabel(frame, text="重命名预览:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=3, column=0, sticky="w", pady=(10, 5))
        self.rename_preview_box = ctk.CTkTextbox(frame, wrap="none", height=200, font=("Consolas", 12))
        self.rename_preview_box.grid(row=4, column=0, sticky="nsew", pady=(0, 15))
        
        action_frame = ctk.CTkFrame(frame, fg_color="transparent")
        action_frame.grid(row=5, column=0, sticky="ew")
        action_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(action_frame, text="预览重命名", height=40, command=lambda: self.on_preview_rename()).grid(row=0, column=0, padx=(0, 10), sticky="ew")
        ctk.CTkButton(action_frame, text="应用重命名", height=40, font=ctk.CTkFont(weight="bold"), command=self.on_apply_rename).grid(row=0, column=1, padx=(10, 0), sticky="ew")

        return frame

    def create_inplace_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.grid(row=0, column=0, pady=20)
        container.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(container, text="原地处理图片路径", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 25))
        ctk.CTkLabel(container, text="此工具将直接修改所选文件夹内的 Markdown 文件及其引用的本地图片路径。\n请务必在操作前备份您的文件。", wraplength=600, justify="left").grid(row=1, column=0, sticky="w", pady=(0, 30))
        ctk.CTkButton(container, text="选择文件夹并开始处理", height=50, font=ctk.CTkFont(size=16), command=self.start_inplace_thread).grid(row=2, column=0, sticky="ew", pady=20)
        return frame

    def create_log_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        log_header = ctk.CTkFrame(frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        log_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_header, text="实时运行日志", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(log_header, text="清空日志", width=80, command=self.clear_logs).grid(row=0, column=1, sticky="e")
        self.log_textbox = ctk.CTkTextbox(frame, wrap="word", font=("Consolas", 12), border_width=1)
        self.log_textbox.grid(row=1, column=0, sticky="nsew")
        return frame

    def toggle_theme(self):
        mode = ctk.get_appearance_mode()
        new_mode = "dark" if mode == "Light" else "light"
        ctk.set_appearance_mode(new_mode)
        self.theme_switch.configure(text="亮色模式" if new_mode == "Light" else "暗色模式")

    def clear_logs(self):
        self.log_textbox.delete("1.0", "end")

    def setup_logging(self):
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        if root_logger.hasHandlers(): root_logger.handlers.clear()
        gui_handler = TextHandler(self.log_textbox)
        gui_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s", "%H:%M:%S"))
        root_logger.addHandler(gui_handler)
    
    def check_dependencies(self):
        if not TkinterDnD:
            logging.error("拖拽功能不可用: 未找到 'tkinterdnd2' 库。")
            messagebox.showwarning("缺少库", "未找到 'tkinterdnd2' 库。\n拖拽功能将被禁用。\n请通过 'pip install tkinterdnd2' 安装。")
        if not REQUESTS_AVAILABLE:
            logging.warning("依赖库 'requests' 未找到，远程图片下载功能已禁用。")
            if hasattr(self, 'download_cb_migration'): self.download_cb_migration.configure(state="disabled")
        if not PILLOW_AVAILABLE:
            logging.warning("依赖库 'Pillow' 未找到，图标将无法显示。")

    def handle_drop(self, event, string_var):
        """处理文件拖拽事件"""
        # event.data 通常是一个包含花括号的字符串，如 '{C:/Users/Test/file.md}'
        # 或者多个文件 '{C:/file1.txt} {C:/file2.txt}'
        # 我们只取第一个有效路径
        path = event.data.strip()
        if '{' in path and '}' in path:
            # 提取第一个花括号内的内容
            path = path[path.find('{')+1 : path.find('}')]
        string_var.set(path)
        logging.info(f"已通过拖拽设置路径: {path}")

    def start_processing_thread(self):
        threading.Thread(target=self.on_process_migration, daemon=True).start()

    def start_inplace_thread(self):
        threading.Thread(target=self.on_select_md_directory, daemon=True).start()

    def on_select_input(self):
        response = messagebox.askyesno("选择模式", "是否批量处理文件夹中的所有 Markdown 文件？\n\n- 是: 请选择一个文件夹。\n- 否: 请选择一个单独的 Markdown 文件。", icon='question')
        path = filedialog.askdirectory() if response else filedialog.askopenfilename(filetypes=[("Markdown files", "*.md")])
        if path: self.path_var.set(path)

    def on_select_target_directory(self):
        path = filedialog.askdirectory()
        if path: self.target_var.set(path)

    def on_process_migration(self):
        source_path, target_path = self.path_var.get().strip(), self.target_var.get().strip()
        if not source_path or not target_path:
            messagebox.showerror("错误", "源路径和目标路径均不能为空！")
            return
        setup_file_logging(target_path)
        logging.info("--- 开始文件迁移任务 ---")
        try:
            if os.path.isdir(source_path):
                process_markdown_directory(source_path, target_path, merge=self.merge_var.get(), use_subfolders=self.subfolder_var.get(), download_remote=self.download_remote_var.get())
            elif os.path.isfile(source_path) and source_path.lower().endswith(".md"):
                process_markdown_file(source_path, target_path, use_subfolders=self.subfolder_var.get(), download_remote=self.download_remote_var.get())
            else:
                raise ValueError("无效的路径类型！")
            logging.info("--- 文件迁移任务完成 ---")
            messagebox.showinfo("完成", "文件迁移任务处理完成！")
        except Exception as e:
            logging.error(f"处理失败：{e}")
            messagebox.showerror("错误", f"处理失败：{e}")

    def on_select_md_directory(self):
        directory = filedialog.askdirectory(title="选择需要原地处理的 Markdown 文件夹")
        if directory:
            setup_file_logging(directory)
            logging.info(f"--- 开始原地处理任务: {directory} ---")
            process_all_md_files(directory)
            logging.info("--- 原地处理任务完成 ---")

    def on_select_rename_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.rename_folder_var.set(path)

    def get_rename_preview(self):
        folder = self.rename_folder_var.get()
        if not os.path.isdir(folder):
            return None, "请先选择一个有效的文件夹。"

        pattern = self.rename_pattern_var.get()
        if not pattern:
            return None, "错误：新文件名范式不能为空。"
            
        try:
            start_num = int(self.rename_start_num_var.get())
            padding = int(self.rename_padding_var.get())
        except ValueError:
            return None, "错误：起始数字和数字位数必须是整数。"

        files = sorted([f for f in os.listdir(folder) if f.lower().endswith(".md")])
        if not files:
            return None, "在指定文件夹中未找到 .md 文件。"

        preview_map = {}
        current_date = datetime.now().strftime('%Y-%m-%d')
        for i, old_name in enumerate(files):
            base, ext = os.path.splitext(old_name)
            
            new_base = pattern
            number_part = str(start_num + i).zfill(padding)

            new_base = new_base.replace("{original}", base)
            new_base = new_base.replace("{num}", number_part)
            new_base = new_base.replace("{date}", current_date)
            
            new_name = new_base + ext
            preview_map[old_name] = new_name
            
        return preview_map, None

    def on_preview_rename(self, *args):
        self.rename_preview_box.delete("1.0", "end")
        preview_map, error = self.get_rename_preview()

        if error:
            self.rename_preview_box.insert("1.0", error)
            return

        max_len = max(len(k) for k in preview_map.keys()) if preview_map else 0
        for old, new in preview_map.items():
            self.rename_preview_box.insert("end", f"{old:<{max_len}}  ->  {new}\n")
    
    def on_apply_rename(self):
        preview_map, error = self.get_rename_preview()
        if error:
            messagebox.showerror("错误", error)
            return
        
        folder = self.rename_folder_var.get()
        
        new_names = list(preview_map.values())
        if len(new_names) != len(set(new_names)):
            messagebox.showerror("错误", "重命名规则导致文件名冲突，请修改规则后重试。")
            return

        msg = "即将按以下规则重命名文件：\n\n"
        for old, new in list(preview_map.items())[:5]:
            msg += f"{old} -> {new}\n"
        if len(preview_map) > 5:
            msg += "...\n"
        msg += f"\n共计 {len(preview_map)} 个文件。此操作不可撤销，是否继续？"

        if not messagebox.askyesno("确认操作", msg):
            return

        logging.info(f"--- 开始批量重命名任务: {folder} ---")
        try:
            for old, new in preview_map.items():
                old_path = os.path.join(folder, old)
                new_path = os.path.join(folder, new)
                os.rename(old_path, new_path)
                logging.info(f"重命名: {old} -> {new}")
            logging.info("--- 批量重命名任务完成 ---")
            messagebox.showinfo("完成", "批量重命名已成功应用！")
        except Exception as e:
            logging.error(f"重命名失败: {e}")
            messagebox.showerror("错误", f"重命名失败: {e}")
        
        self.on_preview_rename()

# --- Helper Classes and Functions ---
class TextHandler(logging.Handler):
    def __init__(self, textbox):
        super().__init__()
        self.textbox = textbox
    def emit(self, record):
        self.textbox.insert("end", self.format(record) + "\n")
        self.textbox.see("end")

def setup_file_logging(target_path):
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_filename = os.path.join(target_path, f"{current_date}_迁移日志.log")
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler): root_logger.removeHandler(handler)
    file_handler = logging.FileHandler(log_filename, mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    root_logger.addHandler(file_handler)
    logging.info(f"日志将记录到文件：{log_filename}")

def _get_unique_filepath(target_dir, filename):
    new_path = os.path.join(target_dir, filename)
    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(new_path):
        new_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
        counter += 1
    return new_path

def normalize_path(path): return os.path.normpath(path).replace("\\", "/")

def extract_image_paths(md_file):
    with open(md_file, "r", encoding="utf-8") as f: content = f.read()
    return re.findall(r'!\[.*?\]\((.*?)\)', content), content

def process_all_md_files(md_dir):
    if not os.path.isdir(md_dir):
        messagebox.showerror("错误", "提供的路径不是有效目录！")
        return
    md_files = [f for f in os.listdir(md_dir) if f.endswith(".md")]
    if not md_files:
        messagebox.showwarning("提示", "未找到任何 Markdown 文件！")
        return
    for file_name in md_files:
        md_file = os.path.join(md_dir, file_name)
        process_images_and_update_md(md_file)
    messagebox.showinfo("完成", f"原地处理完成！共处理 {len(md_files)} 个 Markdown 文件。")

def process_images_and_update_md(md_file):
    md_folder, prefix = os.path.dirname(md_file), os.path.splitext(os.path.basename(md_file))[0]
    images_folder = os.path.join(md_folder, "images")
    os.makedirs(images_folder, exist_ok=True)
    logging.info(f"正在处理：{md_file}")
    image_paths, content = extract_image_paths(md_file)
    if not image_paths:
        logging.info(f"无图片引用：{md_file}"); return
    for index, old_path in enumerate(image_paths):
        if old_path.startswith(("http://", "https://")): continue
        # BUG FIX: Add check for already processed paths
        if old_path.startswith("./images/"):
            logging.info(f"路径已处理，跳过: {old_path}")
            continue
        old_path_normalized = normalize_path(old_path.strip())
        old_abs_path = os.path.join(md_folder, old_path_normalized) if not os.path.isabs(old_path_normalized) else old_path_normalized
        if not os.path.exists(old_abs_path):
            logging.warning(f"图片文件不存在：{old_path}"); continue
        # BUG FIX: Assign old_filename first before using it
        old_filename = os.path.basename(old_abs_path)
        new_filename = f"{prefix}_{index + 1}{os.path.splitext(old_filename)[1].lower()}"
        new_abs_path, new_relative_path = os.path.join(images_folder, new_filename), f"./images/{new_filename}".replace("\\", "/")
        content = content.replace(old_path, new_relative_path)
        shutil.move(old_abs_path, new_abs_path)
        logging.info(f"图片 '{old_filename}' 已移动并重命名为 '{new_filename}'")
    with open(md_file, "w", encoding="utf-8") as f: f.write(content)
    logging.info(f"完成：{md_file}")

def process_markdown_file(md_file_path, target_path, images_folder="images", use_subfolders=False, download_remote=False):
    if not os.path.exists(md_file_path):
        logging.error(f"Markdown 文件不存在: {md_file_path}"); return ""
    filename_without_ext = os.path.splitext(os.path.basename(md_file_path))[0]
    images_target_path = os.path.join(target_path, images_folder, filename_without_ext) if use_subfolders else os.path.join(target_path, images_folder)
    os.makedirs(images_target_path, exist_ok=True)
    with open(md_file_path, "r", encoding="utf-8") as f: content = f.read()
    found_images = re.findall(r"!\[.*?\]\((.*?)\)", content)
    for img_path in found_images:
        original_img_path_for_replace, new_img_path_abs = img_path, ""
        is_remote = img_path.startswith(("http://", "https://"))
        if is_remote:
            if not download_remote: continue
            if not REQUESTS_AVAILABLE: logging.warning(f"跳过远程图片 (requests 库未安装): {img_path}"); continue
            try:
                logging.info(f"准备下载远程图片: {img_path}")
                response = requests.get(img_path, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()
                parsed_path = urlparse(img_path).path
                img_filename = os.path.basename(parsed_path)
                if not img_filename or '.' not in img_filename:
                    content_type = response.headers.get('content-type')
                    ext = ".jpg"
                    if content_type and 'image' in content_type: ext = "." + content_type.split('/')[-1]
                    img_filename = f"remote_image_{int(time.time())}{ext}"
                new_img_path_abs = _get_unique_filepath(images_target_path, img_filename)
                with open(new_img_path_abs, "wb") as f: f.write(response.content)
                logging.info(f"图片下载成功: {img_path} → {new_img_path_abs}")
            except requests.exceptions.RequestException as e:
                logging.error(f"下载远程图片失败: {img_path}, 错误: {e}"); continue
        else:
            img_source_path = os.path.abspath(os.path.join(os.path.dirname(md_file_path), img_path))
            if not os.path.exists(img_source_path): logging.warning(f"本地图片文件不存在: {img_source_path}"); continue
            img_filename = os.path.basename(img_source_path)
            new_img_path_abs = _get_unique_filepath(images_target_path, img_filename)
            shutil.copy2(img_source_path, new_img_path_abs)
            logging.info(f"本地图片迁移成功: {img_path} → {new_img_path_abs}")
        
        if new_img_path_abs:
            new_relative_path = f"./{images_folder}/{filename_without_ext}/{os.path.basename(new_img_path_abs)}" if use_subfolders else f"./{images_folder}/{os.path.basename(new_img_path_abs)}"
            content = content.replace(original_img_path_for_replace, new_relative_path.replace("\\", "/"))
    
    new_md_file_path = os.path.join(target_path, os.path.basename(md_file_path))
    with open(new_md_file_path, "w", encoding="utf-8") as f: f.write(content)
    logging.info(f"Markdown 文件处理完成: {new_md_file_path}")
    return content

def process_markdown_directory(md_dir_path, target_path, images_folder="images", merge=False, use_subfolders=False, download_remote=False):
    merged_content = ""
    for root, _, files in os.walk(md_dir_path):
        for file in files:
            if file.lower().endswith(".md"):
                md_file_path = os.path.join(root, file)
                # BUG FIX: Capture the returned content for merging
                processed_content = process_markdown_file(md_file_path, target_path, images_folder, use_subfolders, download_remote)
                if merge and processed_content:
                    header = f"\n\n# 来自文件: {os.path.basename(md_file_path)}\n\n"
                    merged_content += header + processed_content
    if merge:
        merged_file_path = os.path.join(target_path, "合并后的文档.md")
        with open(merged_file_path, "w", encoding="utf-8") as f: f.write(merged_content)
        logging.info(f"所有 Markdown 文件已合并并保存至: {merged_file_path}")

if __name__ == "__main__":
    # 为了使用tkinterdnd2，主窗口需要是TkinterDnD.Tk()
    if TkinterDnD:
        root = TkinterDnD.Tk()
    else:
        # 如果库不存在，则回退到普通的CTk窗口
        root = ctk.CTk()

    root.title("E`Star Markdown 工具集")
    root.geometry("1000x800")
    root.minsize(950, 750)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # BUG FIX: Set a custom icon for the main window
    if PILLOW_AVAILABLE:
        icon_image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(icon_image)
        try:
            # Try to use a more robust font
            font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()
        draw.text((4, 2), "E*", font=font, fill="#1F6AA5")
        photo_icon = ImageTk.PhotoImage(image=icon_image)
        root.iconphoto(True, photo_icon)


    app = App(master=root)
    root.mainloop()
