import sys

import time

import logging

from PyQt5 import QtCore
from PyQt5.QtCore import (
    QObject,
    QThreadPool, 
    QRunnable, 
    pyqtSignal, 
    pyqtSlot
)

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QComboBox,
    QHBoxLayout,
    QWidget,
)

import serial
import serial.tools.list_ports


# Globals
CONN_STATUS = False


# Logging config
logging.basicConfig(format="%(message)s", level=logging.INFO)   #level grado di importanza dei messaggi oltre il quale vengono visualizzati


#########################
# SERIAL_WORKER_SIGNALS #
#########################
class SerialWorkerSignals(QObject): #suggerimento dare nome del thread parallelo a cui si riferisce
    """!
    @brief Class that defines the signals available to a serialworker.

    Available signals (with respective inputs) are:
        - device_port:
            str --> port name to which a device is connected
        - status:
            str --> port name
            int --> macro representing the state (0 - error during opening, 1 - success)
    """
    device_port = pyqtSignal(str)   #porterà il nome della porta alla quale ho trovato un device connesso
    status = pyqtSignal(str, int)   #info su nome della porta + 0 se errore/1 se tutto ok


#################
# SERIAL_WORKER #
#################
class SerialWorker(QRunnable):  #classe del thread parallelo
    """!
    @brief Main class for serial communication: handles connection with device.
    """
    def __init__(self, serial_port_name):
        """!
        @brief Init worker.
        """
        self.is_killed = False  #variabile booleana controllo quando utente chiude er interrompere task qrunnable
        super().__init__()
        # init port, params and signals
        self.port = serial.Serial()
        self.port_name = serial_port_name   #dall'istanza del serial worker quando lo lancio vuole nome della porta
        self.baudrate = 9600 # hard coded but can be a global variable, or an input param
        self.signals = SerialWorkerSignals()

    @pyqtSlot() #decoratore metodi da usare come slot in applicazioni multithread
    def run(self):  #metodo run lanciato quando chiamato thread, quando arriva alla fine thread parallelo muore (poi può essere riusato grazie a threadpool) 
        """!
        @brief Estabilish connection with desired serial port.
        """
        global CONN_STATUS

        if not CONN_STATUS:
            try:
                self.port = serial.Serial(port=self.port_name, baudrate=self.baudrate,   #operazione che apre la porta
                                        write_timeout=0, timeout=2)                
                if self.port.is_open:
                    CONN_STATUS = True
                    self.signals.status.emit(self.port_name, 1) #emit per mandare segnale, butta fuori nime della porta affinchè thread principale lo sappia
                    time.sleep(0.01)     #blocca codice per 0.01 secondi, non bello ma necessario per far fisicamente allineare i dispositivi
            except serial.SerialException:  #se non riesce ad aprire comunicazione non andata a buon fine logging print a terminale che c'è stato errore 
                logging.info("Error with port {}.".format(self.port_name))
                self.signals.status.emit(self.port_name, 0) #passo 0 perchè c'è stato errore
                time.sleep(0.01)

    @pyqtSlot()
    def send(self, char):
        """!
        @brief Basic function to send a single char on serial port.
        """
        try:
            self.port.write(char.encode('utf-8'))
            logging.info("Written {} on port {}.".format(char, self.port_name))
        except:
            logging.info("Could not write {} on port {}.".format(char, self.port_name))

   
    @pyqtSlot()
    def killed(self):
        """!
        @brief Cose the serial port before closing the app.
        """
        global CONN_STATUS
        if self.is_killed and CONN_STATUS:
            self.port.close()
            time.sleep(0.01)
            CONN_STATUS = False
            self.signals.device_port.emit(self.port_name)

        logging.info("Killing the process")


