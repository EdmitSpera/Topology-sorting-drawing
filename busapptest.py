import numpy as np
import sys
import threading
import networkx as nx
import matplotlib.pyplot as plt
import re
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from PySide2.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTextEdit
from PySide2.QtUiTools import loadUiType  # 导入用于加载UI文件的函数
from PySide2.QtCore import QFile, QTextStream
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class GraphVisualizationApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 加载UI文件
        self.ui = loadUiType("busapp.ui")[0]()
        self.ui.setupUi(self)

        # 初始化图像生成状态变量
        self.graphGenerated = False

        self.G = None

        # 创建matplotlib视图和图形canvas
        self.graphView = plt.figure()
        self.graphCanvas = FigureCanvas(self.graphView)
        #
        # 将canvas添加到ui布局中
        self.ui.horizontalLayout.addWidget(self.graphCanvas)

        # 创建QPlainTextEdit对象
        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)

        # 链接ui菜单栏
        self.ui.actionOpenj.triggered.connect(self.importData)
        self.ui.actiongraph.triggered.connect(self.saveGraph)
        self.ui.actiongraph_2.triggered.connect(self.generateGraph)
        self.ui.actionHelp_window.triggered.connect(self.help)
        self.ui.actionExit.triggered.connect(self.close_window)
        self.ui.actionTopological_Sorting.triggered.connect(self.exportResults)
        self.ui.actionweighted_graph.triggered.connect(self.weightedGraph)
    def generate_Graph(self):
        graph_thread = threading.Thread(target=self.generateGraph)
        graph_thread.start()

    def generateGraph(self):
        # 获取文本框中的输入，每行定义一个关系，格式为 "<a,b>"
        input_text = self.ui.plainTextEdit.toPlainText()
        input_text = input_text.replace('<', '').replace('>', '')  # 去掉尖括号
        edges = []
        for line in input_text.split('\n'):
            if line.strip():
                if ',' in line:
                    a, b = line.strip().split(',')
                    edges.append((a.strip(), b.strip()))
                else:
                    # 输入不符合规范，显示错误提示
                    QMessageBox.warning(self, "警告", "请输入正确的格式，例如：<a,b>", QMessageBox.Ok)
                    return
        # 创建有向图
        G = nx.DiGraph()
        G.add_edges_from(edges)

        # 检查是否存在依赖关系
        if not nx.is_directed_acyclic_graph(G):
            # 存在依赖关系，显示错误提示
            QMessageBox.warning(self, "警告", "输入的数据存在依赖关系", QMessageBox.Ok)
            return

        pos = nx.circular_layout(G)  # 默认使用spring_layout布局

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
        #
        # # print("排序结果：")
        # result_text = "\n".join(["->".join(order) for order in all_topo_orders])
        # # self.ui.textEdit.setPlainText(result_text)
        # # print(result_text)
        return  all_topo_orders
    # ----------------------------------------------------------------------------------------------------------------------
    def floyd_shortest_paths(self,start_vertex):
        if not self.graphGenerated:
            QMessageBox.warning(self, "警告", "您未生成任何图像", QMessageBox.Ok)
            return

        if self.G is None:
            QMessageBox.warning(self, "警告", "带权图为空，请先导入带权图数据", QMessageBox.Ok)
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

            # 打印最短路径
        print("从顶点 '{}' 出发的最短路径：".format(start_vertex))
        for i in range(num_nodes):
            if index_to_node[i] != start_vertex:
                shortest_path = distance_matrix[node_to_index[start_vertex]][i]
                if shortest_path == np.inf:
                    print("顶点 '{}' 不可达到顶点 '{}'。".format(start_vertex, index_to_node[i]))
                else:
                    print("到顶点 '{}' 的最短路径为：{}".format(index_to_node[i], shortest_path))


    def weightedGraph(self):
        # 获取文本框中的输入，每行定义一个带权边，格式为 "<a,b,c>"
        # a和b为顶点，c为ab边的权重
        input_text = self.ui.plainTextEdit.toPlainText()
        weighted_edges = []
        for line in input_text.split('\n'):
            if line.strip():
                # 使用正则表达式提取带权边信息
                match = re.match(r'<(\w+),(\w+),(\d+)>', line.strip())
                if match:
                    a, b, weight = match.groups()
                    weighted_edges.append((a.strip(), b.strip(), int(weight)))
                else:
                    # 输入不符合规范，显示错误提示
                    QMessageBox.warning(self, "警告", "请输入正确的格式，例如：<a,b,c>", QMessageBox.Ok)
                    return

        # 创建带权有向图
        self.G = nx.DiGraph()
        for edge in weighted_edges:
            a, b, weight = edge
            self.G.add_edge(a, b, weight=weight)

        plt.clf()
        if not self.graphGenerated:
            plt.clf()
            pos = nx.spring_layout(self.G, seed=10)
            labels = {(a, b): weight for a, b, weight in self.G.edges(data="weight")}
            edge_weights = [weight for a, b, weight in self.G.edges(data="weight")]

            nx.draw(self.G, pos, with_labels=True, node_size=500, node_color="skyblue", font_size=10)
            nx.draw_networkx_edge_labels(self.G, pos, edge_labels=labels, font_size=8, rotate=False)

            plt.title("带权图")
            self.graphCanvas.draw()
            self.graphGenerated = True

        self.generateOptimalRoute()

    def generateOptimalRoute(self):
        # 在这里实现生成最优路线的功能
        # 使用图算法（如最短路径算法）计算最优路线
        # 这里以最短路径算法Dijkstra为例
        # 假设起始点为start_vertex，可以根据实际情况修改
        start_vertex = self.ui.textEdit.toPlainText()
        if not self.graphGenerated:
            QMessageBox.warning(self, "警告", "您未生成任何图像", QMessageBox.Ok)
            return

        if not start_vertex:
            QMessageBox.warning(self, "警告", "请输入起始点", QMessageBox.Ok)

        if self.G is None:
            QMessageBox.warning(self, "警告", "带权图为空，请先导入带权图数据", QMessageBox.Ok)
            return

        self.floyd_shortest_paths(start_vertex)

    def saveGraph(self):
        if not self.graphGenerated:
            # 如果没有生成图像，显示弹出窗口提示
            QMessageBox.warning(self, "警告", "您未生成任何图像", QMessageBox.Ok)
            return

        # 弹出文件对话框，允许用户选择保存图像的路径和文件名
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "保存图像", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            # 保存图像到指定路径
            self.graphView.savefig(file_path, format='png')

    def exportResults(self,result_text):
        if not self.graphGenerated:
            # 如果没有生成图像，显示弹出窗口提示
            QMessageBox.warning(self, "警告", "您未生成任何图像", QMessageBox.Ok)
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

    def importData(self):
        # 弹出文件对话框，允许用户自行选择要导入的本地文本文件
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "导入数据", "", "Text Files (*.txt);;All Files (*)")
        # 如果用户选择了文件，就将文件内容加载到文本编辑框
        if file_path:
            # 读取文件内容
            file = QFile(file_path)
            # with open(file_path, 'r', encoding='utf-8') as f:
            #     self.dataTextEdit.setText(f.read())
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                self.ui.plainTextEdit.setPlainText(stream.readAll())
                file.close()
    def help(self):
        # 弹出帮助文档
        QMessageBox.about(self, 'Help', '在文本编辑框中按要求输入多个邻近站点名称\n点击generate生成结果\n可在菜单栏中导入数据txt')

    def close_window(self):
        # 创建一个确认退出的消息框
        reply = QMessageBox.question(self, "确认退出", "确定要退出吗？", QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        # 如果用户选择是（Yes），则关闭窗口
        if reply == QMessageBox.Yes:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GraphVisualizationApp()
    ex.show()
    sys.exit(app.exec_())
