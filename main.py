import os
import sys

from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import PdfReadError
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QPdfWriter, QPainter, QFont, QPageSize, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QWidget, QMessageBox, QListWidget, QListWidgetItem,
    QMenu, QLineEdit, QDialog, QCheckBox,
    QDialogButtonBox
)

COLORS = {
    "background": "#0a0a0a",
    "surface": "#111111",
    "primary": "#0070f3",
    "secondary": "#444444",
    "text": "#ffffff",
    "text-secondary": "#888888",
    "border": "#333333",
    "hover": "#1a1a1a",
}

STYLESHEET = f"""
    QWidget {{
        background-color: {COLORS['background']};
        color: {COLORS['text']};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell;
        font-size: 14px;
    }}

    QPushButton {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 10px 20px;
        min-width: 100px;
    }}

    QPushButton:hover {{
        background-color: {COLORS['hover']};
        border-color: {COLORS['primary']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['primary']};
        color: white;
    }}

    QListWidget {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px;
    }}

    QListWidget::item {{
        background-color: {COLORS['surface']};
        border-radius: 4px;
        padding: 8px;
    }}

    QListWidget::item:hover {{
        background-color: {COLORS['hover']};
    }}

    QCheckBox {{
        spacing: 8px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
    }}

    QCheckBox::indicator:checked {{
        background-color: {COLORS['primary']};
        border-color: {COLORS['primary']};
    }}

    QLineEdit {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 10px;
    }}

    QScrollBar:vertical {{
        background: {COLORS['surface']};
        width: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {COLORS['secondary']};
        min-height: 20px;
        border-radius: 4px;
    }}
"""


def create_placeholder_pdf(output_path):
    pdf_writer = QPdfWriter(output_path)
    pdf_writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    painter = QPainter()
    painter.begin(pdf_writer)
    painter.setFont(QFont("Arial", 12))
    painter.setPen(QColor(COLORS['text']))
    rect = QRectF(50, 50, 500, 100)
    painter.drawText(rect, Qt.AlignmentFlag.AlignLeft,
                     "This PDF was encrypted and couldn't be decrypted due to missing or incorrect password.")
    painter.end()


class PasswordDialog(QDialog):
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Password Required - {filename}")
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QLabel {{
                color: {COLORS['text']};
                font-size: 14px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(f"🔒 Password required for:")
        title.setStyleSheet(f"font-weight: 600; color: {COLORS['primary']};")
        layout.addWidget(title)

        filename_label = QLabel(filename)
        filename_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text-secondary']};")
        layout.addWidget(filename_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password...")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 12px;
                margin-top: 20px;
            }}
        """)
        layout.addWidget(self.password_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_password(self):
        return self.password_input.text()


class PDFDropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['surface']};
                border: 2px dashed {COLORS['border']};
                border-radius: 12px;
                color: {COLORS['text-secondary']};
                font-size: 16px;
                min-height: 200px;
                min-width: 200px;
            }}
            QLabel:hover {{
                border-color: {COLORS['primary']};
                background-color: {COLORS['hover']};
            }}
        """)
        self.setText("\n\n📁 Drag PDF files here\nor click to select\n")
        self.set_scaled_pixmap("resources\down_arrow_icon.png", 80, 80)

    def set_scaled_pixmap(self, image_path, width, height):
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(
                width, height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
        else:
            self.setText("")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile() and url.toLocalFile().lower().endswith('.pdf'):
                self.parent_window.handle_pdf_file(url.toLocalFile())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select PDF Files", "",
                "PDF Files (*.pdf);;All Files (*)"
            )
            for file_path in files:
                self.parent_window.handle_pdf_file(file_path)
        super().mousePressEvent(event)


