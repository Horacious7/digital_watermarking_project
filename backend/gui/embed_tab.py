# embed_tab.py
from backend.gui.qt_compat import QtWidgets, QtGui, QtCore
import os

class EmbedTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.input_path = None
        self.output_path = None

        layout = QtWidgets.QVBoxLayout()

        # File selection
        file_row = QtWidgets.QHBoxLayout()
        self.btn_select = QtWidgets.QPushButton("Select Input Image")
        self.btn_select.clicked.connect(self.select_image)
        file_row.addWidget(self.btn_select)

        self.le_input = QtWidgets.QLineEdit()
        self.le_input.setReadOnly(True)
        file_row.addWidget(self.le_input)

        layout.addLayout(file_row)

        # Preview
        self.preview = QtWidgets.QLabel("No image selected")
        self.preview.setAlignment(QtCore.Qt.AlignCenter)
        self.preview.setFixedHeight(240)
        layout.addWidget(self.preview)

        # Message input
        self.msg_edit = QtWidgets.QLineEdit()
        self.msg_edit.setPlaceholderText("Enter message to embed (text)")
        layout.addWidget(self.msg_edit)

        # Embed options and button
        opts_row = QtWidgets.QHBoxLayout()
        self.spin_block = QtWidgets.QSpinBox()
        self.spin_block.setRange(2, 64)
        self.spin_block.setValue(8)
        opts_row.addWidget(QtWidgets.QLabel("Block size:"))
        opts_row.addWidget(self.spin_block)

        # Auto-fit block size button
        self.btn_auto = QtWidgets.QPushButton("Auto")
        self.btn_auto.setToolTip("Automatically choose the smallest block size that fits the payload")
        self.btn_auto.clicked.connect(self.auto_choose_block_size)
        opts_row.addWidget(self.btn_auto)

        self.btn_embed = QtWidgets.QPushButton("Embed and Save")
        self.btn_embed.clicked.connect(self.embed)
        opts_row.addWidget(self.btn_embed)

        layout.addLayout(opts_row)

        # Status
        self.status = QtWidgets.QLabel("")
        layout.addWidget(self.status)

        self.setLayout(layout)

    def select_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select image", os.getcwd(), "Images (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        self.input_path = path
        self.le_input.setText(path)
        pix = QtGui.QPixmap(path)
        if not pix.isNull():
            self.preview.setPixmap(pix.scaled(self.preview.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        else:
            self.preview.setText("Could not load preview")

    def embed(self):
        # Do a best-effort embed using existing project functions; show friendly errors
        if not self.input_path:
            self.status.setText("Please select an input image first.")
            return
        text = self.msg_edit.text() or ""
        # Ask for output file
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save watermarked image", os.path.join(os.getcwd(), "watermarked", "out.png"), "PNG Files (*.png);;All Files (*)")
        if not out_path:
            self.status.setText("Embed cancelled.")
            return
        self.output_path = out_path
        self.status.setText("Embedding... this may take a few seconds")
        QtWidgets.QApplication.processEvents()

        try:
            # Lazy imports to avoid heavy imports at module load
            from backend.crypto.sign import sign_hash
            from backend.utils.conversions import bytes_to_bits
            from backend.watermarking.embed import embed_watermark
            from pathlib import Path
            import cv2, pywt, numpy as np

            # resolve private key path relative to project root (try both data/keys and keys)
            project_root = Path(__file__).resolve().parent.parent
            candidate_paths = [project_root / 'data' / 'keys' / 'private.pem', project_root / 'keys' / 'private.pem']
            private_key_path = None
            for p in candidate_paths:
                if p.exists():
                    private_key_path = p
                    break
            if private_key_path is None:
                raise FileNotFoundError(f"Private key not found. Tried: {candidate_paths}")

            message_bytes = text.encode('utf-8')
            signature = sign_hash(str(private_key_path), message_bytes)
            sig_len_bytes = len(signature).to_bytes(4, 'big')
            msg_len_bytes = len(message_bytes).to_bytes(4, 'big')
            # New, robust payload format: [4B sig_len][4B msg_len][signature][message]
            payload = sig_len_bytes + msg_len_bytes + signature + message_bytes
            payload_bits = bytes_to_bits(payload)

            # Check capacity before embedding (same logic as embedding code)
            img = cv2.imread(self.input_path, cv2.IMREAD_COLOR)
            if img is None:
                raise FileNotFoundError(f"Input image not found or cannot be read: {self.input_path}")
            blue = img[:, :, 0].astype(np.float32)
            coeffs2 = pywt.dwt2(blue, 'haar')
            cA, _ = coeffs2
            cA_h, cA_w = cA.shape
            block_size = int(self.spin_block.value())
            num_blocks = (cA_h // block_size) * (cA_w // block_size)
            if len(payload_bits) > num_blocks:
                raise ValueError(f"Payload too large for selected block size. Payload bits={len(payload_bits)}, available blocks={num_blocks}. Try a smaller block size or a larger image.")

            embed_watermark(self.input_path, payload_bits, self.output_path, block_size=self.spin_block.value())
            self.status.setText(f"Embed completed: {self.output_path}")
        except Exception as e:
            self.status.setText(f"Error: {e}")
            import traceback
            traceback.print_exc()

    def auto_choose_block_size(self, checked=False):
        """Pick the smallest block size (>=2) that fits current payload (signature+message).
        The clicked signal passes a bool we ignore via 'checked'.
        """
        try:
            from pathlib import Path
            import cv2, pywt
            if not self.input_path:
                self.status.setText("Select an input image first to auto-compute block size.")
                return

            # compute payload bits from current message
            text = self.msg_edit.text() or ""
            from backend.utils.conversions import bytes_to_bits
            from backend.crypto.sign import sign_hash
            project_root = Path(__file__).resolve().parent.parent
            # find private key for signature
            candidate_paths = [project_root / 'data' / 'keys' / 'private.pem', project_root / 'keys' / 'private.pem']
            priv = None
            for p in candidate_paths:
                if p.exists():
                    priv = p
                    break
            if priv is None:
                self.status.setText("Private key not found for auto block selection; please place private.pem in data/keys or keys.")
                return
            message_bytes = text.encode('utf-8')
            signature = sign_hash(str(priv), message_bytes)
            payload = len(signature).to_bytes(4, 'big') + len(message_bytes).to_bytes(4, 'big') + signature + message_bytes
            payload_bits = bytes_to_bits(payload)

            img = cv2.imread(self.input_path, cv2.IMREAD_COLOR)
            if img is None:
                self.status.setText("Cannot read selected image for capacity check.")
                return
            blue = img[:, :, 0].astype('float32')
            cA, _ = pywt.dwt2(blue, 'haar')
            cA_h, cA_w = cA.shape

            for b in range(2, 65):
                num_blocks = (cA_h // b) * (cA_w // b)
                if num_blocks >= len(payload_bits):
                    self.spin_block.setValue(b)
                    self.status.setText(f"Auto chose block size {b} (capacity {num_blocks}).")
                    return
            self.status.setText("No block size in range 2..64 can fit the payload. Use a larger image or shorter message.")
        except Exception as e:
            self.status.setText(f"Auto error: {e}")
            import traceback
            traceback.print_exc()
