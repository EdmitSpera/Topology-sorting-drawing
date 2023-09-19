# 导入必要的库
import numpy as np
import sys
import threading
import networkx as nx
import matplotlib.pyplot as plt
import re
import warnings
import os

warnings.filterwarnings("ignore", category=UserWarning)

# 导入PySide2库中的相关模块
from PySide2.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTextEdit
from PySide2.QtUiTools import loadUiType  # 用于加载UI文件的函数
from PySide2.QtCore import QFile, QTextStream, QSize
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


# 创建一个Qt应用程序
class GraphVisualizationApp(QMainWindow):

    def setWindow(self):
        width = 965
        height = 800
        self.resize(QSize(width, height))

    def __init__(self):
        super().__init__()

        # 加载UI文件
        self.ui = loadUiType("tuopu.ui")[0]()  # 这里加载了一个UI文件
        self.ui.setupUi(self)
        self.setWindow()
        # 初始化图像生成状态变量
        self.graphGenerated = False

        self.G = None  # 用于存储图的变量

        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 使用微软雅黑或其他中文字体
        # 创建matplotlib视图和图形canvas
        self.graphView = plt.figure()  # 创建Matplotlib视图
        self.graphCanvas = FigureCanvas(self.graphView)  # 创建Matplotlib图形的Canvas

        # 将canvas添加到ui布局中
        self.ui.horizontalLayout_2.addWidget(self.graphCanvas)

        # 创建QPlainTextEdit对象，用于文本输入和显示
        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)

        # 链接ui菜单栏中的各个操作到相应的方法
        self.ui.actionOpen.triggered.connect(self.importData)  # 导入数据
        self.ui.actionGraph.triggered.connect(self.saveGraph)  # 保存图像
        self.ui.actionUnauthorized_Graph.triggered.connect(self.generateGraph)  # 生成图
        self.ui.actionReadme.triggered.connect(self.help)  # 显示帮助窗口
        self.ui.actionProgram_Exit.triggered.connect(self.close_window)  # 退出应用
        self.ui.actionfile.triggered.connect(self.exportResults)  # 导出排序结果
        self.ui.actionAuthorized_Graph.triggered.connect(self.weightedGraph)  # 生成带权图数据
        self.ui.pushButton.clicked.connect(self.weightedGraph)  # 生成有权图
        self.ui.pushButton_2.clicked.connect(self.generateGraph)  # 生成无权图

    def generateGraph(self):
        # 获取文本框中的输入，每行定义一个关系，格式为 "<a,b>"
        input_text = self.ui.plainTextEdit.toPlainText()

        # 使用正则表达式匹配输入格式
        pattern = r'<(\w+),(\w+)>|《(\w+),(\w+)》'
        matches = re.findall(pattern, input_text)

        edges = []

        # 判断是否匹配到任何数据
        if not matches:
            QMessageBox.warning(self, "错误", "请添加正确格式的数据，例如：<a,b>", QMessageBox.Ok)
            return

        # 遍历匹配结果
        for match in matches:
            a, b, c, d = match
            if a:  # 使用尖括号的情况
                edges.append((a.strip(), b.strip()))
            elif c:  # 使用双尖括号的情况
                edges.append((c.strip(), d.strip()))
            else:
                # 输入不符合规范，显示错误提示
                QMessageBox.warning(self, "错误", "请添加正确格式的数据，例如：<a,b>", QMessageBox.Ok)
                return

        # 创建有向图
        G = nx.DiGraph()
        G.add_edges_from(edges)

        # 检查是否存在依赖关系
        if not nx.is_directed_acyclic_graph(G):
            # 存在依赖关系，显示错误提示
            QMessageBox.warning(self, "错误", "输入的数据存在依赖关系", QMessageBox.Ok)
            return

        # 根据用户选择的布局来计算节点的位置
        layout_option = self.ui.comboBox.currentText()
        if layout_option == "Spectral Layout":
            pos = nx.spectral_layout(G)
        elif layout_option == "Shell Layout":
            pos = nx.shell_layout(G)
        elif layout_option == "Circular Layout":
            pos = nx.circular_layout(G)
        else:
            pos = nx.spring_layout(G, seed=10)  # 默认使用spring_layout布局

        # 计算所有拓扑排序
        all_topo_orders = list(nx.all_topological_sorts(G))
        if not all_topo_orders:
            print("无法进行拓扑排序，图中存在循环依赖。")
            return []

        # 清空Matplotlib视图并绘制拓扑排序关系图
        plt.clf()
        first_topo_order = all_topo_orders[0]
        nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue", font_size=10)
        plt.title("拓扑排序")
        self.graphCanvas.draw()
        self.graphGenerated = True  # 标记图像已生成

        # 打印所有拓扑排序结果
        print("所有拓扑排序结果:")
        for topo_order in all_topo_orders:
            print(topo_order)
        return all_topo_orders

    # Floyd最短路径算法
    def floyd_shortest_paths(self, start_vertex):
        if not self.graphGenerated:
            QMessageBox.warning(self, "错误", "您未生成任何图像", QMessageBox.Ok)
            return

        if self.G is None:
            QMessageBox.warning(self, "错误", "带权图为空，请先导入带权图数据", QMessageBox.Ok)
            return

        # 获取所有顶点列表
        nodes = list(self.G.nodes())

        # 创建节点到索引的映射和反向映射
        node_to_index = {node: i for i, node in enumerate(nodes)}
        index_to_node = {i: node for i, node in enumerate(nodes)}

        # 初始化距离矩阵，用inf表示不可达
        num_nodes = len(nodes)
        distance_matrix = np.inf * np.ones((num_nodes, num_nodes))

        # 将直接可达的顶点间距离填入距离矩阵
        for edge in self.G.edges(data=True):
            a, b, weight = edge[0], edge[1], edge[2]["weight"]
            distance_matrix[node_to_index[a]][node_to_index[b]] = weight

        # Floyd算法求最短路径
        for k in range(num_nodes):
            for i in range(num_nodes):
                for j in range(num_nodes):
                    if distance_matrix[i][k] + distance_matrix[k][j] < distance_matrix[i][j]:
                        distance_matrix[i][j] = distance_matrix[i][k] + distance_matrix[k][j]

        # 构建最短路径结果字符串
        result_text = "从顶点 '{}' 出发的最短路径：\n".format(start_vertex)
        for i in range(num_nodes):
            if index_to_node[i] != start_vertex:
                shortest_path = distance_matrix[node_to_index[start_vertex]][i]
                if shortest_path == np.inf:
                    result_text += "顶点 '{}' 不可达到顶点 '{}'。\n".format(start_vertex, index_to_node[i])
                else:
                    result_text += "到顶点 '{}' 的最短路径为：{}\n".format(index_to_node[i], shortest_path)

        self.ui.textEdit.setText(result_text)  # 打印最短路径到textEdit框中

    def weightedGraph(self):
        # 获取文本框中的输入，每行定义一个带权边，格式为 "<a,b,1>"
        # a和b为顶点，c为ab边的权重
        input_text = self.ui.plainTextEdit.toPlainText()
        weighted_edges = []

        # 使用正则表达式匹配输入格式
        pattern = r'<(\w+),(\w+),(\d+)>|《(\w+),(\w+),(\d+)》'
        matches = re.findall(pattern, input_text)

        # 判断是否匹配到任何数据
        if not matches:
            QMessageBox.warning(self, "错误", "请添加正确格式的数据，例如：<a,b,1>", QMessageBox.Ok)
            return

        # 遍历匹配结果
        for match in matches:
            a, b, c, d, e, f = match
            if a:  # 使用尖括号的情况
                weighted_edges.append((a.strip(), b.strip(), int(c)))
            elif d:  # 使用双尖括号的情况
                weighted_edges.append((d.strip(), e.strip(), int(f)))
            else:
                # 输入不符合规范，显示错误提示
                QMessageBox.warning(self, "错误", "请添加正确格式的数据，例如：<a,b,1>", QMessageBox.Ok)
                return

        # 创建带权有向图
        self.G = nx.DiGraph()
        for edge in weighted_edges:
            a, b, weight = edge
            self.G.add_edge(a, b, weight=weight)

        layout_option = self.ui.comboBox.currentText()
        if layout_option == "Spectral Layout":
            pos = nx.spectral_layout(self.G)
        elif layout_option == "Kamada-Kawai Layout":
            pos = nx.kamada_kawai_layout(self.G)
        elif layout_option == "Circular Layout":
            pos = nx.circular_layout(self.G)
        else:
            pos = nx.spring_layout(self.G, seed=10)  # 默认使用spring_layout布局

        plt.clf()
        labels = {(a, b): weight for a, b, weight in self.G.edges(data="weight")}
        edge_weights = [weight for a, b, weight in self.G.edges(data="weight")]

        nx.draw(self.G, pos, with_labels=True, node_size=500, node_color="skyblue", font_size=10)
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels=labels, font_size=8, rotate=False)

        plt.title("带权图")
        self.graphCanvas.draw()
        self.graphGenerated = True

        self.generateOptimalRoute()

    # 生成最优路线
    def generateOptimalRoute(self):
        # 在这里实现生成最优路线的功能
        # 使用图算法（如最短路径算法）计算最优路线
        # 这里以最短路径算法Dijkstra为例
        # 假设起始点为start_vertex，可以根据实际情况修改
        start_vertex = self.ui.textEdit.toPlainText()
        if not self.graphGenerated:
            QMessageBox.warning(self, "错误", "您未生成任何图像", QMessageBox.Ok)
            return

        if not start_vertex:
            QMessageBox.warning(self, "错误", "请输入起始点", QMessageBox.Ok)

        if self.G is None:
            QMessageBox.warning(self, "错误", "带权图为空，请先导入带权图数据", QMessageBox.Ok)
            return

        self.floyd_shortest_paths(start_vertex)

    # 保存生成的图像
    def saveGraph(self):
        if not self.graphGenerated:
            # 如果没有生成图像，显示弹出窗口提示
            QMessageBox.warning(self, "错误", "您未生成任何图像", QMessageBox.Ok)
            return

        # 弹出文件对话框，允许用户选择保存图像的路径和文件名
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "保存图像", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            # 保存图像到指定路径
            self.graphView.savefig(file_path, format='png')

    # 导出结果到文本文件
    def exportResults(self, result_text):
        if not self.graphGenerated:
            # 如果没有生成图像，显示弹出窗口提示
            QMessageBox.warning(self, "错误", "您未生成任何图像", QMessageBox.Ok)
            return

        all_topo_orders = self.generateGraph()
        result_text = "\n".join(["->".join(order) for order in all_topo_orders])
        # 弹出文件对话框，允许用户选择保存结果的路径和文件名
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "保存结果", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                # 打开文件并将结果写入
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(result_text)

                QMessageBox.information(self, "提示", "结果已成功导出到文件：" + file_path, QMessageBox.Ok)
            except Exception as e:
                QMessageBox.warning(self, "错误", "导出结果时出现错误：" + str(e), QMessageBox.Ok)

    # 导入数据文件
    def importData(self):
        # 弹出文件对话框，允许用户自行选择要导入的本地文本文件
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "导入数据", "", "Text Files (*.txt);;All Files (*)")
        # 如果用户选择了文件，就将文件内容加载到文本编辑框
        if file_path:
            # 读取文件内容
            file = QFile(file_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                self.ui.plainTextEdit.setPlainText(stream.readAll())
                file.close()

    # 关闭应用程序
    def close_window(self):
        # 创建一个确认退出的消息框
        reply = QMessageBox.question(self, "确认退出", "确定要退出吗？", QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        # 如果用户选择是（Yes），则关闭窗口
        if reply == QMessageBox.Yes:
            self.close()
            
    # 在GraphVisualizationApp类中添加新的help方法
    def help(self):
        # 定义README文件的路径
        readme_file_path = "README.txt"

        # 检查README文件是否存在
        if os.path.exists(readme_file_path):
            try:
                os.system("start notepad " + readme_file_path)
            except Exception as e:
                QMessageBox.warning(self, "错误", "无法打开README文件：" + str(e), QMessageBox.Ok)
        else:
            QMessageBox.warning(self, "错误", "README文件不存在,请检查当前目录是否有README.txt文件", QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GraphVisualizationApp()
    ex.show()
    sys.exit(app.exec_())
