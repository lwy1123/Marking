import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import base64
import os
from openai import OpenAI
from datetime import datetime
from PIL import Image, ImageTk
import threading

class ImageAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("图片分析器")
        self.geometry("1200x800")
        
        # 设置API客户端
        self.client = OpenAI(
            base_url='https://api-inference.modelscope.cn/v1/',
            api_key='44e0e7af-0c7b-4f74-9033-57b949efd676', # ModelScope Token
)
        
        self.setup_ui()
        self.image_paths = []
        self.image_results = []

    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧面板 - 图片列表和控制按钮
        left_frame = ttk.Frame(main_frame, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        # 提示词输入
        prompt_frame = ttk.Frame(left_frame)
        prompt_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(prompt_frame, text="提示词：").pack(side=tk.LEFT)
        self.prompt_entry = ttk.Entry(prompt_frame)
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.prompt_entry.insert(0, "描述这幅图")

        # 按钮区
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_frame, text="选择图片", command=self.select_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="选择文件夹", command=self.select_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="开始分析", command=self.analyze_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出MD", command=self.export_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出TXT", command=self.export_to_txt).pack(side=tk.LEFT, padx=5)

        # 图片预览列表
        self.preview_canvas = tk.Canvas(left_frame, bg='white')
        preview_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        self.preview_frame = ttk.Frame(self.preview_canvas)
        
        self.preview_canvas.configure(yscrollcommand=preview_scroll.set)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.preview_canvas.create_window((0, 0), window=self.preview_frame, anchor='nw')
        self.preview_frame.bind('<Configure>', lambda e: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox('all')))

        # 右侧面板 - 分析结果
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.result_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=('Courier New', 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def select_images(self):
        file_paths = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if not file_paths:
            return

        # 清除现有预览
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        self.image_paths = list(file_paths)
        self.image_results = []

        # 创建预览
        for path in self.image_paths:
            frame = ttk.Frame(self.preview_frame)
            frame.pack(fill=tk.X, pady=5)

            # 加载并缩放图片
            img = Image.open(path)
            img.thumbnail((150, 150))
            photo = ImageTk.PhotoImage(img)
            
            label = ttk.Label(frame, image=photo)
            label.image = photo  # 保持引用
            label.pack(side=tk.LEFT)

            # 显示文件名
            name_label = ttk.Label(frame, text=os.path.basename(path))
            name_label.pack(side=tk.LEFT, padx=5)

        self.status_var.set(f"已选择 {len(self.image_paths)} 张图片")

    def select_folder(self):
        folder_path = filedialog.askdirectory(title="选择图片文件夹")
        if not folder_path:
            return
            
        # 支持的图片格式
        valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        
        # 清空现有图片列表
        self.image_paths = []
        self.image_results = []
        
        # 清除预览
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
            
        # 查找文件夹中的所有图片
        found_images = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(valid_extensions):
                    full_path = os.path.join(root, file)
                    found_images.append(full_path)
        
        if not found_images:
            self.status_var.set("所选文件夹中没有找到图片文件")
            return
            
        # 按文件名排序
        found_images.sort()
        self.image_paths = found_images
        
        # 创建预览
        for path in self.image_paths:
            try:
                img = Image.open(path)
                img.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(img)
                
                frame = ttk.Frame(self.preview_frame)
                frame.pack(pady=5)
                
                label = ttk.Label(frame, image=photo)
                label.image = photo
                label.pack(side=tk.LEFT)
                
                name_label = ttk.Label(frame, text=os.path.basename(path))
                name_label.pack(side=tk.LEFT, padx=5)
                
            except Exception as e:
                error_label = ttk.Label(self.preview_frame, text=f"无法加载图片 {os.path.basename(path)}: {str(e)}")
                error_label.pack(pady=5)
        
        self.status_var.set(f"已加载 {len(self.image_paths)} 张图片")

    def encode_image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def clean_result_text(self, text):
        # 清理特殊符号
        special_chars = ['*', '-', '•']
        result = text
        for char in special_chars:
            result = result.replace(char, '')
        
        # 清理数字序号（如：1. 2. 3.）
        lines = result.split('\n')
        cleaned_lines = []
        for line in lines:
            # 移除行首的数字序号
            line = line.strip()
            if line:
                import re
                # 匹配行首的数字加点号和空格
                line = re.sub(r'^\d+\.\s*', '', line)
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def analyze_single_image(self, image_path):
        try:
            base64_image = self.encode_image_to_base64(image_path)
            prompt = self.prompt_entry.get().strip() or "描述这幅图"

            response = self.client.chat.completions.create(
                model='Qwen/Qwen2.5-VL-72B-Instruct',
                messages=[{
                    'role': 'user',
                    'content': [{
                        'type': 'text',
                        'text': prompt,
                    }, {
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/jpeg;base64,{base64_image}"
                        },
                    }],
                }],
                stream=True
            )

            result = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    result += chunk.choices[0].delta.content

            # 清理结果中的特殊符号
            cleaned_result = self.clean_result_text(result)

            return {
                'image_path': image_path,
                'prompt': prompt,
                'result': cleaned_result,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {
                'image_path': image_path,
                'prompt': prompt,
                'result': f"处理出错: {str(e)}",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def analyze_images(self):
        if not hasattr(self, 'image_paths') or not self.image_paths:
            self.status_var.set("请先选择图片")
            return

        def analyze_thread():
            self.status_var.set("正在分析...")
            self.result_text.delete(1.0, tk.END)
            
            for i, image_path in enumerate(self.image_paths, 1):
                self.status_var.set(f"正在分析第 {i}/{len(self.image_paths)} 张图片...")
                result = self.analyze_single_image(image_path)
                self.image_results.append(result)
                
                # 更新结果显示
                self.result_text.insert(tk.END, f"\n## 图片：{os.path.basename(image_path)}\n\n")
                self.result_text.insert(tk.END, f"{result['result']}\n\n")
                self.result_text.insert(tk.END, f"---\n\n")
                self.result_text.see(tk.END)

            self.status_var.set(f"分析完成，共处理 {len(self.image_paths)} 张图片")

        threading.Thread(target=analyze_thread, daemon=True).start()

    def export_results(self):
        if not self.image_results:
            self.status_var.set("没有可导出的结果")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown文件", "*.md")],
            initialfile="图片分析结果.md"
        )
        
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# 图片分析结果报告\n\n")
                f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for result in self.image_results:
                    f.write(f"## 图片：{os.path.basename(result['image_path'])}\n\n")
                    f.write(f"{result['result']}\n\n")
                    f.write("---\n\n")

            self.status_var.set(f"结果已导出至：{file_path}")
        except Exception as e:
            self.status_var.set(f"导出失败：{str(e)}")

    def export_to_txt(self):
        if not self.image_results:
            self.status_var.set("没有可导出的结果")
            return

        try:
            created_files = []
            updated_files = []
            
            for result in self.image_results:
                image_path = result['image_path']
                txt_path = os.path.splitext(image_path)[0] + '.txt'
                
                # 写入文件，只包含分析结果
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(result['result'])
                
                # 检查是否存在txt文件
                if os.path.exists(txt_path):
                    updated_files.append(os.path.basename(txt_path))
                else:
                    created_files.append(os.path.basename(txt_path))
            
            # 显示结果
            status_msg = []
            if created_files:
                status_msg.append(f"新建：{', '.join(created_files)}")
            if updated_files:
                status_msg.append(f"更新：{', '.join(updated_files)}")
                
            self.status_var.set("导出完成。" + " | ".join(status_msg))
            
            # 显示详细信息
            message = []
            if created_files:
                message.append(f"新建的文件：\n{chr(10).join(created_files)}")
            if updated_files:
                message.append(f"更新的文件：\n{chr(10).join(updated_files)}")
                
            messagebox.showinfo(
                "导出完成",
                "\n\n".join(message)
            )
            
        except Exception as e:
            error_msg = f"导出失败：{str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("导出错误", error_msg)

if __name__ == "__main__":
    app = ImageAnalyzer()
    app.mainloop()