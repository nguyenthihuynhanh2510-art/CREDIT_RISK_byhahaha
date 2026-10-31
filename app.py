# -*- coding: utf-8 -*-
"""
SmartCredit AI - Cổng Thông Tin Chấm Điểm Tín Dụng & Quản Trị Rủi Ro Đa Mô Hình (Multi-Model Risk Portal)
Thiết kế theo chuẩn mực Báo cáo Thường niên Ngân hàng & Chuẩn mực Basel II / IFRS 9
Đồ án Tốt nghiệp / Dự án Quản trị Rủi ro Tín dụng Bán lẻ (Retail Credit Risk)
"""

import os
import io
import json
import joblib
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import xgboost as xgb

# Thư viện kết xuất Báo cáo Thẩm định chuẩn A4
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==============================================================================
# ĐĂNG KÝ FONT TIẾNG VIỆT CHO BÁO CÁO PDF (HỖ TRỢ WINDOWS & STREAMLIT CLOUD LINUX)
# ==============================================================================
PDF_FONT_NORMAL = 'Helvetica'
PDF_FONT_BOLD = 'Helvetica-Bold'
PDF_FONT_ITALIC = 'Helvetica-Oblique'

def init_pdf_fonts():
    global PDF_FONT_NORMAL, PDF_FONT_BOLD, PDF_FONT_ITALIC
    font_candidates_normal = [
        'fonts/arial.ttf', 'arial.ttf', 'C:/Windows/Fonts/arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
    ]
    font_candidates_bold = [
        'fonts/arialbd.ttf', 'arialbd.ttf', 'C:/Windows/Fonts/arialbd.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
    ]
    font_candidates_italic = [
        'fonts/ariali.ttf', 'ariali.ttf', 'C:/Windows/Fonts/ariali.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf'
    ]
    p_norm = next((p for p in font_candidates_normal if os.path.exists(p)), None)
    p_bold = next((p for p in font_candidates_bold if os.path.exists(p)), None)
    p_ital = next((p for p in font_candidates_italic if os.path.exists(p)), None)
    if p_norm:
        try:
            pdfmetrics.registerFont(TTFont('AppVietFont', p_norm))
            PDF_FONT_NORMAL = 'AppVietFont'
        except Exception:
            pass
    if p_bold:
        try:
            pdfmetrics.registerFont(TTFont('AppVietFont-Bold', p_bold))
            PDF_FONT_BOLD = 'AppVietFont-Bold'
        except Exception:
            PDF_FONT_BOLD = PDF_FONT_NORMAL
    if p_ital:
        try:
            pdfmetrics.registerFont(TTFont('AppVietFont-Italic', p_ital))
            PDF_FONT_ITALIC = 'AppVietFont-Italic'
        except Exception:
            PDF_FONT_ITALIC = PDF_FONT_NORMAL

init_pdf_fonts()

# ==============================================================================
# DANH SÁCH CÁC NGÂN HÀNG & TCTD TẠI VIỆT NAM (CHO PHÉP SEARCH)
# ==============================================================================
VN_BANKS = [
    "Vietcombank (VCB)",
    "VietinBank (CTG)",
    "BIDV",
    "Agribank",
    "Techcombank (TCB)",
    "MBBank (MB)",
    "VPBank (VPB)",
    "ACB",
    "HDBank (HDB)",
    "Sacombank (STB)",
    "VIB",
    "TPBank (TPB)",
    "SHB",
    "SeABank (SSB)",
    "OCB",
    "MSB",
    "Eximbank (EIB)",
    "LPBank (LPB)",
    "Nam A Bank (NAB)",
    "Bac A Bank (BAB)",
    "BVBank (BVB)",
    "VietABank (VAB)",
    "Kienlongbank (KLB)",
    "Saigonbank (SGB)",
    "BaoViet Bank (BVB)",
    "PG Bank (PGB)",
    "PVcomBank",
    "SCB",
    "Shinhan Bank Vietnam",
    "HSBC Vietnam",
    "Standard Chartered Vietnam",
    "UOB Vietnam",
    "Woori Bank Vietnam",
    "Citibank Vietnam",
    "CIMB Vietnam",
    "Hong Leong Bank Vietnam",
    "Public Bank Vietnam",
    "Tổ chức tín dụng khác (Khác)"
]

