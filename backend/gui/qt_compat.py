# Small compatibility shim: prefer PySide6, fall back to PyQt5
try:
    from PySide6 import QtWidgets, QtCore, QtGui
    QT_BACKEND = "PySide6"
except Exception:
    try:
        from PyQt5 import QtWidgets, QtCore, QtGui
        QT_BACKEND = "PyQt5"
    except Exception as e:
        raise ImportError("Neither PySide6 nor PyQt5 is available. Install one of them.") from e

