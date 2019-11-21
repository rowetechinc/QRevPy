from PyQt5 import QtWidgets, QtCore
from UI import wSOSSource


class SOSSource(QtWidgets.QDialog, wSOSSource.Ui_sos_source):
    """Dialog to allow users to change speed of sound source.

    Parameters
    ----------
    wSOSSource.Ui_sos_source : QDialog
        Dialog window to allow users to change speed of sound
    """

    def __init__(self, units, setting='internal', sos=None, parent=None):
        super(SOSSource, self).__init__(parent)
        self.setupUi(self)
        self.rb_user.setText('User ' + units['label_V'])
        if setting == 'internal':
            self.ed_sos_user.setEnabled(False)
            self.rb_internal.setChecked(True)
        else:
            self.rb_user.setChecked(True)
            self.ed_sos_user.setText('{:6.1f}'.format(sos * units['V']))
        self.rb_user.toggled.connect(self.user)
        self.rb_internal.toggled.connect(self.internal)
        # self.ed_sos_user.editingFinished.connect(self.user_entered)

    @QtCore.pyqtSlot()
    def user(self):
        if self.rb_user.isChecked():
            self.ed_sos_user.setEnabled(True)

    @QtCore.pyqtSlot()
    def internal(self):
        if self.rb_internal.isChecked():
            self.ed_sos_user.setEnabled(False)


