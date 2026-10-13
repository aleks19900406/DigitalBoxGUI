import datetime
import traceback
from time import sleep
from DigitalBox.dasConnect import SerialConnect, WifiEsp32Connect
from package.tester._clients.das import DAS
from PyQt5.QtCore import QThread
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from DigitalBox.lib import *
from . import state
from .styles import ButtonStyleOff2, ButtonStyleOn, ButtonStyleWhite
from .discovery import ScanWorker, get_local_ip, get_scan_config
from .devices import listConnection
from .helpers import dataFile, listBoxMarks


class ConnectionMixin:
    def start_scan(self):
        self.RefreshingConnection.setEnabled(False)
        self.BoxConnect.clear()
        if self.index_refreshing == 1:
            self.index_refreshing = 0
            self.box.disconnect()
        
        # clear combo but keep editable text if typed
        typed = self.BoxConnect.currentText()
        self.BoxConnect.clear()
        if typed:
            self.BoxConnect.setEditText(typed)
        self.ip_scanning.setText("Scanning network...")
        # create worker and thread
        local_ip = get_local_ip()
        base_ip, start, end = get_scan_config(local_ip)
        self.scanner = ScanWorker(base_ip, start, end, state.PASSWORD)
        self.scan_thread = QThread()
        self.scanner.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scanner.run)
        self.scanner.finished.connect(self.add_ip)
        self.scanner.progress.connect(self.update_progress)
        self.scanner.finished.connect(self.scan_finished)
        self.scan_thread.start()

    def stop_scan(self):
        if self.scanner:
            self.scanner.stop()

    def add_ip(self, results):
        seen_hosts = {
            self.BoxConnect.itemText(index).rsplit(" - ", 1)[0].casefold()
            for index in range(self.BoxConnect.count())
            if self.BoxConnect.itemData(index)
        }
        for result in results:
            try:
                name, ip = result.split("@", 1)
            except ValueError:
                name = ""
                ip = result
            name = name.strip()
            ip = ip.strip()
            host_key = (name or ip).casefold()
            if host_key in seen_hosts:
                continue
            item_text = f'{name} - {ip}' if name else ip
            self.BoxConnect.addItem(item_text, ip)
            seen_hosts.add(host_key)

    def update_progress(self, message):
        self.ip_scanning.setText(message)

    def scan_finished(self):
        self.RefreshingConnection.setEnabled(True)
        self.ip_scanning.setText("Scan finished")
        # cleanup thread
        if self.scan_thread:
            self.scan_thread.quit()
            self.scan_thread.wait()
            self.scan_thread = None
            self.scanner = None

    def animationConnect(self):
        self.connectBar.setVisible(True)
        for value in range(0,110,5):
            self.connectBar.setValue(value)
            sleep(0.05)
        self.connectBar.setVisible(False)
        self.connectBar.setValue(0)

    def connectBox(self,CONNECTBOX):
        """
        - connect digital box with RPI or direct with digital box(serial connection)
        - check if version is correct
        - show warning message if version is not correct  
        """
        rpi_index = self.BoxConnect.findText(CONNECTBOX)
        rpi_ip = self.BoxConnect.itemData(rpi_index) if rpi_index >= 0 else None
        self.backup_save()
        self.Connection = CONNECTBOX
        self.startStopSaving.setEnabled(False)
        self.resetExcelParameters()
        self.connectAnimation.start(self.animationConnect)
        try:
            if self.index_refreshing >= 1:
                sleep(2)
                self.box.disconnect()
            
            if CONNECTBOX[0:3] =='COM':
                self.box = SerialConnect(CONNECTBOX[0:5].replace(' ',''))
                VERSION = self.box.connect()
                self.ip_scanning.setVisible(False)
                self.label_errorSaveFile.setVisible(False)
                self.label_saveFile.setVisible(True)
            elif CONNECTBOX[0:3] =='ESP':
                self.box = WifiEsp32Connect(CONNECTBOX.replace('ESP32 - ',''))
                VERSION = self.box.connect()
                self.ip_scanning.setVisible(False)
                self.label_errorSaveFile.setVisible(False)
                self.label_saveFile.setVisible(True)

            elif rpi_ip or CONNECTBOX.startswith("RPI"):
                VERSION = "0.0"
                self.box = None
                self.ip_scanning.setVisible(False)

                try:
                    box_name = rpi_ip or CONNECTBOX.strip()
                    if box_name.startswith("RPI - "):
                        box_name = box_name[len("RPI - "):].strip()
                    box_name = box_name.rsplit("@", 1)[-1].strip()

                    self.box = DAS(box_name)

                    try:
                        self.box.disconnect()
                    except Exception:
                        pass

                    self.box.connect()

                    read_version = []

                    for _ in range(10):
                        try:
                            box_version = getattr(self.box, "box_version", None)

                            if box_version and len(box_version) > 0:
                                version_value = str(box_version[0]).strip()
                                if version_value:
                                    read_version.append(version_value)
                        except Exception:
                            pass
                        sleep(0.2)
                    print(f"Read versions: {read_version}")

                    for item in read_version:
                        if len(item) == 4:
                            print(item)
                            VERSION = item
                            break

                except Exception as e:
                    print("RPI connection/version read failed: {}".format(e))
                    VERSION = "fail to read"

            
            if self.box_is_connected == 0:
                self.box_is_connected = 1
                self.index_on_off = 1
                self.on_off.setIcon(self.iconOn)
            
            if VERSION is not None and VERSION >= state.VERZIJA_RPI:
                    self.BOX_VERSION.setVisible(False)
                    self.warningMessagePot.setVisible(False)
                    self.warningMessageDac.setVisible(False)
                    self.BoxConnect.setStyleSheet(ButtonStyleOn)
                    self.BOX_VERSION.setFont(QFont('Arial', 10))
                    self.BOX_VERSION.setStyleSheet("color: black")
                    self.BOX_VERSION.setVisible(True)
                    self.BOX_VERSION.setText(f"ARDUINO MEGA/ESP32 SW = {VERSION}")
            else:
                self.BOX_VERSION.setVisible(False)
                self.BOX_VERSION.setFont(QFont('Arial', 14))
                self.BOX_VERSION.setStyleSheet("color: red")
                self.BOX_VERSION.setVisible(True)
                self.BOX_VERSION.setText(
                    f"Digital box version: {VERSION}. Required: >= {state.VERZIJA_ESP}. "
                    f"Please update the digital box or use a compatible GUI version."
                )
            print('connect')
            self.BoxConnect.setStyleSheet(ButtonStyleOn)
            #self.connectAnimation.start(self.animationConnect)
            self.index_refreshing +=1
            self.DIGITAL_BOX_MAIN.start()
            self.dateTimeTimer.start()
            #self.on_off.setIcon(self.iconOn)
            self.ButtonG800.setStyleSheet(ButtonStyleOff2)
            self.ButtonBIO24.setStyleSheet(ButtonStyleOff2)
            self.ButtonHusaModel.setStyleSheet(ButtonStyleOff2)
            self.ButtonPyroSystem.setStyleSheet(ButtonStyleOff2)
            self.ButtonDacSet.setStyleSheet(ButtonStyleOff2)
            self.ButtonSetPot.setStyleSheet(ButtonStyleOff2)
            self.ButtonSetDac.setStyleSheet(ButtonStyleOff2)
            self.ButtonAutomation.setStyleSheet(ButtonStyleOff2)
            self.warningMessageAddFunction.setStyleSheet("color: black")
            self.warningMessageAddFunction.setText("ADDITIONAL FUNCTIONS")     
        except Exception:
            #VERSION = None
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                f.write(f'Das service is not connected to this ip {CONNECTBOX[6:]} \n')
                f.write('Solution:\n')
                f.write(f'-- Open supervisor {CONNECTBOX[6:]}:9001 (copy ip to this ip to browser) and check das service \n')
                f.write('-- Reset das service.Das service must be in running state \n')
                f.write('-- Computer and RPI must be in the same domain \n')
                f.write(f'-- RPI(das {state.VERZIJA_RPI}), digital box(third generation) and tester({state.VERZIJA_RPI}) must be updated \n')
                f.write(f'{state.errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{state.errorNumber*2}\n')
            f.close()
        self.connectParameters = 1
        self.box_is_connected +=1
        if self.box_is_connected >=2:
            self.box_is_connected =0

    def BoxRefreshing(self):
        """
        - refresh box connection,digital pot table and select marks
        """
        self.backup_save()
        self.BoxConnect.setStyleSheet(ButtonStyleWhite)   
        self.BoxMarks.setStyleSheet(ButtonStyleWhite)
        self.SelectPotTable.setStyleSheet(ButtonStyleWhite)
        self.resetExcelParameters()
        self.indexButtonSave = 0
        self.repeatSaveData = 0
        self.ip_scanning.setVisible(True)
        self.BoxConnect.clear()
        self.start_scan()
        self.BoxConnect.addItems(listConnection())
        if  self.index_refreshing == 0:
            self.ExcelFile.clear()
            #self.BoxMarks.clear()
            #self.SelectPotTable.clear()
            #self.BoxMarks.addItems(listBoxMarks())
            #self.SelectPotTable.addItems(listDigitalPotTable())
            self.ExcelFile.addItems(dataFile())
            self.BOX_VERSION.setVisible(False)
        else:
            sleep(2)
            self.index_refreshing +=1
            self.refreshSaveData.stop()
            #self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOff.png')))
            #self.startStopSaving.setIcon(self.iconSaveData)
            self.startStopSaving.setEnabled(False)
            self.DIGITAL_BOX_MAIN.stop()
            self.dateTimeTimer.stop()
            self.DIGITAL_BOX_MAIN.setInterval(1000)
            #self.BoxMarks.clear()
            self.ExcelFile.clear()
            #self.SelectPotTable.clear()
            self.label_connect.setText('BOX CONNECT')
            self.label_marks.setText('SELECT MARKS')
            self.BoxConnect.addItems(listConnection())
            self.BoxMarks.addItems(listBoxMarks())
            self.BoxMarks.setStyleSheet(ButtonStyleWhite)
            self.ExcelFile.setStyleSheet(ButtonStyleWhite)
            self.ExcelFile.addItems(dataFile())
            #self.SelectPotTable.addItems(listDigitalPotTable())
            #for index,TablePot in enumerate(listDigitalPotTable()):
                #eval(f'self.labelDigitalPot{index}.setStyleSheet(MainScreenStyle)')
                #eval(f'self.digital_pot{index}.setStyleSheet(MainScreenStyle)')
            #self.AllTable = listDigitalPotTable()
            #self.on_off.setIcon(self.iconOff)
            """ 
            for index in range(8):
                eval(f'self.OUT{index}.setStyleSheet(ButtonStyleOff2)')
                eval(f'self.OUT{index}.setIcon(self.iconSwitchOff)')
                
            for index in range(6):
                eval(f'self.digital_pot{index}.setStyleSheet(ButtonStyleWhite)')
                eval(f'self.digital_pot{index}.value()')
                #eval(f'self.digital_pot{index}.setEnabled(False)')
                eval(f'self.lcdNumber_digital_pot{index}.display(0)')
            """
            for index in range(4):
                self.index_auto[index] = 0
                eval(f'self.AUTO{index+1}.setStyleSheet(ButtonStyleOff2)')
            sleep(1)
            self.box.disconnect()
            #print('disconnected')
    
        if self.index_refreshing >=2:
            self.index_refreshing =0
