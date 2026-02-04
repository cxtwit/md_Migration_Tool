import sys
import os
import shutil
import re
import logging
import requests
import time
import threading
import subprocess
from datetime import datetime
from urllib.parse import urlparse
from collections import deque

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame, QStackedWidget, QLineEdit, 
    QListWidget, QGraphicsDropShadowEffect, QGridLayout, QSizePolicy,
    QCheckBox, QDialog, QTextEdit, QFileDialog, QMessageBox, QSpinBox, QComboBox
)
from PySide6.QtCore import Qt, QSize, QPoint, Signal, QObject
from PySide6.QtGui import QColor, QPainter, QPen, QIcon, QPixmap, QFont

# ============================================================================
# 1. 视觉样式 (Wide Soft Theme + SpinBox 终极美化)
# ============================================================================

# [SVG 资源]
CHECK_ICON = "url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+')"
ARROW_UP = "url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSIxMiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NjYiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSIxOCAxNSAxMiA5IDYgMTUiPjwvcG9seWxpbmU+PC9zdmc+')"
ARROW_DOWN = "url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSIxMiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NjYiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSI2IDkgMTIgMTUgMTggOSI+PC9wb2x5bGluZT48L3N2Zz4=')"

FLOW_STYLE = f"""
/* 全局去焦框 */
* {{ outline: none; }}

QMainWindow, QWidget#CentralWidget {{
    background-color: #F7F9FC;
    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
    color: #333;
}}

QLabel[class="BigTitle"] {{ font-size: 42px; font-weight: 900; color: #111; letter-spacing: 2px; }}
QLabel[class="SubTitle"] {{ font-size: 16px; color: #666; font-weight: 500; margin-bottom: 30px; }}

/* 启动台卡片 */
QPushButton[class="LaunchCard"] {{
    background-color: #FFFFFF; border: 1px solid #EEEEEE; border-radius: 24px;
    text-align: left; padding: 35px; color: #333;
}}
QPushButton[class="LaunchCard"]:hover {{
    background-color: #FFFFFF; border: 2px solid #0066FF; color: #0066FF;
}}

/* 返回按钮 */
QPushButton[class="BackBtn"] {{
    background-color: #FFFFFF; border: 1px solid #E0E0E0; color: #555; 
    font-size: 14px; font-weight: 700; padding: 8px 15px; border-radius: 18px;
}}
QPushButton[class="BackBtn"]:hover {{
    background-color: #F0F5FF; border: 1px solid #0066FF; color: #0066FF; 
}}

/* 文件夹选择按钮 */
QPushButton[class="FolderBtn"] {{
    background-color: #F0F2F5; border: 1px solid #DDD; border-radius: 10px;
    color: #555; font-weight: 600; font-size: 13px;
}}
QPushButton[class="FolderBtn"]:hover {{
    background-color: #E6E8EB; border-color: #BBB; color: #333;
}}

/* 工作区 */
QFrame[class="Workspace"] {{ 
    background-color: #FFFFFF; border-radius: 20px; border: 1px solid #E5E5E5; 
}}

/* 通用输入框 */
QLineEdit, QComboBox {{
    background: #F0F2F5; border: 1px solid transparent; color: #111;
    padding: 12px 15px; font-size: 14px; border-radius: 12px;
}}
QLineEdit:focus, QComboBox:focus {{ background: #FFFFFF; border: 2px solid #0066FF; }}

/* [重磅修复] QSpinBox 数字选择器 - 加宽、舒适化 */
QSpinBox {{
    background: #F0F2F5; 
    border: 1px solid transparent; 
    color: #111;
    padding: 12px 10px 12px 15px; /* 上右下左 */
    font-size: 14px; 
    border-radius: 12px;
    min-width: 100px; /* 强制最小宽度，解决“挤”的问题 */
}}
QSpinBox:focus {{
    background: #FFFFFF; 
    border: 2px solid #0066FF;
}}
/* 上下按钮容器 */
QSpinBox::up-button, QSpinBox::down-button {{
    subcontrol-origin: border;
    width: 28px; /* 加宽按钮区域 */
    background: transparent; 
    border: none;
}}
QSpinBox::up-button {{
    subcontrol-position: top right;
    margin: 3px;
    border-radius: 4px;
}}
QSpinBox::down-button {{
    subcontrol-position: bottom right;
    margin: 3px;
    border-radius: 4px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: #E0E0E0; 
}}
/* 箭头图标 */
QSpinBox::up-arrow {{
    image: {ARROW_UP}; width: 10px; height: 10px;
}}
QSpinBox::down-arrow {{
    image: {ARROW_DOWN}; width: 10px; height: 10px;
}}

/* 预览框 */
QTextEdit {{
    background: #F9FAFB; border: 1px solid #EEE; border-radius: 12px; padding: 10px; 
    color: #555; font-family: Consolas; font-size: 13px;
}}

/* 按钮组 */
QPushButton[class="ActionBtn"] {{
    background-color: #111; color: #FFF; border: none; padding: 14px 40px;
    font-weight: 700; font-size: 14px; border-radius: 25px;
}}
QPushButton[class="ActionBtn"]:hover {{ background-color: #0066FF; }}
QPushButton[class="ActionBtn"]:disabled {{ background-color: #EEE; color: #BBB; }}

QPushButton[class="GhostBtn"] {{
    background: transparent; border: 2px solid #E0E0E0; color: #666;
    padding: 12px 30px; font-weight: 600; font-size: 14px; border-radius: 25px;
}}
QPushButton[class="GhostBtn"]:hover {{ border-color: #111; color: #111; }}

/* 统计数据 */
QLabel[class="StatNumber"] {{ font-size: 32px; font-weight: 800; color: #111; border: none; }}
QLabel[class="StatLabel"] {{ font-size: 12px; font-weight: 600; color: #999; letter-spacing: 1px; border: none; }}

/* 复选框样式 */
QCheckBox {{ spacing: 10px; font-size: 14px; font-weight: 500; color: #444; margin-left: 2px; }}
QCheckBox::indicator {{ 
    width: 20px; height: 20px; 
    border-radius: 6px; 
    border: 2px solid #DDD; 
    background: #FFF;
}}
QCheckBox::indicator:checked {{ 
    background-color: #0066FF; 
    border-color: #0066FF;
    image: {CHECK_ICON};
}}
QCheckBox::indicator:hover {{ border-color: #0066FF; }}
"""

