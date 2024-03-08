import sys
import os
import pyperclip
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PIL import ImageGrab, Image
from pix2text import Pix2Text, merge_line_texts


def preprocess_latex_string_v2(latex_str):
    new_parts = []
    temp_str = ""
    i = 0

    while i < len(latex_str):
        if latex_str[i] == "$":
            if i + 1 < len(latex_str) and latex_str[i + 1] == "$":
                if temp_str:
                    new_parts.append(temp_str)
                    temp_str = ""
                new_parts.append("$$")
                i += 2
            else:
                if temp_str:
                    new_parts.append(temp_str)
                    temp_str = ""
                new_parts.append("$$")
                i += 1
        else:
            temp_str += latex_str[i]
            i += 1

    if temp_str:
        new_parts.append(temp_str)

    return "".join(new_parts)


class LatexWindow(QMainWindow):
    def __init__(self, latex_str):
        super().__init__()
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.renderLatex(latex_str)

    def renderLatex(self, latex_str):
        html_template = f"""
        <html>
        <head>
          <style>
            p {{ font-size: 24px; }}
          </style>
          <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script> 
          <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        </head>
        <body>
          <p>这里是公式: {latex_str} </p>
        </body>
        </html>
        """
        self.browser.setHtml(html_template)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片转LaTeX")
        self.setStyleSheet("font-size: 24px;")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(800, 600)
        self.browser = QWebEngineView()
        self.initUI()

    def initUI(self):
        self.button = QPushButton("从图片识别并渲染LaTeX公式")
        self.button.clicked.connect(self.onButtonClick)
        self.button.setStyleSheet("font-size: 24px;")

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.browser)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def onButtonClick(self):
        result_text = recognize_image_from_clipboard()
        if result_text:
            self.renderLatex(result_text)

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
        self.browser.setHtml(html_template)
        self.browser.setZoomFactor(1.5)

        self.button.setFixedWidth(200)
        self.button.setFixedHeight(50)


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


def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
