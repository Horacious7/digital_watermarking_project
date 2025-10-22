# verify_tab.py
from gui.qt_compat import QtWidgets, QtGui, QtCore
import os

class VerifyTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.input_path = None

        layout = QtWidgets.QVBoxLayout()

        # File selection
        file_row = QtWidgets.QHBoxLayout()
        self.btn_select = QtWidgets.QPushButton("Select Image to Verify")
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

        # Extract options
        opts_row = QtWidgets.QHBoxLayout()
        self.spin_block = QtWidgets.QSpinBox()
        self.spin_block.setRange(2, 64)
        self.spin_block.setValue(8)
        opts_row.addWidget(QtWidgets.QLabel("Block size:"))
        opts_row.addWidget(self.spin_block)

        self.btn_extract = QtWidgets.QPushButton("Extract & Verify")
        self.btn_extract.clicked.connect(self.extract_and_verify)
        opts_row.addWidget(self.btn_extract)
        layout.addLayout(opts_row)

        # Results
        self.le_message = QtWidgets.QLineEdit()
        self.le_message.setReadOnly(True)
        self.le_message.setPlaceholderText("Recovered message will appear here")
        layout.addWidget(self.le_message)

        self.lbl_valid = QtWidgets.QLabel("")
        layout.addWidget(self.lbl_valid)

        # Capacity hint
        self.lbl_capacity = QtWidgets.QLabel("")
        layout.addWidget(self.lbl_capacity)

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
        # update capacity hint for selected image
        try:
            from pathlib import Path
            import cv2, pywt
            img = cv2.imread(self.input_path, cv2.IMREAD_COLOR)
            if img is not None:
                blue = img[:, :, 0].astype('float32')
                coeffs2 = pywt.dwt2(blue, 'haar')
                cA, _ = coeffs2
                cA_h, cA_w = cA.shape
                block_size = int(self.spin_block.value())
                num_blocks = (cA_h // block_size) * (cA_w // block_size)
                self.lbl_capacity.setText(f"Capacity (bits) with block size {block_size}: {num_blocks}")
        except Exception:
            # ignore, capacity hint is optional
            pass

    def extract_and_verify(self):
        if not self.input_path:
            self.status.setText("Please select an image first.")
            return
        self.status.setText("Extracting...")
        QtWidgets.QApplication.processEvents()

        try:
            # Lazy imports
            from watermarking.extract import extract_watermark
            from utils.conversions import bits_to_bytes
            from crypto.verify import verify_signature
            import cv2, pywt, numpy as np
            from pathlib import Path

            # Determine capacity same as embed logic
            img = cv2.imread(self.input_path, cv2.IMREAD_COLOR)
            if img is None:
                raise FileNotFoundError(f"Image not found: {self.input_path}")
            blue = img[:, :, 0].astype(np.float32)
            coeffs2 = pywt.dwt2(blue, 'haar')
            cA, _ = coeffs2
            cA_h, cA_w = cA.shape
            block_size = int(self.spin_block.value())
            num_blocks = (cA_h // block_size) * (cA_w // block_size)

            # show capacity in UI
            self.lbl_capacity.setText(f"Capacity (bits) with block size {block_size}: {num_blocks}")

            if num_blocks < 32:
                raise ValueError("Not enough capacity to read header (need at least 32 bits). Try smaller block size or larger image.")

            # Try to read 64-bit header first (new format), else 32-bit header (old format)
            header_bits_len = 64 if num_blocks >= 64 else 32
            header_bits = extract_watermark(self.input_path, header_bits_len, block_size=block_size)
            header_bytes = bits_to_bytes(header_bits)
            sig_len = int.from_bytes(header_bytes[0:4], 'big') if len(header_bytes) >= 4 else 0
            has_msg_len = len(header_bytes) >= 8
            msg_len = int.from_bytes(header_bytes[4:8], 'big') if has_msg_len else None

            # Decide format
            use_new_format = False
            if has_msg_len:
                # Compute needed bits for new format
                needed_new = 32 + 32 + sig_len * 8 + (msg_len or 0) * 8
                # Heuristic: if needed_new fits capacity and msg_len isn't absurd, accept new format
                if needed_new <= num_blocks and msg_len is not None and msg_len < 50_000_000:
                    use_new_format = True
                else:
                    # Fallback to old format (header's 2nd dword likely belongs to signature)
                    use_new_format = False

            # Extract signature
            if use_new_format:
                offset = 64
                needed_sig_bits = sig_len * 8
                if offset + needed_sig_bits > num_blocks:
                    raise ValueError(f"Not enough capacity for signature (need {offset + needed_sig_bits}, have {num_blocks}).")
                sig_stream = extract_watermark(self.input_path, offset + needed_sig_bits, block_size=block_size)
                sig_bits = sig_stream[offset:offset + needed_sig_bits]
                sig_bytes = bits_to_bytes(sig_bits)
                # Extract message exactly msg_len bytes (if available)
                needed_msg_bits = (msg_len or 0) * 8
                if msg_len is not None:
                    if offset + needed_sig_bits + needed_msg_bits > num_blocks:
                        raise ValueError("Not enough capacity to read full message as per header. Try smaller block size or correct image.")
                    msg_stream = extract_watermark(self.input_path, offset + needed_sig_bits + needed_msg_bits, block_size=block_size)
                    msg_bits = msg_stream[offset + needed_sig_bits: offset + needed_sig_bits + needed_msg_bits]
                else:
                    # shouldn't happen with new format, but keep safe fallback
                    remaining = num_blocks - (offset + needed_sig_bits)
                    msg_stream = extract_watermark(self.input_path, offset + needed_sig_bits + remaining, block_size=block_size)
                    msg_bits = msg_stream[offset + needed_sig_bits:]
            else:
                # Old format: [sig_len][signature][message]
                offset = 32
                needed_sig_bits = sig_len * 8
                if offset + needed_sig_bits > num_blocks:
                    raise ValueError(f"Not enough capacity for signature (need {offset + needed_sig_bits}, have {num_blocks}).")
                sig_stream = extract_watermark(self.input_path, offset + needed_sig_bits, block_size=block_size)
                sig_bits = sig_stream[offset:offset + needed_sig_bits]
                sig_bytes = bits_to_bytes(sig_bits)
                remaining = num_blocks - (offset + needed_sig_bits)
                msg_stream = extract_watermark(self.input_path, offset + needed_sig_bits + remaining, block_size=block_size)
                msg_bits = msg_stream[offset + needed_sig_bits:]

            message = bits_to_bytes(msg_bits)

            try:
                msg_text = message.decode('utf-8')
            except Exception:
                msg_text = message.decode('utf-8', errors='replace')

            self.le_message.setText(msg_text)

            # resolve public key path relative to project root
            project_root = Path(__file__).resolve().parent.parent
            candidate_pub = [project_root / 'data' / 'keys' / 'public.pem', project_root / 'keys' / 'public.pem']
            public_key_path = None
            for p in candidate_pub:
                if p.exists():
                    public_key_path = p
                    break
            if public_key_path is None:
                raise FileNotFoundError(f"Public key not found. Tried: {candidate_pub}")

            is_valid = verify_signature(str(public_key_path), message, sig_bytes)
            self.lbl_valid.setText("Signature valid ✅" if is_valid else "Signature INVALID ❌")
            self.status.setText("Done")
        except Exception as e:
            self.status.setText(f"Error: {e}")
            import traceback
            traceback.print_exc()
