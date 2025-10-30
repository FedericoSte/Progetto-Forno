import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QProgressBar, QMessageBox, QInputDialog, QLineEdit
from PyQt5.QtCore import QThread, pyqtSignal
import paramiko

class SimpleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commercity:")
        self.resize(400, 300)

        self.layout = QVBoxLayout()

        # Campo di testo per visualizzare il risultato
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)  # Non modificabile dall'utente
        self.layout.addWidget(self.text_area)

        # Barra di caricamento (senza percentuale)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Imposta la barra come caricamento infinito
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)  # Inizialmente non visibile
        self.layout.addWidget(self.progress_bar)

        # Bottone per avviare il ricevimento dei dati
        self.start_button = QPushButton("Ricevi Dati", self)
        self.start_button.clicked.connect(self.ricevi_dati)
        self.layout.addWidget(self.start_button)

        self.setLayout(self.layout)

        self.task_thread = None

    def ricevi_dati(self):
        """Inizia la ricezione dei dati"""
        self.text_area.clear()  # Svuota il campo di testo

        # Disabilita il bottone mentre il task è in esecuzione
        self.start_button.setEnabled(False)

        
        # Chiedi la password all'utente tramite un QInputDialog
        password, ok = QInputDialog.getText(self, "Inserisci la Password", "Password SSH:", echo=QLineEdit.Password)
        


        if not ok:
            QMessageBox.warning(self, "Operazione Annullata", "Connessione SSH annullata.")
            self.start_button.setEnabled(True)
            return

        # Mostra la barra di caricamento infinita
        self.progress_bar.setVisible(True)

        # Crea e avvia il thread che eseguirà il lungo script
        self.task_thread = RiceviDatiThread(password)  # Passa la password al thread
        self.task_thread.progress_updated.connect(self.update_progress)
        self.task_thread.task_finished.connect(self.task_finished)
        self.task_thread.task_error.connect(self.show_error_message)  # Gestione degli errori
        self.task_thread.start()

    def update_progress(self, progress):
        """Aggiorna la barra di progresso (ma non usato in caso di barra infinita)"""
        pass

    def task_finished(self, message):
        """Gestisce la fine del task e aggiorna l'interfaccia"""
        self.text_area.append(message)  # Visualizza il messaggio nel campo di testo
        self.start_button.setEnabled(True)  # Rende di nuovo cliccabile il pulsante
        self.progress_bar.setVisible(False)  # Nasconde la barra di caricamento dopo il completamento

    def show_error_message(self, error_message):
        """Mostra un messaggio di errore in una nuova finestra di dialogo"""
        QMessageBox.critical(self, "Errore", error_message)  # Mostra l'errore in una finestra di dialogo
        self.start_button.setEnabled(True)  # Riabilita il pulsante dopo la chiusura dell'errore
        self.progress_bar.setVisible(False)  # Nasconde la barra di caricamento in caso di errore

class RiceviDatiThread(QThread):
    # Segnala l'aggiornamento del progresso
    progress_updated = pyqtSignal(int)
    # Segnala la fine dell'esecuzione
    task_finished = pyqtSignal(str)
    # Segnala un errore
    task_error = pyqtSignal(str)

    def __init__(self, password):
        super().__init__()
        self.password = password

    def run(self):
        comu = SSHClientApp("100.67.170.50", "22", "costantino", self.password)
        if comu.connect():
            out = comu.execute_command()
            time, temp, hum = out.split("^")

            print(f"h:{time}\nt:{temp}\nh:{hum}")
            comu.close()

            # Una volta terminato, invia il risultato
            self.task_finished.emit(f"Da Commercity:\n\n- Orario:\t\t{time}\n- Temperatura:\t{temp} C°\n- Umidità:\t\t{hum}%")
        else:
            self.task_error.emit("Errore durante la connessione SSH!")  # Invia il messaggio di errore

class SSHClientApp:
    def __init__(self, hostname, port, username, password):
        # Parametri di connessione SSH
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.command = '/home/costantino/venv/bin/python3 /home/costantino/Desktop/V2/mainApp.py'
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        """Stabilisce la connessione SSH al Raspberry Pi."""
        try:
            self.client.connect(self.hostname, port=self.port, username=self.username, password=self.password)
            print(f"Connessione SSH riuscita a {self.hostname}")
        except Exception as e:
            print(f"Errore durante la connessione SSH: {e}")
            return False
        return True

    def execute_command(self):
        """Esegue il comando remoto e restituisce l'output."""
        try:
            stdin, stdout, stderr = self.client.exec_command(self.command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            if error:
                print(f"Errore nel comando: {error}")
            return output[0:-1]
        except Exception as e:
            print(f"Errore durante l'esecuzione del comando: {e}")
            return None

    def close(self):
        """Chiude la connessione SSH."""
        self.client.close()
        print("Connessione SSH chiusa.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleApp()
    window.show()
    sys.exit(app.exec_())
