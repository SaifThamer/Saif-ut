# -*- coding: utf-8 -*-
"""
برنامج أرشفة الكتب الرسمية
تصميم احترافي - PyQt5 - قاعدة بيانات SQLite محلية
"""

import sys
import os
from datetime import datetime

from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QStackedWidget, QFrame, QGridLayout, QAbstractItemView,
    QDialog, QDialogButtonBox, QSizePolicy
)

from database import Database, get_db_path
from styles import APP_STYLESHEET
import config as app_config
import ai_extract

SENDER_TYPES = ["وزارة", "هيئة", "مديرية", "قسم", "شعبة", "وحدة"]
AI_MODELS = [
    ("claude-haiku-4-5-20251001", "سريع واقتصادي (Haiku)"),
    ("claude-sonnet-5", "متوازن - موصى به (Sonnet)"),
    ("claude-opus-5", "أعلى دقة (Opus)"),
]


# ==========================================================
#   خيط منفصل لاستخراج البيانات (حتى لا تتجمد الواجهة)
# ==========================================================
class ExtractWorker(QThread):
    finished_ok = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, api_key, file_path, model):
        super().__init__()
        self.api_key = api_key
        self.file_path = file_path
        self.model = model

    def run(self):
        try:
            data = ai_extract.extract_letter_data(self.api_key, self.file_path, self.model)
            self.finished_ok.emit(data)
        except ai_extract.ExtractionError as e:
            self.failed.emit(str(e))
        except Exception as e:
            self.failed.emit(f"خطأ غير متوقع: {e}")


# ==========================================================
#   نافذة مراجعة وتأكيد الحفظ
# ==========================================================
class ConfirmSaveDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مراجعة بيانات الكتاب قبل الحفظ")
        self.setMinimumWidth(420)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("يرجى مراجعة البيانات التالية قبل التأكيد")
        title.setObjectName("PageSubtitle")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QGridLayout(card)
        card_layout.setSpacing(8)

        fields = [
            ("رقم الكتاب", data["letter_number"]),
            ("نوع الجهة المرسلة", data["sender_type"]),
            ("اسم الجهة المرسلة", data["sender_name"]),
            ("تاريخ الكتاب", data["letter_date"]),
            ("عنوان / موضوع الكتاب", data["subject"]),
            ("الملاحظات", data["notes"] or "-"),
        ]

        for i, (label, value) in enumerate(fields):
            l = QLabel(label + ":")
            l.setStyleSheet("font-weight:bold; color:#16233D;")
            v = QLabel(value if value else "-")
            v.setWordWrap(True)
            card_layout.addWidget(l, i, 1)
            card_layout.addWidget(v, i, 0)

        layout.addWidget(card)

        btn_box = QDialogButtonBox()
        self.confirm_btn = QPushButton("تأكيد الحفظ")
        self.confirm_btn.setObjectName("GoldBtn")
        self.edit_btn = QPushButton("رجوع للتعديل")
        self.edit_btn.setObjectName("SecondaryBtn")
        btn_box.addButton(self.confirm_btn, QDialogButtonBox.AcceptRole)
        btn_box.addButton(self.edit_btn, QDialogButtonBox.RejectRole)
        self.confirm_btn.clicked.connect(self.accept)
        self.edit_btn.clicked.connect(self.reject)
        layout.addWidget(btn_box)


