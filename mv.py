from PyQt5 import QtWidgets,uic
import sys
import os
import re

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.dir=""
        self.currentItem =""
        self.itemNonText =""
        self.tmpSaves=[]
        self.tmpLines=[]
        uic.loadUi("./mv.ui",self)
        self.setFixedSize(1146,604)
        self.setWindowTitle("Metadata viewer")
        #Buttons
        self.b0 = self.findChild(QtWidgets.QPushButton,"pushButton")
        self.b0.clicked.connect(self.select_folder)
        #Selected kit label
        self.l0 = self.findChild(QtWidgets.QLabel,"label_2")
        #list widget
        self.list0 = self.findChild(QtWidgets.QListWidget,"listWidget")
        self.list0.itemClicked.connect(self.selected_item)
        #preview text
        self.preview = self.findChild(QtWidgets.QPlainTextEdit,"plainTextEdit")
        self.preview.setReadOnly(True)
        #Line Edits
        self.lineType = self.findChild(QtWidgets.QLineEdit,"lineEdit")
        self.lineDesorbNumber = self.findChild(QtWidgets.QLineEdit,"lineEdit_2")
        self.lineSorbentType = self.findChild(QtWidgets.QLineEdit,"lineEdit_3")
        self.lineTTFilePath = self.findChild(QtWidgets.QLineEdit,"lineEdit_4")
        self.lineAnalyserSN = self.findChild(QtWidgets.QLineEdit,"lineEdit_5")
        self.lineBaselinePath = self.findChild(QtWidgets.QLineEdit,"lineEdit_6")
        self.lineTubeSlot = self.findChild(QtWidgets.QLineEdit,"lineEdit_7")
        #User comments
        self.comments = self.findChild(QtWidgets.QPlainTextEdit,"plainTextEdit_2")
        ###Save button
        self.b1 = self.findChild(QtWidgets.QPushButton,"pushButton_2")
        self.b1.clicked.connect(self.update_data)

        self.show()

    def select_folder(self):
        self.dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder:", "./", QtWidgets.QFileDialog.ShowDirsOnly)
        if self.dir:
            self.list0.clear()
            self.l0.setText(os.path.basename(self.dir))
            subfolders = [ f.name for f in os.scandir(self.dir) if f.is_dir() ]
            for sb in subfolders:
                targetSR = os.path.join(self.dir,sb,"AutoMeta.meta")
                fileSR = open(targetSR,'r')
                linesSR = fileSR.readlines()
                res1 = re.search('label(.*)desorb no.', linesSR[0])
                a1 = str(str(res1.group(1)).strip()).replace("\n","")
                res2 = re.search('desorb no.(.*)', linesSR[0])
                a2 = str(str(res2.group(1)).strip()).replace("\n","")
                boii = f"{sb}    "+a1+f" / Desorb {a2}"
                self.list0.addItem(QtWidgets.QListWidgetItem(boii))
    
    def selected_item(self,item):
        #clean before loading
        rss = re.search("(.*)    ",str(item.text()))
        self.currentItem = str(str(rss.group(1)).strip()).replace("\n","")
        self.itemNonText = item
        self.tmpSaves = []
        self.tmpLines= []
        self.preview.setPlainText("")
        self.comments.setPlainText("")
        self.lineType.setText("")
        self.lineDesorbNumber.setText("")
        self.lineSorbentType.setText("")
        self.lineTTFilePath.setText("")
        self.lineAnalyserSN.setText("")
        self.lineBaselinePath.setText("")
        self.lineTubeSlot.setText("")
        #Start loading metadata
        target = os.path.join(self.dir,self.currentItem,"AutoMeta.meta")
        file = open(target,'r')
        lines = file.readlines()
        self.tmpLines=lines
        #Type & Desorb#
        l_1=lines[0]
        result10 = re.search('label(.*)desorb no.', l_1)
        self.lineType.setText(str(str(result10.group(1)).strip()).replace("\n",""))
        result11 = re.search('desorb no.(.*)', l_1)
        self.lineDesorbNumber.setText(str(str(result11.group(1)).strip()).replace("\n",""))
        #Sorbent type
        l_2=lines[1]
        result100 = re.search('sorbent(.*)',l_2)
        self.lineSorbentType.setText((str(result100.group(1)).strip()).replace("\n",""))
        #TTFilePath
        l_3=lines[2]
        result13 = re.search('TT_Filepath(.*)',l_3)
        self.lineTTFilePath.setText((str(result13.group(1)).strip()).replace("\n",""))
        #Analyser SN
        l_5=lines[4]
        result14 = re.search('Analyzer_SN(.*)',l_5)
        self.lineAnalyserSN.setText(str(str(result14.group(1)).strip()).replace("\n",""))
        #Baseline Path
        l_6=lines[5]
        result15 = re.search('BaselinePath(.*)',l_6)
        self.lineBaselinePath.setText(str(str(result15.group(1)).strip()).replace("\n",""))
        l_4=lines[3]
        ##Put The text preview together
        self.preview.setPlainText(l_1+l_2+l_3+l_4+l_5+l_6)
        ##Grab Tube Slot and comment from additional file containing extra content
        if os.path.exists(os.path.join(self.dir,self.currentItem,"additionals.txt")):
            xfile = open(os.path.join(self.dir,self.currentItem,"additionals.txt"))
            lineAdd = xfile.readlines()
            if len(lineAdd) > 1:#both exisit
                self.lineTubeSlot.setText(str(lineAdd[0]).replace("\n",""))
                self.comments.setPlainText(lineAdd[1])
            elif len(lineAdd) == 1:#only tune slot exists
                self.lineTubeSlot.setText(str(lineAdd[0]).replace("\n",""))
                self.comments.setPlainText("")
            else:
                self.lineTubeSlot.setText("")
                self.comments.setPlainText("")
        else:
            #if the file does not exist just create an empty one for future use
            open(os.path.join(self.dir,self.currentItem,"additionals.txt"), 'a').close()
            self.lineTubeSlot.setText("")
            self.comments.setPlainText("")
        #SAVE TEMPORARY COPY OF ALL LINE EDITS (needed later for search and replace when we apply metadata update)
        self.tmpSaves.append(str(self.lineType.text()).replace("\n",""))
        self.tmpSaves.append(str(self.lineDesorbNumber.text()).replace("\n",""))
        self.tmpSaves.append(str(self.lineSorbentType.text()).replace("\n",""))
        self.tmpSaves.append(str(self.lineTTFilePath.text()).replace("\n",""))
        self.tmpSaves.append(str(self.lineAnalyserSN.text()).replace("\n",""))
        self.tmpSaves.append(str(self.lineBaselinePath.text()).replace("\n",""))
        self.tmpSaves.append(str(self.lineTubeSlot.text()).replace("\n",""))
        self.tmpSaves.append(str(self.comments.toPlainText()))
    
    def update_data(self):
        #Gather data
        if self.dir !="":
            new_lineType = self.lineType.text()
            old_lineType = self.tmpSaves[0]
            new_lineDesorbNumber = self.lineDesorbNumber.text()
            old_lineDesorbNumber = self.tmpSaves[1]
            new_lineSorbentType = self.lineSorbentType.text()
            old_lineSorbentType = self.tmpSaves[2]
            new_lineTTFilePath = self.lineTTFilePath.text()
            old_lineTTFilePath = self.tmpSaves[3]
            new_lineAnalyserSN = self.lineAnalyserSN.text()
            old_lineAnalyserSN = self.tmpSaves[4]
            new_lineBaselinePath = self.lineBaselinePath.text()
            old_lineBaselinePath = self.tmpSaves[5]
            new_lineTubeSlot = self.lineTubeSlot.text()
            old_lineTubeSlot = self.tmpSaves[6]
            new_comments = self.comments.toPlainText()
            old_comments = self.tmpSaves[7]
            #check data before update
            if str(new_lineDesorbNumber).isnumeric() == False:
                self.alertme(title="Warning",text="desorb number must be a number")
                self.lineDesorbNumber.setText(old_lineDesorbNumber)
                return
            if str(new_lineAnalyserSN).isnumeric() == False:
                self.alertme(title="Warning",text="Analyser_SN must be a number")
                self.lineDesorbNumber.setText(old_lineAnalyserSN)
                return
            #update
            #Type and desorb number
            self.tmpLines[0] = str(self.tmpLines[0]).replace("label	"+old_lineType,"label	"+new_lineType,1)
            self.tmpLines[0] = str(self.tmpLines[0]).replace("desorb no. "+old_lineDesorbNumber,"desorb no. "+new_lineDesorbNumber,1)
            #Sorbent type
            self.tmpLines[1] = str(self.tmpLines[1]).replace("sorbent "+old_lineSorbentType,"sorbent "+new_lineSorbentType,1)
            #TT_FilePath
            self.tmpLines[2] = str(self.tmpLines[2]).replace("TT_Filepath	"+old_lineTTFilePath,"TT_Filepath	"+new_lineTTFilePath,1)
            #Analyzer SN
            self.tmpLines[4] = str(self.tmpLines[4]).replace("Analyzer_SN	"+old_lineAnalyserSN,"Analyzer_SN	"+new_lineAnalyserSN,1)
            #Baseline Path
            self.tmpLines[5] = str(self.tmpLines[5]).replace("BaselinePath	"+old_lineBaselinePath,"BaselinePath	"+new_lineBaselinePath,1)

            f1 = open(os.path.join(self.dir,self.currentItem,"AutoMeta.meta"),"w")
            output = str(self.tmpLines[0]).replace("\n","") + "\n" + str(self.tmpLines[1]).replace("\n","") + "\n" + str(self.tmpLines[2]).replace("\n","") + "\n"
            output += str(self.tmpLines[3]).replace("\n","") + "\n" + str(self.tmpLines[4]).replace("\n","") + "\n" + str(self.tmpLines[5]).replace("\n","") + "\n"
            f1.write(output)
            f1.close()
            self.preview.setPlainText(output)

            f2 = open(os.path.join(self.dir,self.currentItem,"additionals.txt"),"w")
            output2 = new_lineTubeSlot +"\n"+new_comments
            f2.write(output2)
            f2.close()

            #Re Update list
            if self.dir:
                self.list0.clear()
                self.l0.setText(os.path.basename(self.dir))
                subfolders = [ f.name for f in os.scandir(self.dir) if f.is_dir() ]
                for sb in subfolders:
                    targetSR = os.path.join(self.dir,sb,"AutoMeta.meta")
                    fileSR = open(targetSR,'r')
                    linesSR = fileSR.readlines()
                    res1 = re.search('label(.*)desorb no.', linesSR[0])
                    a1 = str(str(res1.group(1)).strip()).replace("\n","")
                    res2 = re.search('desorb no.(.*)', linesSR[0])
                    a2 = str(str(res2.group(1)).strip()).replace("\n","")
                    boii = f"{sb}    "+a1+f" / Desorb {a2}"
                    self.list0.addItem(QtWidgets.QListWidgetItem(boii))
        
            #Show update success message
            self.alertme(title="Done",text="Updated Metadata successfully !")
    
    def alertme(self,title,text):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        x = msg.exec_()



app = QtWidgets.QApplication(sys.argv)
win = Ui()
app.exec_()