###############
# MAIN WINDOW #
###############
class MainWindow(QMainWindow):  #generiamo interfaccia
    def __init__(self):
        """!
        @brief Init MainWindow.
        """
        # define worker
        self.serial_worker = SerialWorker(None) #inizializziamo vuoto thread parallelo

        super(MainWindow, self).__init__()

        # title and geometry
        self.setWindowTitle("GUI")
        width = 400
        height = 320
        self.setMinimumSize(width, height)

        # create thread handler
        self.threadpool = QThreadPool() #contenitore dove vivranno thread che io devo creare

        self.connected = CONN_STATUS
        self.serialscan()   #funzione utente che fa scan delle porte seriali per vedere quali sono attive
        self.initUI()


    #####################
    # GRAPHIC INTERFACE #
    #####################
    def initUI(self):
        """!
        @brief Set up the graphical interface structure.
        """
        # layout
        button_hlay = QHBoxLayout()
        button_hlay.addWidget(self.com_list_widget)
        button_hlay.addWidget(self.conn_btn)
        widget = QWidget()
        widget.setLayout(button_hlay)
        self.setCentralWidget(widget)


    ####################
    # SERIAL INTERFACE #
    ####################
    def serialscan(self):
        """!
        @brief Scans all serial ports and create a list.
        """
        # create the combo box to host port list
        self.port_text = ""
        self.com_list_widget = QComboBox()  #crea menù a tendina inizialmente vuoto e pulsante
        self.com_list_widget.currentTextChanged.connect(self.port_changed)  #segnale cambio selezione menù a tendina
        
        # create the connection button
        self.conn_btn = QPushButton(
            text=("Connect to port {}".format(self.port_text)),     #testo che dipende da testo visualizzato su menù a tendina
            checkable=True, #pulsante non è soltanto clickable ma ha uno stato (premuto o non premuto)
            toggled=self.on_toggle #prima avevamo clicked, ora toggle generato ogni volta il pulsante cambia stato (premuto o rilasciato)
        )

        # acquire list of serial ports and add it to the combo box
        serial_ports = [    #lista delle porte con ciclo fro all'interno, nomi variabile p che fa lo scan delle porte
                p.name
                for p in serial.tools.list_ports.comports()
            ]
        self.com_list_widget.addItems(serial_ports)


    ##################
    # SERIAL SIGNALS #
    ##################
    def port_changed(self):
        """!
        @brief Update conn_btn label based on selected port.
        """
        self.port_text = self.com_list_widget.currentText()
        self.conn_btn.setText("Connect to port {}".format(self.port_text))

    @pyqtSlot(bool)
    def on_toggle(self, checked):   #toggle info in più sullo stato se è prmeuto o non premuto variaible booleana checked
        """!
        @brief Allow connection and disconnection from selected serial port.
        """
        if checked:
            # setup reading worker
            self.serial_worker = SerialWorker(self.port_text) # needs to be re defined #creando l'istanza si definisce il thread parallelo
            # connect worker signals to functions
            self.serial_worker.signals.status.connect(self.check_serialport_status) #funzioni che utilizzerò come slot
            self.serial_worker.signals.device_port.connect(self.connected_device)
            # execute the worker
            self.threadpool.start(self.serial_worker)   #lancio il thread parallelo, start lancia automaticamente il metodo run
        else:
            # kill thread
            self.serial_worker.is_killed = True
            self.serial_worker.killed()
            self.com_list_widget.setDisabled(False) # enable the possibility to change port, riabilito menù a tendina
            self.conn_btn.setText(
                "Connect to port {}".format(self.port_text)
            )

    def check_serialport_status(self, port_name, status):
        """!
        @brief Handle the status of the serial port connection.

        Available status:
            - 0  --> Error during opening of serial port
            - 1  --> Serial port opened correctly
        """
        if status == 0:
            self.conn_btn.setChecked(False) #non riuscito, non cambio stato e testo del pulsante
        elif status == 1:
            # enable all the widgets on the interface
            self.com_list_widget.setDisabled(True) # disable the possibility to change COM port when already connected
            #IMPORTANTE! tutti questi aspetti per evitare confusione per l'utente, i due widgets sono interconnessi
            self.conn_btn.setText(
                "Disconnect from port {}".format(port_name)
            )

    def connected_device(self, port_name):
        """!
        @brief Checks on the termination of the serial worker.
        """
        logging.info("Port {} closed.".format(port_name))


    def ExitHandler(self):
        """!
        @brief Kill every possible running thread upon exiting application.
        """
        self.serial_worker.is_killed = True
        self.serial_worker.killed()




#############
#  RUN APP  #
#############
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    app.aboutToQuit.connect(w.ExitHandler)
    w.show()
    sys.exit(app.exec_())