# ==========================================================
#   صفحة إضافة / تعديل كتاب
# ==========================================================
class AddLetterPage(QWidget):
    def __init__(self, db: Database, on_saved=None):
        super().__init__()
        self.db = db
        self.on_saved = on_saved
        self.editing_id = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(6)

        self.title_label = QLabel("إضافة كتاب جديد")
        self.title_label.setObjectName("PageTitle")
        layout.addWidget(self.title_label)

        subtitle = QLabel("أدخل تفاصيل الكتاب يدويًا، أو استخرجها تلقائيًا من صورة / PDF ثم راجعها قبل الحفظ")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        # بطاقة الاستخراج بالذكاء الاصطناعي
        ai_card = QFrame()
        ai_card.setObjectName("Card")
        ai_row = QHBoxLayout(ai_card)
        ai_row.setContentsMargins(20, 14, 20, 14)
        ai_info = QLabel("📄 استخراج تلقائي: ارفع صورة أو PDF للكتاب وسيقرأ الذكاء الاصطناعي بياناته ويملأ الحقول")
        ai_info.setWordWrap(True)
        ai_row.addWidget(ai_info, 1)
        self.extract_btn = QPushButton("اختيار ملف واستخراج البيانات")
        self.extract_btn.setObjectName("GoldBtn")
        self.extract_btn.clicked.connect(self.import_from_file)
        ai_row.addWidget(self.extract_btn)
        layout.addWidget(ai_card)

        card = QFrame()
        card.setObjectName("Card")
        form = QGridLayout(card)
        form.setContentsMargins(24, 24, 24, 24)
        form.setSpacing(12)

        def field_label(text):
            l = QLabel(text)
            l.setProperty("role", "field")
            return l

        # رقم الكتاب
        form.addWidget(field_label("رقم الكتاب"), 0, 1)
        self.letter_number_edit = QLineEdit()
        self.letter_number_edit.setPlaceholderText("مثال: 1234")
        form.addWidget(self.letter_number_edit, 0, 0)

        # تاريخ الكتاب
        form.addWidget(field_label("تاريخ الكتاب"), 0, 3)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        form.addWidget(self.date_edit, 0, 2)

        # نوع الجهة
        form.addWidget(field_label("نوع الجهة المرسلة"), 1, 1)
        self.sender_type_combo = QComboBox()
        self.sender_type_combo.addItems(SENDER_TYPES)
        self.sender_type_combo.setEditable(True)
        form.addWidget(self.sender_type_combo, 1, 0)

        # اسم الجهة
        form.addWidget(field_label("اسم الجهة المرسلة"), 1, 3)
        self.sender_name_edit = QLineEdit()
        self.sender_name_edit.setPlaceholderText("مثال: مديرية التخطيط")
        form.addWidget(self.sender_name_edit, 1, 2)

        # الموضوع
        form.addWidget(field_label("عنوان / موضوع الكتاب"), 2, 1, 1, 3)
        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText("موضوع الكتاب بإيجاز")
        form.addWidget(self.subject_edit, 3, 0, 1, 4)

        # الملاحظات
        form.addWidget(field_label("الملاحظات"), 4, 1, 1, 3)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("أي ملاحظات إضافية (اختياري)")
        self.notes_edit.setFixedHeight(90)
        form.addWidget(self.notes_edit, 5, 0, 1, 4)

        layout.addWidget(card)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.clear_btn = QPushButton("تفريغ الحقول")
        self.clear_btn.setObjectName("SecondaryBtn")
        self.clear_btn.clicked.connect(self.clear_form)
        self.save_btn = QPushButton("مراجعة وحفظ")
        self.save_btn.setObjectName("GoldBtn")
        self.save_btn.clicked.connect(self.review_and_save)
        btn_row.addWidget(self.clear_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

    def clear_form(self):
        self.editing_id = None
        self.title_label.setText("إضافة كتاب جديد")
        self.save_btn.setText("مراجعة وحفظ")
        self.letter_number_edit.clear()
        self.sender_type_combo.setCurrentIndex(0)
        self.sender_name_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.subject_edit.clear()
        self.notes_edit.clear()

    def import_from_file(self):
        cfg = app_config.load_config()
        api_key = cfg.get("api_key", "").strip()
        if not api_key:
            QMessageBox.warning(
                self, "مفتاح API مطلوب",
                "الرجاء إدخال مفتاح Anthropic API أولاً من صفحة (الإعدادات) قبل استخدام الاستخراج التلقائي."
            )
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "اختر صورة أو ملف PDF للكتاب", "",
            "ملفات مدعومة (*.pdf *.png *.jpg *.jpeg *.webp)"
        )
        if not path:
            return

        model = cfg.get("model", "claude-sonnet-5")
        self.extract_btn.setEnabled(False)
        self.extract_btn.setText("جارٍ الاستخراج... الرجاء الانتظار")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self._worker = ExtractWorker(api_key, path, model)
        self._worker.finished_ok.connect(self._on_extract_success)
        self._worker.failed.connect(self._on_extract_failed)
        self._worker.start()

    def _reset_extract_btn(self):
        QApplication.restoreOverrideCursor()
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("اختيار ملف واستخراج البيانات")

    def _on_extract_success(self, data):
        self._reset_extract_btn()

        self.letter_number_edit.setText(data.get("letter_number", "") or "")

        stype = (data.get("sender_type", "") or "").strip()
        idx = self.sender_type_combo.findText(stype)
        if idx >= 0:
            self.sender_type_combo.setCurrentIndex(idx)
        elif stype:
            self.sender_type_combo.setEditText(stype)

        self.sender_name_edit.setText(data.get("sender_name", "") or "")

        date_str = (data.get("letter_date", "") or "").strip()
        qd = QDate.fromString(date_str, "yyyy-MM-dd")
        if qd.isValid():
            self.date_edit.setDate(qd)

        self.subject_edit.setText(data.get("subject", "") or "")
        self.notes_edit.setPlainText(data.get("notes", "") or "")

        QMessageBox.information(
            self, "تم الاستخراج",
            "تم استخراج البيانات من الملف. راجع كل حقل جيدًا وتأكد من صحته قبل الضغط على (مراجعة وحفظ)."
        )

    def _on_extract_failed(self, error_msg):
        self._reset_extract_btn()
        QMessageBox.critical(self, "تعذر الاستخراج", error_msg)

    def load_for_edit(self, row):
        self.editing_id = row["id"]
        self.title_label.setText(f"تعديل الكتاب رقم {row['id']}")
        self.save_btn.setText("مراجعة وحفظ التعديل")
        self.letter_number_edit.setText(row["letter_number"] or "")
        idx = self.sender_type_combo.findText(row["sender_type"] or "")
        if idx >= 0:
            self.sender_type_combo.setCurrentIndex(idx)
        else:
            self.sender_type_combo.setEditText(row["sender_type"] or "")
        self.sender_name_edit.setText(row["sender_name"] or "")
        if row["letter_date"]:
            qd = QDate.fromString(row["letter_date"], "yyyy-MM-dd")
            if qd.isValid():
                self.date_edit.setDate(qd)
        self.subject_edit.setText(row["subject"] or "")
        self.notes_edit.setPlainText(row["notes"] or "")

    def _collect_data(self):
        return {
            "letter_number": self.letter_number_edit.text().strip(),
            "sender_type": self.sender_type_combo.currentText().strip(),
            "sender_name": self.sender_name_edit.text().strip(),
            "letter_date": self.date_edit.date().toString("yyyy-MM-dd"),
            "subject": self.subject_edit.text().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
        }

    def review_and_save(self):
        data = self._collect_data()

        if not data["subject"]:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال عنوان / موضوع الكتاب.")
            return
        if not data["sender_name"]:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال اسم الجهة المرسلة.")
            return

        dialog = ConfirmSaveDialog(data, self)
        if dialog.exec_() == QDialog.Accepted:
            if self.editing_id:
                self.db.update_letter(self.editing_id, **data)
                QMessageBox.information(self, "تم", "تم تحديث الكتاب بنجاح.")
            else:
                self.db.add_letter(**data)
                QMessageBox.information(self, "تم", "تم حفظ الكتاب في الأرشيف بنجاح.")
            self.clear_form()
            if self.on_saved:
                self.on_saved()


