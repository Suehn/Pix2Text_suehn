import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PIL import ImageGrab, Image
import os
import pyperclip
from pix2text import Pix2Text, merge_line_texts


def preprocess_latex_string_v2(latex_str):
    # 初始化变量
    new_parts = []  # 存储处理后的字符串部分
    temp_str = ""  # 临时存储非数学环境的文本
    i = 0  # 字符串遍历的索引

    while i < len(latex_str):
        if latex_str[i] == "$":
            # 检查是否遇到连续的美元符号（即双美元符号）
            if i + 1 < len(latex_str) and latex_str[i + 1] == "$":
                # 如果temp_str非空，则先添加到new_parts中，然后清空temp_str
                if temp_str:
                    new_parts.append(temp_str)
                    temp_str = ""
                # 直接添加双美元符号到new_parts，并跳过下一个美元符号
                new_parts.append("$$")
                i += 2
            else:
                # 如果遇到单个美元符号，检查temp_str是否非空，如果是，则先添加到new_parts
                if temp_str:
                    new_parts.append(temp_str)
                    temp_str = ""
                # 添加双美元符号代替单个美元符号
                new_parts.append("$$")
                i += 1
        else:
            # 如果当前字符不是美元符号，则添加到temp_str中
            temp_str += latex_str[i]
            i += 1

    # 循环结束后，检查temp_str是否还有剩余的文本，如果有，则添加到new_parts中
    if temp_str:
        new_parts.append(temp_str)

    # 重新组合字符串
    return "".join(new_parts)


# 定义用于显示渲染后的LaTeX公式的窗口类
class LatexWindow(QMainWindow):
    def __init__(self, latex_str):
        super().__init__()
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.renderLatex(latex_str)

    # 渲染LaTeX公式并在浏览器视图中显示
    def renderLatex(self, latex_str):
        html_template = f"""
        <html>
        <head>
          <style>
            p {{ font-size: 24px; }}  /* 设置字体大小为24px */
          </style>
          <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script> 
          <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        </head>
        <body>
          <p>这里是公式: {latex_str} </p>
        </body>
        </html>
        """
        self.browser.setHtml(html_template)  # 更新浏览器视图的HTML内容以显示新的公式


# 主窗口类，用于显示按钮和渲染后的公式
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片转LaTeX")
        self.setStyleSheet("font-size: 24px;")  # 设置主窗口字体大小为24px
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # 设置窗口置顶
        self.resize(800, 600)  # 设置主窗口初始大小
        self.browser = QWebEngineView()  # 将浏览器视图作为成员变量
        self.initUI()

    def initUI(self):
        self.button = QPushButton("从图片识别并渲染LaTeX公式")
        self.button.clicked.connect(self.onButtonClick)
        self.button.setStyleSheet("font-size: 24px;")  # 设置按钮字体大小为18px

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.browser)  # 将浏览器视图添加到布局中

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # 按钮点击事件处理
    def onButtonClick(self):
        result_text = recognize_image_from_clipboard()
        if result_text:
            self.renderLatex(result_text)

    # 渲染LaTeX公式并在浏览器视图中显示
    def renderLatex(self, latex_str):
        html_template = f"""
        <html>
        <head>
        <style>
            p {{ font-size: 24px; }}
        </style>
        <script>
            window.MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\(', '\\)']]
            }},
            svg: {{
                fontCache: 'global'
            }},
            startup: {{
                ready: () => {{
                MathJax.startup.defaultReady();
                MathJax.startup.promise.then(() => {{
                    // 可选：在MathJax处理完成后执行的代码
                }});
                }}
            }}
            }};
        </script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-svg.js"></script>
        </head>
        <body>
        <p>看看: {latex_str}</p>
        </body>
        </html>
        """
        self.browser.setHtml(html_template)  # 更新浏览器视图的HTML内容以显示新的公式
        self.browser.setZoomFactor(1.5)  # 设置浏览器视图缩放比例为1.5

        # 调整按钮宽度和高度
        self.button.setFixedWidth(200)
        self.button.setFixedHeight(50)


# 获取剪贴板中的图片数据
def get_image_from_clipboard():
    img = ImageGrab.grabclipboard()
    if img is not None and isinstance(img, Image.Image):
        return img

    if isinstance(img, list):
        clipboard_content = img[0]
        if isinstance(clipboard_content, str) and os.path.isfile(clipboard_content):
            try:
                img = Image.open(str(clipboard_content))
                return img
            except IOError:
                print("剪贴板中的文件不是有效的图像文件。")
        return None
    print("剪贴板中没有图像数据。返回空值")
    return None


# 识别剪贴板中的图片并返回识别的文本
def recognize_image_from_clipboard():
    img = get_image_from_clipboard()
    if img is None:
        print("剪切板中没有图片，请复制图片后再试。")
        return

    p2t = Pix2Text()
    outs2 = p2t.recognize(img)
    result_text = merge_line_texts(outs2)

    pyperclip.copy(result_text)
    print("识别结果已复制到剪切板。")
    return result_text


# 主函数
def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