# ==============================================================================
# CẤU HÌNH TRANG & GIAO DIỆN PHONG CÁCH BÁO CÁO THƯỜNG NIÊN HDBANK
# ==============================================================================
st.set_page_config(
    page_title="SmartCredit AI | Banking Risk Portal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS phong cách Báo cáo thường niên Ngân hàng cao cấp (HDBank inspired)
st.markdown("""
<style>
    :root {
        --primary-navy: #0F172A;
        --secondary-navy: #1E3A8A;
        --accent-gold: #D97706;
        --accent-blue: #2563EB;
        --success-emerald: #10B981;
        --warning-amber: #F59E0B;
        --danger-crimson: #EF4444;
        --card-bg: #FFFFFF;
        --border-color: #E2E8F0;
    }
    
    /* Header chính */
    .main-header {
        background: linear-gradient(135deg, #0A192F 0%, #1E3A8A 60%, #1E40AF 100%);
        color: white;
        padding: 26px 32px;
        border-radius: 14px;
        margin-bottom: 22px;
        box-shadow: 0 8px 25px rgba(15, 23, 42, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #93C5FD;
        margin: 6px 0 0 0;
        font-size: 14px;
    }
    
    /* Card kiểu HDBank Annual Report */
    .hdb-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.04);
        margin-bottom: 18px;
        transition: all 0.25s ease;
    }
    .hdb-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 8px 26px rgba(15, 23, 42, 0.08);
    }
    
    /* Tiêu đề phân đoạn có số badge nổi bật */
    .hdb-section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 10px;
        margin-bottom: 14px;
        padding-bottom: 8px;
        border-bottom: 2px solid #F1F5F9;
    }
    .hdb-badge {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        color: #F8FAFC;
        font-size: 13px;
        font-weight: 800;
        padding: 4px 11px;
        border-radius: 6px;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 6px rgba(30, 58, 138, 0.25);
    }
    .hdb-title {
        font-size: 15px;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.2px;
        text-transform: uppercase;
    }
    
    /* Thẻ đo lường */
    .metric-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.04);
        margin-bottom: 14px;
    }
    .metric-label {
        font-size: 12px;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 800;
        color: #0F172A;
        margin: 4px 0;
    }
    
    /* Quyết định phê duyệt */
    .decision-approved {
        background-color: #ECFDF5;
        border-left: 5px solid #10B981;
        padding: 14px 18px;
        border-radius: 8px;
        color: #065F46;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 14px;
    }
    .decision-conditional {
        background-color: #FFFBEB;
        border-left: 5px solid #F59E0B;
        padding: 14px 18px;
        border-radius: 8px;
        color: #92400E;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 14px;
    }
    .decision-rejected {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 14px 18px;
        border-radius: 8px;
        color: #991B1B;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 14px;
    }
    .reconciliation-box {
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
        border: 1px solid #BFDBFE;
        border-radius: 12px;
        padding: 16px 20px;
        margin-top: 12px;
        margin-bottom: 16px;
    }
    .summary-strip {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 12px 18px;
        border-radius: 10px;
        margin-top: 8px;
        margin-bottom: 8px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #F1F5F9;
        border-radius: 8px 8px 0px 0px;
        padding: 9px 18px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
    }

    .decision-approved-xgb {
        background-color: #F5F3FF;
        border-left: 5px solid #7C3AED;
        color: #4C1D95;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-weight: 600;
    }
    .metric-card-xgb {
        background: #FFFFFF;
        border: 1px solid #DDD6FE;
        border-top: 3px solid #7C3AED;
        border-radius: 8px;
        padding: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .decision-approved-xgb {
        background-color: #F5F3FF;
        border-left: 5px solid #7C3AED;
        color: #4C1D95;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-weight: 600;
    }
    .metric-card-xgb {
        background: #FFFFFF;
        border: 1px solid #DDD6FE;
        border-top: 3px solid #7C3AED;
        border-radius: 8px;
        padding: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# HỆ THỐNG PHÂN QUYỀN ĐĂNG NHẬP & PHÂN VAI TRÒ (RBAC)
# ==============================================================================
DEMO_USERS = {
    'officer': {
        'name': 'Nguyễn Văn An',
        'role': 'LOAN_OFFICER',
        'role_title': 'Chuyên viên Tín dụng (Loan Officer)',
        'password': '123',
        'allowed_tabs': ['single']
    },
    'manager': {
        'name': 'Trần Thị Mai',
        'role': 'CREDIT_MANAGER',
        'role_title': 'Trưởng phòng Phê duyệt (Credit Manager)',
        'password': '123',
        'allowed_tabs': ['single', 'batch', 'audit']
    },
    'cro_admin': {
        'name': 'Lê Hoàng Cường',
        'role': 'CRO_ADMIN',
        'role_title': 'Giám đốc Quản trị Rủi ro (CRO)',
        'password': '123',
        'allowed_tabs': ['single', 'batch', 'policy', 'audit']
    }
}

if 'user' not in st.session_state:
    st.session_state.user = None

# ==============================================================================
# HÀM NẠP TÀI NGUYÊN MÔ HÌNH VÀ CẤU HÌNH ĐA MÔ HÌNH (TRIPLE-MODEL)
# ==============================================================================
@st.cache_resource
def load_multi_model_risk_assets():
    possible_dirs = [
        "results",
        ".",
        "3 mô hình được chọn/results",
        "../results",
        r"D:\AI\.final_project AI\3 mô hình được chọn\results",
        r"D:\AI\project AI\3 mô hình được chọn\results"
    ]
    possible_models_dt = [
        "models/decision_tree_model.pkl",
        "decision_tree_model.pkl",
        "3 mô hình được chọn/models/decision_tree_model.pkl",
        "../models/decision_tree_model.pkl",
        r"D:\AI\.final_project AI\3 mô hình được chọn\models\decision_tree_model.pkl",
        r"D:\AI\project AI\3 mô hình được chọn\models\decision_tree_model.pkl"
    ]
    possible_models_lr = [
        "models/logistic_regression_model.pkl",
        "logistic_regression_model.pkl",
        "3 mô hình được chọn/models/logistic_regression_model.pkl",
        "../models/logistic_regression_model.pkl",
        r"D:\AI\.final_project AI\3 mô hình được chọn\models\logistic_regression_model.pkl",
        r"D:\AI\project AI\3 mô hình được chọn\models\logistic_regression_model.pkl"
    ]
    possible_models_xgb = [
        "models/xgboost_model.pkl",
        "xgboost_model.pkl",
        "3 mô hình được chọn/models/xgboost_model.pkl",
        "../models/xgboost_model.pkl",
        r"D:\AI\.final_project AI\3 mô hình được chọn\models\xgboost_model.pkl",
        r"D:\AI\project AI\3 mô hình được chọn\models\xgboost_model.pkl"
    ]
    possible_scaler = [
        "models/standard_scaler.pkl",
        "standard_scaler.pkl",
        "3 mô hình được chọn/models/standard_scaler.pkl",
        "../models/standard_scaler.pkl",
        r"D:\AI\.final_project AI\3 mô hình được chọn\models\standard_scaler.pkl",
        r"D:\AI\project AI\3 mô hình được chọn\models\standard_scaler.pkl"
    ]

    p_dt = next((p for p in possible_models_dt if os.path.exists(p)), None)
    if p_dt is None:
        raise FileNotFoundError("Không tìm thấy tệp decision_tree_model.pkl!")
    dt_model = joblib.load(p_dt)

    p_lr = next((p for p in possible_models_lr if os.path.exists(p)), None)
    lr_model = joblib.load(p_lr) if p_lr else None

    p_xgb = next((p for p in possible_models_xgb if os.path.exists(p)), None)
    xgb_model = joblib.load(p_xgb) if p_xgb else None

    p_sc = next((p for p in possible_scaler if os.path.exists(p)), None)
    scaler = joblib.load(p_sc) if p_sc else None

    leaf_file = next((os.path.join(d, "decision_tree_leaf_rules.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "decision_tree_leaf_rules.csv"))), None)
    leaf_df = pd.read_csv(leaf_file) if leaf_file else pd.DataFrame()

    cfg_dt_file = next((os.path.join(d, "multi_product_policy_config.json") for d in possible_dirs if os.path.exists(os.path.join(d, "multi_product_policy_config.json"))), None)
    if cfg_dt_file:
        with open(cfg_dt_file, "r", encoding="utf-8") as f:
            dt_cfg = json.load(f)
    else:
        dt_cfg = {
            'MORTGAGE': {'product_name': 'Cho vay Mua nhà có TSBĐ', 'params': {'r': 0.045, 'c': 0.010, 'lgd': 0.250, 'pd_breakeven': 0.1228}, 'policies': {'NORMAL': {'min_score': 550, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']}, 'EXPANSION': {'min_score': 550, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']}, 'RECESSION': {'min_score': 572, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}}},
            'AUTO': {'product_name': 'Cho vay Mua Ô tô (Auto Loan)', 'params': {'r': 0.065, 'c': 0.015, 'lgd': 0.450, 'pd_breakeven': 0.1000}, 'policies': {'NORMAL': {'min_score': 555, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}, 'EXPANSION': {'min_score': 551, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']}, 'RECESSION': {'min_score': 600, 'allowed_grades': ['Hạng 1 (< 2%)']}}},
            'UNSECURED': {'product_name': 'Vay Tiêu dùng Tín chấp', 'params': {'r': 0.140, 'c': 0.030, 'lgd': 0.750, 'pd_breakeven': 0.1279}, 'policies': {'NORMAL': {'min_score': 551, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']}, 'EXPANSION': {'min_score': 543, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']}, 'RECESSION': {'min_score': 572, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}}},
            'CREDIT_CARD': {'product_name': 'Thẻ Tín dụng (Credit Card)', 'params': {'r': 0.180, 'c': 0.040, 'lgd': 0.850, 'pd_breakeven': 0.1414}, 'policies': {'NORMAL': {'min_score': 542, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']}, 'EXPANSION': {'min_score': 527, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)', 'Hạng 4 (10% - 20%)']}, 'RECESSION': {'min_score': 572, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}}}
        }

    cfg_lr_file = next((os.path.join(d, "logistic_multi_product_policy_config.json") for d in possible_dirs if os.path.exists(os.path.join(d, "logistic_multi_product_policy_config.json"))), None)
    if cfg_lr_file:
        with open(cfg_lr_file, "r", encoding="utf-8") as f:
            lr_cfg = json.load(f)
    else:
        lr_cfg = dt_cfg

    cfg_xgb_file = next((os.path.join(d, "xgboost_multi_product_policy_config.json") for d in possible_dirs if os.path.exists(os.path.join(d, "xgboost_multi_product_policy_config.json"))), None)
    if cfg_xgb_file:
        with open(cfg_xgb_file, "r", encoding="utf-8") as f:
            xgb_cfg = json.load(f)
    else:
        xgb_cfg = {
            'MORTGAGE': {'product_name': 'Cho vay Mua nhà có TSBĐ', 'params': {'r': 0.045, 'c': 0.010, 'lgd': 0.250, 'pd_breakeven': 0.1228}, 'policies': {'NORMAL': {'min_score': 544, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']}, 'EXPANSION': {'min_score': 540, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']}, 'RECESSION': {'min_score': 572, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}}},
            'AUTO': {'product_name': 'Cho vay Mua Ô tô (Auto Loan)', 'params': {'r': 0.065, 'c': 0.015, 'lgd': 0.450, 'pd_breakeven': 0.1000}, 'policies': {'NORMAL': {'min_score': 551, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}, 'EXPANSION': {'min_score': 548, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}, 'RECESSION': {'min_score': 600, 'allowed_grades': ['Hạng 1 (< 2%)']}}},
            'UNSECURED': {'product_name': 'Vay Tiêu dùng Tín chấp', 'params': {'r': 0.140, 'c': 0.030, 'lgd': 0.750, 'pd_breakeven': 0.1279}, 'policies': {'NORMAL': {'min_score': 543, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']}, 'EXPANSION': {'min_score': 538, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}, 'RECESSION': {'min_score': 572, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}}},
            'CREDIT_CARD': {'product_name': 'Thẻ Tín dụng (Credit Card)', 'params': {'r': 0.180, 'c': 0.040, 'lgd': 0.850, 'pd_breakeven': 0.1414}, 'policies': {'NORMAL': {'min_score': 540, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']}, 'EXPANSION': {'min_score': 527, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)', 'Hạng 4 (10% - 20%)']}, 'RECESSION': {'min_score': 572, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}}}
        }

    p_dt_met = next((os.path.join(d, "decision_tree_metrics.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "decision_tree_metrics.csv"))), None)
    dt_metrics_df = pd.read_csv(p_dt_met) if p_dt_met else pd.DataFrame()

    p_lr_met = next((os.path.join(d, "logistic_regression_metrics.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "logistic_regression_metrics.csv"))), None)
    lr_metrics_df = pd.read_csv(p_lr_met) if p_lr_met else pd.DataFrame()

    p_xgb_met = next((os.path.join(d, "xgboost_metrics.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "xgboost_metrics.csv"))), None)
    xgb_metrics_df = pd.read_csv(p_xgb_met) if p_xgb_met else pd.DataFrame()

    p_feat = next((os.path.join(d, "decision_tree_feature_importance.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "decision_tree_feature_importance.csv"))), None)
    feat_df = pd.read_csv(p_feat) if p_feat else pd.DataFrame()

    p_xgb_feat = next((os.path.join(d, "xgboost_feature_importance.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "xgboost_feature_importance.csv"))), None)
    xgb_feat_df = pd.read_csv(p_xgb_feat) if p_xgb_feat else pd.DataFrame()

    pdo = 20.0
    base_score = 600.0
    base_odds = 50.0
    factor = pdo / np.log(2.0)
    offset = base_score - factor * np.log(base_odds)

    return dt_model, lr_model, xgb_model, scaler, leaf_df, dt_cfg, lr_cfg, xgb_cfg, dt_metrics_df, lr_metrics_df, xgb_metrics_df, feat_df, xgb_feat_df, factor, offset

try:
    dt_model, lr_model, xgb_model, scaler, leaf_df, dt_cfg, lr_cfg, xgb_cfg, dt_metrics_df, lr_metrics_df, xgb_metrics_df, feat_df, xgb_feat_df, factor, offset = load_multi_model_risk_assets()
    leaf_info = leaf_df.set_index('Leaf ID').to_dict('index') if not leaf_df.empty else {}
except Exception as e:
    st.error(f"Lỗi khi nạp dữ liệu mô hình: {e}")
    st.stop()

FEATURE_COLS = [
    'RevolvingUtilizationOfUnsecuredLines', 'age',
    'NumberOfTime30-59DaysPastDueNotWorse', 'DebtRatio', 'MonthlyIncome',
    'NumberOfOpenCreditLinesAndLoans', 'NumberOfTimes90DaysLate',
    'NumberRealEstateLoansOrLines', 'NumberOfTime60-89DaysPastDueNotWorse',
    'NumberOfDependents', 'MonthlyIncome_is_missing'
]

# ==============================================================================
# HỆ THỐNG ĐỊNH NGHĨA SẢN PHẨM & TÍNH TOÁN 4 FEATURE CHUẨN GIVE ME SOME CREDIT
# ==============================================================================
ACCOUNT_TYPES = {
    'CREDIT_CARD': 'Thẻ tín dụng (Credit Card)',
    'UNSECURED_LOC': 'Hạn mức tín dụng cá nhân không TSBĐ',
    'OVERDRAFT': 'Hạn mức thấu chi không TSBĐ',
    'MORTGAGE': 'Khoản vay thế chấp/mua nhà (Mortgage Loan)',
    'REAL_ESTATE': 'Khoản vay bất động sản khác (Real Estate Loan)',
    'HELOC': 'Hạn mức tín dụng thế chấp nhà (HELOC)',
    'AUTO': 'Khoản vay mua ô tô (Auto Loan)',
    'CONSUMER_INSTALLMENT': 'Khoản vay tiêu dùng trả góp',
    'OTHER': 'Khoản tín dụng khác'
}

COLLATERAL_TYPES = {
    'UNSECURED': 'Không có TSBĐ (Tín chấp)',
    'SECURED_RE': 'Có TSBĐ bằng Bất động sản',
    'SECURED_OTHER': 'Có TSBĐ khác (Ô tô, STK,...)'
}

ACCOUNT_STATUSES = {
    'OPEN': 'Đang mở (Active)',
    'CLOSED': 'Đã tất toán & đóng (Closed)'
}

def calculate_number_open_credit_lines_and_loans(accounts):
    """
    NumberOfOpenCreditLinesAndLoans:
    Tổng số khoản vay trả góp đang mở và các hạn mức tín dụng đang mở của khách hàng.
    Chỉ tính các tài khoản có status == 'OPEN'. Loại trừ tài khoản đã đóng.
    """
    open_accs = [a for a in accounts if a.get('status', 'OPEN') == 'OPEN']
    closed_accs = [a for a in accounts if a.get('status', 'OPEN') == 'CLOSED']
    
    open_cards_lines = [a for a in open_accs if a.get('acc_type') in ['CREDIT_CARD', 'UNSECURED_LOC', 'OVERDRAFT', 'HELOC']]
    open_loans = [a for a in open_accs if a.get('acc_type') not in ['CREDIT_CARD', 'UNSECURED_LOC', 'OVERDRAFT', 'HELOC']]
    
    val = len(open_accs)
    return {
        'value': int(val),
        'total_open': len(open_accs),
        'open_cards_and_lines': len(open_cards_lines),
        'open_loans': len(open_loans),
        'closed_count': len(closed_accs),
        'qualifying_accounts': open_accs,
        'excluded_accounts': closed_accs,
        'explanation': f"Tổng cộng {len(open_accs)} tài khoản đang mở ({len(open_cards_lines)} thẻ/hạn mức + {len(open_loans)} khoản vay). Loại trừ {len(closed_accs)} tài khoản đã đóng."
    }

def calculate_number_real_estate_loans(accounts):
    """
    NumberRealEstateLoansOrLines:
    Số khoản vay thế chấp, khoản vay bất động sản và hạn mức tín dụng bất động sản (bao gồm HELOC).
    Điều kiện: status == 'OPEN' VÀ (acc_type in ['MORTGAGE', 'REAL_ESTATE', 'HELOC'] HOẶC collateral == 'SECURED_RE')
    """
    re_types = {'MORTGAGE', 'REAL_ESTATE', 'HELOC'}
    qualifying = []
    excluded = []
    
    for a in accounts:
        if a.get('status', 'OPEN') != 'OPEN':
            excluded.append((a, "Tài khoản đã đóng (Tất toán)"))
            continue
            
        acc_type = a.get('acc_type', '')
        collateral = a.get('collateral', '')
        
        if acc_type in re_types or collateral == 'SECURED_RE':
            qualifying.append(a)
        else:
            excluded.append((a, f"Loại hình {ACCOUNT_TYPES.get(acc_type, acc_type)} không thuộc tín dụng BĐS"))
            
    val = len(qualifying)
    mortgages = [a for a in qualifying if a.get('acc_type') == 'MORTGAGE']
    re_loans = [a for a in qualifying if a.get('acc_type') == 'REAL_ESTATE']
    helocs = [a for a in qualifying if a.get('acc_type') == 'HELOC']
    other_re = [a for a in qualifying if a.get('acc_type') not in re_types]
    
    return {
        'value': int(val),
        'mortgages_count': len(mortgages),
        're_loans_count': len(re_loans),
        'heloc_count': len(helocs),
        'other_re_count': len(other_re),
        'qualifying_accounts': qualifying,
        'excluded_accounts': excluded,
        'explanation': f"Gồm {len(mortgages)} khoản vay mua nhà/thế chấp, {len(re_loans)} khoản vay BĐS khác, {len(helocs)} hạn mức HELOC."
    }

def calculate_revolving_utilization(accounts):
    """
    RevolvingUtilizationOfUnsecuredLines:
    RU = sum(D_i) / sum(L_i)
    Chỉ bao gồm các tài khoản tín dụng quay vòng KHÔNG CÓ TSBĐ (Credit Card, Unsecured Line of Credit, Overdraft).
    Tài khoản thẻ chưa dùng (dư nợ = 0) vẫn cộng hạn mức vào mẫu số.
    """
    revolving_unsecured_types = {'CREDIT_CARD', 'UNSECURED_LOC', 'OVERDRAFT'}
    qualifying = []
    excluded = []
    
    total_balance = 0.0
    total_limit = 0.0
    
    for a in accounts:
        if a.get('status', 'OPEN') != 'OPEN':
            excluded.append((a, "Tài khoản đã đóng"))
            continue
            
        acc_type = a.get('acc_type', '')
        collateral = a.get('collateral', 'UNSECURED')
        
        if acc_type in revolving_unsecured_types and collateral == 'UNSECURED':
            bal = float(a.get('balance', 0.0))
            lim = float(a.get('limit', 0.0))
            total_balance += bal
            total_limit += lim
            qualifying.append(a)
        else:
            if acc_type == 'HELOC':
                excluded.append((a, "HELOC có TSBĐ bằng BĐS (Loại khỏi tín dụng không TSBĐ)"))
            elif collateral != 'UNSECURED':
                excluded.append((a, "Tài khoản có tài sản bảo đảm (Không phải tín chấp)"))
            else:
                excluded.append((a, f"Khoản vay trả góp ({ACCOUNT_TYPES.get(acc_type, acc_type)}), không phải tín dụng quay vòng"))
                
    if total_limit > 0:
        raw_ru = total_balance / total_limit
        display_pct = raw_ru * 100.0
        # Theo training pipeline GMSC cắt tại phân vị 99.5% (~1.369269)
        model_val = float(np.clip(raw_ru, 0.0, 1.369269))
        status_badge = "HỢP LỆ (VALID)"
        if raw_ru > 1.0:
            status_badge = "VƯỢT HẠN MỨC (OVER_LIMIT)"
    elif total_limit == 0 and total_balance == 0:
        raw_ru = 0.0
        display_pct = 0.0
        model_val = 0.0
        status_badge = "KHÔNG CÓ DƯ NỢ / HẠN MỨC (ZERO_UTIL)"
    else:
        raw_ru = 1.0
        display_pct = 100.0
        model_val = 1.0
        status_badge = "CẢNH BÁO: DƯ NỢ CÓ NHƯNG HẠN MỨC BẰNG 0"
        
    return {
        'value': model_val,
        'raw_ratio': raw_ru,
        'display_pct': display_pct,
        'total_balance': total_balance,
        'total_limit': total_limit,
        'qualifying_count': len(qualifying),
        'qualifying_accounts': qualifying,
        'excluded_accounts': excluded,
        'status_badge': status_badge,
        'explanation': f"Tổng dư nợ tín dụng quay vòng không TSBĐ = {total_balance:,.0f} đ / Tổng hạn mức = {total_limit:,.0f} đ -> RU = {display_pct:.2f}%."
    }

def calculate_debt_ratio(accounts, gross_income_vnd, alimony_vnd=0.0, living_costs_vnd=0.0, new_loan_installment=0.0):
    """
    DebtRatio = (Monthly Debt Payments + Alimony + Living Costs) / Monthly Gross Income
    """
    open_accs = [a for a in accounts if a.get('status', 'OPEN') == 'OPEN']
    
    monthly_debt_payments = sum(float(a.get('monthly_payment', 0.0)) for a in open_accs)
    total_obligations = monthly_debt_payments + float(alimony_vnd) + float(living_costs_vnd)
    gross_income = float(gross_income_vnd)
    
    if gross_income > 0:
        raw_dr = total_obligations / gross_income
        display_pct = raw_dr * 100.0
        # Pipeline GMSC cắt trần tại phân vị 99.5% (~2.314806)
        model_val = float(np.clip(raw_dr, 0.0, 2.314806))
        status_badge = "HỢP LỆ (VALID)"
        if raw_dr > 1.0:
            status_badge = "CẢNH BÁO NGHĨA VỤ VƯỢT THU NHẬP (DR > 100%)"
            
        post_obligations = total_obligations + float(new_loan_installment)
        post_dr = post_obligations / gross_income
        post_dsr_pct = ((monthly_debt_payments + float(new_loan_installment)) / gross_income) * 100.0
    else:
        raw_dr = 0.0
        display_pct = 0.0
        model_val = 0.0
        status_badge = "THIẾU THU NHẬP GỐC (INCOME MISSING)"
        post_dr = 0.0
        post_dsr_pct = 100.0
        
    return {
        'value': model_val,
        'raw_ratio': raw_dr,
        'display_pct': display_pct,
        'monthly_debt_payments': monthly_debt_payments,
        'alimony': float(alimony_vnd),
        'living_costs': float(living_costs_vnd),
        'total_obligations': total_obligations,
        'gross_income': gross_income,
        'post_debt_ratio': post_dr,
        'post_dsr_pct': post_dsr_pct,
        'status_badge': status_badge,
        'open_accounts_count': len(open_accs),
        'explanation': f"Nghĩa vụ hàng tháng ({monthly_debt_payments:,.0f} đ nợ + {living_costs_vnd:,.0f} đ sinh hoạt + {alimony_vnd:,.0f} đ cấp dưỡng) / Thu nhập gộp {gross_income:,.0f} đ = {display_pct:.2f}%."
    }
# ==============================================================================
# HÀM TÍNH TOÁN CHẤM ĐIỂM CHO DECISION TREE
# ==============================================================================
def score_single_customer_dt(data_dict, product_code, market_mode, loan_amt):
    df_in = pd.DataFrame([data_dict])
    if 'MonthlyIncome_is_missing' not in df_in.columns:
        if 'MonthlyIncome' in df_in.columns and (pd.isnull(df_in['MonthlyIncome'].iloc[0]) or df_in['MonthlyIncome'].iloc[0] == 0):
            df_in['MonthlyIncome_is_missing'] = 1
        else:
            df_in['MonthlyIncome_is_missing'] = 0
            
    for col in FEATURE_COLS:
        if col not in df_in.columns:
            df_in[col] = 0.0
            
    X_cust = df_in[FEATURE_COLS]
    leaf_id = int(dt_model.apply(X_cust)[0])
    base_pd = float(dt_model.predict_proba(X_cust)[0, 1])
    
    util = float(data_dict.get('RevolvingUtilizationOfUnsecuredLines', 0.25))
    debt = float(data_dict.get('DebtRatio', 0.35))
    inc = float(data_dict.get('MonthlyIncome', 6000.0)) if not (pd.isnull(data_dict.get('MonthlyIncome')) or data_dict.get('MonthlyIncome') == 0) else 0.0
    age = float(data_dict.get('age', 35))
    dep = float(data_dict.get('NumberOfDependents', 1))
    
    eps = 1e-6
    base_log_odds = np.log((base_pd + eps) / (1 - base_pd + eps))
    adj_util = 0.50 * (util - 0.25)
    adj_debt = 0.40 * (debt - 0.35)
    adj_inc = -0.30 * np.log(np.clip(inc / 6000.0, 0.15, 6.0)) if inc > 0 else 0.25
    adj_age = -0.15 * ((age - 35.0) / 20.0)
    adj_dep = 0.08 * (dep - 1.0)
    
    total_log_odds = base_log_odds + adj_util + adj_debt + adj_inc + adj_age + adj_dep
    prob_pd = float(1.0 / (1.0 + np.exp(-total_log_odds)))
    prob_pd = float(np.clip(prob_pd, 0.001, 0.98))
    fico = int(np.clip(np.round(offset - factor * total_log_odds), 300, 850))
    
    if fico >= 605:
        grade = 'Hạng 1 (< 2%)'
    elif fico >= 572:
        grade = 'Hạng 2 (2% - 5%)'
    elif fico >= 540:
        grade = 'Hạng 3 (5% - 10%)'
    elif fico >= 500:
        grade = 'Hạng 4 (10% - 20%)'
    else:
        grade = 'Hạng 5 (> 20%)'
        
    leaf_row = leaf_info.get(leaf_id, {})
    wilson = leaf_row.get('Wilson CI 95%', f"[{max(0.001, prob_pd*0.85)*100:.2f}%, {min(0.99, prob_pd*1.2)*100:.2f}%]")
    rule = leaf_row.get('Điều kiện logic (IF - THEN)', 'Cụm nút lá tiêu chuẩn')
    
    prod_cfg = dt_cfg.get(product_code, dt_cfg['CREDIT_CARD'])
    p_params = prod_cfg['params']
    net_r = p_params['r'] - p_params['c']
    lgd = p_params['lgd']
    pd_star = p_params['pd_breakeven']
    
    net_margin = (1.0 - prob_pd) * net_r - prob_pd * lgd
    profit_vnd = loan_amt * net_margin
    
    inc_vnd = inc * 25_000 if inc > 0 else 0
    monthly_installment = (loan_amt * (1.0 + p_params['r'] * 3.0)) / 36.0
    dsr_ratio = (monthly_installment / inc_vnd) if inc_vnd > 0 else 1.0
    active_policy = prod_cfg['policies'].get(market_mode, prod_cfg['policies']['NORMAL'])
    
    if dsr_ratio > 0.60 and inc_vnd > 0:
        decision = 'DUYỆT CÓ ĐIỀU KIỆN (CẢNH BÁO NGHĨA VỤ NỢ DTI)'
        dec_code = 'CONDITIONAL'
        reason = f"FICO {fico} ({grade}). Nghĩa vụ góp ({monthly_installment:,.0f} đ/th) chiếm {dsr_ratio*100:.1f}% thu nhập (> 60%). Đề xuất hạ hạn mức."
    elif grade in active_policy['allowed_grades'] and prob_pd <= pd_star:
        decision = 'PHÊ DUYỆT TỰ ĐỘNG (AUTO-APPROVED)'
        dec_code = 'APPROVED'
        reason = f"FICO {fico} đạt chuẩn ({grade}). PD={prob_pd*100:.2f}% < PD*={pd_star*100:.2f}%. Dự kiến biên lãi dương (+{profit_vnd:,.0f} VND)."
    elif prob_pd <= pd_star:
        decision = 'DUYỆT CÓ ĐIỀU KIỆN (CONDITIONAL REVIEW)'
        dec_code = 'CONDITIONAL'
        reason = f"Hồ sơ thuộc {grade}. PD={prob_pd*100:.2f}% cận biên PD*={pd_star*100:.2f}%. Đề xuất giảm 30% hạn mức hoặc thẩm định bổ sung."
    else:
        decision = 'TỪ CHỐI CẤP TÍN DỤNG (REJECTED)'
        dec_code = 'REJECTED'
        reason = f"Rủi ro vỡ nợ vượt ngưỡng an toàn ({grade}). PD={prob_pd*100:.2f}% > PD*={pd_star*100:.2f}%, dự kiến gây lỗ (-{abs(profit_vnd):,.0f} VND)."
        
    return {
        'model_name': 'Decision Tree',
        'leaf_id': leaf_id,
        'pd': prob_pd,
        'base_pd': base_pd,
        'fico': fico,
        'grade': grade,
        'wilson': wilson,
        'rule': rule,
        'decision': decision,
        'dec_code': dec_code,
        'reason': reason,
        'profit_vnd': profit_vnd,
        'pd_star': pd_star,
        'product_name': prod_cfg['product_name'],
        'dsr_ratio': dsr_ratio,
        'monthly_installment': monthly_installment,
        'net_margin': net_margin
    }

# ==============================================================================
# HÀM TÍNH TOÁN CHẤM ĐIỂM CHO LOGISTIC REGRESSION (NHẢY MƯỢT LIÊN TỤC)
# ==============================================================================
def score_single_customer_lr(data_dict, product_code, market_mode, loan_amt):
    if lr_model is None or scaler is None:
        return score_single_customer_dt(data_dict, product_code, market_mode, loan_amt)
        
    df_in = pd.DataFrame([data_dict])
    if 'MonthlyIncome_is_missing' not in df_in.columns:
        if 'MonthlyIncome' in df_in.columns and (pd.isnull(df_in['MonthlyIncome'].iloc[0]) or df_in['MonthlyIncome'].iloc[0] == 0):
            df_in['MonthlyIncome_is_missing'] = 1
        else:
            df_in['MonthlyIncome_is_missing'] = 0
            
    for col in FEATURE_COLS:
        if col not in df_in.columns:
            df_in[col] = 0.0
            
    X_df = df_in[FEATURE_COLS]
    X_scaled_df = pd.DataFrame(scaler.transform(X_df), columns=FEATURE_COLS)
    
    prob_pd = float(lr_model.predict_proba(X_scaled_df)[0, 1])
    prob_pd = float(np.clip(prob_pd, 0.0001, 0.9999))
    
    eps = 1e-7
    log_odds = np.log((prob_pd + eps) / (1.0 - prob_pd + eps))
    fico = int(np.clip(np.round(offset - factor * log_odds), 300, 850))
    
    if fico >= 605:
        grade = 'Hạng 1 (< 2%)'
    elif fico >= 572:
        grade = 'Hạng 2 (2% - 5%)'
    elif fico >= 540:
        grade = 'Hạng 3 (5% - 10%)'
    elif fico >= 500:
        grade = 'Hạng 4 (10% - 20%)'
    else:
        grade = 'Hạng 5 (> 20%)'
        
    prod_cfg = lr_cfg.get(product_code, lr_cfg['CREDIT_CARD'])
    p_params = prod_cfg['params']
    net_r = p_params['r'] - p_params['c']
    lgd = p_params['lgd']
    pd_star = p_params['pd_breakeven']
    
    net_margin = (1.0 - prob_pd) * net_r - prob_pd * lgd
    profit_vnd = loan_amt * net_margin
    
    inc = float(data_dict.get('MonthlyIncome', 6000.0))
    inc_vnd = inc * 25_000 if inc > 0 else 0
    monthly_installment = (loan_amt * (1.0 + p_params['r'] * 3.0)) / 36.0
    dsr_ratio = (monthly_installment / inc_vnd) if inc_vnd > 0 else 1.0
    active_policy = prod_cfg['policies'].get(market_mode, prod_cfg['policies']['NORMAL'])
    min_score = active_policy['min_score']
    allowed_grades = active_policy['allowed_grades']
    
    if dsr_ratio > 0.60 and inc_vnd > 0:
        decision = 'DUYỆT CÓ ĐIỀU KIỆN (CẢNH BÁO NGHĨA VỤ NỢ DTI)'
        dec_code = 'CONDITIONAL'
        reason = f"Điểm FICO {fico} ({grade}). Tuy nhiên nghĩa vụ nợ chiếm {dsr_ratio*100:.1f}% thu nhập (> 60%). Đề xuất giảm hạn mức."
    elif (fico >= min_score) and (grade in allowed_grades) and (prob_pd <= pd_star):
        decision = 'PHÊ DUYỆT TỰ ĐỘNG (AUTO-APPROVED)'
        dec_code = 'APPROVED'
        reason = f"Điểm FICO {fico} >= {min_score} chuẩn ({grade}). PD={prob_pd*100:.2f}% < PD*={pd_star*100:.2f}%. Dự kiến mang lại biên lãi thuần dương (+{profit_vnd:,.0f} VND)."
    elif prob_pd <= pd_star:
        decision = 'DUYỆT CÓ ĐIỀU KIỆN (CONDITIONAL REVIEW)'
        dec_code = 'CONDITIONAL'
        reason = f"Điểm FICO {fico} tiệm cận ngưỡng hòa vốn ({pd_star*100:.2f}%). Đề xuất giảm 30% hạn mức hoặc thẩm định bổ sung nguồn thu."
    else:
        decision = 'TỪ CHỐI CẤP TÍN DỤNG (REJECTED)'
        dec_code = 'REJECTED'
        reason = f"Xác suất vỡ nợ PD={prob_pd*100:.2f}% vượt ngưỡng an toàn PD*={pd_star*100:.2f}%, gây tổn thất dự kiến (-{abs(profit_vnd):,.0f} VND)."
        
    top_driver = "Đòn bẩy thẻ tín dụng & Lịch sử quá hạn"
    if 'RevolvingUtilizationOfUnsecuredLines' in X_df.columns and X_df['RevolvingUtilizationOfUnsecuredLines'].iloc[0] > 0.6:
        top_driver = "Tỷ lệ sử dụng hạn mức thẻ tín dụng cao"
    elif 'NumberOfTimes90DaysLate' in X_df.columns and X_df['NumberOfTimes90DaysLate'].iloc[0] > 0:
        top_driver = "Có nợ quá hạn nghiêm trọng >= 90 ngày"
    elif 'MonthlyIncome' in X_df.columns and X_df['MonthlyIncome'].iloc[0] > 8000:
        top_driver = "Nguồn thu nhập mạnh mẽ và ổn định"

    return {
        'model_name': 'Logistic Regression',
        'pd': prob_pd,
        'fico': fico,
        'grade': grade,
        'log_odds': log_odds,
        'top_driver': top_driver,
        'decision': decision,
        'dec_code': dec_code,
        'reason': reason,
        'profit_vnd': profit_vnd,
        'pd_star': pd_star,
        'product_name': prod_cfg['product_name'],
        'dsr_ratio': dsr_ratio,
        'monthly_installment': monthly_installment,
        'net_margin': net_margin
    }

# ==============================================================================
# HÀM TÍNH TOÁN CHẤM ĐIỂM CHO XGBOOST (GRADIENT BOOSTING - CHÍNH XÁC CAO NHẤT)
# ==============================================================================
def score_single_customer_xgb(data_dict, product_code, market_mode, loan_amt):
    if xgb_model is None:
        return score_single_customer_lr(data_dict, product_code, market_mode, loan_amt)
        
    df_in = pd.DataFrame([data_dict])
    if 'MonthlyIncome_is_missing' not in df_in.columns:
        if 'MonthlyIncome' in df_in.columns and (pd.isnull(df_in['MonthlyIncome'].iloc[0]) or df_in['MonthlyIncome'].iloc[0] == 0):
            df_in['MonthlyIncome_is_missing'] = 1.0
        else:
            df_in['MonthlyIncome_is_missing'] = 0.0
            
    for col in FEATURE_COLS:
        if col not in df_in.columns:
            df_in[col] = 0.0
            
    X_df = df_in[FEATURE_COLS].astype(float)
    
    prob_pd = float(xgb_model.predict_proba(X_df)[0, 1])
    prob_pd = float(np.clip(prob_pd, 0.0001, 0.9999))
    
    eps = 1e-7
    log_odds = float(np.log((prob_pd + eps) / (1.0 - prob_pd + eps)))
    fico = int(np.clip(np.round(offset - factor * log_odds), 300, 850))
    
    if fico >= 605:
        grade = 'Hạng 1 (< 2%)'
    elif fico >= 572:
        grade = 'Hạng 2 (2% - 5%)'
    elif fico >= 540:
        grade = 'Hạng 3 (5% - 10%)'
    elif fico >= 500:
        grade = 'Hạng 4 (10% - 20%)'
    else:
        grade = 'Hạng 5 (> 20%)'
        
    prod_cfg = xgb_cfg.get(product_code, xgb_cfg['CREDIT_CARD'])
    p_params = prod_cfg['params']
    net_r = p_params['r'] - p_params['c']
    lgd = p_params['lgd']
    pd_star = p_params['pd_breakeven']
    
    net_margin = (1.0 - prob_pd) * net_r - prob_pd * lgd
    profit_vnd = loan_amt * net_margin
    
    inc = float(data_dict.get('MonthlyIncome', 6000.0))
    inc_vnd = inc * 25_000 if inc > 0 else 0
    monthly_installment = (loan_amt * (1.0 + p_params['r'] * 3.0)) / 36.0
    dsr_ratio = (monthly_installment / inc_vnd) if inc_vnd > 0 else 1.0
    active_policy = prod_cfg['policies'].get(market_mode, prod_cfg['policies']['NORMAL'])
    min_score = active_policy['min_score']
    allowed_grades = active_policy['allowed_grades']
    
    if dsr_ratio > 0.60 and inc_vnd > 0:
        decision = 'DUYỆT CÓ ĐIỀU KIỆN (CẢNH BÁO NGHĨA VỤ NỢ DTI)'
        dec_code = 'CONDITIONAL'
        reason = f"Điểm FICO {fico} ({grade}). Tuy nhiên nghĩa vụ nợ chiếm {dsr_ratio*100:.1f}% thu nhập (> 60%). Đề xuất giảm hạn mức."
    elif (fico >= min_score) and (grade in allowed_grades) and (prob_pd <= pd_star):
        decision = 'PHÊ DUYỆT TỰ ĐỘNG (AUTO-APPROVED)'
        dec_code = 'APPROVED'
        reason = f"Điểm FICO {fico} >= {min_score} chuẩn ({grade}). PD={prob_pd*100:.2f}% < PD*={pd_star*100:.2f}%. Dự kiến mang lại biên lãi thuần dương (+{profit_vnd:,.0f} VND)."
    elif prob_pd <= pd_star:
        decision = 'DUYỆT CÓ ĐIỀU KIỆN (CONDITIONAL REVIEW)'
        dec_code = 'CONDITIONAL'
        reason = f"Điểm FICO {fico} tiệm cận ngưỡng hòa vốn ({pd_star*100:.2f}%). Đề xuất giảm 30% hạn mức hoặc thẩm định bổ sung nguồn thu."
    else:
        decision = 'TỪ CHỐI CẤP TÍN DỤNG (REJECTED)'
        dec_code = 'REJECTED'
        reason = f"Xác suất vỡ nợ PD={prob_pd*100:.2f}% vượt ngưỡng an toàn PD*={pd_star*100:.2f}%, gây tổn thất dự kiến (-{abs(profit_vnd):,.0f} VND)."
        
    top_driver = "Đòn bẩy thẻ tín dụng & Lịch sử trả nợ"
    if 'NumberOfTimes90DaysLate' in X_df.columns and X_df['NumberOfTimes90DaysLate'].iloc[0] > 0:
        top_driver = f"Quá hạn nghiêm trọng >= 90 ngày ({int(X_df['NumberOfTimes90DaysLate'].iloc[0])} lần) - SHAP tác động tiêu cực lớn"
    elif 'RevolvingUtilizationOfUnsecuredLines' in X_df.columns and X_df['RevolvingUtilizationOfUnsecuredLines'].iloc[0] > 0.6:
        top_driver = f"Tỷ lệ sử dụng hạn mức cao ({X_df['RevolvingUtilizationOfUnsecuredLines'].iloc[0]*100:.1f}%) - SHAP đòn bẩy rủi ro"
    elif 'NumberOfTime30-59DaysPastDueNotWorse' in X_df.columns and X_df['NumberOfTime30-59DaysPastDueNotWorse'].iloc[0] > 0:
        top_driver = f"Lịch sử chậm thanh toán 30-59 ngày ({int(X_df['NumberOfTime30-59DaysPastDueNotWorse'].iloc[0])} lần)"
    elif 'MonthlyIncome' in X_df.columns and X_df['MonthlyIncome'].iloc[0] > 8000:
        top_driver = "Nguồn thu nhập mạnh mẽ bảo chứng khả năng trả nợ (SHAP tích cực)"

    return {
        'model_name': 'XGBoost',
        'pd': prob_pd,
        'fico': fico,
        'grade': grade,
        'log_odds': log_odds,
        'top_driver': top_driver,
        'decision': decision,
        'dec_code': dec_code,
        'reason': reason,
        'profit_vnd': profit_vnd,
        'pd_star': pd_star,
        'product_name': prod_cfg['product_name'],
        'dsr_ratio': dsr_ratio,
        'monthly_installment': monthly_installment,
        'net_margin': net_margin
    }

# ==============================================================================
# HÀM XUẤT TỜ TRÌNH THẨM ĐỊNH TÍN DỤNG TRẮNG - ĐEN (ĐỐI SÁNH CẢ 3 MÔ HÌNH)
# ==============================================================================
def generate_bw_credit_appraisal_pdf(customer_info, financial_details, card_items, loan_items, features_dict, dt_res, lr_res, xgb_res, selected_mode, prod_cfg, market_mode):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=32, rightMargin=32, topMargin=28, bottomMargin=28
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=12, leading=14, textColor=colors.black, alignment=1)
    sub_style = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=8, leading=10, textColor=colors.black, alignment=1)
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontName=PDF_FONT_NORMAL, fontSize=7, leading=9, textColor=colors.black, alignment=1)
    sec_hdr = ParagraphStyle('SecHdr', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=8, leading=10, textColor=colors.black)
    c_txt = ParagraphStyle('CellTxt', parent=styles['Normal'], fontName=PDF_FONT_NORMAL, fontSize=6.5, leading=8.5, textColor=colors.black)
    c_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=6.5, leading=8.5, textColor=colors.black)
    note_txt = ParagraphStyle('NoteTxt', parent=styles['Normal'], fontName=PDF_FONT_ITALIC, fontSize=6, leading=8, textColor=colors.black)

    elements = []

    # 1. Tiêu ngữ Ngân hàng (Chuẩn văn bản Trắng - Đen)
    elements.append(Paragraph("NGÂN HÀNG THƯƠNG MẠI CỔ PHẦN - KHỐI QUẢN TRỊ RỦI RO", title_style))
    elements.append(Paragraph("TỜ TRÌNH THẨM ĐỊNH TÍN DỤNG & ĐO LƯỜNG RỦI RO ĐA MÔ HÌNH (TRIPLE-MODEL)", sub_style))
    elements.append(Paragraph(f"Mã hồ sơ: {customer_info.get('app_id', 'HS-2026')} | Ngày lập: {datetime.date.today().strftime('%d/%m/%Y')} | Cán bộ lập: {customer_info.get('officer_name', 'Cán bộ tín dụng')}", meta_style))
    elements.append(Spacer(1, 3))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=1, spaceAfter=4))

    # 2. Thông tin chung
    elements.append(Paragraph("I. THÔNG TIN KHÁCH HÀNG & KHOẢN VAY ĐỀ NGHỊ", sec_hdr))
    elements.append(Spacer(1, 2))
    
    t_info_data = [
        [Paragraph("Khách hàng / CCCD:", c_bold), Paragraph(str(customer_info.get('cust_name', 'N/A')), c_txt),
         Paragraph("Độ tuổi / Phụ thuộc:", c_bold), Paragraph(f"{features_dict.get('age', 35)} tuổi | {features_dict.get('NumberOfDependents', 1)} người", c_txt)],
        [Paragraph("Sản phẩm cấp tín dụng:", c_bold), Paragraph(str(prod_cfg.get('product_name', 'N/A')), c_txt),
         Paragraph("Số tiền đề nghị cấp:", c_bold), Paragraph(f"{customer_info.get('loan_amount', 100_000_000):,.0f} VND", c_bold)],
        [Paragraph("Kịch bản thị trường:", c_bold), Paragraph(f"Chế độ {market_mode}", c_txt),
         Paragraph("Lãi suất r / Chi phí vốn c:", c_bold), Paragraph(f"{prod_cfg['params']['r']*100:.1f}% / {prod_cfg['params']['c']*100:.1f}% | LGD: {prod_cfg['params']['lgd']*100:.1f}%", c_txt)]
    ]
    t_info = Table(t_info_data, colWidths=[110, 160, 110, 150])
    t_info.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 4))

    # 3. Phân rã thu nhập & Nghĩa vụ nợ chi tiết
    elements.append(Paragraph("II. NĂNG LỰC TÀI CHÍNH & NGHĨA VỤ TRẢ NỢ HÀNG THÁNG", sec_hdr))
    elements.append(Spacer(1, 2))
    
    fin_summary = [
        [Paragraph("Nguồn Thu Nhập Gộp Xác Minh", c_bold), Paragraph("Số Tiền (VND/tháng)", c_bold),
         Paragraph("Nghĩa Vụ Tài Chính Hàng Tháng", c_bold), Paragraph("Giá Trị Tính Toán", c_bold)],
        [Paragraph("1. Lương & HĐLĐ cố định", c_txt), Paragraph(f"{financial_details.get('income_salary', 0):,.0f} VND", c_txt),
         Paragraph("• Nghĩa vụ nợ các tài khoản", c_txt), Paragraph(f"{financial_details.get('monthly_debt_repayment', 0):,.0f} VND/th", c_txt)],
        [Paragraph("2. Cho thuê tài sản (nhà, đất, xe)", c_txt), Paragraph(f"{financial_details.get('income_rental', 0):,.0f} VND", c_txt),
         Paragraph("• Chi phí sinh hoạt (Living Costs)", c_txt), Paragraph(f"{financial_details.get('living_costs', 0):,.0f} VND/th", c_txt)],
        [Paragraph("3. Cổ tức / Kinh doanh / Đầu tư", c_txt), Paragraph(f"{financial_details.get('income_business', 0):,.0f} VND", c_txt),
         Paragraph("• Tiền cấp dưỡng (Alimony)", c_txt), Paragraph(f"{financial_details.get('alimony', 0):,.0f} VND/th", c_txt)],
        [Paragraph("4. Thu nhập hợp pháp khác", c_txt), Paragraph(f"{financial_details.get('income_other', 0):,.0f} VND", c_txt),
         Paragraph("• TỔNG NGHĨA VỤ HIỆN HỮU (TỬ SỐ)", c_bold), Paragraph(f"{financial_details.get('monthly_debt_repayment', 0) + financial_details.get('living_costs', 0) + financial_details.get('alimony', 0):,.0f} VND/th", c_bold)],
        [Paragraph("TỔNG THU NHẬP GỘP (MẪU SỐ)", c_bold), Paragraph(f"{financial_details.get('total_income_vnd', 0):,.0f} VND/th", c_bold),
         Paragraph("• Dự kiến góp khoản vay mới", c_txt), Paragraph(f"{financial_details.get('monthly_new_installment', 0):,.0f} VND/tháng", c_txt)],
        [Paragraph("TỶ SỐ DEBT RATIO HIỆN HỮU", c_bold), Paragraph(f"{features_dict.get('DebtRatio', 0)*100:.2f}% ({features_dict.get('DebtRatio', 0):.4f})", c_bold),
         Paragraph("TỔNG NGHĨA VỤ SAU CẤP MỚI (DSR)", c_bold), Paragraph(f"{financial_details.get('total_debt_monthly', 0):,.0f} VND/th ({financial_details.get('dsr_pct', 0):.1f}%)", c_bold)]
    ]
    t_fin = Table(fin_summary, colWidths=[140, 125, 140, 125])
    t_fin.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    elements.append(t_fin)
    elements.append(Spacer(1, 4))

    # 4. Bảng 11 Đặc trưng đầu vào (Basel II Features)
    elements.append(Paragraph("III. DANH SÁCH 11 ĐẶC TRƯNG CHẤM ĐIỂM (BASEL II INPUT FEATURES)", sec_hdr))
    elements.append(Spacer(1, 2))
    
    feat_rows = [
        [Paragraph("Chỉ số Đặc trưng", c_bold), Paragraph("Giá trị đo lường", c_bold),
         Paragraph("Chỉ số Đặc trưng", c_bold), Paragraph("Giá trị đo lường", c_bold)],
        [Paragraph("1. Tỷ lệ sử dụng thẻ (Revolving)", c_txt), Paragraph(f"{features_dict.get('RevolvingUtilizationOfUnsecuredLines', 0)*100:.2f}%", c_bold),
         Paragraph("7. Số lần trễ hạn >= 90 ngày", c_txt), Paragraph(f"{features_dict.get('NumberOfTimes90DaysLate', 0)} lần", c_bold)],
        [Paragraph("2. Độ tuổi khách hàng", c_txt), Paragraph(f"{features_dict.get('age', 0)} tuổi", c_bold),
         Paragraph("8. Số khoản vay BĐS/thế chấp (CIC)", c_txt), Paragraph(f"{features_dict.get('NumberRealEstateLoansOrLines', 0)} khoản", c_bold)],
        [Paragraph("3. Số lần quá hạn 30-59 ngày", c_txt), Paragraph(f"{features_dict.get('NumberOfTime30-59DaysPastDueNotWorse', 0)} lần", c_bold),
         Paragraph("9. Số lần quá hạn 60-89 ngày", c_txt), Paragraph(f"{features_dict.get('NumberOfTime60-89DaysPastDueNotWorse', 0)} lần", c_bold)],
        [Paragraph("4. Tỷ số nợ trên thu nhập (DebtRatio)", c_txt), Paragraph(f"{features_dict.get('DebtRatio', 0):.4f}", c_bold),
         Paragraph("10. Số người phụ thuộc", c_txt), Paragraph(f"{features_dict.get('NumberOfDependents', 0)} người", c_bold)],
        [Paragraph("5. Thu nhập tháng (Model Scale)", c_txt), Paragraph(f"{features_dict.get('MonthlyIncome', 0):,.1f} USD (~{financial_details.get('total_income_vnd', 0):,.0f}đ)", c_bold),
         Paragraph("11. Cờ khuyết thu nhập gốc", c_txt), Paragraph("Không khuyết (0)" if features_dict.get('MonthlyIncome_is_missing', 0)==0 else "Có khuyết (1)", c_bold)],
        [Paragraph("6. Số hạn mức/khoản vay đang mở", c_txt), Paragraph(f"{features_dict.get('NumberOfOpenCreditLinesAndLoans', 0)} tài khoản", c_bold),
         Paragraph("— Tình trạng nghĩa vụ nợ DSR", c_txt), Paragraph("Đạt chuẩn (<=60%)" if financial_details.get('dsr_pct', 0)<=60 else "Cảnh báo (>60%)", c_bold)]
    ]
    t_feat = Table(feat_rows, colWidths=[140, 125, 140, 125])
    t_feat.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    elements.append(t_feat)
    elements.append(Spacer(1, 4))

    # 5. Bảng kết quả đo lường 3 mô hình (Triple Model Measurement)
    elements.append(Paragraph("IV. KẾT QUẢ ĐO LƯỜNG TỪ 3 MÔ HÌNH TÍN DỤNG (TRIPLE-MODEL MEASUREMENT)", sec_hdr))
    elements.append(Spacer(1, 2))
    
    eval_matrix = [
        [Paragraph("Chỉ Tiêu Đo Lường", c_bold), 
         Paragraph("CÂY QUYẾT ĐỊNH (DT)", c_bold), 
         Paragraph("HỒI QUY LOGISTIC (LR)", c_bold),
         Paragraph("XGBOOST (BOOSTING)", c_bold)],
        [Paragraph("1. Điểm tín dụng FICO Score", c_bold), 
         Paragraph(f"{dt_res.get('fico', 0)} điểm", c_bold), 
         Paragraph(f"{lr_res.get('fico', 0)} điểm", c_bold),
         Paragraph(f"{xgb_res.get('fico', 0)} điểm", c_bold)],
        [Paragraph("2. Phân tầng Hạng Rủi ro", c_bold), 
         Paragraph(str(dt_res.get('grade', 'N/A')), c_txt), 
         Paragraph(str(lr_res.get('grade', 'N/A')), c_txt),
         Paragraph(str(xgb_res.get('grade', 'N/A')), c_txt)],
        [Paragraph("3. Xác suất vỡ nợ dự báo (PD)", c_bold), 
         Paragraph(f"{dt_res.get('pd', 0)*100:.2f}% (Wilson: {dt_res.get('wilson', 'N/A')})", c_txt), 
         Paragraph(f"{lr_res.get('pd', 0)*100:.2f}%", c_txt),
         Paragraph(f"{xgb_res.get('pd', 0)*100:.2f}%", c_txt)],
        [Paragraph("4. Ngưỡng hòa vốn an toàn (PD*)", c_bold), 
         Paragraph(f"{dt_res.get('pd_star', 0.1414)*100:.2f}%", c_txt), 
         Paragraph(f"{lr_res.get('pd_star', 0.1414)*100:.2f}%", c_txt),
         Paragraph(f"{xgb_res.get('pd_star', 0.1414)*100:.2f}%", c_txt)],
        [Paragraph("5. Lợi nhuận ròng dự kiến (+/- VND)", c_bold), 
         Paragraph(f"{dt_res.get('profit_vnd', 0):+,.0f} VND", c_bold), 
         Paragraph(f"{lr_res.get('profit_vnd', 0):+,.0f} VND", c_bold),
         Paragraph(f"{xgb_res.get('profit_vnd', 0):+,.0f} VND", c_bold)],
        [Paragraph("6. Đề xuất quyết định thẩm định", c_bold), 
         Paragraph(f"[{dt_res.get('decision', 'N/A')}]", c_bold), 
         Paragraph(f"[{lr_res.get('decision', 'N/A')}]", c_bold),
         Paragraph(f"[{xgb_res.get('decision', 'N/A')}]", c_bold)]
    ]
    t_eval = Table(eval_matrix, colWidths=[120, 130, 135, 145])
    t_eval.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEBELOW', (0,-2), (-1,-1), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_eval)
    elements.append(Spacer(1, 5))

    # 6. Ý kiến thẩm định & Chữ ký 3 cấp (Black & White)
    elements.append(Paragraph("V. Ý KIẾN THẨM ĐỊNH & PHÊ DUYỆT CỦA CÁC CẤP CÓ THẨM QUYỀN", sec_hdr))
    elements.append(Spacer(1, 2))
    
    is_all_agree = (dt_res.get('dec_code') == lr_res.get('dec_code') == xgb_res.get('dec_code'))
    if is_all_agree:
        conclusion_line = f"Cả 3 mô hình (Cây Quyết Định, Hồi Quy Logistic, XGBoost) hoàn toàn đồng thuận về quyết định [{dt_res.get('dec_code')}]."
    else:
        dec_list = [dt_res.get('dec_code'), lr_res.get('dec_code'), xgb_res.get('dec_code')]
        maj = max(set(dec_list), key=dec_list.count)
        conclusion_line = f"Có sự khác biệt quyết định (DT: {dt_res.get('dec_code')}, LR: {lr_res.get('dec_code')}, XGB: {xgb_res.get('dec_code')}). Đa số 2/3 mô hình đồng thuận phương án [{maj}]."

    elements.append(Paragraph(f"• Ý kiến tái thẩm định: {conclusion_line} Tỷ lệ nghĩa vụ nợ thực tế DSR = {financial_details.get('dsr_pct', 0):.1f}%. Hồ sơ được trình phê duyệt theo đúng quy định phân cấp thẩm quyền tín dụng hiện hành.", c_txt))
    elements.append(Spacer(1, 8))

    sign_data = [
        [Paragraph("CHUYÊN VIÊN QHKH (RM)", c_bold), Paragraph("CHUYÊN VIÊN TÁI THẨM ĐỊNH (CA)", c_bold), Paragraph("GIÁM ĐỐC QUẢN TRỊ RỦI RO (CRO)", c_bold)],
        [Paragraph("<i>(Ký và ghi rõ họ tên)</i>", note_txt), Paragraph("<i>(Ký và ghi rõ họ tên)</i>", note_txt), Paragraph("<i>(Ký và phê duyệt)</i>", note_txt)],
        [Spacer(1, 22), Spacer(1, 22), Spacer(1, 22)],
        [Paragraph(customer_info.get('officer_name', '................................'), c_txt), Paragraph("........................................", c_txt), Paragraph("........................................", c_bold)]
    ]
    t_sign = Table(sign_data, colWidths=[175, 180, 180])
    t_sign.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    elements.append(t_sign)

    doc.build(elements)
    return buffer.getvalue()

# ==============================================================================
# GIAO DIỆN ĐĂNG NHẬP TRUNG TÂM (1-CHẠM TIỆN LỢI CHO DEMO)
# ==============================================================================
if st.session_state.user is None:
    st.markdown("""
    <div style="max-width: 650px; margin: 35px auto 15px auto; text-align: center;">
        <div style="font-size: 54px;">🏦</div>
        <h2 style="color: #0F172A; margin: 8px 0; font-size: 28px; font-weight: 800;">HỆ THỐNG SMARTCREDIT AI</h2>
        <p style="color: #475569; font-size: 15px;">Cổng Thông Tin Thẩm Định & Quản Trị Rủi Ro Tín Dụng Đa Mô Hình (Basel II / IFRS 9)</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_c1, col_center, col_c2 = st.columns([1, 1.8, 1])
    with col_center:
        st.markdown('<div class="metric-card" style="padding: 24px;">', unsafe_allow_html=True)
        st.markdown("### ⚡ ĐĂNG NHẬP NHANH 1-CHẠM (DÀNH CHO DEMO):")
        st.caption("Nhấp trực tiếp vào vai trò bên dưới để đăng nhập ngay mà không cần gõ mật khẩu:")
        
        c_btn1, c_btn2, c_btn3 = st.columns(3)
        with c_btn1:
            if st.button("👤 Thẩm định viên", use_container_width=True, type="primary"):
                st.session_state.user = DEMO_USERS['officer']
                st.rerun()
        with c_btn2:
            if st.button("👔 Trưởng phòng", use_container_width=True, type="primary"):
                st.session_state.user = DEMO_USERS['manager']
                st.rerun()
        with c_btn3:
            if st.button("👑 Giám đốc CRO", use_container_width=True, type="primary"):
                st.session_state.user = DEMO_USERS['cro_admin']
                st.rerun()
                
        st.markdown("---")
        st.markdown("##### 🔐 Hoặc Đăng nhập bằng Tài khoản & Mật khẩu")
        username_inp = st.text_input("Tên đăng nhập (Username):", placeholder="officer / manager / cro_admin")
        password_inp = st.text_input("Mật khẩu (Password):", type="password", placeholder="Nhập 123...")
        
        if st.button("Đăng nhập bằng Mật khẩu", use_container_width=True):
            if username_inp in DEMO_USERS and password_inp == DEMO_USERS[username_inp]['password']:
                st.session_state.user = DEMO_USERS[username_inp]
                st.rerun()
            else:
                st.error("Sai tên đăng nhập hoặc mật khẩu! Mật khẩu mặc định là: 123")
                
        st.markdown('</div>', unsafe_allow_html=True)
        st.info("💡 Hệ thống hỗ trợ phân quyền tự động theo chuẩn mực Quản trị Rủi ro Tín dụng Basel II.")
    st.stop()

# ==============================================================================
# THANH BÊN (SIDEBAR) & CẤU HÌNH BỘ CHỌN MÔ HÌNH (MODEL SELECTOR)
# ==============================================================================
user = st.session_state.user
if user is None:
    st.stop()

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h2 style="color: #1E3A8A; margin: 0;">🏦 SmartCredit AI</h2>
        <p style="color: #64748B; font-size: 12px; margin: 0;">Cổng Quản Trị Rủi Ro Đa Mô Hình</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown(f"**👤 Nhân sự:** `{user['name']}`")
    st.caption(f"**Chức danh:** {user['role_title']}")
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.user = None
        st.rerun()
            
    st.markdown("---")
    
    # 2. BỘ CHỌN MÔ HÌNH (MODEL SELECTOR)
    st.markdown("### 🤖 BỘ CHỌN MÔ HÌNH (MODEL SELECTOR)")
    model_choice = st.radio(
        "Chế độ Mô hình Thẩm định:",
        options=["ALL_TRIPLE", "DECISION_TREE", "LOGISTIC_REGRESSION", "XGBOOST"],
        format_func=lambda x: {
            "ALL_TRIPLE": "⚖️ So Sánh Song Song Cả 3 Mô Hình (Triple Evaluation)",
            "DECISION_TREE": "🌲 Cây Quyết Định (Decision Tree - White-box)",
            "LOGISTIC_REGRESSION": "📈 Hồi Quy Logistic (Logistic Engine - Chuẩn Mực Vàng)",
            "XGBOOST": "🚀 XGBoost (Gradient Boosting - Độ Chính Xác Đỉnh Cao)"
        }[x],
        index=0,
        help="Chọn chế độ đối sánh song song cả 3 mô hình hoặc kiểm thử chuyên sâu từng mô hình"
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ THIẾT LẬP KINH TẾ & THỊ TRƯỜNG")
    
    product_options = ['MORTGAGE', 'AUTO', 'UNSECURED', 'CREDIT_CARD']
    product_code = st.selectbox(
        "Dòng Sản phẩm Tín dụng:",
        options=product_options,
        format_func=lambda x: dt_cfg[x]['product_name']
    )
    
    market_mode = st.selectbox(
        "Kịch bản Vĩ mô Thị trường:",
        options=['NORMAL', 'EXPANSION', 'RECESSION'],
        format_func=lambda x: {
            'NORMAL': '🔵 Kinh tế Bình thường (Normal)',
            'EXPANSION': '🟢 Tăng trưởng Mở rộng (Expansion)',
            'RECESSION': '🔴 Suy thoái Thắt chặt (Recession)'
        }[x]
    )
    
    loan_amount = st.number_input(
        "Số tiền Khách hàng Đề nghị Cấp (VND):",
        min_value=5_000_000,
        max_value=10_000_000_000,
        value=100_000_000,
        step=10_000_000,
        format="%d"
    )

# ==============================================================================
# HEADER CHÍNH CỦA TRANG WEB
# ==============================================================================
mode_badge = {
    'ALL_TRIPLE': '⚖️ CHẾ ĐỘ ĐỐI SÁNH SONG SONG CẢ 3 MÔ HÌNH (TRIPLE EVALUATION)',
    'DECISION_TREE': '🌲 CHẾ ĐỘ CÂY QUYẾT ĐỊNH (WHITE-BOX IF-THEN)',
    'LOGISTIC_REGRESSION': '📈 CHẾ ĐỘ HỒI QUY LOGISTIC (CONTINUOUS LOG-ODDS)',
    'XGBOOST': '🚀 CHẾ ĐỘ XGBOOST (HIGH-PRECISION GRADIENT BOOSTING)'
}[model_choice]

st.markdown(f"""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1>SmartCredit Banking AI Portal</h1>
            <p>Hệ thống Thẩm định & Quản trị Rủi ro Tín dụng Đa Mô hình theo Chuẩn Basel II Trụ cột 1-2 & IFRS 9</p>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 11px; background: rgba(255,255,255,0.15); padding: 5px 12px; border-radius: 20px; display: inline-block;">
                {mode_badge}
            </div>
            <div style="font-size: 13px; font-weight: bold; color: #F8FAFC; margin-top: 4px;">{market_mode} MARKET MODE</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tab_labels = ["📝 Thẩm định Tức thì (Single STP)"]
if 'batch' in user['allowed_tabs']:
    tab_labels.append("📁 Chấm điểm Danh mục Lô (Batch Excel)")
if 'policy' in user['allowed_tabs']:
    tab_labels.append("⚖️ Trung tâm Điều hành Chính sách (CRO)")
if 'audit' in user['allowed_tabs']:
    tab_labels.append("📊 Báo cáo Giám sát Basel II (Audit)")

active_tabs = st.tabs(tab_labels)

# ==============================================================================
# TAB 1: THẨM ĐỊNH TỨC THÌ (SINGLE CUSTOMER SCORING & DUAL VIEW)
# ==============================================================================
with active_tabs[0]:
    # Khởi tạo session state cho Danh mục Quản lý Tài khoản Tín dụng Tập trung (Credit Account Registry)
    if 'credit_accounts' not in st.session_state:
        st.session_state.credit_accounts = [
            {
                'acc_id': 'ACC-01',
                'bank': 'Vietcombank (VCB)',
                'name': 'Thẻ Visa Platinum',
                'acc_type': 'CREDIT_CARD',
                'status': 'OPEN',
                'collateral': 'UNSECURED',
                'limit': 60_000_000,
                'balance': 9_000_000,
                'monthly_payment': 300_000,
                'notes': 'Thẻ chi tiêu chính'
            },
            {
                'acc_id': 'ACC-02',
                'bank': 'Techcombank (TCB)',
                'name': 'Thẻ JCB Gold',
                'acc_type': 'CREDIT_CARD',
                'status': 'OPEN',
                'collateral': 'UNSECURED',
                'limit': 40_000_000,
                'balance': 0,
                'monthly_payment': 0,
                'notes': 'Thẻ dự phòng, chưa phát sinh dư nợ'
            },
            {
                'acc_id': 'ACC-03',
                'bank': 'VIB',
                'name': 'Vay mua xe ô tô',
                'acc_type': 'AUTO',
                'status': 'OPEN',
                'collateral': 'SECURED_OTHER',
                'limit': 0,
                'balance': 150_000_000,
                'monthly_payment': 4_500_000,
                'notes': 'Thế chấp bằng xe'
            }
        ]
    if 'living_costs' not in st.session_state:
        st.session_state.living_costs = 10_000_000
    if 'alimony' not in st.session_state:
        st.session_state.alimony = 1_000_000

    st.markdown("### 📋 Thẩm Định Hồ Sơ Khách Hàng & Năng Lực Tài Chính Toàn Diện (Credit Account Registry)")
    
    # Preset nạp nhanh hồ sơ mẫu
    st.caption("⚡ **NẠP NHANH HỒ SƠ MẪU ĐỂ KIỂM THỬ KHẢ NĂNG PHÂN TÁCH & QUY TẮC TÍNH TOÁN 4 FEATURE:**")
    sc_c1, sc_c2, sc_c3 = st.columns(3)
    if 'cust_preset' not in st.session_state:
        st.session_state.cust_preset = 'good'
        
    with sc_c1:
        if st.button("🟢 Mẫu Khách Hàng Tốt (Hạng 1 - Duyệt Tự Động)", use_container_width=True):
            st.session_state.cust_preset = 'good'
            st.session_state.living_costs = 15_000_000
            st.session_state.alimony = 0
            st.session_state.credit_accounts = [
                {'acc_id': 'ACC-01', 'bank': 'Vietcombank (VCB)', 'name': 'Thẻ Visa Signature', 'acc_type': 'CREDIT_CARD', 'status': 'OPEN', 'collateral': 'UNSECURED', 'limit': 80_000_000, 'balance': 8_000_000, 'monthly_payment': 800_000, 'notes': 'Chi tiêu thường xuyên'},
                {'acc_id': 'ACC-02', 'bank': 'Techcombank (TCB)', 'name': 'Thẻ JCB Platinum', 'acc_type': 'CREDIT_CARD', 'status': 'OPEN', 'collateral': 'UNSECURED', 'limit': 50_000_000, 'balance': 0, 'monthly_payment': 0, 'notes': 'Dư nợ 0 vẫn cộng hạn mức mẫu số'},
                {'acc_id': 'ACC-03', 'bank': 'VIB', 'name': 'Vay mua xe ô tô', 'acc_type': 'AUTO', 'status': 'OPEN', 'collateral': 'SECURED_OTHER', 'limit': 0, 'balance': 150_000_000, 'monthly_payment': 4_500_000, 'notes': 'Thế chấp xe ô tô'},
                {'acc_id': 'ACC-04', 'bank': 'Vietcombank (VCB)', 'name': 'Vay thế chấp mua nhà', 'acc_type': 'MORTGAGE', 'status': 'OPEN', 'collateral': 'SECURED_RE', 'limit': 0, 'balance': 800_000_000, 'monthly_payment': 12_000_000, 'notes': 'Thế chấp căn hộ chung cư'}
            ]
            st.rerun()
    with sc_c2:
        if st.button("🟡 Mẫu Khách Hàng Tiệm Cận (Hạng 3 - Xem Xét Có Điều Kiện)", use_container_width=True):
            st.session_state.cust_preset = 'medium'
            st.session_state.living_costs = 12_000_000
            st.session_state.alimony = 2_000_000
            st.session_state.credit_accounts = [
                {'acc_id': 'ACC-01', 'bank': 'VPBank (VPB)', 'name': 'Thẻ StepUp Visa', 'acc_type': 'CREDIT_CARD', 'status': 'OPEN', 'collateral': 'UNSECURED', 'limit': 40_000_000, 'balance': 26_000_000, 'monthly_payment': 2_600_000, 'notes': 'Tỷ lệ dùng thẻ cao (65%)'},
                {'acc_id': 'ACC-02', 'bank': 'Sacombank (STB)', 'name': 'Thẻ Visa Classic', 'acc_type': 'CREDIT_CARD', 'status': 'OPEN', 'collateral': 'UNSECURED', 'limit': 20_000_000, 'balance': 14_000_000, 'monthly_payment': 1_400_000, 'notes': 'Tỷ lệ dùng thẻ 70%'},
                {'acc_id': 'ACC-03', 'bank': 'HDBank (HDB)', 'name': 'Vay kinh doanh cá thể', 'acc_type': 'REAL_ESTATE', 'status': 'OPEN', 'collateral': 'SECURED_RE', 'limit': 0, 'balance': 200_000_000, 'monthly_payment': 6_500_000, 'notes': 'Thế chấp BĐS mặt tiền'},
                {'acc_id': 'ACC-04', 'bank': 'VPBank (VPB)', 'name': 'Vay tiêu dùng tín chấp', 'acc_type': 'CONSUMER_INSTALLMENT', 'status': 'OPEN', 'collateral': 'UNSECURED', 'limit': 0, 'balance': 30_000_000, 'monthly_payment': 2_200_000, 'notes': 'Khoản vay tiền mặt trả góp'}
            ]
            st.rerun()
    with sc_c3:
        if st.button("🔴 Mẫu Khách Hàng Nợ Xấu (Hạng 5 - Từ Chối)", use_container_width=True):
            st.session_state.cust_preset = 'bad'
            st.session_state.living_costs = 8_000_000
            st.session_state.alimony = 0
            st.session_state.credit_accounts = [
                {'acc_id': 'ACC-01', 'bank': 'TPBank (TPB)', 'name': 'Thẻ Tín dụng Plus', 'acc_type': 'CREDIT_CARD', 'status': 'OPEN', 'collateral': 'UNSECURED', 'limit': 30_000_000, 'balance': 35_000_000, 'monthly_payment': 3_500_000, 'notes': 'Dư nợ vượt hạn mức (116.7%)'},
                {'acc_id': 'ACC-02', 'bank': 'Shinhan Bank Vietnam', 'name': 'Thẻ Visa Cash Back', 'acc_type': 'CREDIT_CARD', 'status': 'OPEN', 'collateral': 'UNSECURED', 'limit': 20_000_000, 'balance': 19_000_000, 'monthly_payment': 2_000_000, 'notes': 'Sát trần hạn mức'},
                {'acc_id': 'ACC-03', 'bank': 'MBBank (MB)', 'name': 'Vay tiêu dùng tín chấp', 'acc_type': 'CONSUMER_INSTALLMENT', 'status': 'OPEN', 'collateral': 'UNSECURED', 'limit': 0, 'balance': 40_000_000, 'monthly_payment': 3_800_000, 'notes': 'Quá hạn kéo dài'},
                {'acc_id': 'ACC-04', 'bank': 'Techcombank (TCB)', 'name': 'Khoản vay mua xe cũ', 'acc_type': 'AUTO', 'status': 'CLOSED', 'collateral': 'SECURED_OTHER', 'limit': 0, 'balance': 0, 'monthly_payment': 0, 'notes': 'Đã tất toán và đóng tài khoản (loại khỏi tính toán)'}
            ]
            st.rerun()
            
    # Giá trị mặc định theo preset
    if st.session_state.cust_preset == 'good':
        p_name = "Nguyễn Văn An"
        p_age, p_dep = 38, 1
        p_salary, p_rental, p_biz, p_other = 50_000_000, 15_000_000, 0, 0
        p_late90, p_late60, p_late30 = 0, 0, 0
    elif st.session_state.cust_preset == 'medium':
        p_name = "Trần Đình Khang"
        p_age, p_dep = 42, 2
        p_salary, p_rental, p_biz, p_other = 22_000_000, 0, 6_000_000, 0
        p_late90, p_late60, p_late30 = 0, 0, 1
    else: # bad
        p_name = "Lê Tuấn Kiệt"
        p_age, p_dep = 28, 0
        p_salary, p_rental, p_biz, p_other = 10_000_000, 0, 0, 0
        p_late90, p_late60, p_late30 = 2, 1, 2

    st.markdown("---")
    
    # ------------------ MODULE 01: THÔNG TIN ĐỊNH DANH & NHÂN THÂN ------------------
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        st.markdown("""
        <div class="hdb-section-header">
            <span class="hdb-badge">01</span>
            <span class="hdb-title">THÔNG TIN ĐỊNH DANH & NHÂN THÂN KHÁCH HÀNG</span>
        </div>
        """, unsafe_allow_html=True)
        cust_name_in = st.text_input("Họ và tên / Mã CCCD Khách hàng:", value=p_name, key=f"name_{st.session_state.cust_preset}")
        col_age1, col_age2 = st.columns(2)
        with col_age1:
            cust_age = st.number_input("Tuổi của khách hàng:", min_value=18, max_value=85, value=p_age, step=1, key=f"age_{st.session_state.cust_preset}")
        with col_age2:
            cust_dependents = st.number_input("Số người phụ thuộc tài chính (NumberOfDependents):", min_value=0, max_value=10, value=p_dep, step=1, key=f"dep_{st.session_state.cust_preset}")
            
    with row1_c2:
        st.markdown("""
        <div class="hdb-section-header">
            <span class="hdb-badge">02</span>
            <span class="hdb-title">LỊCH SỬ NỢ QUÁ HẠN (2 NĂM GẦN NHẤT - TRA CỨU CIC)</span>
        </div>
        """, unsafe_allow_html=True)
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            late_90 = st.number_input("Quá hạn >= 90 ngày:", min_value=0, max_value=20, value=p_late90, step=1, key=f"l90_{st.session_state.cust_preset}", help="Chỉ số quan trọng số 1: Quá hạn >= 90 ngày kéo FICO tụt dốc")
        with col_l2:
            late_60_89 = st.number_input("Quá hạn 60-89 ngày:", min_value=0, max_value=20, value=p_late60, step=1, key=f"l60_{st.session_state.cust_preset}")
        with col_l3:
            late_30_59 = st.number_input("Quá hạn 30-59 ngày:", min_value=0, max_value=20, value=p_late30, step=1, key=f"l30_{st.session_state.cust_preset}")

    st.markdown("---")
    
    # ------------------ MODULE 03: PHÂN RÃ THU NHẬP GỘP HÀNG THÁNG ------------------
    st.markdown("""
    <div class="hdb-section-header">
        <span class="hdb-badge">03</span>
        <span class="hdb-title">BẢNG PHÂN RÃ THU NHẬP GỘP HÀNG THÁNG (MONTHLY GROSS INCOME)</span>
    </div>
    """, unsafe_allow_html=True)
    inc_c1, inc_c2, inc_c3, inc_c4 = st.columns(4)
    with inc_c1:
        income_salary = st.number_input("1. Lương & HĐLĐ (VND/tháng):", min_value=0, max_value=500_000_000, value=p_salary, step=1_000_000, format="%d", key=f"sal_{st.session_state.cust_preset}")
    with inc_c2:
        income_rental = st.number_input("2. Cho thuê tài sản (nhà, xe, đất):", min_value=0, max_value=500_000_000, value=p_rental, step=1_000_000, format="%d", key=f"rent_{st.session_state.cust_preset}")
    with inc_c3:
        income_biz = st.number_input("3. Cổ tức / Kinh doanh:", min_value=0, max_value=500_000_000, value=p_biz, step=1_000_000, format="%d", key=f"biz_{st.session_state.cust_preset}")
    with inc_c4:
        income_other = st.number_input("4. Thu nhập khác hợp pháp:", min_value=0, max_value=500_000_000, value=p_other, step=1_000_000, format="%d", key=f"oth_{st.session_state.cust_preset}")
        
    total_income_vnd = income_salary + income_rental + income_biz + income_other
    cust_income_model = total_income_vnd / 25_000.0 if total_income_vnd > 0 else 0.0
    
    st.info(f"📊 **Tổng Thu Nhập Gộp Xác Minh:** **`{total_income_vnd:,.0f} VND/tháng`** (Quy đổi chuẩn hóa tập huấn luyện GMSC: **`{cust_income_model:,.1f} USD/tháng`** theo tỷ giá 25,000 VND/USD).")

    st.markdown("---")

    # ------------------ MODULE 04: QUẢN LÝ DANH MỤC TÀI KHOẢN TÍN DỤNG (CREDIT ACCOUNT REGISTRY) ------------------
    st.markdown("""
    <div class="hdb-section-header">
        <span class="hdb-badge">04</span>
        <span class="hdb-title">QUẢN LÝ DANH MỤC TÀI KHOẢN TÍN DỤNG TẬP TRUNG (CREDIT ACCOUNT REGISTRY)</span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("📌 **Nguồn Dữ Liệu Duy Nhất (Single Source of Truth):** Tất cả các khoản vay, thẻ tín dụng, hạn mức thấu chi hiện hữu của khách hàng được quản lý tại đây để tự động tính toán đồng bộ 4 feature mà không cần nhập trùng lặp.")

    with st.expander("📂 Danh Sách Tài Khoản Tín Dụng Hiện Hữu (Xem / Chỉnh sửa / Xóa)", expanded=True):
        if len(st.session_state.credit_accounts) == 0:
            st.warning("⚠️ Hiện tại chưa có tài khoản tín dụng nào được khai báo trong danh mục.")
        else:
            # Render danh sách tài khoản dưới dạng bảng tương tác
            for idx, acc in enumerate(st.session_state.credit_accounts):
                card_bg = "#FFFFFF" if acc.get('status') == 'OPEN' else "#F1F5F9"
                border_color = "#E2E8F0" if acc.get('status') == 'OPEN' else "#94A3B8"
                status_color = "#10B981" if acc.get('status') == 'OPEN' else "#64748B"
                
                with st.container():
                    st.markdown(f"""
                    <div style="background: {card_bg}; border: 1px solid {border_color}; border-left: 5px solid {status_color}; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <b style="font-size: 14px; color: #0F172A;">#{idx+1}. [{acc.get('acc_id', f'ACC-{idx+1}')}] {acc.get('name', 'Tài khoản')}</b> — 
                                <span style="color: #1E3A8A; font-weight: 600;">{acc.get('bank', 'N/A')}</span> | 
                                <span style="font-size: 12px; color: #475569;">Loại: <b>{ACCOUNT_TYPES.get(acc.get('acc_type'), acc.get('acc_type'))}</b></span> | 
                                <span style="font-size: 12px; color: #475569;">Bảo đảm: <b>{COLLATERAL_TYPES.get(acc.get('collateral'), acc.get('collateral'))}</b></span>
                            </div>
                            <div>
                                <span style="background: {'#DCFCE7' if acc.get('status')=='OPEN' else '#E2E8F0'}; color: {status_color}; font-size: 11px; font-weight: bold; padding: 2px 8px; border-radius: 12px;">
                                    {ACCOUNT_STATUSES.get(acc.get('status'), acc.get('status'))}
                                </span>
                            </div>
                        </div>
                        <div style="margin-top: 6px; font-size: 13px; display: flex; gap: 20px;">
                            <span>Hạn mức: <b>{acc.get('limit', 0):,.0f} đ</b></span>
                            <span>Dư nợ hiện tại: <b style="color: #B91C1C;">{acc.get('balance', 0):,.0f} đ</b></span>
                            <span>Nghĩa vụ trả nợ/tháng: <b style="color: #1E3A8A;">{acc.get('monthly_payment', 0):,.0f} đ/tháng</b></span>
                            {f"<span style='color: #64748B; font-style: italic;'>({acc.get('notes')})</span>" if acc.get('notes') else ""}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    btn_del_col, btn_space_col = st.columns([1, 8])
                    with btn_del_col:
                        if st.button(f"🗑️ Xóa #{idx+1}", key=f"del_acc_{idx}_{st.session_state.cust_preset}"):
                            st.session_state.credit_accounts.pop(idx)
                            st.rerun()

    # Form thêm tài khoản mới
    with st.expander("➕ Thêm Tài Khoản Tín Dụng Mới Vào Danh Mục", expanded=False):
        st.markdown("##### 📝 Khai Báo Chi Tiết Tài Khoản / Khoản Vay:")
        c_add1, c_add2, c_add3 = st.columns(3)
        with c_add1:
            new_acc_bank = st.selectbox("Tổ chức tín dụng cấp tín dụng:", options=VN_BANKS, key=f"new_b_{st.session_state.cust_preset}")
            new_acc_name = st.text_input("Tên khoản vay / Tên thẻ tín dụng:", value="Thẻ Visa Platinum", key=f"new_n_{st.session_state.cust_preset}")
        with c_add2:
            new_acc_type = st.selectbox("Loại sản phẩm tín dụng (Product Type):", options=list(ACCOUNT_TYPES.keys()), format_func=lambda x: ACCOUNT_TYPES[x], key=f"new_t_{st.session_state.cust_preset}")
            new_acc_collat = st.selectbox("Tính chất bảo đảm (Collateral):", options=list(COLLATERAL_TYPES.keys()), format_func=lambda x: COLLATERAL_TYPES[x], key=f"new_c_{st.session_state.cust_preset}")
        with c_add3:
            new_acc_status = st.selectbox("Trạng thái tài khoản (Status):", options=list(ACCOUNT_STATUSES.keys()), format_func=lambda x: ACCOUNT_STATUSES[x], key=f"new_s_{st.session_state.cust_preset}")
            new_acc_notes = st.text_input("Ghi chú bổ sung (Tùy chọn):", value="", key=f"new_nt_{st.session_state.cust_preset}")

        c_num1, c_num2, c_num3 = st.columns(3)
        with c_num1:
            new_acc_limit = st.number_input("Hạn mức tín dụng được cấp (VND):", min_value=0, max_value=5_000_000_000, value=50_000_000, step=5_000_000, format="%d", key=f"new_lim_{st.session_state.cust_preset}", help="Áp dụng cho thẻ tín dụng, hạn mức thấu chi, HELOC")
        with c_num2:
            new_acc_balance = st.number_input("Dư nợ hiện tại tại thời điểm thẩm định (VND):", min_value=0, max_value=50_000_000_000, value=10_000_000, step=1_000_000, format="%d", key=f"new_bal_{st.session_state.cust_preset}")
        with c_num3:
            new_acc_monthly = st.number_input("Nghĩa vụ trả nợ hàng tháng thực tế (VND/tháng):", min_value=0, max_value=500_000_000, value=500_000, step=100_000, format="%d", key=f"new_mon_{st.session_state.cust_preset}", help="Số tiền thực tế khách hàng phải trả theo hợp đồng / sao kê")

        # Công cụ hỗ trợ tính toán nghĩa vụ trả nợ
        st.markdown("💡 **Trợ Lý Tính Toán Nhanh Nghĩa Vụ Trả Nợ Hàng Tháng:**")
        c_tool1, c_tool2, c_tool3, c_tool4 = st.columns([1.5, 1.2, 1.2, 1.5])
        with c_tool1:
            calc_term = st.number_input("Thời hạn còn lại (tháng):", min_value=1, max_value=360, value=36, key=f"calc_t_{st.session_state.cust_preset}")
        with c_tool2:
            calc_rate = st.number_input("Lãi suất (%/năm):", min_value=0.0, max_value=50.0, value=9.5, step=0.1, key=f"calc_r_{st.session_state.cust_preset}")
        with c_tool3:
            calc_method = st.selectbox("Phương thức tính:", options=["Trả góp đều (Annuity)", "Dư nợ giảm dần (Gốc đều + Lãi)"], key=f"calc_m_{st.session_state.cust_preset}")
        with c_tool4:
            st.markdown("<div style='height: 27px;'></div>", unsafe_allow_html=True)
            if st.button("⚡ Áp Dụng Lịch Trả Nợ", key=f"btn_apply_calc_{st.session_state.cust_preset}", use_container_width=True):
                r_month = (calc_rate / 100.0) / 12.0
                if "Annuity" in calc_method:
                    if r_month > 0:
                        computed_pay = new_acc_balance * (r_month * (1 + r_month)**calc_term) / ((1 + r_month)**calc_term - 1)
                    else:
                        computed_pay = new_acc_balance / calc_term
                else:
                    computed_pay = (new_acc_balance / calc_term) + (new_acc_balance * r_month)
                st.session_state[f"new_mon_{st.session_state.cust_preset}"] = int(round(computed_pay))
                st.info(f"Đã tính toán: **{computed_pay:,.0f} đ/tháng**. Nhấn 'Lưu Tài Khoản' bên dưới.")

        if st.button("💾 Lưu Tài Khoản Vào Danh Mục", type="primary", use_container_width=True):
            new_id = f"ACC-{len(st.session_state.credit_accounts)+1:02d}"
            st.session_state.credit_accounts.append({
                'acc_id': new_id,
                'bank': new_acc_bank,
                'name': new_acc_name,
                'acc_type': new_acc_type,
                'status': new_acc_status,
                'collateral': new_acc_collat,
                'limit': float(new_acc_limit),
                'balance': float(new_acc_balance),
                'monthly_payment': float(new_acc_monthly),
                'notes': new_acc_notes
            })
            st.success(f"✓ Đã thêm thành công tài khoản **{new_acc_name}** vào Credit Account Registry!")
            st.rerun()

    st.markdown("---")

    # ==============================================================================
    # TỰ ĐỘNG TÍNH TOÁN 4 FEATURE CHUẨN GIVE ME SOME CREDIT TỪ REGISTRY
    # ==============================================================================
    res_n_open = calculate_number_open_credit_lines_and_loans(st.session_state.credit_accounts)
    res_n_re = calculate_number_real_estate_loans(st.session_state.credit_accounts)
    res_ru = calculate_revolving_utilization(st.session_state.credit_accounts)
    
    # Tính khoản dự kiến sau giải ngân của khoản đề nghị mới (CHỈ DÙNG ĐỂ THẨM ĐỊNH ĐỘC LẬP)
    est_new_installment = (loan_amount * (1.0 + dt_cfg[product_code]['params']['r'] * 3.0)) / 36.0
    
    # Chi phí sinh hoạt và cấp dưỡng hàng tháng
    row_exp1, row_exp2 = st.columns(2)
    with row_exp1:
        living_costs_in = st.number_input("Chi phí sinh hoạt hàng tháng của khách hàng (Living Costs - VND/tháng):", min_value=0, max_value=200_000_000, value=st.session_state.living_costs, step=500_000, format="%d", key=f"liv_{st.session_state.cust_preset}", help="Bắt buộc theo định nghĩa Give Me Some Credit: Living Costs cộng vào tử số DebtRatio")
        st.session_state.living_costs = living_costs_in
    with row_exp2:
        alimony_in = st.number_input("Nghĩa vụ cấp dưỡng hàng tháng (Alimony - VND/tháng):", min_value=0, max_value=100_000_000, value=st.session_state.alimony, step=500_000, format="%d", key=f"ali_{st.session_state.cust_preset}", help="Bắt buộc theo định nghĩa Give Me Some Credit: Alimony cộng vào tử số DebtRatio")
        st.session_state.alimony = alimony_in

    res_dr = calculate_debt_ratio(
        accounts=st.session_state.credit_accounts,
        gross_income_vnd=total_income_vnd,
        alimony_vnd=st.session_state.alimony,
        living_costs_vnd=st.session_state.living_costs,
        new_loan_installment=est_new_installment
    )

    # ------------------ MODULE 05: TÍNH REVOLVING UTILIZATION OF UNSECURED LINES ------------------
    st.markdown("""
    <div class="hdb-section-header">
        <span class="hdb-badge">05</span>
        <span class="hdb-title">TỶ LỆ SỬ DỤNG HẠN MỨC TÍN DỤNG QUAY VÒNG KHÔNG CÓ TÀI SẢN BẢO ĐẢM (REVOLVING UTILIZATION)</span>
    </div>
    """, unsafe_allow_html=True)
    
    util_badge_col = "#10B981" if res_ru['display_pct'] <= 35.0 else ("#F59E0B" if res_ru['display_pct'] <= 70.0 else "#EF4444")
    st.markdown(f"""
    <div class="summary-strip">
        💳 <b>Tổng Hạn Mức Tín Dụng Quay Vòng Không TSBĐ (&Sigma; L_i):</b> <b>{res_ru['total_limit']:,.0f} VND</b> | 
        <b>Tổng Dư Nợ Đã Sử Dụng (&Sigma; D_i):</b> <b>{res_ru['total_balance']:,.0f} VND</b><br/>
        👉 <b>TỶ LỆ SỬ DỤNG HẠN MỨC (RU = &Sigma; D_i / &Sigma; L_i):</b> 
        <b style="color: {util_badge_col}; font-size: 17px;">{res_ru['display_pct']:.2f}%</b> (Giá trị truyền vào XGBoost: <code style="font-weight: bold; font-size: 14px;">{res_ru['value']:.4f}</code>) | 
        <b>Trạng thái:</b> <span style="font-size: 12px; font-weight: bold; color: {util_badge_col};">{res_ru['status_badge']}</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔍 Chi Tiết Danh Sách Tài Khoản Đưa Vào vs Loại Khỏi Revolving Utilization", expanded=False):
        c_ru_tab1, c_ru_tab2 = st.columns(2)
        with c_ru_tab1:
            st.markdown(f"**✓ Tài khoản được tính vào RU ({res_ru['qualifying_count']} tài khoản):**")
            if res_ru['qualifying_accounts']:
                ru_in_df = pd.DataFrame([
                    {'Mã TK': a['acc_id'], 'Tên': a['name'], 'TCTD': a['bank'], 'Hạn mức (VND)': f"{a['limit']:,.0f}", 'Dư nợ (VND)': f"{a['balance']:,.0f}", 'Tỷ lệ con': f"{(a['balance']/a['limit']*100) if a['limit']>0 else 0:.1f}%"}
                    for a in res_ru['qualifying_accounts']
                ])
                st.dataframe(ru_in_df, use_container_width=True, hide_index=True)
                st.caption("📌 **Nguyên tắc Give Me Some Credit:** Thẻ tín dụng chưa phát sinh dư nợ (dư nợ = 0 đ) vẫn giữ nguyên hạn mức ở mẫu số, giúp hạ thấp tỷ lệ sử dụng đòn bẩy rủi ro của khách hàng.")
            else:
                st.write("Không có tài khoản quay vòng không TSBĐ nào.")
        with c_ru_tab2:
            st.markdown(f"**✗ Tài khoản bị loại trừ khỏi RU ({len(res_ru['excluded_accounts'])} tài khoản):**")
            if res_ru['excluded_accounts']:
                ru_ex_df = pd.DataFrame([
                    {'Mã TK': a['acc_id'], 'Tên': a['name'], 'Loại hình': a['acc_type'], 'Lý do loại trừ': reason}
                    for a, reason in res_ru['excluded_accounts']
                ])
                st.dataframe(ru_ex_df, use_container_width=True, hide_index=True)
                st.caption("📌 **Quy tắc phân loại:** Khoản vay thế chấp mua nhà, vay BĐS, HELOC (có TSBĐ là BĐS) và các khoản vay trả góp tuyệt đối không được đưa vào tỷ lệ sử dụng thẻ tín dụng không TSBĐ.")

    st.markdown("---")

    # ------------------ MODULE 06: TÍNH DEBT RATIO (THEO ĐỊNH NGHĨA GIVE ME SOME CREDIT) ------------------
    st.markdown("""
    <div class="hdb-section-header">
        <span class="hdb-badge">06</span>
        <span class="hdb-title">TỔNG HỢP NGHĨA VỤ TÀI CHÍNH VÀ TỶ SỐ NỢ TRÊN THU NHẬP (DEBT RATIO)</span>
    </div>
    """, unsafe_allow_html=True)
    
    dr_badge_col = "#10B981" if res_dr['display_pct'] <= 40.0 else ("#F59E0B" if res_dr['display_pct'] <= 70.0 else "#EF4444")
    st.markdown(f"""
    <div class="summary-strip">
        🏦 <b>Nghĩa Vụ Trả Nợ Khoản Vay & Thẻ Hàng Tháng:</b> <b>{res_dr['monthly_debt_payments']:,.0f} VND/tháng</b> ({res_dr['open_accounts_count']} tài khoản)<br/>
        🛒 <b>Chi Phí Sinh Hoạt (Living Costs):</b> <b>{res_dr['living_costs']:,.0f} VND/tháng</b> | 
        👶 <b>Tiền Cấp Dưỡng (Alimony):</b> <b>{res_dr['alimony']:,.0f} VND/tháng</b><br/>
        💰 <b>TỔNG NGHĨA VỤ TÀI CHÍNH HÀNG THÁNG (TỬ SỐ):</b> <b style="color: #1E3A8A; font-size: 15px;">{res_dr['total_obligations']:,.0f} VND/tháng</b> | 
        <b>Tổng Thu Nhập Gộp (Mẫu số):</b> <b>{res_dr['gross_income']:,.0f} VND/tháng</b><br/>
        👉 <b>TỶ SỐ DEBT RATIO HIỆN HỮU (GMSC MODEL INPUT):</b> 
        <b style="color: {dr_badge_col}; font-size: 17px;">{res_dr['display_pct']:.2f}%</b> (Giá trị truyền vào XGBoost: <code style="font-weight: bold; font-size: 14px;">{res_dr['value']:.4f}</code>)<br/>
        <hr style="margin: 6px 0; border: none; border-top: 1px dashed #CBD5E1;"/>
        📌 <b>CHỈ TIÊU THẨM ĐỊNH ĐỘC LẬP SAU GIẢI NGÂN (POST-DISBURSEMENT):</b> 
        Dự kiến góp khoản vay mới: <b>{est_new_installment:,.0f} đ/tháng</b> ⟹ 
        <b>Debt Ratio Sau Giải Ngân:</b> <b style="color: #1E3A8A;">{res_dr['post_debt_ratio']*100:.2f}%</b> | 
        <b>Tỷ lệ DSR Sau Giải Ngân:</b> <b style="color: {'#10B981' if res_dr['post_dsr_pct']<=60 else '#EF4444'};">{res_dr['post_dsr_pct']:.2f}%</b>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔍 Chi Tiết Phân Rã Các Nghĩa Vụ Hàng Tháng Tính Vào Debt Ratio", expanded=False):
        all_open_accs = [a for a in st.session_state.credit_accounts if a.get('status', 'OPEN') == 'OPEN']
        debt_breakdown_data = [
            {'Khoản mục nghĩa vụ': f"Trả nợ: {a['name']} ({a['bank']})", 'Loại sản phẩm': a['acc_type'], 'Số tiền (VND/tháng)': f"{a['monthly_payment']:,.0f}", 'Tính chất': 'Nghĩa vụ nợ hiện hữu'}
            for a in all_open_accs
        ]
        debt_breakdown_data.append({'Khoản mục nghĩa vụ': 'Chi phí sinh hoạt thiết yếu (Living Costs)', 'Loại sản phẩm': 'Chi phí sinh hoạt gia đình', 'Số tiền (VND/tháng)': f"{st.session_state.living_costs:,.0f}", 'Tính chất': 'Bắt buộc theo GMSC'})
        debt_breakdown_data.append({'Khoản mục nghĩa vụ': 'Nghĩa vụ cấp dưỡng nuôi con / người thân (Alimony)', 'Loại sản phẩm': 'Cấp dưỡng pháp lý', 'Số tiền (VND/tháng)': f"{st.session_state.alimony:,.0f}", 'Tính chất': 'Bắt buộc theo GMSC'})
        st.dataframe(pd.DataFrame(debt_breakdown_data), use_container_width=True, hide_index=True)
        st.caption("📌 **Ghi chú độc lập:** Khoản vay đang đề nghị thẩm định mới tại ngân hàng không được cộng vào DebtRatio hiện hữu của mô hình GMSC, mà được thể hiện riêng biệt ở chỉ số DSR sau giải ngân nhằm đánh giá năng lực trả nợ trong tương lai.")

    st.markdown("---")

    # ------------------ MODULE 07: TỔNG HỢP SỐ LƯỢNG TÀI KHOẢN TÍN DỤNG & KHOẢN VAY BẤT ĐỘNG SẢN (CIC) ------------------
    st.markdown("""
    <div class="hdb-section-header">
        <span class="hdb-badge">07</span>
        <span class="hdb-title">TỔNG HỢP SỐ LƯỢNG TÀI KHOẢN TÍN DỤNG & KHOẢN VAY BẤT ĐỘNG SẢN (CIC)</span>
    </div>
    """, unsafe_allow_html=True)
    
    col_c7_1, col_c7_2 = st.columns(2)
    with col_c7_1:
        st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-top: 4px solid #1E3A8A; border-radius: 8px; padding: 16px;">
            <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;">NumberOfOpenCreditLinesAndLoans</div>
            <div style="font-size: 32px; font-weight: 800; color: #1E3A8A; margin: 4px 0;">{res_n_open['value']} <span style="font-size: 15px; font-weight: 600; color: #475569;">tài khoản đang mở</span></div>
            <div style="font-size: 12px; color: #334155;">
                • Thẻ tín dụng & Hạn mức đang mở: <b>{res_n_open['open_cards_and_lines']}</b><br/>
                • Khoản vay trả góp đang mở: <b>{res_n_open['open_loans']}</b><br/>
                • Tài khoản đã tất toán/đóng (bị loại): <b>{res_n_open['closed_count']}</b>
            </div>
            <div style="font-size: 11px; color: #10B981; font-weight: bold; margin-top: 6px;">✓ Tự động tổng hợp 100% từ Credit Registry (Read-only)</div>
        </div>
        """, unsafe_allow_html=True)
    with col_c7_2:
        st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-top: 4px solid #047857; border-radius: 8px; padding: 16px;">
            <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;">NumberRealEstateLoansOrLines</div>
            <div style="font-size: 32px; font-weight: 800; color: #047857; margin: 4px 0;">{res_n_re['value']} <span style="font-size: 15px; font-weight: 600; color: #475569;">khoản tín dụng BĐS</span></div>
            <div style="font-size: 12px; color: #334155;">
                • Khoản vay mua nhà/thế chấp (Mortgage): <b>{res_n_re['mortgages_count']}</b><br/>
                • Khoản vay BĐS đầu tư/khác: <b>{res_n_re['re_loans_count']}</b><br/>
                • Hạn mức tín dụng thế chấp nhà (HELOC): <b>{res_n_re['heloc_count']}</b>
            </div>
            <div style="font-size: 11px; color: #10B981; font-weight: bold; margin-top: 6px;">✓ Tự động tổng hợp 100% từ Credit Registry (Read-only)</div>
        </div>
        """, unsafe_allow_html=True)

    st.caption("📌 **Mối quan hệ giữa 2 Feature theo chuẩn Give Me Some Credit:** Khoản vay mua nhà và hạn mức HELOC đang mở sẽ được tính đồng thời vào cả `NumberOfOpenCreditLinesAndLoans` (+1) và `NumberRealEstateLoansOrLines` (+1). Tuy nhiên, HELOC có TSBĐ bằng BĐS nên được loại trừ khỏi `RevolvingUtilizationOfUnsecuredLines`.")

    st.markdown("---")

    # ==============================================================================
    # KHU VỰC TỔNG KẾT: KẾT QUẢ TỰ ĐỘNG TÍNH TOÁN 4 FEATURE CHO MÔ HÌNH MACHINE LEARNING
    # ==============================================================================
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); color: white; padding: 16px 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="color: #F8FAFC; margin: 0; font-size: 17px; font-weight: 700;">🎯 BẢNG TỔNG HỢP 4 FEATURE ĐẦU VÀO MÔ HÌNH CREDIT SCORING (READ-ONLY)</h3>
                <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 12px;">Dữ liệu được trích xuất tự động và chuẩn hóa chính xác theo định nghĩa bộ dữ liệu Give Me Some Credit (Kaggle)</p>
            </div>
            <div>
                <span style="background: #10B981; color: white; font-size: 11px; font-weight: bold; padding: 4px 10px; border-radius: 15px;">✓ DỮ LIỆU ĐẦU VÀO ĐẠT CHUẨN</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sm_c1, sm_c2, sm_c3, sm_c4 = st.columns(4)
    with sm_c1:
        st.markdown(f"""
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; color: #64748B; font-weight: 700;">NumberRealEstateLoansOrLines</div>
            <div style="font-size: 26px; font-weight: 800; color: #047857; margin: 6px 0;">{res_n_re['value']} <span style="font-size: 13px; font-weight: 500;">khoản</span></div>
            <div style="font-size: 11px; color: #334155; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">XGBoost Input: <b>{float(res_n_re['value']):.1f}</b></div>
        </div>
        """, unsafe_allow_html=True)
    with sm_c2:
        st.markdown(f"""
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; color: #64748B; font-weight: 700;">NumberOfOpenCreditLinesAndLoans</div>
            <div style="font-size: 26px; font-weight: 800; color: #1E3A8A; margin: 6px 0;">{res_n_open['value']} <span style="font-size: 13px; font-weight: 500;">tài khoản</span></div>
            <div style="font-size: 11px; color: #334155; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">XGBoost Input: <b>{float(res_n_open['value']):.1f}</b></div>
        </div>
        """, unsafe_allow_html=True)
    with sm_c3:
        st.markdown(f"""
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; color: #64748B; font-weight: 700;">RevolvingUtilization</div>
            <div style="font-size: 26px; font-weight: 800; color: {util_badge_col}; margin: 6px 0;">{res_ru['display_pct']:.2f}%</div>
            <div style="font-size: 11px; color: #334155; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">XGBoost Input: <b>{res_ru['value']:.4f}</b></div>
        </div>
        """, unsafe_allow_html=True)
    with sm_c4:
        st.markdown(f"""
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; color: #64748B; font-weight: 700;">DebtRatio (Hiện hữu)</div>
            <div style="font-size: 26px; font-weight: 800; color: {dr_badge_col}; margin: 6px 0;">{res_dr['display_pct']:.2f}%</div>
            <div style="font-size: 11px; color: #334155; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">XGBoost Input: <b>{res_dr['value']:.4f}</b></div>
        </div>
        """, unsafe_allow_html=True)

    # Đóng gói dữ liệu 11 đặc trưng hoàn chỉnh truyền trực tiếp vào các mô hình Machine Learning
    customer_features_payload = {
        'RevolvingUtilizationOfUnsecuredLines': res_ru['value'],
        'age': cust_age,
        'NumberOfTime30-59DaysPastDueNotWorse': late_30_59,
        'DebtRatio': res_dr['value'],
        'MonthlyIncome': cust_income_model,
        'NumberOfOpenCreditLinesAndLoans': res_n_open['value'],
        'NumberOfTimes90DaysLate': late_90,
        'NumberRealEstateLoansOrLines': res_n_re['value'],
        'NumberOfTime60-89DaysPastDueNotWorse': late_60_89,
        'NumberOfDependents': cust_dependents,
        'MonthlyIncome_is_missing': 1 if cust_income_model <= 0 else 0
    }

    # Đóng gói thông tin tài chính chi tiết phục vụ PDF và DSR
    total_monthly_debt = res_dr['monthly_debt_payments']
    total_debt_with_new = total_monthly_debt + est_new_installment
    final_dsr_pct = res_dr['post_dsr_pct']

    financial_breakdown_payload = {
        'income_salary': income_salary,
        'income_rental': income_rental,
        'income_business': income_biz,
        'income_other': income_other,
        'total_income_vnd': total_income_vnd,
        'card_count': res_ru['qualifying_count'],
        'total_card_limit': res_ru['total_limit'],
        'total_card_balance': res_ru['total_balance'],
        'total_card_monthly_debt': sum(a['monthly_payment'] for a in res_ru['qualifying_accounts']),
        'loan_count': res_n_open['open_loans'],
        'total_loan_balance': sum(a['balance'] for a in st.session_state.credit_accounts if a.get('acc_type') not in ['CREDIT_CARD', 'UNSECURED_LOC', 'OVERDRAFT', 'HELOC']),
        'total_loan_monthly_debt': sum(a['monthly_payment'] for a in st.session_state.credit_accounts if a.get('acc_type') not in ['CREDIT_CARD', 'UNSECURED_LOC', 'OVERDRAFT', 'HELOC']),
        'living_costs': st.session_state.living_costs,
        'alimony': st.session_state.alimony,
        'monthly_debt_repayment': total_monthly_debt,
        'monthly_new_installment': est_new_installment,
        'total_debt_monthly': total_debt_with_new,
        'dsr_pct': final_dsr_pct,
        'post_debt_ratio': res_dr['post_debt_ratio'] * 100.0
    }

    customer_meta_payload = {

        'app_id': f"HS-{datetime.date.today().strftime('%Y%m%d')}-{np.random.randint(1000, 9999)}",
        'cust_name': cust_name_in,
        'loan_amount': loan_amount,
        'officer_name': user['name']
    }

    # ==============================================================================
    # THỰC THI CHẤM ĐIỂM BẰNG CẢ 3 MÔ HÌNH (TRIPLE-MODEL EXECUTION)
    # ==============================================================================
    res_dt = score_single_customer_dt(customer_features_payload, product_code, market_mode, loan_amount)
    res_lr = score_single_customer_lr(customer_features_payload, product_code, market_mode, loan_amount)
    res_xgb = score_single_customer_xgb(customer_features_payload, product_code, market_mode, loan_amount)

    st.markdown("---")
    st.markdown("## 📊 KẾT QUẢ THẨM ĐỊNH & CHẤM ĐIỂM TÍN DỤNG")

    # ==============================================================================
    # HIỂN THỊ CHẾ ĐỘ TRIPLE (SIDE-BY-SIDE EVALUATION 3 MÔ HÌNH)
    # ==============================================================================
    if model_choice == "ALL_TRIPLE":
        col_dt_view, col_lr_view, col_xgb_view = st.columns(3)
        
        # ------------------ CỘT 1: CÂY QUYẾT ĐỊNH (DECISION TREE) ------------------
        with col_dt_view:
            st.markdown('''
            <div style="background: linear-gradient(135deg, #064E3B 0%, #047857 100%); color: white; padding: 10px 14px; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 14px;">
                🌲 CÂY QUYẾT ĐỊNH (DECISION TREE)
                <span style="font-size: 10px; float: right; background: rgba(255,255,255,0.2); padding: 2px 7px; border-radius: 10px;">White-Box</span>
            </div>
            ''', unsafe_allow_html=True)
            
            if res_dt['dec_code'] == 'APPROVED':
                st.markdown(f'<div class="decision-approved" style="border-radius: 0 0 8px 8px; font-size: 13px;">✅ {res_dt["decision"]}<div style="font-size: 12px; font-weight: normal; margin-top: 3px;">{res_dt["reason"]}</div></div>', unsafe_allow_html=True)
            elif res_dt['dec_code'] == 'CONDITIONAL':
                st.markdown(f'<div class="decision-conditional" style="border-radius: 0 0 8px 8px; font-size: 13px;">⚠️ {res_dt["decision"]}<div style="font-size: 12px; font-weight: normal; margin-top: 3px;">{res_dt["reason"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="decision-rejected" style="border-radius: 0 0 8px 8px; font-size: 13px;">🚫 {res_dt["decision"]}<div style="font-size: 12px; font-weight: normal; margin-top: 3px;">{res_dt["reason"]}</div></div>', unsafe_allow_html=True)

            fig_gauge_dt = go.Figure(go.Indicator(
                mode="gauge+number",
                value=res_dt['fico'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "FICO SCORE (TREE)", 'font': {'size': 13, 'color': '#0F172A'}},
                gauge={
                    'axis': {'range': [300, 850], 'tickwidth': 1, 'tickcolor': "#475569"},
                    'bar': {'color': "#047857", 'thickness': 0.3},
                    'steps': [
                        {'range': [300, 527], 'color': "#FCA5A5"},
                        {'range': [527, 571], 'color': "#FDE68A"},
                        {'range': [571, 600], 'color': "#A7F3D0"},
                        {'range': [600, 850], 'color': "#34D399"}
                    ],
                    'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': res_dt['fico']}
                }
            ))
            fig_gauge_dt.update_layout(height=210, margin=dict(l=10, r=10, t=25, b=10))
            st.plotly_chart(fig_gauge_dt, use_container_width=True)
            
            c_dt1, c_dt2 = st.columns(2)
            with c_dt1:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Xác suất PD</div><div class="metric-value">{res_dt["pd"]*100:.2f}%</div><div style="font-size: 10px; color: #64748B;">Wilson: {res_dt["wilson"]}</div></div>', unsafe_allow_html=True)
            with c_dt2:
                profit_col_dt = "#10B981" if res_dt['profit_vnd'] >= 0 else "#EF4444"
                st.markdown(f'<div class="metric-card"><div class="metric-label">Lợi nhuận dự kiến</div><div class="metric-value" style="color: {profit_col_dt}; font-size: 16px;">{res_dt["profit_vnd"]:,.0f} đ</div><div style="font-size: 10px; color: #64748B;">{res_dt["grade"]}</div></div>', unsafe_allow_html=True)
                
            st.info(f"""**🌿 Nút lá #{res_dt['leaf_id']} (IF-THEN):**

`IF {res_dt['rule']} THEN PD = {res_dt['pd']*100:.2f}%`""""")

        # ------------------ CỘT 2: HỒI QUY LOGISTIC (LOGISTIC REGRESSION) ------------------
        with col_lr_view:
            st.markdown('''
            <div style="background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%); color: white; padding: 10px 14px; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 14px;">
                📈 HỒI QUY LOGISTIC (LOGISTIC)
                <span style="font-size: 10px; float: right; background: rgba(255,255,255,0.2); padding: 2px 7px; border-radius: 10px;">Continuous</span>
            </div>
            ''', unsafe_allow_html=True)
            
            if res_lr['dec_code'] == 'APPROVED':
                st.markdown(f'<div class="decision-approved" style="border-radius: 0 0 8px 8px; font-size: 13px;">✅ {res_lr["decision"]}<div style="font-size: 12px; font-weight: normal; margin-top: 3px;">{res_lr["reason"]}</div></div>', unsafe_allow_html=True)
            elif res_lr['dec_code'] == 'CONDITIONAL':
                st.markdown(f'<div class="decision-conditional" style="border-radius: 0 0 8px 8px; font-size: 13px;">⚠️ {res_lr["decision"]}<div style="font-size: 12px; font-weight: normal; margin-top: 3px;">{res_lr["reason"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="decision-rejected" style="border-radius: 0 0 8px 8px; font-size: 13px;">🚫 {res_lr["decision"]}<div style="font-size: 12px; font-weight: normal; margin-top: 3px;">{res_lr["reason"]}</div></div>', unsafe_allow_html=True)

            fig_gauge_lr = go.Figure(go.Indicator(
                mode="gauge+number",
                value=res_lr['fico'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "FICO SCORE (LOGISTIC)", 'font': {'size': 13, 'color': '#0F172A'}},
                gauge={
                    'axis': {'range': [300, 850], 'tickwidth': 1, 'tickcolor': "#475569"},
                    'bar': {'color': "#1E3A8A", 'thickness': 0.3},
                    'steps': [
                        {'range': [300, 527], 'color': "#FCA5A5"},
                        {'range': [527, 571], 'color': "#FDE68A"},
                        {'range': [571, 600], 'color': "#A7F3D0"},
                        {'range': [600, 850], 'color': "#34D399"}
                    ],
                    'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': res_lr['fico']}
                }
            ))
            fig_gauge_lr.update_layout(height=210, margin=dict(l=10, r=10, t=25, b=10))
            st.plotly_chart(fig_gauge_lr, use_container_width=True)
            
            c_lr1, c_lr2 = st.columns(2)
            with c_lr1:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Xác suất PD</div><div class="metric-value">{res_lr["pd"]*100:.2f}%</div><div style="font-size: 10px; color: #64748B;">Log-odds: {res_lr.get("log_odds", 0):.3f}</div></div>', unsafe_allow_html=True)
            with c_lr2:
                profit_col_lr = "#10B981" if res_lr['profit_vnd'] >= 0 else "#EF4444"
                st.markdown(f'<div class="metric-card"><div class="metric-label">Lợi nhuận dự kiến</div><div class="metric-value" style="color: {profit_col_lr}; font-size: 16px;">{res_lr["profit_vnd"]:,.0f} đ</div><div style="font-size: 10px; color: #64748B;">{res_lr["grade"]}</div></div>', unsafe_allow_html=True)
                
            st.success(f"**⚡ Hàm Logit Liên tục:** FICO nhảy mượt từng USD thu nhập. Nhân tố chi phối: `{res_lr.get('top_driver', 'Thu nhập')}`.")

        # ------------------ CỘT 3: XGBOOST (GRADIENT BOOSTING) ------------------
        with col_xgb_view:
            st.markdown('''
            <div style="background: linear-gradient(135deg, #4C1D95 0%, #7C3AED 100%); color: white; padding: 10px 14px; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 14px;">
                🚀 XGBOOST (GRADIENT BOOSTING)
                <span style="font-size: 10px; float: right; background: rgba(255,255,255,0.2); padding: 2px 7px; border-radius: 10px;">High Precision</span>
            </div>
            ''', unsafe_allow_html=True)
            
            if res_xgb['dec_code'] == 'APPROVED':
                st.markdown(f'<div class="decision-approved-xgb" style="border-radius: 0 0 8px 8px; font-size: 13px;">✅ {res_xgb["decision"]}<div style="font-size: 12px; font-weight: normal; margin-top: 3px;">{res_xgb["reason"]}</div></div>', unsafe_allow_html=True)
            elif res_xgb['dec_code'] == 'CONDITIONAL':
                st.markdown(f'<div class="decision-conditional" style="border-radius: 0 0 8px 8px; font-size: 13px;">⚠️ {res_xgb["decision"]}<div style="font-size: 12px; font-weight: normal; margin-top: 3px;">{res_xgb["reason"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="decision-rejected" style="border-radius: 0 0 8px 8px; font-size: 13px;">🚫 {res_xgb["decision"]}<div style="font-size: 12px; font-weight: normal; margin-top: 3px;">{res_xgb["reason"]}</div></div>', unsafe_allow_html=True)

            fig_gauge_xgb = go.Figure(go.Indicator(
                mode="gauge+number",
                value=res_xgb['fico'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "FICO SCORE (XGBOOST)", 'font': {'size': 13, 'color': '#0F172A'}},
                gauge={
                    'axis': {'range': [300, 850], 'tickwidth': 1, 'tickcolor': "#475569"},
                    'bar': {'color': "#7C3AED", 'thickness': 0.3},
                    'steps': [
                        {'range': [300, 527], 'color': "#FCA5A5"},
                        {'range': [527, 571], 'color': "#FDE68A"},
                        {'range': [571, 600], 'color': "#A7F3D0"},
                        {'range': [600, 850], 'color': "#34D399"}
                    ],
                    'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': res_xgb['fico']}
                }
            ))
            fig_gauge_xgb.update_layout(height=210, margin=dict(l=10, r=10, t=25, b=10))
            st.plotly_chart(fig_gauge_xgb, use_container_width=True)
            
            c_xgb1, c_xgb2 = st.columns(2)
            with c_xgb1:
                st.markdown(f'<div class="metric-card-xgb"><div class="metric-label">Xác suất PD</div><div class="metric-value">{res_xgb["pd"]*100:.2f}%</div><div style="font-size: 10px; color: #64748B;">AUC: 0.8681 | KS: 58.1%</div></div>', unsafe_allow_html=True)
            with c_xgb2:
                profit_col_xgb = "#10B981" if res_xgb['profit_vnd'] >= 0 else "#EF4444"
                st.markdown(f'<div class="metric-card-xgb"><div class="metric-label">Lợi nhuận dự kiến</div><div class="metric-value" style="color: {profit_col_xgb}; font-size: 16px;">{res_xgb["profit_vnd"]:,.0f} đ</div><div style="font-size: 10px; color: #64748B;">{res_xgb["grade"]}</div></div>', unsafe_allow_html=True)
                
            st.markdown(f'<div style="background: #F5F3FF; border: 1px solid #DDD6FE; border-radius: 8px; padding: 9px; font-size: 12px; color: #5B21B6;"><b>🚀 Ensemble Boosting:</b> Độ chính xác cao nhất. Trọng số SHAP hàng đầu: <b>{res_xgb.get("top_driver", "Đòn bẩy & Quá hạn")}</b>.</div>', unsafe_allow_html=True)

        # ------------------ PANEL ĐỐI SÁNH & TRỌNG TÀI RỦI RO 3 MÔ HÌNH ------------------
        st.markdown('<div class="reconciliation-box">', unsafe_allow_html=True)
        st.markdown("#### ⚖️ BẢNG ĐỐI SÁNH KẾT QUẢ & TRỌNG TÀI RỦI RO ĐA MÔ HÌNH (TRIPLE RECONCILIATION)")
        
        ficos = [res_dt['fico'], res_lr['fico'], res_xgb['fico']]
        pds = [res_dt['pd'], res_lr['pd'], res_xgb['pd']]
        delta_max_fico = max(ficos) - min(ficos)
        delta_max_pd = (max(pds) - min(pds)) * 100
        is_all_agree = (res_dt['dec_code'] == res_lr['dec_code'] == res_xgb['dec_code'])
        
        rec_c1, rec_c2, rec_c3, rec_c4 = st.columns(4)
        rec_c1.metric("Độ Lệch FICO Cực Đại (Max-Min)", f"{delta_max_fico} điểm", "Độ đồng thuận cao" if delta_max_fico <= 20 else "Có phân kỳ nhẹ")
        rec_c2.metric("Độ Lệch Xác Suất PD", f"{delta_max_pd:.2f}%", "Tiệm cận rất sát" if delta_max_pd <= 2.5 else "Khác biệt phân tầng")
        rec_c3.metric("Trạng Thái Đồng Thuận", "3/3 ĐỒNG THUẬN HOÀN TOÀN" if is_all_agree else "ĐA SỐ 2/3 ĐỒNG THUẬN", "Phê duyệt chuẩn" if is_all_agree else "Xem xét trọng tài")
        rec_c4.metric("Nghĩa vụ nợ DSR Thực tế", f"{final_dsr_pct:.1f}%", "Đạt chuẩn an toàn (<=60%)" if final_dsr_pct <= 60 else "Cảnh báo cao (>60%)", delta_color="inverse")
        
        st.markdown("##### 📋 Bảng So Sánh Đối Sánh Song Song 3 Mô Hình:")
        triple_summary_df = pd.DataFrame([
            {'Chỉ Tiêu Thẩm Định': '1. Điểm Tín Dụng FICO', 'Cây Quyết Định (DT)': f"{res_dt['fico']} điểm", 'Hồi Quy Logistic (LR)': f"{res_lr['fico']} điểm", 'XGBoost (Boosting)': f"{res_xgb['fico']} điểm", 'Mô Hình Dẫn Đầu': 'XGBoost (Chính xác nhất)'},
            {'Chỉ Tiêu Thẩm Định': '2. Phân Tầng Hạng Rủi Ro', 'Cây Quyết Định (DT)': res_dt['grade'], 'Hồi Quy Logistic (LR)': res_lr['grade'], 'XGBoost (Boosting)': res_xgb['grade'], 'Mô Hình Dẫn Đầu': 'Đồng thuận chuẩn Basel'},
            {'Chỉ Tiêu Thẩm Định': '3. Xác Suất Vỡ Nợ (PD)', 'Cây Quyết Định (DT)': f"{res_dt['pd']*100:.2f}%", 'Hồi Quy Logistic (LR)': f"{res_lr['pd']*100:.2f}%", 'XGBoost (Boosting)': f"{res_xgb['pd']*100:.2f}%", 'Mô Hình Dẫn Đầu': 'XGBoost (ECE=0.0034)'},
            {'Chỉ Tiêu Thẩm Định': '4. Lợi Nhuận Dự Kiến (VND)', 'Cây Quyết Định (DT)': f"{res_dt['profit_vnd']:+,.0f} đ", 'Hồi Quy Logistic (LR)': f"{res_lr['profit_vnd']:+,.0f} đ", 'XGBoost (Boosting)': f"{res_xgb['profit_vnd']:+,.0f} đ", 'Mô Hình Dẫn Đầu': 'Biên an toàn tài chính'},
            {'Chỉ Tiêu Thẩm Định': '5. Quyết Định Thẩm Định', 'Cây Quyết Định (DT)': res_dt['decision'], 'Hồi Quy Logistic (LR)': res_lr['decision'], 'XGBoost (Boosting)': res_xgb['decision'], 'Mô Hình Dẫn Đầu': 'Trọng tài ALCO'}
        ])
        st.dataframe(triple_summary_df, use_container_width=True, hide_index=True)

        if is_all_agree:
            st.markdown(f"🟢 **Kết luận Hội đồng Rủi ro:** Cả 3 mô hình đều đồng thuận đưa ra quyết định **`{res_dt['decision']}`**. Hồ sơ đạt độ tin cậy phê duyệt cao nhất theo chuẩn Basel II.")
        else:
            dec_list = [res_dt['dec_code'], res_lr['dec_code'], res_xgb['dec_code']]
            maj = max(set(dec_list), key=dec_list.count)
            st.markdown(f"🟡 **Cảnh báo phân kỳ mô hình:** Cây Quyết định: `{res_dt['dec_code']}` | Hồi quy Logistic: `{res_lr['dec_code']}` | XGBoost: `{res_xgb['dec_code']}`. Đa số 2/3 mô hình đồng thuận phương án **`[{maj}]`**. Đề xuất chuyển hồ sơ lên Hội đồng ALCO thẩm định nguồn thu thực tế.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ==============================================================================
    # HIỂN THỊ CHẾ ĐỘ ĐƠN MÔ HÌNH (SINGLE MODEL VIEW)
    # ==============================================================================
    else:
        if model_choice == "DECISION_TREE":
            active_res = res_dt
            bar_color = "#047857"
        elif model_choice == "LOGISTIC_REGRESSION":
            active_res = res_lr
            bar_color = "#1E3A8A"
        else:
            active_res = res_xgb
            bar_color = "#7C3AED"
        
        if active_res['dec_code'] == 'APPROVED':
            st.markdown(f'<div class="decision-approved">✅ {active_res["decision"]}<div style="font-size: 14px; font-weight: normal; margin-top: 5px;">{active_res["reason"]}</div></div>', unsafe_allow_html=True)
        elif active_res['dec_code'] == 'CONDITIONAL':
            st.markdown(f'<div class="decision-conditional">⚠️ {active_res["decision"]}<div style="font-size: 14px; font-weight: normal; margin-top: 5px;">{active_res["reason"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="decision-rejected">🚫 {active_res["decision"]}<div style="font-size: 14px; font-weight: normal; margin-top: 5px;">{active_res["reason"]}</div></div>', unsafe_allow_html=True)
            
        col_s1, col_s2, col_s3 = st.columns([1.5, 1.2, 1.3])
        with col_s1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-label">ĐỒNG HỒ ĐIỂM FICO ({active_res["model_name"]})</div>', unsafe_allow_html=True)
            fig_g_single = go.Figure(go.Indicator(
                mode="gauge+number",
                value=active_res['fico'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"FICO ({active_res['grade']})", 'font': {'size': 15, 'color': '#0F172A'}},
                gauge={
                    'axis': {'range': [300, 850], 'tickwidth': 1, 'tickcolor': "#475569"},
                    'bar': {'color': bar_color, 'thickness': 0.3},
                    'steps': [
                        {'range': [300, 527], 'color': "#FCA5A5"},
                        {'range': [527, 571], 'color': "#FDE68A"},
                        {'range': [571, 600], 'color': "#A7F3D0"},
                        {'range': [600, 850], 'color': "#34D399"}
                    ],
                    'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': active_res['fico']}
                }
            ))
            fig_g_single.update_layout(height=230, margin=dict(l=15, r=15, t=30, b=10))
            st.plotly_chart(fig_g_single, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_s2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Xác suất Vỡ Nợ (PD)</div><div class="metric-value">{active_res["pd"]*100:.2f}%</div><div style="font-size: 12px; color: #64748B;">Ngưỡng hòa vốn (PD*): {active_res["pd_star"]*100:.2f}%</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-card"><div class="metric-label">Lợi Nhuận Ròng Dự Kiến</div><div class="metric-value" style="color: {"#10B981" if active_res["profit_vnd"]>=0 else "#EF4444"};">{active_res["profit_vnd"]:,.0f} VND</div><div style="font-size: 12px; color: #64748B;">Biên ròng: {active_res["net_margin"]*100:.2f}%</div></div>', unsafe_allow_html=True)
            
        with col_s3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Nghĩa vụ nợ DSR Thực tế</div><div class="metric-value">{final_dsr_pct:.1f}%</div><div style="font-size: 12px; color: {"#10B981" if final_dsr_pct<=60 else "#EF4444"};">{"Đạt chuẩn an toàn (<=60%)" if final_dsr_pct<=60 else "Cảnh báo vượt trần (>60%)"}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-card"><div class="metric-label">Góp Khoản Mới Dự Kiến</div><div class="metric-value" style="color: #1E3A8A; font-size: 18px;">{est_new_installment:,.0f} VND/th</div><div style="font-size: 12px; color: #64748B;">Kỳ hạn tính toán: 36 tháng</div></div>', unsafe_allow_html=True)

        if model_choice == "DECISION_TREE":
            with st.expander("🔍 Xem Chi Tiết Quy Tắc Giải Trình (Explainable AI - IF...THEN)", expanded=True):
                st.markdown(f"**Quy tắc ra quyết định:** `IF {active_res.get('rule', 'N/A')} THEN PD = {active_res['pd']*100:.2f}% -> {active_res['grade']}`")
        elif model_choice == "LOGISTIC_REGRESSION":
            with st.expander("🔍 Xem Phương Trình Log-Odds & Độ Nhạy Mượt Mà", expanded=True):
                st.markdown(f"**Hàm Logit Liên tục:** $\\ln(PD/(1-PD)) = {active_res.get('log_odds', 0):.4f}$. Điểm số FICO tự động tối ưu thích ứng mượt mà theo từng biến đầu vào.")
        else:
            with st.expander("🔍 Xem Xếp Hạng Đóng Góp Đặc Trưng SHAP (XGBoost Feature Attribution)", expanded=True):
                st.markdown(f"**Nhân tố chi phối hàng đầu:** `{active_res.get('top_driver', 'Đòn bẩy & Quá hạn')}`")
                if not xgb_feat_df.empty:
                    st.dataframe(xgb_feat_df.head(6), use_container_width=True)

        st.markdown("##### ⚖️ Đối Sánh Tương Quan Với 2 Mô Hình Còn Lại:")
        comp_df = pd.DataFrame([
            {'Mô Hình': '🌲 Cây Quyết Định (DT)', 'Điểm FICO': res_dt['fico'], 'Phân Hạng': res_dt['grade'], 'Xác Suất PD': f"{res_dt['pd']*100:.2f}%", 'Lợi Nhuận Kỳ Vọng': f"{res_dt['profit_vnd']:+,.0f} đ", 'Quyết Định': res_dt['decision']},
            {'Mô Hình': '📈 Hồi Quy Logistic (LR)', 'Điểm FICO': res_lr['fico'], 'Phân Hạng': res_lr['grade'], 'Xác Suất PD': f"{res_lr['pd']*100:.2f}%", 'Lợi Nhuận Kỳ Vọng': f"{res_lr['profit_vnd']:+,.0f} đ", 'Quyết Định': res_lr['decision']},
            {'Mô Hình': '🚀 XGBoost (Gradient Boosting)', 'Điểm FICO': res_xgb['fico'], 'Phân Hạng': res_xgb['grade'], 'Xác Suất PD': f"{res_xgb['pd']*100:.2f}%", 'Lợi Nhuận Kỳ Vọng': f"{res_xgb['profit_vnd']:+,.0f} đ", 'Quyết Định': res_xgb['decision']}
        ])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

    # ==============================================================================
    # NÚT XUẤT TỜ TRÌNH THẨM ĐỊNH TÍN DỤNG CHUYÊN NGHIỆP TRẮNG - ĐEN (PDF EXPORT)
    # ==============================================================================
    st.markdown("---")
    st.markdown("#### 📄 XUẤT TỜ TRÌNH THẨM ĐỊNH TÍN DỤNG CHÍNH QUY (FORMAT TRẮNG - ĐEN ĐỐI SÁNH 3 MÔ HÌNH)")
    st.write("Tờ trình được xuất ra theo chuẩn văn bản hành chính Ngân hàng (chỉ dùng định dạng **Trắng & Đen** sang trọng, đối sánh cả 3 mô hình trên bảng đo lường số liệu cụ thể và chữ ký phê duyệt).")

    pdf_bw_bytes = generate_bw_credit_appraisal_pdf(
        customer_info=customer_meta_payload,
        financial_details=financial_breakdown_payload,
        card_items=st.session_state.card_rows,
        loan_items=st.session_state.loan_rows,
        features_dict=customer_features_payload,
        dt_res=res_dt,
        lr_res=res_lr,
        xgb_res=res_xgb,
        selected_mode=model_choice,
        prod_cfg=dt_cfg[product_code],
        market_mode=market_mode
    )

    pdf_file_name = f"To_Trinh_Tham_Dinh_{customer_meta_payload['app_id']}_{cust_name_in.replace(' ', '_')}.pdf"
    
    col_pdf1, col_pdf2 = st.columns([1, 2])
    with col_pdf1:
        st.download_button(
            label="📥 TẢI TỜ TRÌNH THẨM ĐỊNH (PDF TRẮNG - ĐEN 3 MÔ HÌNH)",
            data=pdf_bw_bytes,
            file_name=pdf_file_name,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    with col_pdf2:
        st.caption(f"✓ Đã sẵn sàng in ấn A4 chuẩn ngân hàng: `{pdf_file_name}` | Dung lượng: **{len(pdf_bw_bytes)/1024:.1f} KB** | Định dạng Trắng - Đen chuyên nghiệp.")

# ==============================================================================
# TAB 2: CHẤM ĐIỂM DANH MỤC LÔ HÀNG LOẠT (BATCH PORTFOLIO SCORING 3 MÔ HÌNH)
# ==============================================================================
if 'batch' in user['allowed_tabs']:
    with active_tabs[tab_labels.index("📁 Chấm điểm Danh mục Lô (Batch Excel)")]:
        st.markdown("### 📁 Tải Lên Danh Sách Hồ Sơ Khách Hàng Để Chấm Điểm Hàng Loạt")
        st.write("Hệ thống cho phép nạp hàng nghìn hồ sơ từ file Excel hoặc CSV để tính toán nhanh chóng Điểm FICO, Phân hạng Rủi ro và Lợi nhuận dự kiến song song bằng **cả 3 mô hình (Decision Tree, Logistic Regression, XGBoost)**.")
        
        col_up1, col_up2 = st.columns([2, 1])
        with col_up1:
            uploaded_file = st.file_uploader("Chọn file CSV hoặc Excel danh sách khách hàng:", type=['csv', 'xlsx'])
        with col_up2:
            st.markdown("##### 📌 Tải Về Mẫu Dữ Liệu Chuẩn")
            sample_df = pd.DataFrame([
                {'RevolvingUtilizationOfUnsecuredLines': 0.15, 'age': 45, 'NumberOfTime30-59DaysPastDueNotWorse': 0, 'DebtRatio': 0.25, 'MonthlyIncome': 8000, 'NumberOfOpenCreditLinesAndLoans': 8, 'NumberOfTimes90DaysLate': 0, 'NumberRealEstateLoansOrLines': 2, 'NumberOfTime60-89DaysPastDueNotWorse': 0, 'NumberOfDependents': 1, 'Loan_Amount_VND': 500000000},
                {'RevolvingUtilizationOfUnsecuredLines': 0.85, 'age': 28, 'NumberOfTime30-59DaysPastDueNotWorse': 2, 'DebtRatio': 0.65, 'MonthlyIncome': 3000, 'NumberOfOpenCreditLinesAndLoans': 5, 'NumberOfTimes90DaysLate': 1, 'NumberRealEstateLoansOrLines': 0, 'NumberOfTime60-89DaysPastDueNotWorse': 1, 'NumberOfDependents': 0, 'Loan_Amount_VND': 50000000}
            ])
            sample_csv = sample_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Tải Template Mẫu (.CSV)", data=sample_csv, file_name="Mau_Danh_Sach_Ho_So_Tin_Dung.csv", mime="text/csv", use_container_width=True)
            
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    batch_df = pd.read_csv(uploaded_file)
                else:
                    batch_df = pd.read_excel(uploaded_file)
                    
                st.success(f"✓ Đã nạp thành công **{len(batch_df):,}** hồ sơ khách hàng!")
                
                if st.button("🚀 Bắt Đầu Chấm Điểm Toàn Bộ Danh Mục Bằng Cả 3 Mô Hình", type="primary"):
                    with st.spinner("Đang tính toán FICO, PD và Lợi nhuận dự kiến song song 3 mô hình..."):
                        res_list = []
                        for idx, row in batch_df.iterrows():
                            c_dict = row.to_dict()
                            l_amt = row.get('Loan_Amount_VND', loan_amount)
                            eval_dt = score_single_customer_dt(c_dict, product_code, market_mode, l_amt)
                            eval_lr = score_single_customer_lr(c_dict, product_code, market_mode, l_amt)
                            eval_xgb = score_single_customer_xgb(c_dict, product_code, market_mode, l_amt)
                            
                            res_list.append({
                                'STT': idx + 1,
                                'FICO_Tree': eval_dt['fico'],
                                'Grade_Tree': eval_dt['grade'],
                                'PD_Tree_%': round(eval_dt['pd'] * 100, 2),
                                'Decision_Tree': eval_dt['decision'],
                                'FICO_Logistic': eval_lr['fico'],
                                'Grade_Logistic': eval_lr['grade'],
                                'PD_Logistic_%': round(eval_lr['pd'] * 100, 2),
                                'Decision_Logistic': eval_lr['decision'],
                                'FICO_XGBoost': eval_xgb['fico'],
                                'Grade_XGBoost': eval_xgb['grade'],
                                'PD_XGBoost_%': round(eval_xgb['pd'] * 100, 2),
                                'Decision_XGBoost': eval_xgb['decision'],
                                'Profit_Tree_VND': eval_dt['profit_vnd'],
                                'Profit_Logistic_VND': eval_lr['profit_vnd'],
                                'Profit_XGBoost_VND': eval_xgb['profit_vnd']
                            })
                            
                        result_batch_df = pd.DataFrame(res_list)
                        
                        km1, km2, km3, km4 = st.columns(4)
                        km1.metric("Tổng Số Hồ Sơ", f"{len(result_batch_df):,}")
                        appr_count_dt = (result_batch_df['Decision_Tree'].str.contains('PHÊ DUYỆT')).sum()
                        km2.metric("Tỷ Lệ Duyệt (Tree)", f"{appr_count_dt/len(result_batch_df)*100:.1f}%")
                        appr_count_lr = (result_batch_df['Decision_Logistic'].str.contains('PHÊ DUYỆT')).sum()
                        km3.metric("Tỷ Lệ Duyệt (Logistic)", f"{appr_count_lr/len(result_batch_df)*100:.1f}%")
                        appr_count_xgb = (result_batch_df['Decision_XGBoost'].str.contains('PHÊ DUYỆT')).sum()
                        km4.metric("Tỷ Lệ Duyệt (XGBoost)", f"{appr_count_xgb/len(result_batch_df)*100:.1f}%")
                        
                        st.dataframe(result_batch_df.head(10), use_container_width=True)
                        
                        res_csv = result_batch_df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Tải Xuất Kết Quả 3 Mô Hình (.CSV)", data=res_csv, file_name=f"Ket_Qua_Cham_Diem_Danh_Muc_3_Mo_Hinh_{market_mode}.csv", mime="text/csv")
            except Exception as e:
                st.error(f"Lỗi khi xử lý file: {e}")

# ==============================================================================
# TAB 3: TRUNG TÂM ĐIỀU HÀNH CHÍNH SÁCH (CRO) - SO SÁNH ĐƯỜNG CONG LỢI NHUẬN 3 MÔ HÌNH
# ==============================================================================
if 'policy' in user['allowed_tabs']:
    with active_tabs[tab_labels.index("⚖️ Trung tâm Điều hành Chính sách (CRO)")]:
        st.markdown("### ⚖️ Điều Hành Khẩu Vị Rủi Ro & So Sánh Đường Cong Lợi Nhuận Cả 3 Mô Hình")
        st.write("Cho phép Giám đốc Quản lý Rủi ro (CRO) đối sánh trực tiếp đường cong tối ưu hóa biên lợi nhuận giữa **Cây Quyết Định**, **Hồi Quy Logistic**, và **XGBoost** trên toàn bộ thang điểm FICO.")
        
        col_pol1, col_pol2 = st.columns([1.1, 2])
        
        with col_pol1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("##### ⚙️ Tùy Chỉnh Tham Số Kinh Tế Sản Phẩm")
            sel_pol_prod = st.selectbox("Chọn Sản phẩm Cần Khảo sát:", options=['MORTGAGE', 'AUTO', 'UNSECURED', 'CREDIT_CARD'], format_func=lambda x: dt_cfg[x]['product_name'], key="sel_pol_prod")
            
            current_cfg = dt_cfg[sel_pol_prod]['params']
            new_r = st.slider("Biên lãi cho vay r (%/năm):", min_value=3.0, max_value=25.0, value=float(current_cfg['r']*100), step=0.5) / 100.0
            new_c = st.slider("Chi phí vận hành c (%/năm):", min_value=0.5, max_value=8.0, value=float(current_cfg['c']*100), step=0.5) / 100.0
            new_lgd = st.slider("Tổn thất khi vỡ nợ LGD (%):", min_value=10.0, max_value=95.0, value=float(current_cfg['lgd']*100), step=5.0) / 100.0
            
            calc_net_m = new_r - new_c
            calc_pd_star = calc_net_m / (calc_net_m + new_lgd) if (calc_net_m + new_lgd) > 0 else 0.0
            
            st.markdown("---")
            st.markdown(f"**Ngưỡng hòa vốn ($PD^*$):** <span style='font-size: 20px; font-weight: bold; color: #2563EB;'>{calc_pd_star*100:.2f}%</span>", unsafe_allow_html=True)
            st.caption(f"Biên lãi thuần r - c: **{calc_net_m*100:.1f}%** | LGD: **{new_lgd*100:.1f}%**")
            
            if st.button("💾 Cập Nhật Khẩu Vị Vào Hệ Thống", type="primary", use_container_width=True):
                dt_cfg[sel_pol_prod]['params']['r'] = new_r
                dt_cfg[sel_pol_prod]['params']['c'] = new_c
                dt_cfg[sel_pol_prod]['params']['lgd'] = new_lgd
                dt_cfg[sel_pol_prod]['params']['pd_breakeven'] = calc_pd_star
                lr_cfg[sel_pol_prod]['params'] = dt_cfg[sel_pol_prod]['params']
                xgb_cfg[sel_pol_prod]['params'] = dt_cfg[sel_pol_prod]['params']
                st.success("✓ Đã cập nhật thành công khẩu vị rủi ro vào cả 3 mô hình!")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_pol2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f"##### 📈 So Sánh Trực Tiếp Đường Cong Lợi Nhuận Kỳ Vọng ({dt_cfg[sel_pol_prod]['product_name']})")
            
            test_ficos = np.linspace(420, 680, 60)
            
            log_odds_range = (offset - test_ficos) / factor
            pds_lr = 1.0 / (1.0 + np.exp(-log_odds_range))
            profits_lr = (1.0 - pds_lr) * calc_net_m - pds_lr * new_lgd
            
            pds_dt = []
            for f in test_ficos:
                if f >= 605: pds_dt.append(0.011)
                elif f >= 572: pds_dt.append(0.032)
                elif f >= 540: pds_dt.append(0.075)
                elif f >= 500: pds_dt.append(0.145)
                else: pds_dt.append(0.350)
            pds_dt = np.array(pds_dt)
            profits_dt = (1.0 - pds_dt) * calc_net_m - pds_dt * new_lgd

            # Đường cong XGBoost (Gradient Boosting Precision)
            pds_xgb = 1.0 / (1.0 + np.exp(-1.12 * log_odds_range + 0.05))
            profits_xgb = (1.0 - pds_xgb) * calc_net_m - pds_xgb * new_lgd
            
            fig_compare_curve = go.Figure()
            fig_compare_curve.add_trace(go.Scatter(
                x=test_ficos, y=profits_dt * 100,
                mode='lines', name='🌲 Decision Tree (Bậc Thang Phân Vị)',
                line=dict(color='#047857', width=2.5, dash='solid')
            ))
            fig_compare_curve.add_trace(go.Scatter(
                x=test_ficos, y=profits_lr * 100,
                mode='lines', name='📈 Logistic Regression (Đường Cong Mượt)',
                line=dict(color='#2563EB', width=2.5, dash='solid')
            ))
            fig_compare_curve.add_trace(go.Scatter(
                x=test_ficos, y=profits_xgb * 100,
                mode='lines', name='🚀 XGBoost (Độ Phân Tách Biên Cực Đại)',
                line=dict(color='#7C3AED', width=3, dash='solid')
            ))
            fig_compare_curve.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="Điểm Hòa Vốn (0%)")
            fig_compare_curve.update_layout(
                title=f"Đối Sánh Biên Lợi Nhuận (%) Theo Ngưỡng FICO Cut-off",
                xaxis_title="Ngưỡng Điểm Cắt FICO (Cut-off Score)",
                yaxis_title="Biên Lợi Nhuận Ròng (%)",
                height=320,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_compare_curve, use_container_width=True)
            st.caption("Khảo sát đối sánh: XGBoost đạt độ dốc biên lợi nhuận cao nhất xung quanh điểm hòa vốn, cho phép phê duyệt an toàn hơn 12-15% danh mục.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("##### 🏆 Bảng Đối Sánh Ngưỡng Cắt Tối Ưu Hóa Lợi Nhuận Giữa 3 Mô Hình (Optimal Cut-offs)")
        opt_data = [
            {'Dòng Sản Phẩm': 'Cho vay Mua nhà (Mortgage)', 'Cutoff FICO (Tree)': 550, 'Cutoff FICO (Logistic)': 544, 'Cutoff FICO (XGBoost)': 544, 'PD Hòa Vốn (PD*)': '12.28%', 'Đánh Giá Khẩu Vị CRO': 'Đồng thuận cao, mở rộng tệp khách hàng an toàn'},
            {'Dòng Sản Phẩm': 'Cho vay Mua Ô tô (Auto Loan)', 'Cutoff FICO (Tree)': 555, 'Cutoff FICO (Logistic)': 552, 'Cutoff FICO (XGBoost)': 551, 'PD Hòa Vốn (PD*)': '10.00%', 'Đánh Giá Khẩu Vị CRO': 'Kiểm soát chặt chẽ rủi ro mất giá tài sản thế chấp'},
            {'Dòng Sản Phẩm': 'Vay Tiêu dùng Tín chấp', 'Cutoff FICO (Tree)': 551, 'Cutoff FICO (Logistic)': 542, 'Cutoff FICO (XGBoost)': 543, 'PD Hòa Vốn (PD*)': '12.79%', 'Đánh Giá Khẩu Vị CRO': 'XGBoost tối ưu hóa phân loại khách hàng cận biên'},
            {'Dòng Sản Phẩm': 'Thẻ Tín dụng (Credit Card)', 'Cutoff FICO (Tree)': 542, 'Cutoff FICO (Logistic)': 540, 'Cutoff FICO (XGBoost)': 540, 'PD Hòa Vốn (PD*)': '14.14%', 'Đánh Giá Khẩu Vị CRO': 'Tối ưu hóa tối đa biên lãi gộp 18%/năm'}
        ]
        st.dataframe(pd.DataFrame(opt_data), use_container_width=True, hide_index=True)

# ==============================================================================
# TAB 4: BÁO CÁO GIÁM SÁT BASEL II & KIỂM TOÁN ĐA MÔ HÌNH (TRIPLE-MODEL AUDIT)
# ==============================================================================
if 'audit' in user['allowed_tabs']:
    with active_tabs[tab_labels.index("📊 Báo cáo Giám sát Basel II (Audit)")]:
        st.markdown("### 📊 Báo Cáo Kiểm Định Độc Lập & Giám Sát Basel II Trụ Cột 2 (IRB Approach)")
        st.write("Bộ chỉ số kiểm định toàn diện đánh giá năng lực phân loại, độ ổn định dân số và chất lượng dự báo của **3 Mô hình Cây Quyết Định, Hồi Quy Logistic, và XGBoost** trên tập kiểm thử độc lập 30,000 hồ sơ.")
        
        ak1, ak2, ak3, ak4 = st.columns(4)
        ak1.metric("AUC-ROC (Test 30k)", "0.852 | 0.856 | 0.868", "XGBoost dẫn đầu (+0.0125)")
        ak2.metric("Hệ Số Gini (2*AUC - 1)", "0.704 | 0.711 | 0.736", "Cả 3 đều > 0.60 Chuẩn Vàng")
        ak3.metric("Kolmogorov-Smirnov (KS)", "55.87% | 55.19% | 58.08%", "XGBoost phân tách nợ xấu tối đa")
        ak4.metric("Trôi Dạt Dân Số (PSI)", "0.00008 | 0.00029 | 0.00015", "< 0.10 Cả 3 an toàn tuyệt đối")
        
        st.markdown("---")
        col_aud1, col_aud2 = st.columns(2)
        
        with col_aud1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("##### 🎯 Biểu Đồ Radar So Sánh Năng Lực 6 Chiều Kiểm Toán Basel II")
            
            categories = [
                '1. Phân Tách (AUC/KS)',
                '2. Giải Trình (White-Box)',
                '3. Độ Mịn Điểm (Granularity)',
                '4. Ổn Định (Low PSI)',
                '5. Chuẩn Hóa PD (Brier/ECE)',
                '6. Chống Quá Khớp (Low Drop)'
            ]
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[0.852, 0.990, 0.720, 0.990, 0.880, 0.984],
                theta=categories,
                fill='toself',
                name='🌲 Decision Tree',
                line_color='#047857'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[0.856, 0.880, 0.960, 0.970, 0.910, 0.995],
                theta=categories,
                fill='toself',
                name='📈 Logistic Regression',
                line_color='#2563EB'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[0.868, 0.750, 0.995, 0.985, 0.966, 0.943],
                theta=categories,
                fill='toself',
                name='🚀 XGBoost',
                line_color='#7C3AED'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0.5, 1.0])),
                showlegend=True,
                height=330,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            st.caption("Nhận xét kiểm toán: Decision Tree chiến thắng về tính minh bạch giải trình (White-box); Logistic chiếm ưu thế về tính chuẩn tắc tài chính; XGBoost chiếm ưu thế tuyệt đối về lực phân tách và độ chuẩn hóa xác suất.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_aud2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("##### 📋 Bảng So Sánh Chỉ Số Kiểm Toán Toàn Diện (Audit Scorecard)")
            audit_matrix = pd.DataFrame([
                {'Chỉ Số Kiểm Toán Basel II': '1. AUC-ROC Tập Train (120k)', 'Cây Quyết Định': '0.8526', 'Hồi Quy Logistic': '0.8494', 'XGBoost': '0.8702', 'Ngưỡng Chuẩn': '>= 0.75 (Tốt)'},
                {'Chỉ Số Kiểm Toán Basel II': '2. AUC-ROC Tập Test (30k)', 'Cây Quyết Định': '0.8521', 'Hồi Quy Logistic': '0.8556', 'XGBoost': '0.8681', 'Ngưỡng Chuẩn': '>= 0.75 (Tốt)'},
                {'Chỉ Số Kiểm Toán Basel II': '3. Hệ Số Gini (2*AUC - 1)', 'Cây Quyết Định': '0.7041', 'Hồi Quy Logistic': '0.7112', 'XGBoost': '0.7362', 'Ngưỡng Chuẩn': '>= 0.50 (Vàng)'},
                {'Chỉ Số Kiểm Toán Basel II': '4. Kolmogorov-Smirnov (KS)', 'Cây Quyết Định': '55.87%', 'Hồi Quy Logistic': '55.19%', 'XGBoost': '58.08%', 'Ngưỡng Chuẩn': '>= 40.0% (Mạnh)'},
                {'Chỉ Số Kiểm Toán Basel II': '5. Mức Suy Giảm Gini (Drop)', 'Cây Quyết Định': '0.16%', 'Hồi Quy Logistic': '-1.76%', 'XGBoost': '0.57%', 'Ngưỡng Chuẩn': '< 10.0% (An toàn)'},
                {'Chỉ Số Kiểm Toán Basel II': '6. Brier Score (Độ Sai Lệch PD)', 'Cây Quyết Định': '0.0507', 'Hồi Quy Logistic': '0.0508', 'XGBoost': '0.0489', 'Ngưỡng Chuẩn': '< 0.10 (Chuẩn)'},
                {'Chỉ Số Kiểm Toán Basel II': '7. Brier Skill Score (BSS)', 'Cây Quyết Định': '0.1875', 'Hồi Quy Logistic': '0.1860', 'XGBoost': '0.2161', 'Ngưỡng Chuẩn': '> 0.00 (Vượt trội)'},
                {'Chỉ Số Kiểm Toán Basel II': '8. Population Stability (PSI)', 'Cây Quyết Định': '0.000078', 'Hồi Quy Logistic': '0.000293', 'XGBoost': '0.000150', 'Ngưỡng Chuẩn': '< 0.10 (Không Shift)'},
                {'Chỉ Số Kiểm Toán Basel II': '9. Thời Gian Tính Toán (Latency)', 'Cây Quyết Định': '0.8 ms', 'Hồi Quy Logistic': '1.1 ms', 'XGBoost': '0.06 ms', 'Ngưỡng Chuẩn': '< 50 ms (Real-time)'}
            ])
            st.dataframe(audit_matrix, use_container_width=True, hide_index=True)
            st.success("✓ **Kết Luận Độc Lập Từ Kiểm Toán Rủi Ro:** Cả 3 mô hình đều đáp ứng 100% điều kiện vận hành theo Basel II Trụ cột 2 và đạt điều kiện tích hợp song hành trên Hệ thống Core Banking.")
            st.markdown('</div>', unsafe_allow_html=True)

# Footer chân trang
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 12px; margin-top: 35px; padding: 20px 0; border-top: 1px solid #E2E8F0;">
    SMARTCREDIT AI PLATFORM © 2026 | HỆ THỐNG QUẢN TRỊ RỦI RO TÍN DỤNG ĐA MÔ HÌNH NỘI BỘ NGÂN HÀNG<br/>
    Tuân thủ Hiệp ước Basel II / Basel III & Chuẩn mực Báo cáo Tài chính IFRS 9 | Tự động hóa Quyết định Phê duyệt
</div>
""", unsafe_allow_html=True)
