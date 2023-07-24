import sys
import os
import subprocess
import shutil
import requests
from bs4 import BeautifulSoup
from termcolor import colored
from PyQt5.QtWidgets import QApplication, QWidget, QLabel,QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QTextEdit, QMessageBox, QProgressBar, QFormLayout,QSpacerItem,QSizePolicy
from PyQt5.QtCore import QThread, pyqtSignal, Qt


# 环境链接字典
environment_urls = {
    "team1": "",
    "team2": "",
    "team3": "",      #根据自己需要配置
    "team4": "",
    "team9": ""
}

# 重启服务器链接字典
another_environment_urls = {
    "team1": "",
    "team2": "",
    "team3": "",           #根据自己需要配置
    "team4": "",
    "team9": ""
}

# 发布配置表链接字典
release_environment_urls = {
    "team1": "",
    "team2": "",                  #根据自己需要配置
    "team3": "",
    "team4": "",
    "team9": ""
}


        # 获取程序所在的文件夹路径
executable_path = sys.argv[0] # 获取可执行文件的路径
program_dir = os.path.dirname(executable_path)  # 获取可执行文件所在的目录


        # 获取程序所在文件夹中的所有文件夹名称
folder_names1 = [name for name in os.listdir(program_dir) if os.path.isdir(os.path.join(program_dir, name))]

        # 创建文件夹路径列表
repo_paths = [os.path.join(program_dir, name) for name in folder_names1]


folder_paths = [path for path in repo_paths if "****" in path]   #读取唯一特征码的文件夹
folder_names = []

for path in folder_paths:
    names = [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]
    folder_names.extend(names)
version_names = [name for name in folder_names if name[0].isdigit()]
if version_names:
    version_names.pop()
else:
    print("version_names列表为空，无法执行pop操作。")

version_names.reverse()


