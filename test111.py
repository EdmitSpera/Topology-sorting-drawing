import sys
import networkx as nx
import matplotlib.pyplot as plt
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtUiTools import loadUiType  # 导入用于加载UI文件的函数
from PySide6.QtCore import QFile, QTextStream
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
class GraphVisualizationApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 加载UI文件
        self.ui = loadUiType("iiitem.ui")[0]()
        self.ui.setupUi(self)

        # 初始化图像生成状态变量
        self.graphGenerated = False
        #
        # 创建matplotlib视图和图形canvas
        self.graphView = plt.figure()
        self.graphCanvas = FigureCanvas(self.graphView)
        #
        # # 将canvas添加到ui布局中
        self.ui.horizontalLayout.addWidget(self.graphCanvas)
        #
        # # 连接按钮的点击事件
        # self.ui.get_Button.clicked.connect(self.generateGraph)
        # self.ui.save_Button.clicked.connect(self.saveGraph)
        # self.ui.layout_combo.currentIndexChanged.connect(self.generateGraph)
        #
        # # 链接导入文件
        # self.ui.load_Button = QPushButton('导入',self)
        # self.ui.layout.addWidget(self.ui.load_Button)
        # self.ui.load_Button.clicked.connect(self.importData)
        # 链接打开文件
        self.ui.actionOpenj.triggered.connect(self.importData)
        self.ui.actiongraph.triggered.connect(self.saveGraph)
        self.ui.actiongraph_2.triggered.connect(self.generateGraph)

    def generateGraph(self,layout):
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

        pos = nx.spring_layout(G, seed=10)  # 默认使用spring_layout布局

        # 计算所有拓扑排序
        all_topo_orders = list(nx.all_topological_sorts(G))
        if not all_topo_orders:
            print("无法进行拓扑排序，图中存在循环依赖。")
            return

        # 清空Matplotlib视图并绘制第一个拓扑排序结果
        plt.clf()
        first_topo_order = all_topo_orders[0]
        nx.draw(G, pos, with_labels=True, node_size=700, node_color="skyblue", font_size=10)
        plt.title("拓扑排序")
        self.graphCanvas.draw()
        self.graphGenerated = True  # 标记图像已生成

        # 打印所有拓扑排序结果
        print("所有拓扑排序结果:")
        for topo_order in all_topo_orders:
            print(topo_order)
    # ----------------------------------------------------------------------------------------------------------------------
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GraphVisualizationApp()
    ex.show()
    sys.exit(app.exec_())