# ============================================================================
# 2. 几何图标
# ============================================================================
class GeoIcon:
    @staticmethod
    def get(name, color="#111111"):
        size = 64
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(color)); pen.setWidth(3); 
        pen.setCapStyle(Qt.RoundCap); pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        
        if name == "audit": 
            p.drawEllipse(QPoint(32, 32), 12, 12)
            p.drawLine(8, 32, 16, 32); p.drawLine(48, 32, 56, 32)
            p.drawLine(32, 8, 32, 16); p.drawLine(32, 48, 32, 56)
        elif name == "migrate": 
            p.drawLine(14, 20, 50, 20); p.drawLine(40, 12, 50, 20); p.drawLine(40, 28, 50, 20)
            p.drawLine(50, 44, 14, 44); p.drawLine(24, 36, 14, 44); p.drawLine(24, 52, 14, 44)
        elif name == "rename": 
            p.drawRoundedRect(12, 16, 32, 32, 6, 6)
            p.drawLine(44, 16, 54, 26); p.drawLine(54, 26, 54, 38)
            p.drawLine(54, 38, 44, 48); p.drawLine(44, 48, 12, 48)
        elif name == "inplace": 
            p.drawRoundedRect(14, 22, 36, 32, 6, 6)
            p.drawLine(14, 22, 22, 10); p.drawLine(50, 22, 42, 10); p.drawLine(22, 10, 42, 10)
        elif name == "arrow_left":
            p.drawLine(38, 18, 22, 32); p.drawLine(22, 32, 38, 46)
        elif name == "log":
            p.drawRect(16, 12, 32, 40)
            p.drawLine(22, 22, 42, 22); p.drawLine(22, 30, 42, 30); p.drawLine(22, 38, 32, 38)
        elif name == "folder": 
            p.drawLine(8, 20, 24, 20); p.drawLine(28, 16, 56, 16); p.drawLine(56, 16, 56, 48); p.drawLine(56, 48, 8, 48); p.drawLine(8, 48, 8, 20)
            
        p.end()
        return QIcon(pix)

# ============================================================================
# 3. 启动台卡片
# ============================================================================
class LaunchCard(QPushButton):
    def __init__(self, title, subtitle, icon_name, parent_win, target_idx):
        super().__init__()
        self.setProperty("class", "LaunchCard")
        self.setMinimumSize(240, 260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)
        self.parent_win = parent_win
        self.target_idx = target_idx
        self.icon_name = icon_name
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setColor(QColor(0,0,0,8)); shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
        
        l = QVBoxLayout(self); l.setContentsMargins(30, 30, 30, 30)
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(GeoIcon.get(icon_name, "#333").pixmap(64, 64))
        l.addWidget(self.icon_lbl); l.addStretch()
        t = QLabel(title); t.setStyleSheet("font-size: 22px; font-weight: 800; color: #111; border: none;")
        l.addWidget(t)
        s = QLabel(subtitle); s.setStyleSheet("font-size: 13px; color: #888; border: none;")
        s.setWordWrap(True); l.addWidget(s)
        self.clicked.connect(lambda: self.parent_win.navigate_to(self.target_idx))

    def enterEvent(self, e):
        self.icon_lbl.setPixmap(GeoIcon.get(self.icon_name, "#0066FF").pixmap(64, 64))
        super().enterEvent(e)
    def leaveEvent(self, e):
        self.icon_lbl.setPixmap(GeoIcon.get(self.icon_name, "#333").pixmap(64, 64))
        super().leaveEvent(e)

