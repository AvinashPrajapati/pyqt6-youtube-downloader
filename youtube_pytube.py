import sys
import os
import threading
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QProgressBar,
    QComboBox,
    QCheckBox,
)

# import youtube_dl
from slugify import slugify
from pytube import YouTube


class DownloaderThread(QObject, threading.Thread):
    progress_updated = pyqtSignal(int)
    video_downloaded = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, url, quality, download_audio):
        super().__init__()
        self.url = url
        self.quality = quality
        self.download_audio = download_audio
        self.is_canceled = False

    def run(self):
        try:
            # yt = YouTube(
            #     self.url,
            #     on_progress_callback=self.progress_callback,
            # )
            # print(yt)
            # strm = yt.streams
            if self.download_audio:
                yt = (
                    YouTube(
                        self.url,
                        on_progress_callback=self.progress_callback,
                    )
                    .streams.filter(progressive=True, only_audio=True)
                    .first()
                    .download()
                )

            else:
                yt = (
                    (
                        YouTube(
                            self.url,
                            on_progress_callback=self.progress_callback,
                        ).streams.filter(progressive=True, file_extension="mp4")
                    )
                    .order_by("resolution")
                    .desc()
                    .first()
                )
                # print(yt)
                filenm = f"{slugify(yt.title)}.mp4"
                yt.download(filename=filenm)

            if not self.is_canceled:
                self.video_downloaded.emit(filenm)
        except Exception as e:
            print("Error:", str(e))

    def progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = int((bytes_downloaded / total_size) * 100)
        print(percentage)
        self.progress_updated.emit(percentage)

    def cancel(self):
        self.is_canceled = True


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Video Downloader")
        self.setGeometry(100, 100, 500, 250)

        # Create a layout and set it as central
        self.layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        # Create labels, input field, and buttons
        self.label = QLabel("Enter YouTube video URL:")
        self.layout.addWidget(self.label)

        self.url_input = QLineEdit()
        self.layout.addWidget(self.url_input)

        self.quality_label = QLabel("Select quality:")
        self.layout.addWidget(self.quality_label)

        self.quality_combobox = QComboBox()
        self.quality_combobox.addItem("Low")
        self.quality_combobox.addItem("Medium")
        self.quality_combobox.addItem("High")
        self.layout.addWidget(self.quality_combobox)

        self.audio_checkbox = QCheckBox("Download audio only")
        self.layout.addWidget(self.audio_checkbox)

        self.download_button = QPushButton("Download")
        self.layout.addWidget(self.download_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.layout.addWidget(self.cancel_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.layout.addWidget(self.progress_bar)

        self.video_label = QLabel()
        self.layout.addWidget(self.video_label)

        # Connect the button signals to the respective functions
        self.download_button.clicked.connect(self.start_download)
        self.cancel_button.clicked.connect(self.cancel_download)

        # Initialize the downloader thread
        self.downloader_thread = None

    def start_download(self):
        # Get the entered URL, quality, and download_audio flag
        url = self.url_input.text()
        quality = self.quality_combobox.currentText()
        download_audio = self.audio_checkbox.isChecked()

        # Disable input fields and buttons while downloading
        self.url_input.setEnabled(False)
        self.quality_combobox.setEnabled(False)
        self.audio_checkbox.setEnabled(False)
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        # Clear previous video label and reset progress bar
        self.video_label.setText("")
        self.progress_bar.setValue(0)

        # Create and start the downloader thread
        self.downloader_thread = DownloaderThread(url, quality, download_audio)
        self.downloader_thread.progress_updated.connect(self.update_progress)
        self.downloader_thread.video_downloaded.connect(self.video_downloaded)
        self.downloader_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def video_downloaded(self, filename):
        # Enable input fields and buttons after downloading
        self.url_input.setEnabled(True)
        self.quality_combobox.setEnabled(True)
        self.audio_checkbox.setEnabled(True)
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.video_label.setText(f"Video downloaded: {filename}")

    def cancel_download(self):
        if self.downloader_thread:
            self.downloader_thread.cancel()
            self.downloader_thread = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
