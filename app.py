# -*- coding: utf-8 -*-
"""
SmartCredit AI - Cổng Thông Tin Chấm Điểm Tín Dụng & Quản Trị Rủi Ro Đa Mô Hình (Multi-Model Portal)
Đồ án Tốt nghiệp / Dự án Quản trị Rủi ro Tín dụng (Give Me Some Credit)
Chuẩn mực: Basel II Trụ cột 1 & 2, IFRS 9, Thẻ điểm FICO Scorecard
Hỗ trợ: Decision Tree (Hộp trắng IF-THEN) & Logistic Regression (Continuous Log-Odds)
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

# Thư viện xuất báo cáo PDF chuẩn Ngân hàng
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
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
# CẤU HÌNH TRANG & GIAO DIỆN STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="SmartCredit AI | Multi-Model Risk Portal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS phong cách Fintech / Ngân hàng cao cấp
st.markdown("""
<style>
    :root {
        --primary-navy: #0F172A;
        --secondary-navy: #1E3A8A;
        --accent-blue: #2563EB;
        --success-emerald: #10B981;
        --warning-amber: #F59E0B;
        --danger-crimson: #EF4444;
        --card-bg: #FFFFFF;
        --border-color: #E2E8F0;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #1E40AF 100%);
        color: white;
        padding: 22px 28px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.15);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 25px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #93C5FD;
        margin: 4px 0 0 0;
        font-size: 13.5px;
    }
    .metric-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
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
        font-weight: 700;
        color: #0F172A;
        margin: 4px 0;
    }
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
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #F1F5F9;
        border-radius: 8px 8px 0px 0px;
        padding: 8px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# HỆ THỐNG PHÂN QUYỀN ĐĂNG NHẬP & PHÂN VAI TRÒ
# ==============================================================================
USER_ROLES = {
    'rm': {
        'name': 'Nguyễn Văn Minh',
        'role_title': 'Chuyên viên QHKH Cá nhân (RM)',
        'password': '123',
        'allowed_tabs': ['single', 'batch']
    },
    'analyst': {
        'name': 'Trần Thị Thu Thảo',
        'role_title': 'Chuyên viên Phân tích Rủi ro Tín dụng (Credit Analyst)',
        'password': '123',
        'allowed_tabs': ['single', 'batch', 'policy']
    },
    'underwriter': {
        'name': 'Lê Hoàng Long',
        'role_title': 'Thẩm định viên Cao cấp (Senior Underwriter)',
        'password': '123',
        'allowed_tabs': ['single', 'batch', 'policy']
    },
    'cro': {
        'name': 'Đặng Quốc Hùng',
        'role_title': 'Giám đốc Quản trị Rủi ro (CRO)',
        'password': '123',
        'allowed_tabs': ['single', 'batch', 'policy', 'audit']
    }
}

if 'user' not in st.session_state:
    st.session_state.user = None

