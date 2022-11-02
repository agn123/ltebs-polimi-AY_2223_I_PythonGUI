import sys

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget
)

# We import library dedicated to data plot
import pyqtgraph as pg
from pyqtgraph import PlotWidget



###############
# MAIN WINDOW #
###############
class MainWindow(QMainWindow):
    def __init__(self):
        """!
        @brief Init MainWindow.
        """
        super(MainWindow, self).__init__()

        # title and geometry
        self.setWindowTitle("GUI")
        width = 200
        height = 160
        self.setMinimumSize(width, height)

        self.initUI()

    #####################
    # GRAPHIC INTERFACE #
    #####################
    def initUI(self):
        """!
        @brief Set up the graphical interface structure.
        """
        # Create the plot widget
        self.graphWidget = PlotWidget()
        # Define buttons
        self.clear_btn = QPushButton(
            text="Clear",
            clicked=self.graphWidget.clear # .clear() is a method of the PlotWidget class già implementato
        )
        self.draw_btn = QPushButton(
            text="Draw",
            clicked=self.draw   #metodo che dovremo definire noi almeno in parte
        )
        #terzo bottone per aggiungere dato al grafico
        self.add_btn = QPushButton(
            text = "Add data",
            clicked = self.add_data         #gestire il segnale accoppiandolo con uno slot (metodo)
        )



        # layout
        button_hlay = QHBoxLayout()
        button_hlay.addWidget(self.clear_btn)
        button_hlay.addWidget(self.draw_btn)
        button_hlay.addWidget(self.add_btn)
        vlay = QVBoxLayout()
        vlay.addLayout(button_hlay)
        vlay.addWidget(self.graphWidget)
        widget = QWidget()
        widget.setLayout(vlay)
        self.setCentralWidget(widget)

        # Some random data
        self.hour = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.temperature1 = [30, 32, 34, 32, 33, 31, 29, 32, 35, 45]
        self.temperature2 = [16, 20, 17, 23, 30, 25, 28, 26, 22, 32]

        # Plot settings
            # Add grid
        self.graphWidget.showGrid(x=True, y=True)
            # Set background color
        self.graphWidget.setBackground('w')
            # Add title
        self.graphWidget.setTitle("Temperature measurement")
            # Add axis labels
        styles = {'color':'k', 'font-size':'15px'}
        self.graphWidget.setLabel('left', 'Temperature [°C]', **styles)
        self.graphWidget.setLabel('bottom', 'Time [h]', **styles)
            # Add legend
        self.graphWidget.addLegend()

        # Plot data: x, y values
        self.draw()
        

    def draw(self):
        """!
        @brief Draw the plots.
        """
        self.temp1line = self.plot(self.graphWidget, self.hour, self.temperature1, 'Temp 1', 'r')
        self.temp2line = self.plot(self.graphWidget, self.hour, self.temperature2, 'Temp 2', 'b')

    def plot(self, graph, x, y, curve_name, color):
        """!
        @brief Draw graph.
        """
        pen = pg.mkPen(color=color) #definire riga di colore
        line = graph.plot(x, y, name=curve_name, pen=pen)
        return line     #linea che collega punti x e y èer aggiornare grafico basta aggiungere dati nella variabile linea, non serve ridisegnare grafico

    def add_data(self):
        self.hour.append(11)
        self.temperature1.append(41)
        self.temperature2.append(34)
        
        #update plot by valling the existing line
        self.temp1line.setData(x=self.hour, y=self.temperature1)
        self.temp2line.setData(x=self.hour, y=self.temperature2)
    
#############
#  RUN APP  #
#############
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())