# ==========================================
# 4. 业务逻辑
# ==========================================
class MarkdownLogicCore(QObject):
    log_signal = Signal(str); task_finished = Signal(bool, str); scan_finished = Signal(list)
    info_ready = Signal(dict); rename_preview_ready = Signal(str); undo_available = Signal(bool)

    def __init__(self):
        super().__init__()
        self.img_pattern = r'!\[.*?\]\((.*?)\)'
        self.rename_history = [] 

    def log(self, msg): self.log_signal.emit(msg); logging.info(msg)
    def normalize_path(self, path): return os.path.normpath(path.strip()).replace("\\", "/")
    
    def _get_unique_path(self, target_dir, filename):
        new_path = os.path.join(target_dir, filename); base, ext = os.path.splitext(filename); counter = 1
        while os.path.exists(new_path): new_path = os.path.join(target_dir, f"{base}_{counter}{ext}"); counter += 1
        return new_path

    # --- Rename Logic ---
    def execute_rename_batch(self, folder, pattern, start_num, pad):
        if not os.path.isdir(folder): return self.task_finished.emit(False, "无效文件夹")
        try:
            files = sorted([f for f in os.listdir(folder) if f.lower().endswith(".md")])
            if not files: return self.task_finished.emit(False, "无 MD 文件")
            trans, succ = [], 0
            self.log(f"--- [重命名] 开始: {len(files)} 文件 ---")
            for i, old in enumerate(files):
                base, ext = os.path.splitext(old)
                new = pattern.replace("{original}", base).replace("{num}", str(start_num + i).zfill(pad)).replace("{date}", datetime.now().strftime("%Y%m%d")) + ext
                op, np = os.path.join(folder, old), os.path.join(folder, new)
                if old != new:
                    try: os.rename(op, np); trans.append((np, op)); succ += 1; self.log(f"Ren: {old}->{new}")
                    except: pass
            if trans: self.rename_history.append(trans); self.undo_available.emit(True); self.task_finished.emit(True, f"成功重命名 {succ} 个文件")
            else: self.task_finished.emit(True, "无变更")
        except Exception as e: self.task_finished.emit(False, str(e))

    def undo_last_rename(self):
        if not self.rename_history: return self.task_finished.emit(False, "无撤销记录")
        trans = self.rename_history.pop(); cnt = 0
        for cp, op in reversed(trans):
            if os.path.exists(cp):
                try: os.rename(cp, op); cnt += 1
                except: pass
        if not self.rename_history: self.undo_available.emit(False)
        self.task_finished.emit(True, f"已撤销 {cnt} 个文件")

    def generate_rename_preview(self, folder, pattern, start, pad):
        if not folder or not os.path.isdir(folder): return
        try:
            files = sorted([f for f in os.listdir(folder) if f.lower().endswith(".md")])
            t = f"预览 {len(files)} 个文件:\n" + "-"*30 + "\n"
            for i, old in enumerate(files):
                new = pattern.replace("{original}", os.path.splitext(old)[0]).replace("{num}", str(start+i).zfill(pad)).replace("{date}", datetime.now().strftime("%Y%m%d"))+os.path.splitext(old)[1]
                t += f"{old} -> {new}\n"
            self.rename_preview_ready.emit(t)
        except: pass

    # --- Audit Logic ---
    def analyze_path_entry(self, ipath):
        self.log(f"--- [审计] {ipath} ---")
        if os.path.isfile(ipath): self._analyze_single(ipath)
        elif os.path.isdir(ipath): self._analyze_batch(ipath)
        else: self.task_finished.emit(False, "路径无效")

    def _analyze_batch(self, f):
        mds = [os.path.join(r,x) for r,_,fs in os.walk(f) for x in fs if x.endswith('.md')]
        tr, tp, reds = 0,0,[]
        for m in mds:
            r = self._core_audit(m)
            if r: tr+=r['ref']; tp+=r['phy']; reds.extend(r['red'])
        self.info_ready.emit({"md_cnt":len(mds),"ref_cnt":tr,"phy_cnt":tp,"red_cnt":len(reds),"red_list":reds})

    def _analyze_single(self, f):
        r = self._core_audit(f)
        if r: self.info_ready.emit({"md_cnt":1,"ref_cnt":r['ref'],"phy_cnt":r['phy'],"red_cnt":len(r['red']),"red_list":r['red']})

    def _core_audit(self, fpath):
        try:
            with open(fpath,'r',encoding='utf-8',errors='ignore') as f: c=f.read()
            refs={os.path.basename(self.normalize_path(m)) for m in re.findall(self.img_pattern,c) if not m.startswith('http')}
            d=os.path.dirname(fpath); n=os.path.splitext(os.path.basename(fpath))[0]
            cands=[os.path.join(d,"images",n), os.path.join(d,"images"), os.path.join(d,"assets"), d]
            tgt,phys=None,[]
            for cd in cands:
                if os.path.exists(cd) and os.path.isdir(cd):
                    fs=[x for x in os.listdir(cd) if os.path.isfile(os.path.join(cd,x))]
                    if (set(fs)&refs) or (cd.endswith(n) and "images" in cd): tgt,phys=cd,fs; break
            reds=[os.path.join(tgt,x) for x in phys if x not in refs and not x.endswith('.md')] if tgt else []
            return {"ref":len(refs),"phy":len(phys) if tgt else 0,"red":reds}
        except: return None

    def cleanup_files(self, fl, forever):
        cnt=0
        for p in fl:
            if os.path.exists(p):
                try:
                    if forever: os.remove(p); self.log(f"[删] {os.path.basename(p)}")
                    else:
                        bd=os.path.join(os.path.dirname(p),"unused_backup"); os.makedirs(bd,exist_ok=True)
                        shutil.move(p,os.path.join(bd,os.path.basename(p))); self.log(f"[移] {os.path.basename(p)}")
                    cnt+=1
                except Exception as e: self.log(f"Err: {e}")
        return cnt

    # --- Migration Logic ---
    def process_migration(self, src, dst, cfg):
        try:
            fs = []
            if os.path.isfile(src): fs=[src]
            elif os.path.isdir(src): fs=[os.path.join(r,f) for r,_,x in os.walk(src) for f in x if f.endswith('.md')]
            
            if not fs: return self.task_finished.emit(False, "无 MD 文件")
            
            out_md = os.path.abspath(os.path.join(dst, "合并后的文档.md"))
            fs = [f for f in fs if os.path.abspath(f) != out_md]
            
            merged, procs = "", []
            self.log(f"--- [迁移] {len(fs)} 文件 -> {dst} ---")
            
            for f in fs:
                self.log(f"处理: {os.path.basename(f)}")
                cnt = self._mig_core(f, dst, cfg); procs.append(cnt)
                if cfg['merge']: merged += f"\n\n# {os.path.basename(f)}\n\n"+cnt
            
            if cfg['merge'] and merged:
                with open(out_md,'w',encoding='utf-8') as f: f.write(merged)
                self.log(f"合并完成: {out_md}")
            
            unused = self._scan_unused(procs, dst) if cfg['cleanup'] else []
            self.scan_finished.emit(unused)
            
            self.task_finished.emit(True, f"迁移成功！已处理 {len(fs)} 个文件。")
            
        except Exception as e: self.task_finished.emit(False, str(e))

    def _mig_core(self, fpath, root, cfg):
        name = os.path.splitext(os.path.basename(fpath))[0]
        tdir = os.path.join(root, "images", name) if cfg['subfolder'] else os.path.join(root, "images")
        os.makedirs(tdir, exist_ok=True)
        with open(fpath,'r',encoding='utf-8') as f: txt=f.read()
        for u in re.findall(self.img_pattern, txt):
            new_abs=""
            if u.startswith('http'):
                if cfg['download']:
                    try:
                        r=requests.get(u,timeout=10); n=os.path.basename(urlparse(u).path) or f"web_{int(time.time())}.jpg"
                        p=self._get_unique_path(tdir,n); open(p,'wb').write(r.content); new_abs=p
                        self.log(f" [下载] {n}")
                    except: pass
            else:
                src=os.path.abspath(os.path.join(os.path.dirname(fpath),self.normalize_path(u)))
                if os.path.exists(src):
                    new_abs=self._get_unique_path(tdir,os.path.basename(src)); shutil.copy2(src,new_abs)
            
            if new_abs:
                sub = f"{name}/" if cfg['subfolder'] else ""
                rel = f"./images/{sub}{os.path.basename(new_abs)}".replace("//","/")
                txt = txt.replace(u, rel)
        
        if not cfg.get('merge'):
            open(os.path.join(root,os.path.basename(fpath)),'w',encoding='utf-8').write(txt)
        return txt

    def _scan_unused(self, cnts, root):
        refs = {os.path.basename(self.normalize_path(r)) for c in cnts for r in re.findall(self.img_pattern,c)}
        u=[]
        img_root = os.path.join(root,"images")
        if os.path.exists(img_root):
            for r,_,fs in os.walk(img_root):
                if "unused" in r: continue
                for f in fs:
                    if f not in refs: u.append(os.path.join(r,f))
        return u

    # --- Inplace Logic ---
    def process_inplace(self, folder, cln):
        try:
            fs = [f for f in os.listdir(folder) if f.endswith('.md')]
            if not fs: return self.task_finished.emit(False, "无 MD 文件")
            self.log(f"--- [原地] 处理 {len(fs)} 文件 ---")
            procs = []
            for fn in fs:
                fp=os.path.join(folder,fn); md_dir=os.path.dirname(fp); pfx=os.path.splitext(fn)[0]
                img_dir=os.path.join(md_dir,"images"); os.makedirs(img_dir,exist_ok=True)
                with open(fp,'r',encoding='utf-8') as f: txt=f.read()
                for i,u in enumerate(re.findall(self.img_pattern, txt)):
                    if u.startswith(('http','./images/')): continue
                    src=os.path.join(md_dir,self.normalize_path(u))
                    if os.path.exists(src):
                        nn=f"{pfx}_{i+1}{os.path.splitext(src)[1]}"; shutil.move(src,os.path.join(img_dir,nn))
                        txt=txt.replace(u, f"./images/{nn}")
                        self.log(f" [整理] {os.path.basename(src)} -> {nn}")
                open(fp,'w',encoding='utf-8').write(txt); procs.append(txt)
            u=self._scan_unused(procs,folder) if cln else []
            self.scan_finished.emit(u)
            self.task_finished.emit(True, f"整理完成！已处理 {len(fs)} 个文件。")
        except Exception as e: self.task_finished.emit(False, str(e))