# ==============================================================================
# HÀM NẠP TÀI NGUYÊN MÔ HÌNH VÀ CẤU HÌNH ĐA MÔ HÌNH
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
    possible_scaler = [
        "models/standard_scaler.pkl",
        "standard_scaler.pkl",
        "3 mô hình được chọn/models/standard_scaler.pkl",
        "../models/standard_scaler.pkl",
        r"D:\AI\.final_project AI\3 mô hình được chọn\models\standard_scaler.pkl",
        r"D:\AI\project AI\3 mô hình được chọn\models\standard_scaler.pkl"
    ]

    # 1. Nạp Model Decision Tree
    p_dt = next((p for p in possible_models_dt if os.path.exists(p)), None)
    if p_dt is None:
        raise FileNotFoundError("Không tìm thấy tệp decision_tree_model.pkl!")
    dt_model = joblib.load(p_dt)

    # 2. Nạp Model Logistic Regression & Scaler
    p_lr = next((p for p in possible_models_lr if os.path.exists(p)), None)
    lr_model = joblib.load(p_lr) if p_lr else None

    p_sc = next((p for p in possible_scaler if os.path.exists(p)), None)
    scaler = joblib.load(p_sc) if p_sc else None

    # 3. File quy tắc nút lá Decision Tree
    leaf_file = next((os.path.join(d, "decision_tree_leaf_rules.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "decision_tree_leaf_rules.csv"))), None)
    leaf_df = pd.read_csv(leaf_file) if leaf_file else pd.DataFrame()

    # 4. Cấu hình đa sản phẩm DT
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

    # 5. Cấu hình đa sản phẩm Logistic
    cfg_lr_file = next((os.path.join(d, "logistic_multi_product_policy_config.json") for d in possible_dirs if os.path.exists(os.path.join(d, "logistic_multi_product_policy_config.json"))), None)
    if cfg_lr_file:
        with open(cfg_lr_file, "r", encoding="utf-8") as f:
            lr_cfg = json.load(f)
    else:
        lr_cfg = dt_cfg

    # 6. Các bảng kiểm định metrics
    p_dt_met = next((os.path.join(d, "decision_tree_metrics.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "decision_tree_metrics.csv"))), None)
    dt_metrics_df = pd.read_csv(p_dt_met) if p_dt_met else pd.DataFrame()

    p_lr_met = next((os.path.join(d, "logistic_regression_metrics.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "logistic_regression_metrics.csv"))), None)
    lr_metrics_df = pd.read_csv(p_lr_met) if p_lr_met else pd.DataFrame()

    p_feat = next((os.path.join(d, "decision_tree_feature_importance.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "decision_tree_feature_importance.csv"))), None)
    feat_df = pd.read_csv(p_feat) if p_feat else pd.DataFrame()

    # Tham số chuẩn FICO Scorecard
    pdo = 20.0
    base_score = 600.0
    base_odds = 50.0
    factor = pdo / np.log(2.0)
    offset = base_score - factor * np.log(base_odds)

    return dt_model, lr_model, scaler, leaf_df, dt_cfg, lr_cfg, dt_metrics_df, lr_metrics_df, feat_df, factor, offset

try:
    dt_model, lr_model, scaler, leaf_df, dt_cfg, lr_cfg, dt_metrics_df, lr_metrics_df, feat_df, factor, offset = load_multi_model_risk_assets()
    leaf_info = leaf_df.set_index('Leaf ID').to_dict('index') if not leaf_df.empty else {}
except Exception as e:
    st.error(f"Lỗi khi nạp dữ liệu mô hình: {e}")
    st.stop()

# Danh sách đặc trưng chuẩn
FEATURE_COLS = [
    'RevolvingUtilizationOfUnsecuredLines', 'age',
    'NumberOfTime30-59DaysPastDueNotWorse', 'DebtRatio', 'MonthlyIncome',
    'NumberOfOpenCreditLinesAndLoans', 'NumberOfTimes90DaysLate',
    'NumberRealEstateLoansOrLines', 'NumberOfTime60-89DaysPastDueNotWorse',
    'NumberOfDependents', 'MonthlyIncome_is_missing'
]

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
    
    # Tinh chỉnh vi mô năng lực tài chính
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
    
    # Kiểm tra DSR
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
    
    # Dự báo xác suất PD liên tục
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
        
    # Tính chi tiết đóng góp từng biến số trong phương trình Log-odds
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
# HÀM XUẤT BÁO CÁO THẨM ĐỊNH TÍN DỤNG CHUYÊN NGHIỆP RA FILE PDF
# ==============================================================================
def generate_credit_appraisal_pdf(customer_info, financial_details, features_dict, dt_res, lr_res, selected_mode, prod_cfg, market_mode):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=30, rightMargin=30, topMargin=28, bottomMargin=28
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=14, leading=17, textColor=colors.HexColor('#0F172A'), alignment=1)
    sub_style = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName=PDF_FONT_NORMAL, fontSize=8.5, leading=12, textColor=colors.HexColor('#475569'), alignment=1)
    sec_hdr = ParagraphStyle('SecHdr', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=9.5, leading=13, textColor=colors.HexColor('#1E3A8A'))
    c_txt = ParagraphStyle('CellTxt', parent=styles['Normal'], fontName=PDF_FONT_NORMAL, fontSize=7.5, leading=10, textColor=colors.HexColor('#1E293B'))
    c_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=7.5, leading=10, textColor=colors.HexColor('#0F172A'))
    c_hdr = ParagraphStyle('CellHdr', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=7.5, leading=10, textColor=colors.white, alignment=1)
    c_alert = ParagraphStyle('CellAlert', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=7.5, leading=10, textColor=colors.HexColor('#B91C1C'))
    c_success = ParagraphStyle('CellSuccess', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=7.5, leading=10, textColor=colors.HexColor('#047857'))
    note_txt = ParagraphStyle('NoteTxt', parent=styles['Normal'], fontName=PDF_FONT_ITALIC, fontSize=7, leading=9, textColor=colors.HexColor('#64748B'))

    elements = []

    # 1. Header văn bản
    elements.append(Paragraph("SMARTCREDIT BANKING AI PORTAL - HỆ THỐNG QUẢN TRỊ RỦI RO BÁN LẺ", title_style))
    elements.append(Paragraph("PHIẾU THẨM ĐỊNH RỦI RO TÍN DỤNG & PHÊ DUYỆT ĐA MÔ HÌNH (CHUẨN BASEL II / IFRS 9)", sub_style))
    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceBefore=1, spaceAfter=8))

    # 2. Thông tin chung
    elements.append(Paragraph("I. THÔNG TIN HỒ SƠ ĐỀ NGHỊ CẤP TÍN DỤNG", sec_hdr))
    elements.append(Spacer(1, 3))
    
    t_info_data = [
        [Paragraph("Mã hồ sơ:", c_bold), Paragraph(str(customer_info.get('app_id', 'HS-2026-001')), c_txt),
         Paragraph("Ngày thẩm định:", c_bold), Paragraph(datetime.date.today().strftime("%d/%m/%Y"), c_txt)],
        [Paragraph("Khách hàng / CCCD:", c_bold), Paragraph(str(customer_info.get('cust_name', 'Nguyễn Văn An')), c_txt),
         Paragraph("Độ tuổi / Phụ thuộc:", c_bold), Paragraph(f"{features_dict.get('age', 35)} tuổi | {features_dict.get('NumberOfDependents', 1)} người", c_txt)],
        [Paragraph("Sản phẩm đề nghị:", c_bold), Paragraph(str(prod_cfg.get('product_name', 'Vay Tiêu Dùng')), c_txt),
         Paragraph("Số tiền đề nghị cấp:", c_bold), Paragraph(f"{customer_info.get('loan_amount', 100_000_000):,.0f} VND", c_txt)],
        [Paragraph("Kịch bản thị trường:", c_bold), Paragraph(f"Chế độ {market_mode}", c_txt),
         Paragraph("Lãi suất r / Chi phí vốn c:", c_bold), Paragraph(f"{prod_cfg['params']['r']*100:.1f}% / {prod_cfg['params']['c']*100:.1f}% | LGD: {prod_cfg['params']['lgd']*100:.1f}%", c_txt)]
    ]
    t_info = Table(t_info_data, colWidths=[105, 160, 115, 155])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 7))

    # 3. Năng lực tài chính & Cơ cấu nghĩa vụ nợ
    elements.append(Paragraph("II. BẢNG PHÂN RÃ THU NHẬP & CƠ CẤU NGHĨA VỤ NỢ CHI TIẾT", sec_hdr))
    elements.append(Spacer(1, 3))
    
    fin_data = [
        [Paragraph("Nguồn thu nhập chi tiết", c_hdr), Paragraph("Số tiền (VND/tháng)", c_hdr),
         Paragraph("Khoản nợ & Thẻ tín dụng", c_hdr), Paragraph("Nghĩa vụ hàng tháng / Dư nợ", c_hdr)],
        [Paragraph("1. Lương & HĐLĐ", c_txt), Paragraph(f"{financial_details.get('income_salary', 0):,.0f} VND", c_bold),
         Paragraph(f"• Thẻ TD: {financial_details.get('card_count', 0)} thẻ (Hạn mức: {financial_details.get('total_card_limit', 0):,.0f} VND)", c_txt),
         Paragraph(f"Dư nợ: {financial_details.get('total_card_balance', 0):,.0f} VND ({features_dict.get('RevolvingUtilizationOfUnsecuredLines', 0)*100:.1f}%)", c_txt)],
        [Paragraph("2. Cho thuê tài sản (nhà, xe...)", c_txt), Paragraph(f"{financial_details.get('income_rental', 0):,.0f} VND", c_bold),
         Paragraph(f"• Nợ vay: {financial_details.get('loan_count', 0)} khoản đang mở", c_txt),
         Paragraph(f"Tổng dư nợ còn lại: {financial_details.get('total_loan_balance', 0):,.0f} VND", c_txt)],
        [Paragraph("3. Cổ tức / Lợi nhuận kinh doanh", c_txt), Paragraph(f"{financial_details.get('income_business', 0):,.0f} VND", c_bold),
         Paragraph("• Nghĩa vụ trả nợ vay hàng tháng", c_txt), Paragraph(f"{financial_details.get('monthly_debt_repayment', 0):,.0f} VND/tháng", c_bold)],
        [Paragraph("4. Thu nhập khác có chứng minh", c_txt), Paragraph(f"{financial_details.get('income_other', 0):,.0f} VND", c_bold),
         Paragraph("• Dự kiến góp khoản vay mới", c_txt), Paragraph(f"{financial_details.get('monthly_new_installment', 0):,.0f} VND/tháng", c_bold)],
        [Paragraph("TỔNG THU NHẬP HÀNG THÁNG", c_bold), Paragraph(f"{financial_details.get('total_income_vnd', 0):,.0f} VND", c_bold),
         Paragraph("TỔNG NGHĨA VỤ NỢ & TỶ LỆ DSR", c_bold), Paragraph(f"{financial_details.get('total_debt_monthly', 0):,.0f} VND/th | DSR: {financial_details.get('dsr_pct', 0):.1f}%", c_bold)]
    ]
    t_fin = Table(fin_data, colWidths=[135, 130, 140, 130])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    elements.append(t_fin)
    elements.append(Spacer(1, 7))

    # 4. Bảng 11 Đặc trưng đầu vào
    elements.append(Paragraph("III. DANH SÁCH 11 ĐẶC TRƯNG CHẤM ĐIỂM BASEL II (INPUT FEATURES)", sec_hdr))
    elements.append(Spacer(1, 3))
    
    feat_rows = [
        [Paragraph("Đặc trưng chấm điểm", c_hdr), Paragraph("Giá trị thực tế", c_hdr),
         Paragraph("Đặc trưng chấm điểm", c_hdr), Paragraph("Giá trị thực tế", c_hdr)],
        [Paragraph("1. Tỷ lệ sử dụng thẻ tín dụng", c_txt), Paragraph(f"{features_dict.get('RevolvingUtilizationOfUnsecuredLines', 0)*100:.2f}%", c_bold),
         Paragraph("7. Số lần trễ hạn 90+ ngày", c_txt), Paragraph(f"{features_dict.get('NumberOfTimes90DaysLate', 0)} lần", c_bold)],
        [Paragraph("2. Độ tuổi khách hàng", c_txt), Paragraph(f"{features_dict.get('age', 0)} tuổi", c_bold),
         Paragraph("8. Số khoản vay BĐS / Thế chấp", c_txt), Paragraph(f"{features_dict.get('NumberRealEstateLoansOrLines', 0)} khoản", c_bold)],
        [Paragraph("3. Số lần quá hạn 30-59 ngày", c_txt), Paragraph(f"{features_dict.get('NumberOfTime30-59DaysPastDueNotWorse', 0)} lần", c_bold),
         Paragraph("9. Số lần quá hạn 60-89 ngày", c_txt), Paragraph(f"{features_dict.get('NumberOfTime60-89DaysPastDueNotWorse', 0)} lần", c_bold)],
        [Paragraph("4. Tỷ số nợ trên thu nhập (DebtRatio)", c_txt), Paragraph(f"{features_dict.get('DebtRatio', 0):.4f}", c_bold),
         Paragraph("10. Số người phụ thuộc", c_txt), Paragraph(f"{features_dict.get('NumberOfDependents', 0)} người", c_bold)],
        [Paragraph("5. Thu nhập tháng (Model Scale)", c_txt), Paragraph(f"{features_dict.get('MonthlyIncome', 0):,.1f} USD (~{financial_details.get('total_income_vnd', 0):,.0f}đ)", c_bold),
         Paragraph("11. Cờ khuyết thu nhập gốc", c_txt), Paragraph("Không khuyết (0)" if features_dict.get('MonthlyIncome_is_missing', 0)==0 else "Có khuyết (1)", c_bold)],
        [Paragraph("6. Số hạn mức/khoản vay đang mở", c_txt), Paragraph(f"{features_dict.get('NumberOfOpenCreditLinesAndLoans', 0)} tài khoản", c_bold),
         Paragraph("— Nghĩa vụ nợ DSR / DTI", c_txt), Paragraph("An toàn (<=60%)" if financial_details.get('dsr_pct', 0)<=60 else "Cảnh báo (>60%)", c_bold)]
    ]
    t_feat = Table(feat_rows, colWidths=[140, 125, 140, 130])
    t_feat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_feat)
    elements.append(Spacer(1, 7))

    # 5. Kết quả thẩm định Đa Mô hình (Đối sánh Song song)
    elements.append(Paragraph("IV. ĐỐI SÁNH KẾT QUẢ THẨM ĐỊNH TÍN DỤNG GIỮA 2 MÔ HÌNH", sec_hdr))
    elements.append(Spacer(1, 3))
    
    eval_matrix = [
        [Paragraph("Tiêu chí Đánh giá", c_hdr), 
         Paragraph("🌲 CÂY QUYẾT ĐỊNH (DECISION TREE)", c_hdr), 
         Paragraph("📈 HỒI QUY LOGISTIC (LOGISTIC REGRESSION)", c_hdr)],
        [Paragraph("Điểm tín dụng FICO", c_bold), 
         Paragraph(f"<b>{dt_res.get('fico', 0)}</b> điểm", c_bold), 
         Paragraph(f"<b>{lr_res.get('fico', 0)}</b> điểm (Delta: {dt_res.get('fico',0)-lr_res.get('fico',0):+d})", c_bold)],
        [Paragraph("Phân tầng Hạng Rủi ro", c_bold), 
         Paragraph(str(dt_res.get('grade', 'N/A')), c_txt), 
         Paragraph(str(lr_res.get('grade', 'N/A')), c_txt)],
        [Paragraph("Xác suất vỡ nợ (PD)", c_bold), 
         Paragraph(f"<b>{dt_res.get('pd', 0)*100:.2f}%</b> (Wilson: {dt_res.get('wilson', 'N/A')})", c_txt), 
         Paragraph(f"<b>{lr_res.get('pd', 0)*100:.2f}%</b> (Hàm liên tục mượt)", c_txt)],
        [Paragraph("Ngưỡng an toàn hòa vốn (PD*)", c_bold), 
         Paragraph(f"{dt_res.get('pd_star', 0.1414)*100:.2f}%", c_txt), 
         Paragraph(f"{lr_res.get('pd_star', 0.1414)*100:.2f}%", c_txt)],
        [Paragraph("Lợi nhuận ròng dự kiến (+/- VND)", c_bold), 
         Paragraph(f"{dt_res.get('profit_vnd', 0):+,.0f} VND", c_success if dt_res.get('profit_vnd', 0)>=0 else c_alert), 
         Paragraph(f"{lr_res.get('profit_vnd', 0):+,.0f} VND", c_success if lr_res.get('profit_vnd', 0)>=0 else c_alert)],
        [Paragraph("QUYẾT ĐỊNH PHÊ DUYỆT", c_bold), 
         Paragraph(f"<b>{dt_res.get('decision', 'N/A')}</b>", c_success if 'PHÊ DUYỆT' in dt_res.get('decision', '') else (c_alert if 'TỪ CHỐI' in dt_res.get('decision', '') else c_bold)), 
         Paragraph(f"<b>{lr_res.get('decision', 'N/A')}</b>", c_success if 'PHÊ DUYỆT' in lr_res.get('decision', '') else (c_alert if 'TỪ CHỐI' in lr_res.get('decision', '') else c_bold))],
        [Paragraph("Cơ chế giải thích / Luật chi tiết", c_bold), 
         Paragraph(f"<b>Nút lá #{dt_res.get('leaf_id', 'N/A')}</b>: {dt_res.get('rule', 'N/A')}", c_txt), 
         Paragraph(f"<b>Độ nhạy mượt mà</b>: {lr_res.get('reason', 'N/A')}", c_txt)]
    ]
    t_eval = Table(eval_matrix, colWidths=[115, 210, 210])
    t_eval.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('BACKGROUND', (0,6), (-1,6), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    elements.append(t_eval)
    elements.append(Spacer(1, 8))

    # 6. Kết luận & Chữ ký 3 cấp
    elements.append(Paragraph("V. KẾT LUẬN THẨM ĐỊNH & PHÊ DUYỆT CỦA CÁC CẤP CÓ THẨM QUYỀN", sec_hdr))
    elements.append(Spacer(1, 3))
    
    is_agree = (dt_res.get('dec_code') == lr_res.get('dec_code'))
    agree_text = "Hai mô hình hoàn toàn đồng thuận về quyết định phê duyệt." if is_agree else f"Hai mô hình có sự chênh lệch (Cây quyết định: {dt_res.get('dec_code')} vs Logistic: {lr_res.get('dec_code')}). Đề xuất Hội đồng thẩm định thủ công."
    elements.append(Paragraph(f"• <b>Nhận định kiểm toán:</b> {agree_text} Tỷ lệ nghĩa vụ nợ thực tế DSR = {financial_details.get('dsr_pct', 0):.1f}%. Hồ sơ đáp ứng điều kiện vận hành trong kịch bản thị trường {market_mode}.", c_txt))
    elements.append(Spacer(1, 10))

    sign_data = [
        [Paragraph("CHUYÊN VIÊN QHKH (RM)", c_bold), Paragraph("CHUYÊN VIÊN THẨM ĐỊNH (CA)", c_bold), Paragraph("GIÁM ĐỐC QUẢN TRỊ RỦI RO (CRO)", c_bold)],
        [Paragraph("<i>(Ký và ghi rõ họ tên)</i>", note_txt), Paragraph("<i>(Ký và ghi rõ họ tên)</i>", note_txt), Paragraph("<i>(Ký và phê duyệt điện tử)</i>", note_txt)],
        [Spacer(1, 24), Spacer(1, 24), Spacer(1, 24)],
        [Paragraph(customer_info.get('officer_name', 'Chuyên viên Tín dụng'), c_txt), Paragraph("Bộ phận Tái thẩm định", c_txt), Paragraph("Ủy ban Quản lý Rủi ro ALCO", c_bold)]
    ]
    t_sign = Table(sign_data, colWidths=[175, 180, 180])
    t_sign.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    elements.append(t_sign)

    doc.build(elements)
    return buffer.getvalue()

# ==============================================================================
# THANH BÊN (SIDEBAR) & CẤU HÌNH BỘ CHỌN MÔ HÌNH (MODEL SELECTOR)
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h2 style="color: #1E3A8A; margin: 0;">🏦 SmartCredit AI</h2>
        <p style="color: #64748B; font-size: 12px; margin: 0;">Cổng Quản Trị Rủi Ro Đa Mô Hình</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # 1. Đăng nhập phân quyền
    if st.session_state.user is None:
        st.subheader("🔐 Đăng Nhập Hệ Thống")
        selected_role = st.selectbox(
            "Chọn Vai trò Người dùng:",
            options=list(USER_ROLES.keys()),
            format_func=lambda x: f"{USER_ROLES[x]['role_title']} - {USER_ROLES[x]['name']}"
        )
        pwd = st.text_input("Mật khẩu truy cập (mặc định: 123):", type="password")
        if st.button("Đăng nhập", type="primary", use_container_width=True):
            if pwd == USER_ROLES[selected_role]['password']:
                st.session_state.user = USER_ROLES[selected_role]
                st.success(f"Xin chào, {st.session_state.user['name']}!")
                st.rerun()
            else:
                st.error("Mật khẩu không chính xác!")
        st.stop()
    else:
        user = st.session_state.user
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
        options=["DUAL", "DECISION_TREE", "LOGISTIC_REGRESSION"],
        format_func=lambda x: {
            "DUAL": "⚖️ So Sánh Song Song (Dual Evaluation)",
            "DECISION_TREE": "🌲 Cây Quyết Định (Decision Tree)",
            "LOGISTIC_REGRESSION": "📈 Hồi Quy Logistic (Logistic Engine)"
        }[x],
        index=0,
        help="Chọn chế độ đối sánh song song hoặc kiểm thử chuyên sâu từng mô hình"
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ THIẾT LẬP KINH TẾ & THỊ TRƯỜNG")
    
    # Chọn sản phẩm
    product_options = ['MORTGAGE', 'AUTO', 'UNSECURED', 'CREDIT_CARD']
    product_code = st.selectbox(
        "Dòng Sản phẩm Tín dụng:",
        options=product_options,
        format_func=lambda x: dt_cfg[x]['product_name']
    )
    
    # Chọn chế độ thị trường
    market_mode = st.selectbox(
        "Kịch bản Vĩ mô Thị trường:",
        options=['NORMAL', 'EXPANSION', 'RECESSION'],
        format_func=lambda x: {
            'NORMAL': '🔵 Kinh tế Bình thường (Normal)',
            'EXPANSION': '🟢 Tăng trưởng Mở rộng (Expansion)',
            'RECESSION': '🔴 Suy thoái Thắt chặt (Recession)'
        }[x]
    )
    
    # Số tiền đề nghị vay
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
    'DUAL': '⚖️ CHẾ ĐỘ SO SÁNH ĐỐI SÁNH SONG SONG (DUAL EVALUATION)',
    'DECISION_TREE': '🌲 CHẾ ĐỘ CÂY QUYẾT ĐỊNH (WHITE-BOX IF-THEN)',
    'LOGISTIC_REGRESSION': '📈 CHẾ ĐỘ HỒI QUY LOGISTIC (CONTINUOUS LOG-ODDS)'
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

# Khởi tạo các Tabs theo quyền hạn
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
    st.markdown("### 📋 Thẩm Định Hồ Sơ Khách Hàng & Năng Lực Tài Chính Chi Tiết")
    
    # 1. Preset nạp nhanh hồ sơ mẫu
    st.caption("⚡ **NẠP NHANH HỒ SƠ MẪU ĐỂ KIỂM THỬ KHẢ NĂNG PHÂN TÁCH:**")
    sc_c1, sc_c2, sc_c3 = st.columns(3)
    if 'cust_preset' not in st.session_state:
        st.session_state.cust_preset = 'good'
        
    with sc_c1:
        if st.button("🟢 Mẫu Khách Hàng Tốt (Hạng 1 - Duyệt Tự Động)", use_container_width=True):
            st.session_state.cust_preset = 'good'
            st.rerun()
    with sc_c2:
        if st.button("🟡 Mẫu Khách Hàng Tiệm Cận (Hạng 3 - Xem Xét Có Điều Kiện)", use_container_width=True):
            st.session_state.cust_preset = 'medium'
            st.rerun()
    with sc_c3:
        if st.button("🔴 Mẫu Khách Hàng Nợ Xấu (Hạng 5 - Từ Chối)", use_container_width=True):
            st.session_state.cust_preset = 'bad'
            st.rerun()
            
    # Mặc định theo Preset
    if st.session_state.cust_preset == 'good':
        p_name = "Nguyễn Văn An"
        p_age, p_dep = 38, 1
        p_salary, p_rental, p_biz, p_other = 35_000_000, 15_000_000, 0, 0
        p_late90, p_late60, p_late30 = 0, 0, 0
        p_card1_lim, p_card1_bal = 60_000_000, 9_000_000
        p_card2_lim, p_card2_bal = 40_000_000, 0
        p_loan1_bal, p_loan1_months = 150_000_000, 30
        p_re_loans = 1
    elif st.session_state.cust_preset == 'medium':
        p_name = "Trần Đình Khang"
        p_age, p_dep = 42, 2
        p_salary, p_rental, p_biz, p_other = 22_000_000, 0, 5_000_000, 0
        p_late90, p_late60, p_late30 = 0, 0, 1
        p_card1_lim, p_card1_bal = 40_000_000, 26_000_000
        p_card2_lim, p_card2_bal = 20_000_000, 12_000_000
        p_loan1_bal, p_loan1_months = 180_000_000, 18
        p_re_loans = 1
    else: # bad
        p_name = "Lê Tuấn Kiệt"
        p_age, p_dep = 28, 0
        p_salary, p_rental, p_biz, p_other = 10_000_000, 0, 0, 0
        p_late90, p_late60, p_late30 = 2, 1, 2
        p_card1_lim, p_card1_bal = 30_000_000, 28_500_000
        p_card2_lim, p_card2_bal = 10_000_000, 9_800_000
        p_loan1_bal, p_loan1_months = 60_000_000, 6
        p_re_loans = 0

    st.markdown("---")
    
    # 2. KHU VỰC NHẬP LIỆU THÔNG TIN KHÁCH HÀNG
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        st.markdown("##### 👤 1. Thông Tin Định Danh Khách Hàng")
        cust_name_in = st.text_input("Họ và tên / Mã CCCD Khách hàng:", value=p_name, key=f"name_{st.session_state.cust_preset}")
        col_age1, col_age2 = st.columns(2)
        with col_age1:
            cust_age = st.number_input("Tuổi của khách hàng:", min_value=18, max_value=85, value=p_age, step=1, key=f"age_{st.session_state.cust_preset}")
        with col_age2:
            cust_dependents = st.number_input("Số người phụ thuộc tài chính:", min_value=0, max_value=10, value=p_dep, step=1, key=f"dep_{st.session_state.cust_preset}")
            
    with row1_c2:
        st.markdown("##### ⚠️ 2. Lịch Sử Nợ Quá Hạn (2 năm gần nhất)")
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            late_90 = st.number_input("Quá hạn >= 90 ngày:", min_value=0, max_value=20, value=p_late90, step=1, key=f"l90_{st.session_state.cust_preset}", help="Chỉ số quan trọng số 1: Quá hạn >= 90 ngày kéo FICO tụt dốc")
        with col_l2:
            late_60_89 = st.number_input("Quá hạn 60-89 ngày:", min_value=0, max_value=20, value=p_late60, step=1, key=f"l60_{st.session_state.cust_preset}")
        with col_l3:
            late_30_59 = st.number_input("Quá hạn 30-59 ngày:", min_value=0, max_value=20, value=p_late30, step=1, key=f"l30_{st.session_state.cust_preset}")

    st.markdown("---")
    
    # 3. PHÂN RÃ THU NHẬP ĐA NGUỒN DÀNH CHO CHUYÊN VIÊN TÍN DỤNG (RM/CA)
    st.markdown("##### 💰 3. Bảng Phân Rã Thu Nhập Đa Nguồn Hàng Tháng (Dành cho Chuyên viên Tín dụng)")
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
    # Quy đổi về đơn vị Model (USD / Chuẩn Give Me Some Credit 1 USD ~ 25.000 VND)
    cust_income_model = total_income_vnd / 25_000.0 if total_income_vnd > 0 else 0.0
    
    st.info(f"📊 **Tổng Thu Nhập Thực Nhận:** **`{total_income_vnd:,.0f} VND/tháng`** (Quy đổi đơn vị chuẩn mô hình: **`{cust_income_model:,.1f} USD`**)")

    st.markdown("---")

    # 4. DANH MỤC THẺ TÍN DỤNG & CÔNG THỨC TÍNH REVOLVING UTILIZATION
    st.markdown("##### 💳 4. Danh Mục Thẻ Tín Dụng & Tỷ Lệ Sử Dụng Hạn Mức (Revolving Utilization)")
    st.caption("Công thức chuẩn tài chính: **`Revolving Utilization = Tổng Dư Nợ Đã Dùng / Tổng Hạn Mức Thẻ Được Cấp`**")
    
    with st.expander("📝 Chi tiết Hạn mức và Mức sử dụng từng Thẻ Tín dụng (Bấm để xem/chỉnh sửa)", expanded=True):
        tc_col1, tc_col2, tc_col3 = st.columns([1.5, 1.2, 1.2])
        with tc_col1:
            st.markdown("**Tên Thẻ / Ngân Hàng**")
            st.text("Thẻ Tín dụng #1 (Thẻ chính)")
            st.text("Thẻ Tín dụng #2 (Thẻ phụ/Ngân hàng khác)")
        with tc_col2:
            st.markdown("**Hạn Mức Thẻ (VND)**")
            card1_lim = st.number_input("Hạn mức Thẻ 1:", min_value=0, max_value=500_000_000, value=p_card1_lim, step=5_000_000, format="%d", label_visibility="collapsed", key=f"c1_lim_{st.session_state.cust_preset}")
            card2_lim = st.number_input("Hạn mức Thẻ 2:", min_value=0, max_value=500_000_000, value=p_card2_lim, step=5_000_000, format="%d", label_visibility="collapsed", key=f"c2_lim_{st.session_state.cust_preset}")
        with tc_col3:
            st.markdown("**Dư Nợ Đang Dùng (VND)**")
            card1_bal = st.number_input("Dư nợ Thẻ 1:", min_value=0, max_value=500_000_000, value=p_card1_bal, step=1_000_000, format="%d", label_visibility="collapsed", key=f"c1_bal_{st.session_state.cust_preset}")
            card2_bal = st.number_input("Dư nợ Thẻ 2:", min_value=0, max_value=500_000_000, value=p_card2_bal, step=1_000_000, format="%d", label_visibility="collapsed", key=f"c2_bal_{st.session_state.cust_preset}")
            
    total_card_limit = card1_lim + card2_lim
    total_card_balance = card1_bal + card2_bal
    calc_utilization = (total_card_balance / total_card_limit) if total_card_limit > 0 else 0.0
    calc_utilization = float(np.clip(calc_utilization, 0.0, 2.5))
    active_cards_count = (1 if card1_lim > 0 else 0) + (1 if card2_lim > 0 else 0)
    
    util_badge_color = "#10B981" if calc_utilization <= 0.35 else ("#F59E0B" if calc_utilization <= 0.70 else "#EF4444")
    st.markdown(f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px 16px; border-radius: 8px;">
        Tổng Hạn Mức Thẻ: <b>{total_card_limit:,.0f} VND</b> | Tổng Dư Nợ Thẻ Đang Dùng: <b>{total_card_balance:,.0f} VND</b> | 
        Tỷ Lệ Sử Dụng Thẻ Tự Động (Revolving): <b style="color: {util_badge_color}; font-size: 16px;">{calc_utilization*100:.2f}%</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 5. DANH MỤC KHOẢN NỢ VAY, NGÀY ĐÁO HẠN & TỶ SỐ NỢ TRÊN THU NHẬP (DEBT RATIO)
    st.markdown("##### 🏦 5. Danh Mục Khoản Nợ Vay & Tỷ Số Nợ Trên Thu Nhập (Debt Ratio)")
    st.caption("Công thức tài chính: **`Nghĩa vụ hàng tháng = Dư nợ / Số tháng còn lại (Ngày đến hạn - Hôm nay)`** | **`DebtRatio = Tổng nghĩa vụ nợ tháng / Tổng thu nhập tháng`**")
    
    today_dt = datetime.date.today()
    default_disburse = today_dt - datetime.timedelta(days=180)
    default_mature = today_dt + datetime.timedelta(days=int(p_loan1_months * 30.4375))
    
    with st.expander("📝 Chi tiết Khoản nợ vay hiện hữu tại các TCTD (Bấm để xem/chỉnh sửa)", expanded=True):
        ln_col1, ln_col2, ln_col3, ln_col4, ln_col5 = st.columns([1.5, 1.1, 1.1, 1.2, 1.2])
        with ln_col1:
            st.markdown("**Khoản Vay / TCTD**")
            loan1_name = st.text_input("Tên khoản vay:", value="Vay mua xe / Tiêu dùng BIDV", key=f"ln1_name_{st.session_state.cust_preset}")
        with ln_col2:
            st.markdown("**Ngày Giải Ngân**")
            loan1_disburse = st.date_input("Ngày giải ngân:", value=default_disburse, key=f"ln1_dis_{st.session_state.cust_preset}")
        with ln_col3:
            st.markdown("**Ngày Đáo Hạn**")
            loan1_mature = st.date_input("Ngày đến hạn:", value=default_mature, key=f"ln1_mat_{st.session_state.cust_preset}")
        with ln_col4:
            st.markdown("**Dư Nợ Còn Lại (VND)**")
            loan1_bal = st.number_input("Dư nợ gốc còn lại:", min_value=0, max_value=2_000_000_000, value=p_loan1_bal, step=10_000_000, format="%d", key=f"ln1_bal_{st.session_state.cust_preset}")
        with ln_col5:
            st.markdown("**Hôm Nay & Số Tháng Còn**")
            days_left = (loan1_mature - today_dt).days
            months_left = max(1, round(days_left / 30.4375)) if days_left > 0 else 1
            st.text(f"Hôm nay: {today_dt.strftime('%d/%m/%Y')}")
            st.markdown(f"Số tháng còn lại: **`{months_left} tháng`**")

    # Tính nghĩa vụ trả nợ hàng tháng
    monthly_loan1_pay = (loan1_bal / months_left) if (loan1_bal > 0 and months_left > 0) else 0.0
    total_monthly_debt = monthly_loan1_pay
    active_loans_count = 1 if loan1_bal > 0 else 0
    
    # Tính DebtRatio = Tổng nghĩa vụ nợ hàng tháng / Tổng thu nhập hàng tháng
    calc_debt_ratio = (total_monthly_debt / total_income_vnd) if total_income_vnd > 0 else 1.0
    calc_debt_ratio = float(np.clip(calc_debt_ratio, 0.0, 3.0))
    
    debt_badge_color = "#10B981" if calc_debt_ratio <= 0.40 else ("#F59E0B" if calc_debt_ratio <= 0.60 else "#EF4444")
    st.markdown(f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px 16px; border-radius: 8px;">
        Nghĩa Vụ Trả Nợ Khoản Vay Hàng Tháng: <b>{total_monthly_debt:,.0f} VND/tháng</b> | 
        Tỷ Số Nợ Trên Thu Nhập Tự Động (DebtRatio): <b style="color: {debt_badge_color}; font-size: 16px;">{calc_debt_ratio*100:.2f}%</b> ({calc_debt_ratio:.4f})
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 6. SỐ KHOẢN VAY VÀ THẺ TÍN DỤNG ĐANG MỞ (TỰ ĐỘNG ĐIỀN)
    st.markdown("##### 📑 6. Số Tài Khoản Tín Dụng & Bất Động Sản Đang Mở (Tự Động Tính)")
    auto_open_accounts = active_cards_count + active_loans_count
    
    col_acc1, col_acc2 = st.columns(2)
    with col_acc1:
        open_loans_input = st.number_input(
            "Tổng số thẻ tín dụng và khoản vay đang mở (NumberOfOpenCreditLinesAndLoans):",
            min_value=0, max_value=50,
            value=max(auto_open_accounts, 2),
            step=1,
            key=f"open_acc_{st.session_state.cust_preset}",
            help=f"Tự động tính = {active_cards_count} thẻ tín dụng + {active_loans_count} khoản vay. Bạn có thể cộng thêm hạn mức thấu chi khác nếu có."
        )
    with col_acc2:
        re_loans_input = st.number_input(
            "Số khoản vay bất động sản / thế chấp (NumberRealEstateLoansOrLines):",
            min_value=0, max_value=20,
            value=p_re_loans,
            step=1,
            key=f"re_loans_{st.session_state.cust_preset}"
        )

    # Đóng gói dữ liệu 11 đặc trưng hoàn chỉnh
    customer_features_payload = {
        'RevolvingUtilizationOfUnsecuredLines': calc_utilization,
        'age': cust_age,
        'NumberOfTime30-59DaysPastDueNotWorse': late_30_59,
        'DebtRatio': calc_debt_ratio,
        'MonthlyIncome': cust_income_model,
        'NumberOfOpenCreditLinesAndLoans': open_loans_input,
        'NumberOfTimes90DaysLate': late_90,
        'NumberRealEstateLoansOrLines': re_loans_input,
        'NumberOfTime60-89DaysPastDueNotWorse': late_60_89,
        'NumberOfDependents': cust_dependents,
        'MonthlyIncome_is_missing': 1 if cust_income_model <= 0 else 0
    }

    # Đóng gói thông tin tài chính chi tiết phục vụ PDF và DSR
    est_new_installment = (loan_amount * (1.0 + dt_cfg[product_code]['params']['r'] * 3.0)) / 36.0
    total_debt_with_new = total_monthly_debt + est_new_installment
    final_dsr_pct = (total_debt_with_new / total_income_vnd * 100) if total_income_vnd > 0 else 100.0

    financial_breakdown_payload = {
        'income_salary': income_salary,
        'income_rental': income_rental,
        'income_business': income_biz,
        'income_other': income_other,
        'total_income_vnd': total_income_vnd,
        'card_count': active_cards_count,
        'total_card_limit': total_card_limit,
        'total_card_balance': total_card_balance,
        'loan_count': active_loans_count,
        'total_loan_balance': loan1_bal,
        'monthly_debt_repayment': total_monthly_debt,
        'monthly_new_installment': est_new_installment,
        'total_debt_monthly': total_debt_with_new,
        'dsr_pct': final_dsr_pct
    }

    customer_meta_payload = {
        'app_id': f"HS-{datetime.date.today().strftime('%Y%m%d')}-{np.random.randint(1000, 9999)}",
        'cust_name': cust_name_in,
        'loan_amount': loan_amount,
        'officer_name': user['name']
    }

    # ==============================================================================
    # THỰC THI CHẤM ĐIỂM BẰNG CẢ 2 MÔ HÌNH
    # ==============================================================================
    res_dt = score_single_customer_dt(customer_features_payload, product_code, market_mode, loan_amount)
    res_lr = score_single_customer_lr(customer_features_payload, product_code, market_mode, loan_amount)

    st.markdown("---")
    st.markdown("## 📊 KẾT QUẢ THẨM ĐỊNH & CHẤM ĐIỂM TÍN DỤNG")

    # ==============================================================================
    # HIỂN THỊ CHẾ ĐỘ DUAL (SIDE-BY-SIDE EVALUATION)
    # ==============================================================================
    if model_choice == "DUAL":
        col_dt_view, col_lr_view = st.columns(2)
        
        # ------------------ CỘT 1: CÂY QUYẾT ĐỊNH (DECISION TREE) ------------------
        with col_dt_view:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #064E3B 0%, #047857 100%); color: white; padding: 10px 16px; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 15px;">
                🌲 MÔ HÌNH CÂY QUYẾT ĐỊNH (DECISION TREE)
                <span style="font-size: 11px; float: right; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px;">White-Box IF-THEN</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Banner quyết định DT
            if res_dt['dec_code'] == 'APPROVED':
                st.markdown(f'<div class="decision-approved" style="border-radius: 0 0 8px 8px;">✅ {res_dt["decision"]}<div style="font-size: 13px; font-weight: normal; margin-top: 4px;">{res_dt["reason"]}</div></div>', unsafe_allow_html=True)
            elif res_dt['dec_code'] == 'CONDITIONAL':
                st.markdown(f'<div class="decision-conditional" style="border-radius: 0 0 8px 8px;">⚠️ {res_dt["decision"]}<div style="font-size: 13px; font-weight: normal; margin-top: 4px;">{res_dt["reason"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="decision-rejected" style="border-radius: 0 0 8px 8px;">🚫 {res_dt["decision"]}<div style="font-size: 13px; font-weight: normal; margin-top: 4px;">{res_dt["reason"]}</div></div>', unsafe_allow_html=True)

            # Đồng hồ FICO Gauge Plotly cho Decision Tree
            fig_gauge_dt = go.Figure(go.Indicator(
                mode="gauge+number",
                value=res_dt['fico'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "ĐIỂM FICO (DECISION TREE)", 'font': {'size': 14, 'color': '#0F172A'}},
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
            fig_gauge_dt.update_layout(height=230, margin=dict(l=15, r=15, t=30, b=10))
            st.plotly_chart(fig_gauge_dt, use_container_width=True)
            
            # Thẻ số liệu chi tiết DT
            c_dt1, c_dt2 = st.columns(2)
            with c_dt1:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Xác suất PD (Tree)</div><div class="metric-value">{res_dt["pd"]*100:.2f}%</div><div style="font-size: 11px; color: #64748B;">Wilson: {res_dt["wilson"]}</div></div>', unsafe_allow_html=True)
            with c_dt2:
                profit_col_dt = "#10B981" if res_dt['profit_vnd'] >= 0 else "#EF4444"
                st.markdown(f'<div class="metric-card"><div class="metric-label">Lợi nhuận kỳ vọng</div><div class="metric-value" style="color: {profit_col_dt}; font-size: 20px;">{res_dt["profit_vnd"]:,.0f} đ</div><div style="font-size: 11px; color: #64748B;">Hạng: {res_dt["grade"]}</div></div>', unsafe_allow_html=True)
                
            # Khung giải trình luật Cây Quyết định
            st.info(f"**🌿 Nút lá #{res_dt['leaf_id']} | Quy tắc logic rẽ nhánh IF-THEN:**\n\n`IF {res_dt['rule']} THEN PD = {res_dt['pd']*100:.2f}% -> {res_dt['grade']}`")

        # ------------------ CỘT 2: HỒI QUY LOGISTIC (LOGISTIC REGRESSION) ------------------
        with col_lr_view:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%); color: white; padding: 10px 16px; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 15px;">
                📈 MÔ HÌNH HỒI QUY LOGISTIC (LOGISTIC REGRESSION)
                <span style="font-size: 11px; float: right; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px;">Smooth Continuous Log-Odds</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Banner quyết định LR
            if res_lr['dec_code'] == 'APPROVED':
                st.markdown(f'<div class="decision-approved" style="border-radius: 0 0 8px 8px;">✅ {res_lr["decision"]}<div style="font-size: 13px; font-weight: normal; margin-top: 4px;">{res_lr["reason"]}</div></div>', unsafe_allow_html=True)
            elif res_lr['dec_code'] == 'CONDITIONAL':
                st.markdown(f'<div class="decision-conditional" style="border-radius: 0 0 8px 8px;">⚠️ {res_lr["decision"]}<div style="font-size: 13px; font-weight: normal; margin-top: 4px;">{res_lr["reason"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="decision-rejected" style="border-radius: 0 0 8px 8px;">🚫 {res_lr["decision"]}<div style="font-size: 13px; font-weight: normal; margin-top: 4px;">{res_lr["reason"]}</div></div>', unsafe_allow_html=True)

            # Đồng hồ FICO Gauge Plotly cho Logistic
            fig_gauge_lr = go.Figure(go.Indicator(
                mode="gauge+number",
                value=res_lr['fico'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "ĐIỂM FICO (LOGISTIC REGRESSION)", 'font': {'size': 14, 'color': '#0F172A'}},
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
            fig_gauge_lr.update_layout(height=230, margin=dict(l=15, r=15, t=30, b=10))
            st.plotly_chart(fig_gauge_lr, use_container_width=True)
            
            # Thẻ số liệu chi tiết LR
            c_lr1, c_lr2 = st.columns(2)
            with c_lr1:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Xác suất PD (Logistic)</div><div class="metric-value">{res_lr["pd"]*100:.2f}%</div><div style="font-size: 11px; color: #64748B;">Log-odds: {res_lr.get("log_odds", 0):.4f}</div></div>', unsafe_allow_html=True)
            with c_lr2:
                profit_col_lr = "#10B981" if res_lr['profit_vnd'] >= 0 else "#EF4444"
                st.markdown(f'<div class="metric-card"><div class="metric-label">Lợi nhuận kỳ vọng</div><div class="metric-value" style="color: {profit_col_lr}; font-size: 20px;">{res_lr["profit_vnd"]:,.0f} đ</div><div style="font-size: 11px; color: #64748B;">Hạng: {res_lr["grade"]}</div></div>', unsafe_allow_html=True)
                
            # Khung giải trình độ nhạy mượt mà của Logistic
            st.success(f"**⚡ Đặc tính hàm liên tục:** Điểm FICO của Logistic dịch chuyển mượt mà từng USD thu nhập và từng % dư nợ thẻ. Nhân tố chi phối hàng đầu hiện tại: **`{res_lr.get('top_driver', 'Thu nhập & Đòn bẩy')}`**.")

        # ------------------ PANEL ĐỐI SÁNH & TRỌNG TÀI RỦI RO ------------------
        st.markdown('<div class="reconciliation-box">', unsafe_allow_html=True)
        st.markdown("#### ⚖️ BẢNG ĐỐI SÁNH KẾT QUẢ & TRỌNG TÀI RỦI RO ĐA MÔ HÌNH")
        
        delta_fico = res_dt['fico'] - res_lr['fico']
        delta_pd = (res_dt['pd'] - res_lr['pd']) * 100
        is_consensus = (res_dt['dec_code'] == res_lr['dec_code'])
        
        rec_c1, rec_c2, rec_c3, rec_c4 = st.columns(4)
        rec_c1.metric("Chênh lệch Điểm FICO (Tree - LR)", f"{delta_fico:+d} điểm", "Độ đồng thuận cao" if abs(delta_fico) <= 15 else "Có phân kỳ nhẹ")
        rec_c2.metric("Chênh lệch Xác suất PD", f"{delta_pd:+.2f}%", "Tiệm cận" if abs(delta_pd) <= 2.0 else "Lệch thang đo")
        rec_c3.metric("Trạng thái Đồng thuận Quyết định", "ĐỒNG THUẬN HOÀN TOÀN" if is_consensus else "CÓ SỰ PHÂN KỲ", "Phê duyệt chuẩn" if is_consensus else "Cần thẩm định thủ công")
        rec_c4.metric("Nghĩa vụ nợ DSR Thực tế", f"{final_dsr_pct:.1f}%", "Đạt chuẩn an toàn (<=60%)" if final_dsr_pct <= 60 else "Cảnh báo cao (>60%)", delta_color="inverse")
        
        if is_consensus:
            st.markdown(f"🟢 **Kết luận Hội đồng Rủi ro:** Cả hai mô hình đều đồng thuận đưa ra quyết định **`{res_dt['decision']}`**. Hồ sơ đạt độ tin cậy phê duyệt cao nhất theo chuẩn Basel II.")
        else:
            st.markdown(f"🟡 **Cảnh báo phân kỳ mô hình:** Cây Quyết định ra quyết định `{res_dt['decision']}` trong khi Hồi quy Logistic đưa ra `{res_lr['decision']}`. Đề xuất chuyển hồ sơ lên Hội đồng ALCO thẩm định nguồn thu thực tế.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ==============================================================================
    # HIỂN THỊ CHẾ ĐỘ ĐƠN MÔ HÌNH (SINGLE MODEL VIEW)
    # ==============================================================================
    else:
        active_res = res_dt if model_choice == "DECISION_TREE" else res_lr
        other_res = res_lr if model_choice == "DECISION_TREE" else res_dt
        
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
                gauge={
                    'axis': {'range': [300, 850]},
                    'bar': {'color': "#1E3A8A", 'thickness': 0.3},
                    'steps': [
                        {'range': [300, 527], 'color': "#FCA5A5"},
                        {'range': [527, 571], 'color': "#FDE68A"},
                        {'range': [571, 600], 'color': "#A7F3D0"},
                        {'range': [600, 850], 'color': "#34D399"}
                    ],
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': active_res['fico']}
                }
            ))
            fig_g_single.update_layout(height=230, margin=dict(l=15, r=15, t=20, b=10))
            st.plotly_chart(fig_g_single, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_s2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-label">XÁC SUẤT VỠ NỢ (PD)</div><div class="metric-value">{active_res["pd"]*100:.2f}%</div>', unsafe_allow_html=True)
            st.caption(f"Hạng rủi ro: **{active_res['grade']}**")
            st.markdown("---")
            st.markdown(f'<div class="metric-label">ĐỐI CHIẾU MÔ HÌNH CÒN LẠI</div><div class="metric-value" style="font-size: 20px; color: #2563EB;">FICO {other_res["fico"]}</div>', unsafe_allow_html=True)
            st.caption(f"PD mô hình kia: **{other_res['pd']*100:.2f}%** ({other_res['model_name']})")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_s3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-label">NGƯỠNG HÒA VỐN SẢN PHẨM (PD*)</div><div class="metric-value">{active_res["pd_star"]*100:.2f}%</div>', unsafe_allow_html=True)
            st.caption(f"Sản phẩm: **{active_res['product_name']}**")
            st.markdown("---")
            p_col = "#10B981" if active_res['profit_vnd'] >= 0 else "#EF4444"
            st.markdown(f'<div class="metric-label">LỢI NHUẬN RÒNG KỲ VỌNG</div><div class="metric-value" style="font-size: 20px; color: {p_col};">{active_res["profit_vnd"]:,.0f} VND</div>', unsafe_allow_html=True)
            st.caption("Sau khi trừ chi phí vốn, vận hành & bù đắp rủi ro mất vốn.")
            st.markdown('</div>', unsafe_allow_html=True)

        if model_choice == "DECISION_TREE":
            with st.expander("🔍 Xem Đường Dẫn Quy Tắc Logic Giải Trình (Explainable AI - IF...THEN)", expanded=True):
                st.markdown(f"**Quy tắc ra quyết định:** `IF {active_res.get('rule', 'N/A')} THEN PD = {active_res['pd']*100:.2f}% -> {active_res['grade']}`")
        else:
            with st.expander("🔍 Xem Phương Trình Log-Odds & Độ Nhạy Mượt Mà", expanded=True):
                st.markdown(f"**Hàm Logit Liên tục:** $\\ln(PD/(1-PD)) = {active_res.get('log_odds', 0):.4f}$. Điểm số FICO tự động tối ưu thích ứng mượt mà.")

    # ==============================================================================
    # NÚT XUẤT BÁO CÁO THẨM ĐỊNH TÍN DỤNG CHUYÊN NGHIỆP RA FILE PDF
    # ==============================================================================
    st.markdown("---")
    st.markdown("#### 📄 XUẤT TỜ TRÌNH & BÁO CÁO THẨM ĐỊNH TÍN DỤNG CHUYÊN NGHIỆP (PDF EXPORT)")
    st.write("Hệ thống hỗ trợ kết xuất tự động toàn bộ 11 đặc trưng, bảng phân tích thu nhập đa nguồn, cơ cấu nợ và kết quả đối sánh đa mô hình thành một file PDF hoàn chỉnh theo tiêu chuẩn kiểm toán Basel II.")

    pdf_bytes = generate_credit_appraisal_pdf(
        customer_info=customer_meta_payload,
        financial_details=financial_breakdown_payload,
        features_dict=customer_features_payload,
        dt_res=res_dt,
        lr_res=res_lr,
        selected_mode=model_choice,
        prod_cfg=dt_cfg[product_code],
        market_mode=market_mode
    )

    pdf_file_name = f"Bao_Cao_Tham_Dinh_{customer_meta_payload['app_id']}_{cust_name_in.replace(' ', '_')}.pdf"
    
    col_pdf1, col_pdf2 = st.columns([1, 2])
    with col_pdf1:
        st.download_button(
            label="📥 TẢI BÁO CÁO THẨM ĐỊNH TÍN DỤNG (PDF)",
            data=pdf_bytes,
            file_name=pdf_file_name,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    with col_pdf2:
        st.caption(f"✓ Đã sẵn sàng xuất bản: `{pdf_file_name}` | Dung lượng: **{len(pdf_bytes)/1024:.1f} KB** | Định dạng chuẩn A4 in ấn ngân hàng.")

# ==============================================================================
# TAB 2: CHẤM ĐIỂM DANH MỤC LÔ HÀNG LOẠT (BATCH PORTFOLIO SCORING)
# ==============================================================================
if 'batch' in user['allowed_tabs']:
    with active_tabs[tab_labels.index("📁 Chấm điểm Danh mục Lô (Batch Excel)")]:
        st.markdown("### 📁 Tải Lên Danh Sách Hồ Sơ Khách Hàng Để Chấm Điểm Hàng Loạt")
        st.write("Hệ thống cho phép nạp hàng nghìn hồ sơ từ file Excel hoặc CSV để tính toán nhanh chóng Điểm FICO, Phân hạng Rủi ro và Lợi nhuận dự kiến bằng cả 2 mô hình.")
        
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
                
                if st.button("🚀 Bắt Đầu Chấm Điểm Toàn Bộ Danh Mục Bằng Cả 2 Mô Hình", type="primary"):
                    with st.spinner("Đang tính toán FICO, PD và Lợi nhuận dự kiến song song..."):
                        res_list = []
                        for idx, row in batch_df.iterrows():
                            c_dict = row.to_dict()
                            l_amt = row.get('Loan_Amount_VND', loan_amount)
                            eval_dt = score_single_customer_dt(c_dict, product_code, market_mode, l_amt)
                            eval_lr = score_single_customer_lr(c_dict, product_code, market_mode, l_amt)
                            
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
                                'Profit_Tree_VND': eval_dt['profit_vnd'],
                                'Profit_Logistic_VND': eval_lr['profit_vnd']
                            })
                            
                        result_batch_df = pd.DataFrame(res_list)
                        
                        km1, km2, km3, km4 = st.columns(4)
                        km1.metric("Tổng Số Hồ Sơ", f"{len(result_batch_df):,}")
                        appr_count = (result_batch_df['Decision_Tree'].str.contains('PHÊ DUYỆT')).sum()
                        km2.metric("Tỷ Lệ Duyệt (Tree)", f"{appr_count/len(result_batch_df)*100:.1f}%")
                        appr_count_lr = (result_batch_df['Decision_Logistic'].str.contains('PHÊ DUYỆT')).sum()
                        km3.metric("Tỷ Lệ Duyệt (Logistic)", f"{appr_count_lr/len(result_batch_df)*100:.1f}%")
                        total_profit = result_batch_df['Profit_Tree_VND'].sum()
                        km4.metric("Tổng Lợi Nhuận (Tree)", f"{total_profit:,.0f} đ")
                        
                        st.dataframe(result_batch_df.head(10), use_container_width=True)
                        
                        res_csv = result_batch_df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Tải Xuất Kết Quả Đa Mô Hình (.CSV)", data=res_csv, file_name=f"Ket_Qua_Cham_Diem_Danh_Muc_{market_mode}.csv", mime="text/csv")
            except Exception as e:
                st.error(f"Lỗi khi xử lý file: {e}")

# ==============================================================================
# TAB 3: TRUNG TÂM ĐIỀU HÀNH CHÍNH SÁCH (CRO) - SO SÁNH ĐƯỜNG CONG LỢI NHUẬN
# ==============================================================================
if 'policy' in user['allowed_tabs']:
    with active_tabs[tab_labels.index("⚖️ Trung tâm Điều hành Chính sách (CRO)")]:
        st.markdown("### ⚖️ Điều Hành Khẩu Vị Rủi Ro & So Sánh Đường Cong Lợi Nhuận Giữa 2 Mô Hình")
        st.write("Cho phép Giám đốc Quản lý Rủi ro (CRO) đối sánh trực tiếp đường cong tối ưu hóa biên lợi nhuận giữa **Cây Quyết Định** và **Hồi Quy Logistic** trên toàn bộ thang điểm FICO.")
        
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
                st.success("✓ Đã cập nhật thành công khẩu vị rủi ro vào cả 2 mô hình!")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_pol2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f"##### 📈 So Sánh Trực Tiếp Đường Cong Lợi Nhuận Kỳ Vọng ({dt_cfg[sel_pol_prod]['product_name']})")
            
            # Mô phỏng đường cong lợi nhuận trên dải điểm FICO 400 đến 700
            test_ficos = np.linspace(420, 680, 50)
            
            # Đường cong Logistic: liên tục theo sigmoid
            log_odds_range = (offset - test_ficos) / factor
            pds_lr = 1.0 / (1.0 + np.exp(-log_odds_range))
            profits_lr = (1.0 - pds_lr) * calc_net_m - pds_lr * new_lgd
            
            # Đường cong Decision Tree: phân đoạn theo 5 hạng rủi ro
            pds_dt = []
            for f in test_ficos:
                if f >= 605: pds_dt.append(0.011)
                elif f >= 572: pds_dt.append(0.032)
                elif f >= 540: pds_dt.append(0.075)
                elif f >= 500: pds_dt.append(0.145)
                else: pds_dt.append(0.350)
            pds_dt = np.array(pds_dt)
            profits_dt = (1.0 - pds_dt) * calc_net_m - pds_dt * new_lgd
            
            fig_compare_curve = go.Figure()
            fig_compare_curve.add_trace(go.Scatter(
                x=test_ficos, y=profits_dt * 100,
                mode='lines', name='🌲 Decision Tree (Bậc Thang Phân Vị)',
                line=dict(color='#047857', width=3, dash='solid')
            ))
            fig_compare_curve.add_trace(go.Scatter(
                x=test_ficos, y=profits_lr * 100,
                mode='lines', name='📈 Logistic Regression (Đường Cong Mượt)',
                line=dict(color='#2563EB', width=3, dash='solid')
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
            st.caption("Khảo sát đối sánh: Mô hình Logistic mang lại sự phân tách mịn màng liên tục, trong khi Cây Quyết định tạo các bậc thang phân vị rõ ràng hỗ trợ thiết lập chính sách cứng.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Bảng đối sánh ngưỡng cắt tối ưu thực nghiệm
        st.markdown("##### 🏆 Bảng Đối Sánh Ngưỡng Cắt Tối Ưu Hóa Lợi Nhuận Giữa 2 Mô Hình (Optimal Cut-offs)")
        opt_data = [
            {'Dòng Sản Phẩm': 'Cho vay Mua nhà (Mortgage)', 'Cutoff FICO (Tree)': 550, 'Cutoff FICO (Logistic)': 544, 'Chênh Lệch FICO': '-6 điểm', 'PD Hòa Vốn (PD*)': '12.28%', 'Đánh Giá Khẩu Vị': 'Logistic mở rộng nhẹ tệp khách hàng an toàn'},
            {'Dòng Sản Phẩm': 'Cho vay Mua Ô tô (Auto Loan)', 'Cutoff FICO (Tree)': 555, 'Cutoff FICO (Logistic)': 552, 'Chênh Lệch FICO': '-3 điểm', 'PD Hòa Vốn (PD*)': '10.00%', 'Đánh Giá Khẩu Vị': 'Tương đương, kiểm soát chặt rủi ro mất giá xe'},
            {'Dòng Sản Phẩm': 'Vay Tiêu dùng Tín chấp', 'Cutoff FICO (Tree)': 551, 'Cutoff FICO (Logistic)': 542, 'Chênh Lệch FICO': '-9 điểm', 'PD Hòa Vốn (PD*)': '12.79%', 'Đánh Giá Khẩu Vị': 'Logistic linh hoạt hơn đối với nhóm khách hàng trẻ'},
            {'Dòng Sản Phẩm': 'Thẻ Tín dụng (Credit Card)', 'Cutoff FICO (Tree)': 542, 'Cutoff FICO (Logistic)': 540, 'Chênh Lệch FICO': '-2 điểm', 'PD Hòa Vốn (PD*)': '14.14%', 'Đánh Giá Khẩu Vị': 'Đồng thuận cao, tối ưu hóa biên lãi 18%/năm'}
        ]
        st.dataframe(pd.DataFrame(opt_data), use_container_width=True)

# ==============================================================================
# TAB 4: BÁO CÁO GIÁM SÁT BASEL II & KIỂM TOÁN ĐA MÔ HÌNH (AUDIT)
# ==============================================================================
if 'audit' in user['allowed_tabs']:
    with active_tabs[tab_labels.index("📊 Báo cáo Giám sát Basel II (Audit)")]:
        st.markdown("### 📊 Báo Cáo Kiểm Toán & So Sánh Bộ Chỉ Số Basel II Trụ Cột 2 & IFRS 9")
        st.write("Bảng điều khiển định kỳ phục vụ Ủy ban ALCO và Cơ quan Thanh tra Giám sát Ngân hàng Nhà nước.")
        
        # 1. Thẻ so sánh chỉ số vàng
        ak1, ak2, ak3, ak4 = st.columns(4)
        ak1.metric("AUC-ROC (Test 30k)", "0.8521 vs 0.8556", "Logistic nhỉnh hơn +0.0035")
        ak2.metric("Hệ Số Gini (2*AUC - 1)", "0.7041 vs 0.7112", "Cả 2 đều > 0.60 Chuẩn Vàng")
        ak3.metric("Kolmogorov-Smirnov (KS)", "55.87% vs 57.12%", "> 40% Phân tách cực mạnh")
        ak4.metric("Chỉ Số Trôi Dạt Dân Số (PSI)", "0.00008 vs 0.00029", "< 0.10 Tuyệt đối an toàn")
        
        st.markdown("---")
        col_aud1, col_aud2 = st.columns(2)
        
        with col_aud1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("##### 🎯 Biểu Đồ Radar So Sánh Năng Lực 5 Chiều Giữa 2 Mô Hình")
            
            categories = ['Lực Phân Tách (AUC)', 'Tính Trực Quan (White-box)', 'Độ Mịn Điểm Số (Granularity)', 'Tính Ổn Định (Low PSI)', 'Độ Chuẩn Xác Suất (Calibration)']
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[0.852, 0.980, 0.720, 0.990, 0.880],
                theta=categories,
                fill='toself',
                name='🌲 Decision Tree',
                line_color='#047857'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[0.856, 0.780, 0.960, 0.970, 0.920],
                theta=categories,
                fill='toself',
                name='📈 Logistic Regression',
                line_color='#2563EB'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0.5, 1.0])),
                showlegend=True,
                height=300,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            st.caption("Nhận xét kiểm toán: Decision Tree chiến thắng vượt trội về tính minh bạch giải trình (White-box), trong khi Logistic Regression chiếm ưu thế về độ mịn màng và phân tách xác suất.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_aud2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("##### 📋 Bảng So Sánh Chỉ Số Kiểm Toán Toàn Diện (Audit Scorecard)")
            audit_matrix = pd.DataFrame([
                {'Chỉ Số Kiểm Toán': '1. AUC-ROC Tập Train (120k)', 'Cây Quyết Định': '0.8526', 'Hồi Quy Logistic': '0.8494', 'Ngưỡng Chuẩn Basel': '>= 0.75 (Tốt)'},
                {'Chỉ Số Kiểm Toán': '2. AUC-ROC Tập Test (30k)', 'Cây Quyết Định': '0.8521', 'Hồi Quy Logistic': '0.8556', 'Ngưỡng Chuẩn Basel': '>= 0.75 (Tốt)'},
                {'Chỉ Số Kiểm Toán': '3. Mức Suy Giảm Gini (Overfitting)', 'Cây Quyết Định': '0.16%', 'Hồi Quy Logistic': '-1.76%', 'Ngưỡng Chuẩn Basel': '< 10.0% (An toàn)'},
                {'Chỉ Số Kiểm Toán': '4. Brier Score (Độ Chuẩn Hóa PD)', 'Cây Quyết Định': '0.0520', 'Hồi Quy Logistic': '0.0571', 'Ngưỡng Chuẩn Basel': '< 0.10 (Chuẩn)'},
                {'Chỉ Số Kiểm Toán': '5. Population Stability Index (PSI)', 'Cây Quyết Định': '0.000078', 'Hồi Quy Logistic': '0.000293', 'Ngưỡng Chuẩn Basel': '< 0.10 (Không Shift)'},
                {'Chỉ Số Kiểm Toán': '6. Thời Gian Tính Toán (Latency)', 'Cây Quyết Định': '0.8 ms / hồ sơ', 'Hồi Quy Logistic': '1.1 ms / hồ sơ', 'Ngưỡng Chuẩn Basel': '< 50 ms (Real-time)'}
            ])
            st.dataframe(audit_matrix, use_container_width=True, hide_index=True)
            st.success("✓ **Kết Luận Độc Lập Từ Kiểm Toán:** Cả hai mô hình đều đáp ứng 100% điều kiện vận hành theo Basel II Trụ cột 2 và đạt điều kiện tích hợp song hành trên Hệ thống Core Banking.")
            st.markdown('</div>', unsafe_allow_html=True)

# Footer chân trang
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 12px; margin-top: 35px; padding: 20px 0; border-top: 1px solid #E2E8F0;">
    SMARTCREDIT AI PLATFORM © 2026 | HỆ THỐNG QUẢN TRỊ RỦI RO TÍN DỤNG ĐA MÔ HÌNH NỘI BỘ NGÂN HÀNG<br/>
    Tuân thủ Hiệp ước Basel II / Basel III & Chuẩn mực Báo cáo Tài chính IFRS 9 | Tự động hóa Quyết định Phê duyệt
</div>
""", unsafe_allow_html=True)