class PullAllThread(QThread):
    output_received = pyqtSignal(str)  # 定义信号，在输出日志时发送信号
    pull_completed = pyqtSignal()  # 定义信号，在拉取全部表完成时发送信号

    def __init__(self, repo_paths):
        super().__init__()
        self.repo_paths = repo_paths

    def run(self):
        for repo_path in self.repo_paths:
            self.output_received.emit(f"处理仓库：{repo_path}")

            # 切换到仓库目录
            os.chdir(repo_path)

            # 执行 git 拉取更新命令
            result = subprocess.run("git pull", shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                self.output_received.emit("<span style='color: green;'>拉取成功</span>")
                self.output_received.emit(result.stdout)
            else:
                self.output_received.emit("<span style='color: red;'>拉取失败</span>")
                self.output_received.emit(result.stderr)

        self.pull_completed.emit()  # 发送 pull_completed 信号，表示拉取全部表完成

class UpdateTableThread(QThread):
    output_received = pyqtSignal(str)  # 定义信号，在输出日志时发送信号
    update_completed = pyqtSignal()  # 定义信号，在更表完成时发送信号
    update_progress = pyqtSignal(int)  # 定义信号，在复制和替换文件时发送进度信号
    pull_all_completed = pyqtSignal()    # 定义一个信号，表示"拉全部表"操作已完成

    def __init__(self, version, file_path):
        super().__init__()
        self.version = version
        self.file_path = file_path

        # 获取包含"****"的路径
        source_folder_path = next((path for path in folder_paths if "****" in path), "")
        self.source_folder = os.path.join(source_folder_path, self.version)

        # 获取包含"******"的路径
        target_folder_path = next((path for path in folder_paths if "*****" in path), "")
        self.target_folder = os.path.join(target_folder_path, self.file_path)


        self.source_folder = os.path.join(source_folder_path, self.version)
        self.target_folder = os.path.join(target_folder_path, self.file_path)
        self.copied_files = []

    def run(self):
        self.output_received.emit(f"<span style='color: cyan;'>正在替换文件：{self.version} -> {self.file_path}</span>")

        # 检查源文件夹是否存在
        if not os.path.exists(self.source_folder):
            self.output_received.emit("<span style='color: red;'>源文件夹不存在，无法进行替换</span>")
            self.update_completed.emit()
            return

        # # 检查目标文件夹是否存在，如果不存在则创建
        # os.makedirs(self.target_folder, exist_ok=True)

        # 统计文件总数
        total_files = sum(len(files) for _, _, files in os.walk(self.source_folder))
        current_file_count = 0

        # 复制整个文件夹的内容并替换目标文件夹中对应的文件夹目录下的文件
        for root, dirs, files in os.walk(self.source_folder):
            for file in files:
                source_path = os.path.join(root, file)
                relative_path = os.path.relpath(source_path, self.source_folder)
                target_path = os.path.join(self.target_folder, relative_path)
                target_dir = os.path.dirname(target_path)

                # # 检查目标文件夹是否存在，如果不存在则创建
                # os.makedirs(target_dir, exist_ok=True)

                shutil.copy2(source_path, target_path)
                

                # try:
                #     shutil.copy2(source_path, target_path)
                #     self.copied_files.append(target_path)
                #     urrent_file_count += 1
                #     progress = int(current_file_count / total_files * 100)
                #     self.update_progress.emit(progress)
                # except FileNotFoundError as e:
                #     self.output_received.emit(f"<span style='color: red;'>文件未找到错误，请先执行拉全部表操作：{e}</span>")
                # except Exception as e:
                #     self.output_received.emit(f"<span style='color: red;'>发生了错误，请先执行拉全部表操作：{e}</span>")

                self.copied_files.append(target_path)

                current_file_count += 1
                progress = int(current_file_count / total_files * 100)
                self.update_progress.emit(progress)

        self.output_received.emit("<span style='color: green;'>文件替换完成</span>")

        if len(self.copied_files) == 0:
            self.output_received.emit("<span style='color: yellow;'>没有文件需要提交</span>")
        else:
            # 执行 git 提交和推送命令，并输出结果
            self.output_received.emit("<span style='color: yellow;'>执行 git 提交和推送命令</span>")
            os.chdir(self.target_folder)  # 切换到目标文件夹

            # 执行 Git 提交命令
            subprocess.run(["git", "add", "."], capture_output=True)
            subprocess.run(["git", "commit", "-m", "1"], capture_output=True)

            # 执行 Git 推送命令
            push_result = subprocess.run(["git", "push", "origin", "master"], capture_output=True, text=True)
            self.output_received.emit(push_result.stdout)
            if push_result.stderr:
                self.output_received.emit(push_result.stderr)

            self.output_received.emit("<span style='color: green;'>提交推送完成</span>")

        self.update_completed.emit()

class FetchContentThread(QThread):
    content_fetched = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    finished_parsing = pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        content = self.fetch_url_content(self.url)
        self.content_fetched.emit(content)
        self.finished_parsing.emit()

    def fetch_url_content(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()  # 检查请求是否成功
            content = response.text
            return content
        except requests.exceptions.RequestException as e:
            print("Error occurred:", e)
            return None

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小工具1.0")
        self.layout = QVBoxLayout()
        self.resize(800, 600)  # 设置窗口初始大小为800x600
        self.first_time_opened = True

        self.form_layout = QFormLayout()  # Create a QFormLayout for the form elements

        self.version_label = QLabel("<h1>版本号:</h1>")
        self.version_label.setStyleSheet("color: red;")
        self.form_layout.setWidget(0, QFormLayout.LabelRole, self.version_label)

        self.version_combo = QComboBox()
        self.populate_versions()
        self.form_layout.setWidget(0, QFormLayout.FieldRole, self.version_combo)

        self.file_label = QLabel("<h1>环境:</h1>")
        self.file_label.setStyleSheet("color: red;")
        self.form_layout.setWidget(1, QFormLayout.LabelRole, self.file_label)

        self.file_combo = QComboBox()
        self.populate_files()
        self.form_layout.setWidget(1, QFormLayout.FieldRole, self.file_combo)

        self.layout.addLayout(self.form_layout)  # Add the form layout to the main layout

        # 创建一个水平布局用于放置按钮
        button_layout = QHBoxLayout()

        # 拉全部表按钮
        self.pull_all_button = QPushButton("拉全部表")
        self.pull_all_button.setStyleSheet("QPushButton {font-size: 16px; width: 100px; height: 100px;}")
        self.pull_all_button.clicked.connect(self.on_pull_all_clicked)
        button_layout.addWidget(self.pull_all_button)

        # 更表按钮
        self.update_table_button = QPushButton("更表")
        self.update_table_button.setStyleSheet("QPushButton {font-size: 16px; width: 100px; height: 100px;}")
        self.update_table_button.clicked.connect(self.on_update_table_clicked)
        button_layout.addWidget(self.update_table_button)

        self.layout.addLayout(button_layout)  # 将按钮布局添加到主布局中

        self.output_text = QTextEdit()
        self.output_text.setStyleSheet("background-color: black; color: white;")
        self.layout.addWidget(self.output_text)

        self.setLayout(self.layout)

        self.pull_all_thread = None
        self.update_table_thread = None


        # 添加环境链接相关的部分
        self.environment_label = QLabel("<h1>更代码发表:</h1>")
        self.environment_label.setStyleSheet("color: red;")
        self.layout.addWidget(self.environment_label)

        self.environment_combo = QComboBox()
        self.populate_environment_combo()
        self.layout.addWidget(self.environment_combo)

        self.confirm_button = QPushButton("更新代码")
        self.confirm_button.clicked.connect(self.on_confirm_clicked)
        self.layout.addWidget(self.confirm_button)

        self.release_button = QPushButton("发布配置表")
        self.release_button.clicked.connect(self.on_release_clicked)
        self.layout.addWidget(self.release_button)

        self.restart_button = QPushButton("重启")
        self.restart_button.clicked.connect(self.on_restart_clicked)
        self.layout.addWidget(self.restart_button)


            # 创建一个水平布局用于放置"更新代码"按钮和下拉框
        environment_layout = QHBoxLayout()
        environment_layout.addWidget(self.environment_label)
        environment_layout.addWidget(self.environment_combo)
        environment_layout.addWidget(self.confirm_button)
        environment_layout.addWidget(self.release_button)
        # environment_layout.addWidget(self.restart_button)
            # 创建一个弹性空间（空白可伸缩区域）将重启按钮推到最右侧
        spacer_item = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        environment_layout.addItem(spacer_item)
        environment_layout.addWidget(self.restart_button)

        self.layout.addLayout(environment_layout)


        environment_layout.addStretch()  # Add a stretch to push the buttons to the left

        environment_container = QWidget()
        environment_container.setLayout(environment_layout)

        self.layout.addWidget(environment_container)



        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        # self.output_text = QTextEdit()
        # self.layout.addWidget(self.output_text)
        self.initUI()

    def initUI(self):
        # 初始化界面元素...
        # 程序启动时执行“拉取全部表”操作
        self.on_pull_all_clicked()

    def populate_environment_combo(self):
        # 清空下拉框并重新填充选项
        self.environment_combo.clear()
        self.environment_combo.addItem("team1")
        self.environment_combo.addItem("team2")
        self.environment_combo.addItem("team3")
        self.environment_combo.addItem("team4")
        self.environment_combo.addItem("team9")

    def on_confirm_clicked(self):
        selected_environment = self.environment_combo.currentText()
        url = environment_urls.get(selected_environment, "")
        if url:
            self.confirm_button.setEnabled(False)  # 禁用更新代码按钮
            self.restart_button.setEnabled(False)  # 禁用重启按钮
            self.release_button.setEnabled(False)  # 禁用发布配置表按钮
            self.pull_all_button.setEnabled(False)  # 禁用拉全部表按钮，避免重复点击
            self.update_table_button.setEnabled(False)  # 禁用更表按钮，避免重复点击
            self.version_combo.setEnabled(False)
            self.environment_combo.setEnabled(False)
            self.file_combo.setEnabled(False)

            self.progress_bar.setValue(0)  # 设置进度条初始值为0

            self.fetch_thread = FetchContentThread(url)
            self.fetch_thread.content_fetched.connect(self.on_content_fetched)
            self.fetch_thread.finished_parsing.connect(self.on_finished_parsing)
            self.fetch_thread.start()

    def on_content_fetched(self, content):
        if content:
            # 使用BeautifulSoup解析HTML响应
            soup = BeautifulSoup(content, "html.parser")

            # 找到所有文本元素并将其包装在带有内联样式的<span>标签中
            for element in soup.find_all(text=True):
                if element.strip():  # 排除空文本节点
                    try:
                        colored_text = colored(element, attrs=["color"])
                        element.replace_with(BeautifulSoup(colored_text, "html.parser"))
                    except Exception:
                        # 如果无法使用颜色，则将文本作为普通文本进行处理
                        element.replace_with(BeautifulSoup(element, "html.parser"))

            # 获取修改后的HTML内容
            modified_content = str(soup)

            # 输出带有颜色的HTML文本到控制台
            print(modified_content)

            # 在QTextEdit部件中设置修改后的内容
            self.output_text.setHtml(modified_content)
            self.confirm_button.setEnabled(True)  # 恢复更新代码按钮
            self.restart_button.setEnabled(True)  # 恢复重启按钮
            self.release_button.setEnabled(True)  # 恢复发布配置表按钮
            self.pull_all_button.setEnabled(True)  # 恢复拉全部表按钮，避免重复点击
            self.update_table_button.setEnabled(True)  # 恢复更表按钮，避免重复点击
            self.version_combo.setEnabled(True)
            self.environment_combo.setEnabled(True)
            self.file_combo.setEnabled(True)
            
            

    def on_finished_parsing(self):
        self.progress_bar.setValue(100)  # 将进度条设置为100
        self.confirm_button.setEnabled(True)  # 启用确认按钮
        self.fetch_thread = None

    def on_restart_clicked(self):
        selected_environment = self.environment_combo.currentText()
        new_url = ""  # 声明新的链接变量

        # 根据选择的环境设置新的链接
        if selected_environment in another_environment_urls:
            new_url = another_environment_urls[selected_environment]

        if new_url:
            self.confirm_button.setEnabled(False)  # 禁用更新代码按钮
            self.restart_button.setEnabled(False)  # 禁用重启按钮
            self.release_button.setEnabled(False)  # 禁用发布配置表按钮
            self.pull_all_button.setEnabled(False)  # 禁用拉全部表按钮，避免重复点击
            self.update_table_button.setEnabled(False)  # 禁用更表按钮，避免重复点击
            self.version_combo.setEnabled(False)
            self.environment_combo.setEnabled(False)
            self.file_combo.setEnabled(False)
            
            self.progress_bar.setValue(0)  # 设置进度条初始值为0

            self.fetch_thread = FetchContentThread(new_url)
            self.fetch_thread.content_fetched.connect(self.on_content_fetched)
            self.fetch_thread.finished_parsing.connect(self.on_finished_parsing)
            self.fetch_thread.start()
        
    def on_release_clicked(self):
        selected_environment = self.environment_combo.currentText()
        new2_url = ""  # 声明新的链接变量

        # 根据选择的环境设置新的链接
        if selected_environment in release_environment_urls:
            new2_url = release_environment_urls[selected_environment]

        if new2_url:
            self.confirm_button.setEnabled(False)  # 禁用更新代码按钮
            self.restart_button.setEnabled(False)  # 禁用重启按钮
            self.release_button.setEnabled(False)  # 禁用发布配置表按钮
            self.pull_all_button.setEnabled(False)  # 禁用拉全部表按钮，避免重复点击
            self.update_table_button.setEnabled(False)  # 禁用更表按钮，避免重复点击
            self.version_combo.setEnabled(False)
            self.environment_combo.setEnabled(False)
            self.file_combo.setEnabled(False)

            self.progress_bar.setValue(0)  # 设置进度条初始值为0

            self.fetch_thread = FetchContentThread(new2_url)
            self.fetch_thread.content_fetched.connect(self.on_content_fetched)
            self.fetch_thread.finished_parsing.connect(self.on_finished_parsing)
            self.fetch_thread.start()


        

    def populate_versions(self):

        self.version_combo.addItems(version_names)

    def populate_files(self):
        # 添加文件地址选项到下拉框
        # 示例数据
        file_names = ["team1", "team2", "team3", "team4", "team9"]
        self.file_combo.addItems(file_names)

    def on_pull_all_clicked(self):

        self.confirm_button.setEnabled(False)  # 禁用更新代码按钮
        self.restart_button.setEnabled(False)  # 禁用重启按钮
        self.release_button.setEnabled(False)  # 禁用发布配置表按钮
        self.pull_all_button.setEnabled(False)  # 禁用拉全部表按钮，避免重复点击
        self.update_table_button.setEnabled(False)  # 禁用更表按钮，避免重复点击
        self.version_combo.setEnabled(False)
        self.environment_combo.setEnabled(False)
        self.file_combo.setEnabled(False)

        self.pull_all_thread = PullAllThread(repo_paths)
        self.pull_all_thread.output_received.connect(self.output_text.append)  # 连接信号与槽函数
        self.pull_all_thread.pull_completed.connect(self.on_pull_all_completed)
        self.pull_all_thread.start()

    def on_pull_all_completed(self):
        self.output_text.append("<span style='color: cyan;'>拉取全部表完成。</span>")
        self.pull_all_completed = True  # 设置"拉全部表"完成的标志为True
        self.confirm_button.setEnabled(True)  # 恢复更新代码按钮
        self.restart_button.setEnabled(True)  # 恢复重启按钮
        self.release_button.setEnabled(True)  # 恢复发布配置表按钮
        self.pull_all_button.setEnabled(True)  # 恢复拉全部表按钮，避免重复点击
        self.update_table_button.setEnabled(True)  # 恢复更表按钮，避免重复点击
        self.version_combo.setEnabled(True)
        self.environment_combo.setEnabled(True)
        self.file_combo.setEnabled(True)

    def on_update_table_clicked(self):
        version = self.version_combo.currentText()
        file_path = self.file_combo.currentText()


        # 创建确认弹窗，并设置为模态对话框
        confirm_dialog = QMessageBox(self)
        confirm_dialog.setWindowTitle("确认")
        confirm_dialog.setText(f"版本号：<span style='color: red;'>{version}</span><br>环境：<span style='color: red;'>{file_path}</span>")
        confirm_dialog.setIcon(QMessageBox.Question)
        confirm_dialog.addButton(QMessageBox.Yes)
        confirm_dialog.addButton(QMessageBox.Cancel)
        confirm_dialog.setWindowModality(Qt.ApplicationModal)
        confirm_dialog.move(self.geometry().center())  # 居中显示在主窗口内

        result = confirm_dialog.exec_()
        if result == QMessageBox.Yes:
            self.output_text.append(f"<b>版本号:</b> <span style='color: yellow;'>{version}</span>")
            self.output_text.append(f"<b>环境:</b> <span style='color: yellow;'>{file_path}</span>")

            self.confirm_button.setEnabled(False)  # 禁用更新代码按钮
            self.restart_button.setEnabled(False)  # 禁用重启按钮
            self.release_button.setEnabled(False)  # 禁用发布配置表按钮
            self.pull_all_button.setEnabled(False)  # 禁用拉全部表按钮，避免重复点击
            self.update_table_button.setEnabled(False)  # 禁用更表按钮，避免重复点击
            self.version_combo.setEnabled(False)
            self.environment_combo.setEnabled(False)
            self.file_combo.setEnabled(False)

            self.update_table_thread = UpdateTableThread(version, file_path)
            self.update_table_thread.output_received.connect(self.output_text.append)  # 连接信号与槽函数
            self.update_table_thread.update_completed.connect(self.on_update_table_completed)
            self.update_table_thread.update_progress.connect(self.on_update_table_progress)
            self.update_table_thread.start()
        else:
            self.output_text.append("<span style='color: yellow;'>已取消操作</span>")

    def on_restart_clicked(self):
        version = self.version_combo.currentText()
        file1_path = self.environment_combo.currentText()

        # 创建确认弹窗，并设置为模态对话框
        confirm_dialog = QMessageBox(self)
        confirm_dialog.setWindowTitle("确认")
        confirm_dialog.setText(f"版本号：<span style='color: red;'>{version}</span><br>环境：<span style='color: red;'>{file1_path}</span>")
        confirm_dialog.setIcon(QMessageBox.Question)
        confirm_dialog.addButton(QMessageBox.Yes)
        confirm_dialog.addButton(QMessageBox.Cancel)
        confirm_dialog.setWindowModality(Qt.ApplicationModal)
        confirm_dialog.move(self.geometry().center())  # 居中显示在主窗口内

        result = confirm_dialog.exec_()
        if result == QMessageBox.Yes:
                self.output_text.append(f"<b>环境:</b> <span style='color: yellow;'>{file1_path}重启中.....</span>")

                selected_environment = self.environment_combo.currentText()
                new_url = ""  # 声明新的链接变量

            # 根据选择的环境设置新的链接
                if selected_environment in another_environment_urls:
                    new_url = another_environment_urls[selected_environment]

                if new_url:
                    self.confirm_button.setEnabled(False)  # 禁用更新代码按钮
                    self.restart_button.setEnabled(False)  # 禁用重启按钮
                    self.release_button.setEnabled(False)  # 禁用发布配置表按钮
                    self.pull_all_button.setEnabled(False)  # 禁用拉全部表按钮，避免重复点击
                    self.update_table_button.setEnabled(False)  # 禁用更表按钮，避免重复点击
                    self.version_combo.setEnabled(False)
                    self.environment_combo.setEnabled(False)
                    self.file_combo.setEnabled(False)

                    self.progress_bar.setValue(0)  # 设置进度条初始值为0

                    self.fetch_thread = FetchContentThread(new_url)
                    self.fetch_thread.content_fetched.connect(self.on_content_fetched)
                    self.fetch_thread.finished_parsing.connect(self.on_finished_parsing)
                    self.fetch_thread.start()
        else:
            self.output_text.append("<span style='color: yellow;'>已取消操作</span>")
        

    def on_update_table_completed(self):
        self.output_text.append("<span style='color: green;'>文件替换完成</span>")
        self.progress_bar.setValue(100)  # 设置进度条为100%完成
        self.confirm_button.setEnabled(True)  # 恢复更新代码按钮
        self.restart_button.setEnabled(True)  # 恢复重启按钮
        self.release_button.setEnabled(True)  # 恢复发布配置表按钮
        self.pull_all_button.setEnabled(True)  # 恢复拉全部表按钮，避免重复点击
        self.update_table_button.setEnabled(True)  # 恢复更表按钮，避免重复点击
        self.version_combo.setEnabled(True)
        self.environment_combo.setEnabled(True)
        self.file_combo.setEnabled(True)

    def on_update_table_progress(self, progress):
        self.progress_bar.setValue(progress)  # 更新进度条的值

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