# ============================================================================
# 5. 主窗口 (Application)
# ============================================================================
class EStarApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MarkDown 小助手 v2026.30")
        self.resize(1180, 800)
        
        app = QApplication.instance()
        if app: app.setStyleSheet(FLOW_STYLE)
        
        self.core = MarkdownLogicCore()
        
        self.core.log_signal.connect(self.append_log)
        self.core.task_finished.connect(self.on_task_done)
        self.core.scan_finished.connect(self.on_scan_done)
        self.core.info_ready.connect(self.on_info_ready)
        self.core.rename_preview_ready.connect(self.on_ren_preview)
        self.core.undo_available.connect(self.on_undo_state_change)
        
        self.recent_logs = deque(maxlen=100)
        self.current_log_file = f"EStar_{datetime.now().strftime('%Y%m%d')}.log"
        self.setup_logging()
        
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        self.init_launchpad()
        self.init_tool_page(1, "资源审计", "RESOURCE AUDIT", self.ui_audit_content)
        self.init_tool_page(2, "迁移合并", "MIGRATION", self.ui_migrate_content)
        self.init_tool_page(3, "批量重命名", "BATCH RENAME", self.ui_rename_content)
        self.init_tool_page(4, "原地整理", "INPLACE FIX", self.ui_inplace_content)

    def navigate_to(self, idx): self.stack.setCurrentIndex(idx)
    def go_home(self): self.stack.setCurrentIndex(0)
    
    def setup_logging(self):
        logging.basicConfig(filename=self.current_log_file, level=logging.INFO, 
                            format='%(asctime)s %(message)s', encoding='utf-8')

    def append_log(self, t):
        self.recent_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {t}")

    def show_logs(self):
        d = QDialog(self); d.setWindowTitle("运行日志"); d.resize(800, 600)
        d.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QTextEdit { background-color: #F7F9FC; color: #333; border: 1px solid #E0E0E0; font-family: Consolas; font-size: 13px; border-radius: 8px; padding: 10px; }
            QPushButton { background-color: #111; color: white; border-radius: 20px; padding: 10px 20px; font-weight: bold; border:none; }
            QPushButton:hover { background-color: #0066FF; }
        """)
        l = QVBoxLayout(d); t = QTextEdit(); t.setReadOnly(True)
        t.setPlainText("\n".join(self.recent_logs))
        l.addWidget(t)
        b = QPushButton("打开日志文件"); b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(lambda: os.startfile(self.current_log_file) if os.path.exists(self.current_log_file) else None)
        l.addWidget(b); d.exec()

    # --- 首页 ---
    def init_launchpad(self):
        p = QWidget(); l = QVBoxLayout(p); l.setAlignment(Qt.AlignCenter)
        
        header = QLabel("MarkDown 小助手"); header.setProperty("class", "BigTitle"); header.setAlignment(Qt.AlignCenter); l.addWidget(header)
        sub = QLabel("一站式 Markdown 图片与链接管理工具"); sub.setProperty("class", "SubTitle"); sub.setAlignment(Qt.AlignCenter); l.addWidget(sub)
        l.addSpacing(40)
        
        grid_container = QWidget(); grid_container.setMaximumWidth(1000)
        grid = QGridLayout(grid_container); grid.setSpacing(30)
        
        grid.addWidget(LaunchCard("资源审计", "扫描冗余图片", "audit", self, 1), 0, 0)
        grid.addWidget(LaunchCard("迁移合并", "移动与合并文档", "migrate", self, 2), 0, 1)
        grid.addWidget(LaunchCard("批量重命名", "自定义规则重命名", "rename", self, 3), 1, 0)
        grid.addWidget(LaunchCard("原地整理", "归档当前目录图片", "inplace", self, 4), 1, 1)
        
        h_box = QHBoxLayout(); h_box.addStretch(); h_box.addWidget(grid_container); h_box.addStretch()
        l.addLayout(h_box); l.addStretch()
        
        log_btn = QPushButton(" 查看运行日志"); log_btn.setIcon(GeoIcon.get("log", "#888"))
        log_btn.setStyleSheet("border:none; color:#888; font-weight:bold; margin-bottom:20px; background:transparent;")
        log_btn.setCursor(Qt.PointingHandCursor); log_btn.clicked.connect(self.show_logs)
        l.addWidget(log_btn, alignment=Qt.AlignCenter)
        
        self.stack.addWidget(p)

    def init_tool_page(self, idx, title_cn, title_en, filler):
        p = QWidget(); top = QHBoxLayout(); top.setContentsMargins(40, 20, 40, 20)
        b = QPushButton("  返回主页"); b.setIconSize(QSize(18, 18)); b.setIcon(GeoIcon.get("arrow_left", "#555")) 
        b.setProperty("class", "BackBtn"); b.setCursor(Qt.PointingHandCursor); b.clicked.connect(self.go_home)
        lbl = QLabel(title_cn); lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #111; border:none;")
        top.addWidget(b); top.addStretch(); top.addWidget(lbl)
        
        paper = QFrame(); paper.setProperty("class", "Workspace")
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(30); shadow.setColor(QColor(0,0,0,10)); shadow.setOffset(0, 5)
        paper.setGraphicsEffect(shadow)
        paper.setMaximumWidth(1000); paper.setMinimumSize(600, 400)
        
        pl = QVBoxLayout(paper); pl.setContentsMargins(60, 50, 60, 50)
        filler(pl)
        
        root = QVBoxLayout(p); root.setContentsMargins(0,0,0,0); root.addLayout(top)
        hc = QHBoxLayout(); hc.addStretch(); hc.addWidget(paper); hc.addStretch()
        root.addLayout(hc); root.addStretch()
        self.stack.addWidget(p)

    def mk_stat(self, label, val):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(0,0,0,0); v.setSpacing(5)
        vl = QLabel(str(val)); vl.setProperty("class", "StatNumber"); v.addWidget(vl)
        tl = QLabel(label); tl.setProperty("class", "StatLabel"); v.addWidget(tl)
        return w, vl

    # --- 文件夹按钮 ---
    def mk_input(self, l, label, ph=""):
        lbl = QLabel(label); lbl.setStyleSheet("font-weight:700; font-size:12px; color:#AAA; letter-spacing:1px; margin-bottom: 8px; border:none;")
        l.addWidget(lbl)
        h = QHBoxLayout(); e = QLineEdit(); e.setPlaceholderText(ph)
        b = QPushButton(" 选择"); b.setFixedWidth(80); b.setFixedHeight(38)
        b.setIcon(GeoIcon.get("folder", "#666")); b.setIconSize(QSize(16,16))
        b.setProperty("class", "FolderBtn"); b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(lambda: self.sel(e))
        h.addWidget(e); h.addWidget(b); l.addLayout(h)
        return e

    def sel(self, e):
        path = QFileDialog.getExistingDirectory(self, "选择目录")
        if path: e.setText(path)

    # 1. 审计
    def ui_audit_content(self, l):
        self.audit_path = self.mk_input(l, "目标路径 (文件/文件夹)", "拖入文件夹开始扫描...")
        l.addSpacing(30)
        
        stats = QHBoxLayout(); stats.setSpacing(60)
        c1, self.lbl_md = self.mk_stat("MD 文件", "-"); stats.addWidget(c1)
        c2, self.lbl_ref = self.mk_stat("有效引用", "-"); stats.addWidget(c2)
        c3, self.lbl_red = self.mk_stat("冗余文件", "-"); stats.addWidget(c3)
        stats.addStretch(); l.addLayout(stats)
        
        l.addSpacing(30)
        l.addWidget(QLabel("冗余清单", styleSheet="font-weight:700; color:#999; margin-bottom:5px; border:none;"))
        self.red_list_ui = QListWidget(); self.red_list_ui.setFixedHeight(120)
        l.addWidget(self.red_list_ui); l.addStretch()
        
        btns = QHBoxLayout(); btns.setSpacing(20)
        b1 = QPushButton("开始扫描"); b1.setProperty("class", "ActionBtn"); b1.setCursor(Qt.PointingHandCursor)
        b1.clicked.connect(lambda: threading.Thread(target=self.core.analyze_path_entry, args=(self.audit_path.text(),), daemon=True).start())
        
        # [修改] 默认变灰，直到有数据
        self.b_clean = QPushButton("清理冗余"); self.b_clean.setProperty("class", "GhostBtn"); self.b_clean.setCursor(Qt.PointingHandCursor)
        self.b_clean.setEnabled(False)
        self.b_clean.clicked.connect(self.do_clean_check)
        
        btns.addWidget(b1); btns.addWidget(self.b_clean); btns.addStretch(); l.addLayout(btns)

    # 2. 迁移
    def ui_migrate_content(self, l):
        self.mig_src = self.mk_input(l, "源路径", "C:/Docs"); l.addSpacing(20)
        self.mig_dst = self.mk_input(l, "目标路径", "D:/Export"); l.addSpacing(40)
        
        opts = QGridLayout(); opts.setVerticalSpacing(20); opts.setHorizontalSpacing(40)
        self.mig_opts = {
            'm': QCheckBox("合并为一个文档"), 's': QCheckBox("图片存入子文件夹"),
            'd': QCheckBox("下载远程图片"), 'c': QCheckBox("完成后清理")
        }
        self.mig_opts['s'].setChecked(True); self.mig_opts['d'].setChecked(True)
        
        opts.addWidget(self.mig_opts['m'], 0, 0); opts.addWidget(self.mig_opts['s'], 0, 1)
        opts.addWidget(self.mig_opts['d'], 1, 0); opts.addWidget(self.mig_opts['c'], 1, 1)
        l.addLayout(opts); l.addStretch()
        
        b = QPushButton("执行迁移"); b.setProperty("class", "ActionBtn"); b.clicked.connect(self.start_mig)
        l.addWidget(b, alignment=Qt.AlignRight)

    # 3. 重命名
    def ui_rename_content(self, l):
        self.ren_path = self.mk_input(l, "目标文件夹"); l.addSpacing(25)
        
        tk = QHBoxLayout(); tk.setSpacing(10)
        l.addWidget(QLabel("快速规则", styleSheet="font-weight:700; color:#999; margin-bottom:5px; border:none;"))
        for t, c in [("原名", "{original}"), ("序号", "{num}"), ("日期", "{date}"), ("下划线", "_")]:
            btn = QPushButton(t); btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("border:1px solid #DDD; border-radius: 18px; padding: 6px 12px; background:#FFF; font-weight:600; color:#555;")
            btn.clicked.connect(lambda _, x=c: self.ren_pat.insert(x))
            tk.addWidget(btn)
        tk.addStretch(); l.addLayout(tk); l.addSpacing(20)
        
        h_pat = QHBoxLayout()
        self.ren_pat = QLineEdit("{original}_{num}"); h_pat.addWidget(self.ren_pat)
        self.ren_start = QSpinBox(); self.ren_start.setPrefix("起始: "); self.ren_start.setValue(1); h_pat.addWidget(self.ren_start)
        self.ren_pad = QSpinBox(); self.ren_pad.setPrefix("位数: "); self.ren_pad.setValue(3); h_pat.addWidget(self.ren_pad)
        l.addLayout(h_pat)
        
        for w in [self.ren_path, self.ren_pat, self.ren_start, self.ren_pad]:
            if isinstance(w, QLineEdit): w.textChanged.connect(self.trigger_preview)
            else: w.valueChanged.connect(self.trigger_preview)
            
        l.addSpacing(10)
        self.ren_view = QTextEdit(); self.ren_view.setFixedHeight(100); self.ren_view.setReadOnly(True)
        l.addWidget(self.ren_view); l.addStretch()
        
        h_act = QHBoxLayout()
        b_run = QPushButton("执行重命名"); b_run.setProperty("class","ActionBtn"); b_run.clicked.connect(self.exec_rename)
        self.b_undo = QPushButton("撤销"); self.b_undo.setProperty("class","GhostBtn"); self.b_undo.setEnabled(False)
        self.b_undo.clicked.connect(lambda: threading.Thread(target=self.core.undo_last_rename, daemon=True).start())
        h_act.addWidget(b_run); h_act.addWidget(self.b_undo); h_act.addStretch(); l.addLayout(h_act)

    # 4. 原地整理
    def ui_inplace_content(self, l):
        l.addStretch()
        icon = QLabel(); icon.setPixmap(GeoIcon.get("inplace", "#EEE").pixmap(80,80)); icon.setAlignment(Qt.AlignCenter); icon.setStyleSheet("border:none;")
        l.addWidget(icon)
        t = QLabel("原地整理"); t.setAlignment(Qt.AlignCenter); t.setStyleSheet("font-size: 28px; font-weight:800; margin-top:20px; color:#111; border:none;")
        l.addWidget(t)
        info = QLabel("自动归档当前目录图片至 ./images 并修复链接"); info.setAlignment(Qt.AlignCenter); info.setStyleSheet("color:#888; font-size:14px; margin-bottom:40px; border:none;")
        l.addWidget(info)
        
        h = QHBoxLayout(); h.setSpacing(20); h.setAlignment(Qt.AlignCenter)
        b1 = QPushButton("仅整理"); b1.setProperty("class", "GhostBtn"); b1.setFixedWidth(150)
        b1.clicked.connect(lambda: self.start_inp(False))
        b2 = QPushButton("整理并清理"); b2.setProperty("class", "ActionBtn"); b2.setFixedWidth(180)
        b2.clicked.connect(lambda: self.start_inp(True))
        h.addWidget(b1); h.addWidget(b2); l.addLayout(h); l.addStretch()

    # --- 逻辑回调 ---
    def on_info_ready(self, d):
        self.lbl_md.setText(str(d['md_cnt']))
        self.lbl_ref.setText(str(d['ref_cnt']))
        self.lbl_red.setText(str(d['red_cnt']))
        self.red_list_ui.clear()
        if not d['red_list']: 
            self.red_list_ui.addItem("✨ 完美！无冗余文件")
            self.b_clean.setEnabled(False)
        else: 
            self.red_list = d['red_list']
            for x in d['red_list']: self.red_list_ui.addItem(os.path.basename(x))
            self.b_clean.setEnabled(True)

    # [新增] 清理方式询问逻辑
    def do_clean_check(self):
        if not self.red_list: return
        
        msg = QMessageBox(self)
        msg.setWindowTitle("清理确认")
        msg.setText(f"发现 {len(self.red_list)} 个冗余文件。\n请选择处理方式：")
        
        btn_backup = msg.addButton("移动到备份 (推荐)", QMessageBox.ActionRole)
        btn_delete = msg.addButton("直接永久删除", QMessageBox.ActionRole)
        msg.addButton("取消", QMessageBox.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == btn_backup:
            self.core.cleanup_files(self.red_list, False)
            self.core.analyze_path_entry(self.audit_path.text())
        elif msg.clickedButton() == btn_delete:
            self.core.cleanup_files(self.red_list, True)
            self.core.analyze_path_entry(self.audit_path.text())

    def start_mig(self):
        c = {k: v.isChecked() for k, v in self.mig_opts.items()}
        c['download'] = self.mig_opts['d'].isChecked(); c['subfolder'] = self.mig_opts['s'].isChecked()
        c['merge'] = self.mig_opts['m'].isChecked(); c['cleanup'] = self.mig_opts['c'].isChecked()
        threading.Thread(target=self.core.process_migration, args=(self.mig_src.text(), self.mig_dst.text(), c), daemon=True).start()

    def trigger_preview(self):
        threading.Thread(target=self.core.generate_rename_preview, 
                         args=(self.ren_path.text(), self.ren_pat.text(), self.ren_start.value(), self.ren_pad.value()), 
                         daemon=True).start()
    def on_ren_preview(self, t): self.ren_view.setPlainText(t)
    def exec_rename(self):
        threading.Thread(target=self.core.execute_rename_batch, 
                         args=(self.ren_path.text(), self.ren_pat.text(), self.ren_start.value(), self.ren_pad.value()), daemon=True).start()
    def on_undo_state_change(self, v): self.b_undo.setEnabled(v)

    def start_inp(self, cln):
        p = QFileDialog.getExistingDirectory(self, "选目录")
        if p: threading.Thread(target=self.core.process_inplace, args=(p, cln), daemon=True).start()

    def on_task_done(self, ok, msg):
        if ok: QMessageBox.information(self, "完成", msg)
        else: QMessageBox.warning(self, "提示", msg)
    
    def on_scan_done(self, u):
        if u:
            # 扫描结束后也复用这个询问逻辑
            self.red_list = u
            self.do_clean_check()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EStarApp()
    win.show()
    sys.exit(app.exec())