class PDFDecryptor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Decryptor")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet(STYLESHEET)

        if os.path.exists("resources/app_icon.png"):
            self.setWindowIcon(QIcon("resources/app_icon.png"))

        self.file_paths = []
        self.passwords = {}

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QLabel("PDF Decryptor")
        header.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 600;
            color: {COLORS['primary']};
            padding: 10px 0;
        """)
        layout.addWidget(header)

        # Drop zone
        self.drop_zone = PDFDropLabel(self)
        self.drop_zone.setFixedHeight(200)
        layout.addWidget(self.drop_zone)

        # File list
        self.file_list = QListWidget()
        self.file_list.setFixedHeight(250)
        self.file_list.setStyleSheet("""
            QListWidget {
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item {
                border-bottom: 1px solid #333333;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """)
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.file_list)

        # Options
        self.overwrite_checkbox = QCheckBox("Overwrite existing files")
        self.overwrite_checkbox.setStyleSheet(f"color: {COLORS['text-secondary']};")
        layout.addWidget(self.overwrite_checkbox)

        # Process button
        self.process_btn = QPushButton("Process PDFs")
        self.process_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                font-weight: 600;
                border: none;
                padding: 14px 28px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #0061d1;
            }}
        """)
        self.process_btn.setFixedHeight(50)
        self.process_btn.clicked.connect(self.process_files)
        layout.addWidget(self.process_btn)

    def handle_pdf_file(self, file_path):
        if file_path in self.file_paths:
            return

        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                encrypted = reader.is_encrypted

                if encrypted:
                    if reader.decrypt("") > 0:
                        try:
                            _ = len(reader.pages)
                            self.add_valid_file(file_path)
                            return
                        except Exception:
                            pass
                    self.handle_encrypted_file(file_path)
                else:
                    self.add_valid_file(file_path)

        except PdfReadError as e:
            if "not been decrypted" in str(e):
                self.handle_encrypted_file(file_path)
            else:
                self.show_error(f"Error reading {os.path.basename(file_path)}:\n{str(e)}")
        except Exception as e:
            self.show_error(f"Failed to process {os.path.basename(file_path)}:\n{str(e)}")

    def handle_encrypted_file(self, file_path):
        dialog = PasswordDialog(os.path.basename(file_path), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            password = dialog.get_password()
            try:
                with open(file_path, 'rb') as f:
                    reader = PdfReader(f)
                    if reader.decrypt(password) > 0:
                        _ = len(reader.pages)
                        self.add_valid_file(file_path)
                        self.passwords[file_path] = password
                    else:
                        self.show_error("Incorrect password for\n" + os.path.basename(file_path))
            except Exception as e:
                self.show_error(f"Decryption failed for {os.path.basename(file_path)}:\n{str(e)}")

    def add_valid_file(self, file_path):
        self.file_paths.append(file_path)
        self.file_list.addItem(QListWidgetItem(file_path))
        self.update_drop_zone_text()

    def update_drop_zone_text(self):
        count = len(self.file_paths)
        self.drop_zone.setText(
            f"{count} PDF file{'s' if count != 1 else ''} ready\n"
            f"Drag more or click to add" if count > 0 else
            "\nDrag PDF files here\nor click to select\n"
        )

    def show_context_menu(self, position):
        menu = QMenu()
        remove_action = menu.addAction("Remove selected")
        clear_action = menu.addAction("Clear all")

        action = menu.exec(self.file_list.mapToGlobal(position))
        if action == remove_action:
            self.remove_selected_files()
        elif action == clear_action:
            self.clear_all_files()

    def remove_selected_files(self):
        for item in self.file_list.selectedItems():
            file_path = item.text()
            self.file_paths.remove(file_path)
            if file_path in self.passwords:
                del self.passwords[file_path]
            self.file_list.takeItem(self.file_list.row(item))
        self.update_drop_zone_text()

    def clear_all_files(self):
        reply = QMessageBox.question(
            self, "Confirm Clear", "Remove all files from list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.file_paths.clear()
            self.passwords.clear()
            self.file_list.clear()
            self.update_drop_zone_text()

    def process_files(self):
        if not self.file_paths:
            self.show_warning("No files to process")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return

        results = {'success': [], 'placeholder': [], 'error': []}

        for input_path in self.file_paths:
            try:
                output_path = os.path.join(output_dir, "decrypted_" + os.path.basename(input_path))

                if os.path.exists(output_path) and not self.overwrite_checkbox.isChecked():
                    results['error'].append((input_path, "File exists"))
                    continue

                with open(input_path, 'rb') as f:
                    reader = PdfReader(f)

                    if reader.is_encrypted:
                        decrypted = False
                        password = self.passwords.get(input_path, None)

                        # Try stored password first
                        if password is not None:
                            if reader.decrypt(password) > 0:
                                decrypted = True

                        # Try empty password if not decrypted
                        if not decrypted:
                            if reader.decrypt("") > 0:
                                decrypted = True

                        if not decrypted:
                            create_placeholder_pdf(output_path)
                            results['placeholder'].append(input_path)
                            continue

                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)

                    with open(output_path, 'wb') as out_file:
                        writer.write(out_file)

                    results['success'].append(input_path)

            except Exception as e:
                results['error'].append((input_path, str(e)))

        self.show_results(results)

    def show_results(self, results):
        summary = []
        if results['success']:
            summary.append(f"Successfully processed: {len(results['success'])}")
        if results['placeholder']:
            summary.append(f"Created placeholders: {len(results['placeholder'])}")
        if results['error']:
            summary.append(f"Errors encountered: {len(results['error'])}")

        details = []
        for category in ['success', 'placeholder', 'error']:
            if results[category]:
                details.append("\n" + category.capitalize() + ":")
                details.extend([
                    f"• {os.path.basename(f)}" if category != 'error' else f"• {os.path.basename(f[0])}: {f[1]}"
                    for f in results[category]
                ])

        msg = QMessageBox(self)
        msg.setWindowTitle("Processing Results")
        msg.setText("\n".join(summary))
        msg.setDetailedText("\n".join(details))
        msg.exec()

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_warning(self, message):
        QMessageBox.warning(self, "Warning", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PDFDecryptor()
    window.show()
    sys.exit(app.exec())
