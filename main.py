from ui import *

if __name__ == "__main__":
    app = QApplication(sys.argv)

    mainWin = MainUIWindow()
    mainWin.show()

    sys.exit(app.exec_())