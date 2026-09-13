# -*- coding: utf-8 -*-
"""تنسيقات الواجهة (QSS) - تصميم احترافي هادئ بدرجات كحلي/رمادي/ذهبي"""

APP_STYLESHEET = """
QWidget {
    background-color: #F4F6F8;
    color: #1F2A44;
    font-family: 'Segoe UI', 'Tahoma', sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: #F4F6F8;
}

/* ------- الشريط الجانبي ------- */
#SideBar {
    background-color: #16233D;
}

#SideBar QPushButton {
    background-color: transparent;
    color: #D7DEEA;
    text-align: right;
    padding: 14px 18px;
    border: none;
    font-size: 15px;
    font-weight: 600;
}

#SideBar QPushButton:hover {
    background-color: #223357;
}

#SideBar QPushButton:checked {
    background-color: #C9A24B;
    color: #16233D;
}

#LogoLabel {
    color: #C9A24B;
    font-size: 20px;
    font-weight: bold;
    padding: 24px 10px;
}

#SubLogoLabel {
    color: #8FA0C0;
    font-size: 12px;
    padding: 0px 10px 20px 10px;
}

/* ------- العناوين ------- */
#PageTitle {
    font-size: 22px;
    font-weight: bold;
    color: #16233D;
    padding-bottom: 4px;
}

#PageSubtitle {
    font-size: 13px;
    color: #6B7A99;
    padding-bottom: 10px;
}

/* ------- البطاقات ------- */
#Card {
    background-color: #FFFFFF;
    border-radius: 10px;
    border: 1px solid #E3E8EF;
}

/* ------- الحقول ------- */
QLineEdit, QComboBox, QDateEdit, QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px;
    color: #1F2A44;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1px solid #C9A24B;
}

QLabel[role="field"] {
    font-weight: 600;
    color: #33415C;
    padding-top: 6px;
}

/* ------- الأزرار ------- */
QPushButton#PrimaryBtn {
    background-color: #16233D;
    color: white;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
}
QPushButton#PrimaryBtn:hover {
    background-color: #223357;
}

QPushButton#GoldBtn {
    background-color: #C9A24B;
    color: #16233D;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
}
QPushButton#GoldBtn:hover {
    background-color: #D9B968;
}

QPushButton#DangerBtn {
    background-color: #B3332A;
    color: white;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
}
QPushButton#DangerBtn:hover {
    background-color: #C7453B;
}

QPushButton#SecondaryBtn {
    background-color: #E3E8EF;
    color: #16233D;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 600;
}
QPushButton#SecondaryBtn:hover {
    background-color: #D3DAE5;
}

/* ------- الجدول ------- */
QTableWidget {
    background-color: white;
    border: 1px solid #E3E8EF;
    border-radius: 8px;
    gridline-color: #EEF1F5;
    selection-background-color: #C9A24B;
    selection-color: #16233D;
}

QHeaderView::section {
    background-color: #16233D;
    color: white;
    padding: 8px;
    border: none;
    font-weight: bold;
}

QTableWidget::item {
    padding: 6px;
}

/* ------- شريط الحالة ------- */
QStatusBar {
    background-color: #E3E8EF;
    color: #33415C;
}
"""