# ==========================================================
#   صفحة الأرشيف والبحث
# ==========================================================
class ArchivePage(QWidget):
    def __init__(self, db: Database, on_edit=None):
        super().__init__()
        self.db = db
        self.on_edit = on_edit
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(6)

        title = QLabel("الأرشيف والبحث")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        subtitle = QLabel("ابحث عن أي كتاب من خلال أي من تفاصيله")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        # بطاقة البحث
        search_card = QFrame()
        search_card.setObjectName("Card")
        search_layout = QGridLayout(search_card)
        search_layout.setContentsMargins(20, 16, 20, 16)
        search_layout.setSpacing(10)

        search_layout.addWidget(QLabel("بحث عام (اسم الجهة / الموضوع / الملاحظات / رقم الكتاب)"), 0, 0, 1, 4)
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("اكتب كلمة أو جزء من البيانات...")
        self.keyword_edit.returnPressed.connect(self.do_search)
        search_layout.addWidget(self.keyword_edit, 1, 0, 1, 4)

        search_layout.addWidget(QLabel("نوع الجهة"), 2, 3)
        self.filter_sender_type = QComboBox()
        self.filter_sender_type.addItem("الكل")
        self.filter_sender_type.addItems(SENDER_TYPES)
        search_layout.addWidget(self.filter_sender_type, 2, 2)

        search_layout.addWidget(QLabel("رقم الكتاب"), 2, 1)
        self.filter_number = QLineEdit()
        search_layout.addWidget(self.filter_number, 2, 0)

        search_layout.addWidget(QLabel("من تاريخ"), 3, 3)
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setDate(QDate(2000, 1, 1))
        search_layout.addWidget(self.date_from, 3, 2)

        search_layout.addWidget(QLabel("إلى تاريخ"), 3, 1)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDate(QDate.currentDate())
        search_layout.addWidget(self.date_to, 3, 0)

        btn_row = QHBoxLayout()
        self.search_btn = QPushButton("بحث")
        self.search_btn.setObjectName("GoldBtn")
        self.search_btn.clicked.connect(self.do_search)
        self.reset_btn = QPushButton("إظهار الكل")
        self.reset_btn.setObjectName("SecondaryBtn")
        self.reset_btn.clicked.connect(self.refresh)
        btn_row.addWidget(self.search_btn)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()
        search_layout.addLayout(btn_row, 4, 0, 1, 4)

        layout.addWidget(search_card)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "م", "رقم الكتاب", "نوع الجهة", "اسم الجهة",
            "تاريخ الكتاب", "الموضوع", "الملاحظات"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        self.result_count_label = QLabel("")
        self.result_count_label.setObjectName("PageSubtitle")
        action_row.addWidget(self.result_count_label)
        action_row.addStretch()
        self.edit_btn = QPushButton("تعديل الكتاب المحدد")
        self.edit_btn.setObjectName("SecondaryBtn")
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn = QPushButton("حذف الكتاب المحدد")
        self.delete_btn.setObjectName("DangerBtn")
        self.delete_btn.clicked.connect(self.delete_selected)
        action_row.addWidget(self.edit_btn)
        action_row.addWidget(self.delete_btn)
        layout.addLayout(action_row)

    def _fill_table(self, rows):
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            values = [
                str(row["id"]), row["letter_number"] or "", row["sender_type"] or "",
                row["sender_name"] or "", row["letter_date"] or "",
                row["subject"] or "", row["notes"] or "",
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, c, item)
        self.result_count_label.setText(f"عدد النتائج: {len(rows)}")

    def refresh(self):
        rows = self.db.get_all()
        self._fill_table(rows)

    def do_search(self):
        sender_type = self.filter_sender_type.currentText()
        if sender_type == "الكل":
            sender_type = ""
        rows = self.db.search(
            keyword=self.keyword_edit.text().strip(),
            sender_type=sender_type,
            date_from=self.date_from.date().toString("yyyy-MM-dd"),
            date_to=self.date_to.date().toString("yyyy-MM-dd"),
            letter_number=self.filter_number.text().strip(),
        )
        self._fill_table(rows)

    def _get_selected_id(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار كتاب من الجدول أولاً.")
            return None
        row_index = selected[0].row()
        return int(self.table.item(row_index, 0).text())

    def edit_selected(self):
        letter_id = self._get_selected_id()
        if letter_id is None:
            return
        row = self.db.get_by_id(letter_id)
        if row and self.on_edit:
            self.on_edit(row)

    def delete_selected(self):
        letter_id = self._get_selected_id()
        if letter_id is None:
            return
        confirm = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل أنت متأكد من حذف الكتاب رقم {letter_id}؟\nلا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.db.delete_letter(letter_id)
            self.refresh()


# ==========================================================
#   صفحة النسخ الاحتياطي والاستعادة
# ==========================================================
class BackupPage(QWidget):
    def __init__(self, db: Database, on_restored=None):
        super().__init__()
        self.db = db
        self.on_restored = on_restored
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(6)

        title = QLabel("النسخ الاحتياطي والاستعادة")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        subtitle = QLabel("احتفظ بنسخة احتياطية من الأرشيف بشكل دوري، ويمكنك استعادتها في أي وقت")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        self.count_label = QLabel()
        card_layout.addWidget(self.count_label)

        backup_btn = QPushButton("إنشاء نسخة احتياطية الآن")
        backup_btn.setObjectName("GoldBtn")
        backup_btn.clicked.connect(self.do_backup)
        card_layout.addWidget(backup_btn)

        restore_btn = QPushButton("استعادة من نسخة احتياطية")
        restore_btn.setObjectName("SecondaryBtn")
        restore_btn.clicked.connect(self.do_restore)
        card_layout.addWidget(restore_btn)

        note = QLabel(
            "ملاحظة: عملية الاستعادة ستستبدل كامل بيانات الأرشيف الحالية "
            "بالبيانات الموجودة في ملف النسخة الاحتياطية المختار."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#B3332A; font-size:12px;")
        card_layout.addWidget(note)

        layout.addWidget(card)
        layout.addStretch()
        self.refresh_count()

    def refresh_count(self):
        self.count_label.setText(f"عدد الكتب المؤرشفة حاليًا: {self.db.count()}")

    def do_backup(self):
        default_name = f"نسخة_احتياطية_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.db"
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ النسخة الاحتياطية", default_name, "ملفات قاعدة البيانات (*.db)"
        )
        if path:
            try:
                self.db.backup_to(path)
                QMessageBox.information(self, "تم", "تم إنشاء النسخة الاحتياطية بنجاح.")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء النسخ الاحتياطي:\n{e}")

    def do_restore(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "اختيار ملف النسخة الاحتياطية", "", "ملفات قاعدة البيانات (*.db)"
        )
        if not path:
            return
        confirm = QMessageBox.question(
            self, "تأكيد الاستعادة",
            "سيتم استبدال جميع البيانات الحالية بالبيانات الموجودة في الملف المختار.\n"
            "هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                self.db.restore_from(path)
                QMessageBox.information(self, "تم", "تمت الاستعادة بنجاح.")
                self.refresh_count()
                if self.on_restored:
                    self.on_restored()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الاستعادة:\n{e}")


# ==========================================================
#   صفحة الإعدادات (مفتاح Anthropic API)
# ==========================================================
class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(6)

        title = QLabel("الإعدادات")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        subtitle = QLabel("إعداد مفتاح الذكاء الاصطناعي (Anthropic API) المستخدم في الاستخراج التلقائي للبيانات")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("Card")
        form = QGridLayout(card)
        form.setContentsMargins(24, 24, 24, 24)
        form.setSpacing(12)

        form.addWidget(QLabel("مفتاح Anthropic API"), 0, 1)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("sk-ant-...")
        form.addWidget(self.api_key_edit, 0, 0)

        self.show_key_btn = QPushButton("إظهار")
        self.show_key_btn.setObjectName("SecondaryBtn")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self._toggle_key_visibility)
        form.addWidget(self.show_key_btn, 0, 2)

        form.addWidget(QLabel("النموذج المستخدم في الاستخراج"), 1, 1)
        self.model_combo = QComboBox()
        for model_id, label in AI_MODELS:
            self.model_combo.addItem(label, model_id)
        form.addWidget(self.model_combo, 1, 0, 1, 3)

        layout.addWidget(card)

        note = QLabel(
            "⚠️ ملاحظة هامة بخصوص الخصوصية: عند استخدام ميزة الاستخراج التلقائي، سيتم إرسال "
            "محتوى الصورة أو ملف الـ PDF إلى خوادم Anthropic عبر الإنترنت لتحليله. "
            "لا تستخدم هذه الميزة مع كتب تحتوي معلومات سرّية للغاية إلا وفق سياسة جهتك.\n\n"
            "يتم حفظ المفتاح في ملف config.json بجانب البرنامج بشكل نصي غير مشفّر — "
            "احتفظ بجهازك بشكل آمن."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#B3332A; font-size:12px;")
        layout.addWidget(note)

        save_row = QHBoxLayout()
        save_row.addStretch()
        self.save_btn = QPushButton("حفظ الإعدادات")
        self.save_btn.setObjectName("GoldBtn")
        self.save_btn.clicked.connect(self.save_settings)
        save_row.addWidget(self.save_btn)
        layout.addLayout(save_row)

        layout.addStretch()

    def _toggle_key_visibility(self, checked):
        self.api_key_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.show_key_btn.setText("إخفاء" if checked else "إظهار")

    def _load_current(self):
        cfg = app_config.load_config()
        self.api_key_edit.setText(cfg.get("api_key", ""))
        model_id = cfg.get("model", "claude-sonnet-5")
        idx = self.model_combo.findData(model_id)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

    def save_settings(self):
        cfg = {
            "api_key": self.api_key_edit.text().strip(),
            "model": self.model_combo.currentData(),
        }
        app_config.save_config(cfg)
        QMessageBox.information(self, "تم", "تم حفظ الإعدادات بنجاح.")


# ==========================================================
#   النافذة الرئيسية
# ==========================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام أرشفة الكتب الرسمية")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(1150, 700)

        self.db = Database()

        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- الشريط الجانبي ---
        sidebar = QWidget()
        sidebar.setObjectName("SideBar")
        sidebar.setFixedWidth(230)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(2)

        logo = QLabel("الأرشيف الرسمي")
        logo.setObjectName("LogoLabel")
        logo.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(logo)

        sub_logo = QLabel("نظام إدارة وأرشفة الكتب")
        sub_logo.setObjectName("SubLogoLabel")
        sub_logo.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(sub_logo)

        self.nav_buttons = []
        nav_items = [
            ("إضافة كتاب جديد", 0),
            ("الأرشيف والبحث", 1),
            ("النسخ الاحتياطي", 2),
            ("الإعدادات", 3),
        ]
        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, i=idx: self.switch_page(i))
            side_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        side_layout.addStretch()

        version_label = QLabel("الإصدار 1.0")
        version_label.setObjectName("SubLogoLabel")
        version_label.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(version_label)

        main_layout.addWidget(sidebar)

        # --- الصفحات ---
        self.stack = QStackedWidget()

        self.add_page = AddLetterPage(self.db, on_saved=self.after_data_change)
        self.archive_page = ArchivePage(self.db, on_edit=self.go_to_edit)
        self.backup_page = BackupPage(self.db, on_restored=self.after_data_change)
        self.settings_page = SettingsPage()

        self.stack.addWidget(self.add_page)
        self.stack.addWidget(self.archive_page)
        self.stack.addWidget(self.backup_page)
        self.stack.addWidget(self.settings_page)

        main_layout.addWidget(self.stack)

        self.setCentralWidget(central)
        self.statusBar().showMessage(f"قاعدة البيانات: {get_db_path()}")

        self.switch_page(1)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        if index == 1:
            self.archive_page.refresh()
        if index == 2:
            self.backup_page.refresh_count()

    def go_to_edit(self, row):
        self.add_page.load_for_edit(row)
        self.switch_page(0)

    def after_data_change(self):
        self.archive_page.refresh()
        self.backup_page.refresh_count()
        self.switch_page(1)


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyleSheet(APP_STYLESHEET)
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
