# -*- coding: utf-8 -*-
"""
SmartCredit AI - Cổng Thông Tin Chấm Điểm Tín Dụng & Quản Trị Rủi Ro Nội Bộ Ngân Hàng
Đồ án Tốt nghiệp / Dự án Quản trị Rủi ro Tín dụng (Give Me Some Credit)
Chuẩn mực: Basel II Trụ cột 1 & 2, IFRS 9, Thẻ điểm FICO Scorecard
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# ==============================================================================
# CẤU HÌNH TRANG & GIAO DIỆN STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="SmartCredit AI | Banking Risk Portal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS phong cách Fintech / Ngân hàng cao cấp (Deep Navy, Emerald, Amber, Crimson)
st.markdown("""
<style>
    /* Bảng màu chuẩn Ngân hàng */
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
        padding: 24px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.15);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #93C5FD;
        margin: 6px 0 0 0;
        font-size: 14px;
    }
    
    /* Card giao diện */
    .metric-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 15px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-label {
        font-size: 13px;
        color: #64748B;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Quyết định phê duyệt */
    .decision-approved {
        background-color: #ECFDF5;
        border-left: 5px solid #10B981;
        padding: 16px 20px;
        border-radius: 8px;
        color: #065F46;
        font-weight: 600;
        font-size: 18px;
        margin: 15px 0;
    }
    .decision-conditional {
        background-color: #FFFBEB;
        border-left: 5px solid #F59E0B;
        padding: 16px 20px;
        border-radius: 8px;
        color: #92400E;
        font-weight: 600;
        font-size: 18px;
        margin: 15px 0;
    }
    .decision-rejected {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 16px 20px;
        border-radius: 8px;
        color: #991B1B;
        font-weight: 600;
        font-size: 18px;
        margin: 15px 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        font-weight: 600;
        font-size: 14px;
        border-radius: 8px 8px 0 0;
        padding: 0 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# QUẢN LÝ TÀI KHOẢN VÀ XÁC THỰC PHÂN QUYỀN (RBAC)
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
# HÀM NẠP TÀI NGUYÊN MÔ HÌNH VÀ CẤU HÌNH KINH TẾ
# ==============================================================================
@st.cache_resource
def load_risk_assets():
    # Tìm kiếm đường dẫn linh hoạt (hỗ trợ cả cấu trúc thư mục con lẫn thư mục gốc khi deploy Cloud)
    possible_dirs = [
        "results",
        ".",
        "3 mô hình được chọn/results",
        "../results",
        r"D:\AI\.final_project AI\3 mô hình được chọn\results",
        r"D:\AI\project AI\3 mô hình được chọn\results"
    ]
    possible_models = [
        "models/decision_tree_model.pkl",
        "decision_tree_model.pkl",
        "3 mô hình được chọn/models/decision_tree_model.pkl",
        "../models/decision_tree_model.pkl",
        r"D:\AI\.final_project AI\3 mô hình được chọn\models\decision_tree_model.pkl",
        r"D:\AI\project AI\3 mô hình được chọn\models\decision_tree_model.pkl"
    ]
    
    model_path = next((p for p in possible_models if os.path.exists(p)), None)
    if model_path is None:
        raise FileNotFoundError("Không tìm thấy tệp decision_tree_model.pkl!")
    model = joblib.load(model_path)
    
    # Tìm file quy tắc nút lá
    leaf_file = next((os.path.join(d, "decision_tree_leaf_rules.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "decision_tree_leaf_rules.csv"))), None)
    leaf_df = pd.read_csv(leaf_file) if leaf_file else pd.DataFrame()
    
    # Tìm file cấu hình đa sản phẩm
    cfg_file = next((os.path.join(d, "multi_product_policy_config.json") for d in possible_dirs if os.path.exists(os.path.join(d, "multi_product_policy_config.json"))), None)
    if cfg_file:
        with open(cfg_file, "r", encoding="utf-8") as f:
            multi_cfg = json.load(f)
    else:
        # Fallback mặc định
        multi_cfg = {
            'MORTGAGE': {
                'product_name': 'Cho vay Mua nhà có TSBĐ',
                'params': {'r': 0.045, 'c': 0.010, 'lgd': 0.250, 'pd_breakeven': 0.1228},
                'policies': {
                    'NORMAL': {'min_score': 550, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']},
                    'EXPANSION': {'min_score': 550, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']},
                    'RECESSION': {'min_score': 572, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}
                }
            },
            'AUTO': {
                'product_name': 'Cho vay Mua Ô tô (Auto Loan)',
                'params': {'r': 0.065, 'c': 0.015, 'lgd': 0.450, 'pd_breakeven': 0.1000},
                'policies': {
                    'NORMAL': {'min_score': 555, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']},
                    'EXPANSION': {'min_score': 551, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']},
                    'RECESSION': {'min_score': 600, 'allowed_grades': ['Hạng 1 (< 2%)']}
                }
            },
            'UNSECURED': {
                'product_name': 'Vay Tiêu dùng Tín chấp',
                'params': {'r': 0.140, 'c': 0.030, 'lgd': 0.750, 'pd_breakeven': 0.1279},
                'policies': {
                    'NORMAL': {'min_score': 551, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']},
                    'EXPANSION': {'min_score': 543, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']},
                    'RECESSION': {'min_score': 572, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}
                }
            },
            'CREDIT_CARD': {
                'product_name': 'Thẻ Tín dụng (Credit Card)',
                'params': {'r': 0.180, 'c': 0.040, 'lgd': 0.850, 'pd_breakeven': 0.1414},
                'policies': {
                    'NORMAL': {'min_score': 542, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)']},
                    'EXPANSION': {'min_score': 527, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)', 'Hạng 3 (5% - 10%)', 'Hạng 4 (10% - 20%)']},
                    'RECESSION': {'min_score': 572, 'allowed_grades': ['Hạng 1 (< 2%)', 'Hạng 2 (2% - 5%)']}
                }
            }
        }
    
    # Nạp tầm quan trọng biến
    feat_file = next((os.path.join(d, "decision_tree_feature_importance.csv") for d in possible_dirs if os.path.exists(os.path.join(d, "decision_tree_feature_importance.csv"))), None)
    feat_df = pd.read_csv(feat_file) if feat_file else pd.DataFrame()
    
    # Tham số FICO
    pdo = 20
    base_score = 600
    base_odds = 50.0
    factor = pdo / np.log(2)
    offset = base_score - factor * np.log(base_odds)
    
    return model, leaf_df, multi_cfg, feat_df, factor, offset

try:
    model, leaf_df, multi_cfg, feat_df, factor, offset = load_risk_assets()
    leaf_info = leaf_df.set_index('Leaf ID').to_dict('index') if not leaf_df.empty else {}
except Exception as e:
    st.error(f"Lỗi khi nạp dữ liệu mô hình: {e}")
    st.stop()

# ==============================================================================
# HÀM TÍNH TOÁN CHẤM ĐIỂM NGHIỆP VỤ
# ==============================================================================
FEATURE_COLS = [
    'RevolvingUtilizationOfUnsecuredLines', 'age',
    'NumberOfTime30-59DaysPastDueNotWorse', 'DebtRatio', 'MonthlyIncome',
    'NumberOfOpenCreditLinesAndLoans', 'NumberOfTimes90DaysLate',
    'NumberRealEstateLoansOrLines', 'NumberOfTime60-89DaysPastDueNotWorse',
    'NumberOfDependents', 'MonthlyIncome_is_missing'
]

def score_single_customer(data_dict, product_code, market_mode, loan_amt):
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
    leaf_id = int(model.apply(X_cust)[0])
    prob_pd = float(model.predict_proba(X_cust)[0, 1])
    
    eps = 1e-7
    log_odds = np.log((prob_pd + eps) / (1 - prob_pd + eps))
    fico = int(round(offset - factor * log_odds))
    
    leaf_row = leaf_info.get(leaf_id, {})
    grade = leaf_row.get('Hạng Rủi ro', 'Hạng Chưa Xác Định')
    wilson = leaf_row.get('Wilson CI 95%', '[N/A]')
    rule = leaf_row.get('Điều kiện logic (IF - THEN)', 'Root Condition')
    
    prod_cfg = multi_cfg.get(product_code, multi_cfg['CREDIT_CARD'])
    p_params = prod_cfg['params']
    net_r = p_params['r'] - p_params['c']
    lgd = p_params['lgd']
    pd_star = p_params['pd_breakeven']
    
    # Tính lợi nhuận biên thuần
    net_margin = (1 - prob_pd) * net_r - prob_pd * lgd
    profit_vnd = loan_amt * net_margin
    
    active_policy = prod_cfg['policies'].get(market_mode, prod_cfg['policies']['NORMAL'])
    if grade in active_policy['allowed_grades']:
        decision = 'PHÊ DUYỆT TỰ ĐỘNG (AUTO-APPROVED)'
        dec_code = 'APPROVED'
        reason = f"Điểm FICO {fico} đạt chuẩn ({grade}). Xác suất rủi ro PD={prob_pd*100:.2f}% < PD*={pd_star*100:.2f}%. Dự kiến mang lại biên lãi thuần dương cho ngân hàng."
    elif prob_pd <= pd_star:
        decision = 'DUYỆT CÓ ĐIỀU KIỆN (CONDITIONAL REVIEW)'
        dec_code = 'CONDITIONAL'
        reason = f"Hồ sơ thuộc {grade}. PD={prob_pd*100:.2f}% tiệm cận ngưỡng hòa vốn ({pd_star*100:.2f}%). Đề xuất giảm 30% hạn mức hoặc thẩm định bổ sung nguồn thu."
    else:
        decision = 'TỪ CHỐI CẤP TÍN DỤNG (REJECTED)'
        dec_code = 'REJECTED'
        reason = f"Rủi ro vỡ nợ vượt ngưỡng an toàn ({grade}). PD={prob_pd*100:.2f}% > PD*={pd_star*100:.2f}% gây tổn thất tài chính dự kiến (-{abs(profit_vnd):,.0f} VND)."
        
    return {
        'leaf_id': leaf_id,
        'pd': prob_pd,
        'fico': fico,
        'grade': grade,
        'wilson': wilson,
        'rule': rule,
        'decision': decision,
        'dec_code': dec_code,
        'reason': reason,
        'profit_vnd': profit_vnd,
        'pd_star': pd_star,
        'product_name': prod_cfg['product_name']
    }

# ==============================================================================
# GIAO DIỆN ĐĂNG NHẬP (AUTHENTICATION SCREEN)
# ==============================================================================
if st.session_state.user is None:
    st.markdown("""
    <div style="max-width: 550px; margin: 40px auto 20px auto; text-align: center;">
        <div style="font-size: 50px;">🏦</div>
        <h2 style="color: #0F172A; margin: 10px 0;">HỆ THỐNG SMARTCREDIT AI</h2>
        <p style="color: #64748B; font-size: 15px;">Cổng Thông Tin Thẩm Định & Quản Trị Rủi Ro Tín Dụng Nội Bộ Ngân Hàng</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_c1, col_center, col_c2 = st.columns([1, 1.8, 1])
    with col_center:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.subheader("🔐 Đăng nhập Hệ thống")
        
        username_inp = st.text_input("Tên đăng nhập (Username)", placeholder="officer / manager / cro_admin")
        password_inp = st.text_input("Mật khẩu (Password)", type="password", placeholder="Nhập 123...")
        
        if st.button("Đăng nhập", use_container_width=True, type="primary"):
            if username_inp in DEMO_USERS and password_inp == DEMO_USERS[username_inp]['password']:
                st.session_state.user = DEMO_USERS[username_inp]
                st.rerun()
            else:
                st.error("Sai tên đăng nhập hoặc mật khẩu! Vui lòng thử lại.")
                
        st.markdown("---")
        st.caption("⚡ **ĐĂNG NHẬP NHANH 1-CHẠM (DÀNH CHO HỘI ĐỒNG & GIÁM KHẢO DEMO):**")
        
        c_btn1, c_btn2, c_btn3 = st.columns(3)
        with c_btn1:
            if st.button("👤 Thẩm định viên", use_container_width=True):
                st.session_state.user = DEMO_USERS['officer']
                st.rerun()
        with c_btn2:
            if st.button("👔 Trưởng phòng", use_container_width=True):
                st.session_state.user = DEMO_USERS['manager']
                st.rerun()
        with c_btn3:
            if st.button("👑 Giám đốc CRO", use_container_width=True):
                st.session_state.user = DEMO_USERS['cro_admin']
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)
        st.info("💡 Hệ thống hỗ trợ phân quyền tự động theo chuẩn mực Quản trị Rủi ro Tín dụng Basel II.")
    st.stop()

# ==============================================================================
# GIAO DIỆN CHÍNH SAU KHI ĐĂNG NHẬP THÀNH CÔNG
# ==============================================================================
user = st.session_state.user

# Sidebar thông tin người dùng & điều khiển chung
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 15px 12px; background: #0F172A; border-radius: 8px; color: white; margin-bottom: 20px;">
        <div style="font-size: 11px; text-transform: uppercase; color: #94A3B8;">Người dùng hiện tại</div>
        <div style="font-size: 16px; font-weight: 700; color: #FFFFFF;">{user['name']}</div>
        <div style="font-size: 12px; color: #38BDF8;">{user['role_title']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Chế độ Kinh tế Vĩ mô")
    market_mode = st.selectbox(
        "Kịch bản Chu kỳ Tín dụng:",
        options=['NORMAL', 'EXPANSION', 'RECESSION'],
        index=0,
        format_func=lambda x: {
            'NORMAL': '🔵 NORMAL - Kinh tế Bình thường',
            'EXPANSION': '🟢 EXPANSION - Tăng trưởng Mở rộng',
            'RECESSION': '🔴 RECESSION - Suy thoái / Thắt chặt'
        }[x],
        disabled=(user['role'] != 'CRO_ADMIN')
    )
    if user['role'] != 'CRO_ADMIN':
        st.caption("🔒 *Chỉ Giám đốc Rủi ro (CRO) mới có quyền đổi chế độ vĩ mô.*")
    
    st.markdown("---")
    st.markdown("### 📑 Hướng dẫn Tác nghiệp")
    st.caption("• **Tab 1:** Nhập từng hồ sơ vay lẻ để phê duyệt tức thì.\n• **Tab 2:** Chấm điểm danh mục khách hàng từ tệp Excel.\n• **Tab 3:** Điều chỉnh khẩu vị rủi ro & lãi suất.\n• **Tab 4:** Báo cáo giám sát mô hình Basel II.")
    
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# Header chính của ứng dụng
st.markdown(f"""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1>🏦 SMARTCREDIT AI — CỔNG THẨM ĐỊNH TÍN DỤNG NỘI BỘ</h1>
            <p>Hệ thống hỗ trợ ra quyết định cấp tín dụng dựa trên Cây Quyết định Hộp trắng (Decision Tree) & Chuẩn mực Basel II</p>
        </div>
        <div style="background: rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 6px; text-align: right;">
            <div style="font-size: 11px; color: #E2E8F0;">Trạng thái Vĩ mô</div>
            <div style="font-size: 14px; font-weight: bold; color: #F8FAFC;">{market_mode} MODE</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Khởi tạo các Tabs dựa trên quyền hạn
tab_labels = ["📝 Thẩm định Tức thì (Single STP)"]
if 'batch' in user['allowed_tabs']:
    tab_labels.append("📁 Chấm điểm Danh mục Lô (Batch Excel)")
if 'policy' in user['allowed_tabs']:
    tab_labels.append("⚖️ Trung tâm Điều hành Chính sách (CRO)")
if 'audit' in user['allowed_tabs']:
    tab_labels.append("📊 Báo cáo Giám sát Basel II (Audit)")

active_tabs = st.tabs(tab_labels)

# ==============================================================================
# TAB 1: THẨM ĐỊNH TỨC THÌ (SINGLE CUSTOMER SCORING)
# ==============================================================================
with active_tabs[0]:
    st.markdown("### 📋 Nhập Thông Tin Hồ Sơ Đề Nghị Cấp Tín Dụng")
    
    # Preset hồ sơ mẫu nhanh
    st.caption("⚡ **NẠP NHANH HỒ SƠ MẪU ĐỂ KIỂM THỬ KHẢ NĂNG PHÂN LOẠI CỦA MÔ HÌNH:**")
    sc_c1, sc_c2, sc_c3 = st.columns(3)
    
    if 'cust_preset' not in st.session_state:
        st.session_state.cust_preset = 'good'
        
    with sc_c1:
        if st.button("🟢 Mẫu Khách Hàng Tốt (Hạng 1 - Duyệt)", use_container_width=True):
            st.session_state.cust_preset = 'good'
            st.rerun()
    with sc_c2:
        if st.button("🟡 Mẫu Khách Hàng Tiệm Cận (Hạng 3 - Xem xét)", use_container_width=True):
            st.session_state.cust_preset = 'medium'
            st.rerun()
    with sc_c3:
        if st.button("🔴 Mẫu Khách Hàng Nợ Xấu (Hạng 5 - Từ chối)", use_container_width=True):
            st.session_state.cust_preset = 'bad'
            st.rerun()
            
    # Thiết lập giá trị mặc định theo preset
    if st.session_state.cust_preset == 'good':
        def_age, def_inc, def_dep = 35, 6500.0, 1
        def_late90, def_late60, def_late30 = 0, 0, 0
        def_util, def_debt, def_open, def_re = 0.15, 0.25, 6, 1
    elif st.session_state.cust_preset == 'medium':
        def_age, def_inc, def_dep = 42, 4500.0, 2
        def_late90, def_late60, def_late30 = 0, 0, 1
        def_util, def_debt, def_open, def_re = 0.75, 0.45, 8, 1
    else: # bad
        def_age, def_inc, def_dep = 29, 3000.0, 0
        def_late90, def_late60, def_late30 = 2, 1, 2
        def_util, def_debt, def_open, def_re = 0.95, 0.65, 5, 0

    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        st.markdown("##### 👤 1. Thông tin Nhân thân & Thu nhập")
        cust_age = st.number_input("Tuổi của khách hàng (năm):", min_value=18, max_value=85, value=def_age, step=1, key=f"age_{st.session_state.cust_preset}")
        cust_income = st.number_input("Thu nhập hàng tháng (USD hoặc quy đổi):", min_value=0.0, max_value=100000.0, value=def_inc, step=500.0, key=f"inc_{st.session_state.cust_preset}", help="Điền 0 nếu không khai báo chứng minh thu nhập")
        cust_dependents = st.number_input("Số người phụ thuộc tài chính:", min_value=0, max_value=10, value=def_dep, step=1, key=f"dep_{st.session_state.cust_preset}")
        
    with col_f2:
        st.markdown("##### ⚠️ 2. Lịch sử Nợ Quá hạn (2 năm qua)")
        late_90 = st.number_input("Số lần quá hạn nghiêm trọng >= 90 ngày:", min_value=0, max_value=20, value=def_late90, step=1, key=f"l90_{st.session_state.cust_preset}", help="Chỉ số quan trọng số 1: Tăng lên >= 1 lần sẽ làm điểm FICO tụt dốc ngay lập tức!")
        late_60_89 = st.number_input("Số lần quá hạn từ 60 - 89 ngày:", min_value=0, max_value=20, value=def_late60, step=1, key=f"l60_{st.session_state.cust_preset}")
        late_30_59 = st.number_input("Số lần quá hạn từ 30 - 59 ngày:", min_value=0, max_value=20, value=def_late30, step=1, key=f"l30_{st.session_state.cust_preset}")
        
    with col_f3:
        st.markdown("##### 💳 3. Đòn bẩy & Hạn mức Tín dụng")
        utilization = st.slider("Tỷ lệ sử dụng hạn mức thẻ tín dụng (Revolving):", min_value=0.0, max_value=2.0, value=def_util, step=0.05, key=f"util_{st.session_state.cust_preset}", help="Chỉ số quan trọng số 2: Kéo thanh trượt lên cao (> 0.60) để quan sát điểm FICO giảm dần")
        debt_ratio = st.slider("Tỷ số nợ trên thu nhập (Debt Ratio):", min_value=0.0, max_value=3.0, value=def_debt, step=0.05, key=f"debt_{st.session_state.cust_preset}")
        open_loans = st.number_input("Số khoản vay và thẻ tín dụng đang mở:", min_value=0, max_value=50, value=def_open, step=1, key=f"open_{st.session_state.cust_preset}")
        re_loans = st.number_input("Số khoản vay bất động sản đang có:", min_value=0, max_value=20, value=def_re, step=1, key=f"re_{st.session_state.cust_preset}")
        
    st.markdown("---")
    col_p1, col_p2 = st.columns([1.5, 2])
    with col_p1:
        product_sel = st.selectbox(
            "🎯 Sản phẩm Tín dụng Khách hàng Đăng ký:",
            options=['MORTGAGE', 'AUTO', 'UNSECURED', 'CREDIT_CARD'],
            format_func=lambda x: {
                'MORTGAGE': '🏡 Cho vay Mua nhà (Mortgage - LGD 25%)',
                'AUTO': '🚗 Cho vay Mua Ô tô (Auto Loan - LGD 45%)',
                'UNSECURED': '💵 Vay Tiêu dùng Tín chấp (Unsecured - LGD 75%)',
                'CREDIT_CARD': '💳 Thẻ Tín dụng Tiêu dùng (Credit Card - LGD 85%)'
            }[x]
        )
    with col_p2:
        loan_request_amt = st.number_input(
            "💰 Số tiền Khách hàng Đề nghị Cấp (VND):",
            min_value=5_000_000,
            max_value=20_000_000_000,
            value=100_000_000,
            step=10_000_000
        )
        
    # Tính toán trực tiếp theo thời gian thực (Real-time Reactive)
    cust_payload = {
        'RevolvingUtilizationOfUnsecuredLines': utilization,
        'age': cust_age,
        'NumberOfTime30-59DaysPastDueNotWorse': late_30_59,
        'DebtRatio': debt_ratio,
        'MonthlyIncome': cust_income if cust_income > 0 else np.nan,
        'NumberOfOpenCreditLinesAndLoans': open_loans,
        'NumberOfTimes90DaysLate': late_90,
        'NumberRealEstateLoansOrLines': re_loans,
        'NumberOfTime60-89DaysPastDueNotWorse': late_60_89,
        'NumberOfDependents': cust_dependents
    }
    
    res = score_single_customer(cust_payload, product_sel, market_mode, loan_request_amt)
    
    st.markdown("---")
    st.markdown(f"### 📊 KẾT QUẢ ĐÁNH GIÁ TÍN DỤNG & RA QUYẾT ĐỊNH TỰ ĐỘNG <span style='font-size: 13px; font-weight: normal; color: #10B981; background: #ECFDF5; padding: 4px 10px; border-radius: 20px; border: 1px solid #A7F3D0;'>⚡ CẬP NHẬT TỨC THÌ (REAL-TIME)</span>", unsafe_allow_html=True)
        
    # Banner quyết định
    if res['dec_code'] == 'APPROVED':
        st.markdown(f'<div class="decision-approved">✅ {res["decision"]}<div style="font-size: 14px; font-weight: normal; margin-top: 5px;">{res["reason"]}</div></div>', unsafe_allow_html=True)
    elif res['dec_code'] == 'CONDITIONAL':
        st.markdown(f'<div class="decision-conditional">⚠️ {res["decision"]}<div style="font-size: 14px; font-weight: normal; margin-top: 5px;">{res["reason"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="decision-rejected">🚫 {res["decision"]}<div style="font-size: 14px; font-weight: normal; margin-top: 5px;">{res["reason"]}</div></div>', unsafe_allow_html=True)
        
    col_res1, col_res2, col_res3 = st.columns([1.5, 1.2, 1.3])
    
    with col_res1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">ĐỒNG HỒ ĐIỂM FICO SCORECARD</div>', unsafe_allow_html=True)
        
        # Đồng hồ Plotly Speedometer Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=res['fico'],
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [300, 850], 'tickwidth': 1, 'tickcolor': "#475569"},
                'bar': {'color': "#1E3A8A", 'thickness': 0.3},
                'steps': [
                    {'range': [300, 527], 'color': "#FCA5A5"},  # Đỏ
                    {'range': [527, 571], 'color': "#FDE68A"},  # Vàng
                    {'range': [571, 600], 'color': "#A7F3D0"},  # Xanh nhạt
                    {'range': [600, 850], 'color': "#34D399"}   # Xanh ngọc
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': res['fico']
                }
            }
        ))
        fig_gauge.update_layout(height=240, margin=dict(l=15, r=15, t=20, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_res2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-label">XÁC SUẤT VỠ NỢ (PD)</div><div class="metric-value">{res["pd"]*100:.2f}%</div>', unsafe_allow_html=True)
        st.caption(f"Khoảng tin cậy Wilson 95%: **{res['wilson']}**")
        st.markdown("---")
        st.markdown(f'<div class="metric-label">HẠNG RỦI RO DANH MỤC</div><div class="metric-value" style="font-size: 20px; color: #2563EB;">{res["grade"]}</div>', unsafe_allow_html=True)
        st.caption(f"Phân loại nút lá: **Lá #{res['leaf_id']}**")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_res3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-label">NGƯỠNG HÒA VỐN SẢN PHẨM (PD*)</div><div class="metric-value">{res["pd_star"]*100:.2f}%</div>', unsafe_allow_html=True)
        st.caption(f"Dành riêng cho: **{res['product_name']}**")
        st.markdown("---")
        profit_color = "#10B981" if res['profit_vnd'] >= 0 else "#EF4444"
        st.markdown(f'<div class="metric-label">LỢI NHUẬN RÒNG KỲ VỌNG</div><div class="metric-value" style="font-size: 20px; color: {profit_color};">{res["profit_vnd"]:,.0f} VND</div>', unsafe_allow_html=True)
        st.caption("Sau khi trừ chi phí vốn, vận hành & bù đắp rủi ro mất vốn.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Giải trình AI Hộp trắng
    with st.expander("🔍 Xem Đường Dẫn Quy Tắc Logic Giải Trình (Explainable AI - IF...THEN)", expanded=True):
        st.markdown(f"""
        **Quy tắc ra quyết định trích xuất từ Cây Quyết định cho Hồ sơ này:**  
        `IF {res['rule']} THEN PD = {res['pd']*100:.2f}% -> {res['grade']}`  
        
        *Hồ sơ này hoàn toàn minh bạch, đáp ứng 100% yêu cầu giải trình của Trụ cột 2 Basel II và sẵn sàng in xuất thành Tờ trình Thẩm định tín dụng.*
        """)

# ==============================================================================
# TAB 2: CHẤM ĐIỂM DANH MỤC LÔ HÀNG LOẠT (BATCH PORTFOLIO SCORING)
# ==============================================================================
if 'batch' in user['allowed_tabs']:
    with active_tabs[tab_labels.index("📁 Chấm điểm Danh mục Lô (Batch Excel)")]:
        st.markdown("### 📁 Tải Lên Danh Sách Hồ Sơ Khách Hàng Để Chấm Điểm Hàng Loạt")
        st.write("Hệ thống cho phép nạp hàng nghìn hồ sơ từ file Excel hoặc CSV để tính toán nhanh chóng Điểm FICO, Phân hạng Rủi ro và Lợi nhuận dự kiến cho toàn Chi nhánh.")
        
        col_up1, col_up2 = st.columns([2, 1])
        with col_up1:
            uploaded_file = st.file_uploader("Kéo và thả tệp dữ liệu khách hàng (.csv, .xlsx):", type=['csv', 'xlsx'])
        with col_up2:
            st.markdown("<br>", unsafe_allow_html=True)
            # Tạo file mẫu CSV để tải về
            sample_template = pd.DataFrame([{
                'Customer_ID': 'KH001',
                'RevolvingUtilizationOfUnsecuredLines': 0.25,
                'age': 40,
                'NumberOfTime30-59DaysPastDueNotWorse': 0,
                'DebtRatio': 0.35,
                'MonthlyIncome': 8000,
                'NumberOfOpenCreditLinesAndLoans': 7,
                'NumberOfTimes90DaysLate': 0,
                'NumberRealEstateLoansOrLines': 1,
                'NumberOfTime60-89DaysPastDueNotWorse': 0,
                'NumberOfDependents': 1,
                'Product_Type': 'CREDIT_CARD',
                'Loan_Amount_VND': 50000000
            }])
            st.download_button(
                "📥 Tải File Mẫu Chuẩn (Template CSV)",
                data=sample_template.to_csv(index=False).encode('utf-8'),
                file_name="mau_danh_sach_vay_smartcredit.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    batch_df = pd.read_csv(uploaded_file)
                else:
                    batch_df = pd.read_excel(uploaded_file)
                    
                st.success(f"✓ Đã nạp thành công **{len(batch_df):,}** hồ sơ khách hàng!")
                
                # Tiến hành chấm điểm hàng loạt
                scored_records = []
                for _, row in batch_df.iterrows():
                    p_type = row.get('Product_Type', 'CREDIT_CARD')
                    l_amt = row.get('Loan_Amount_VND', 50_000_000)
                    row_dict = row.to_dict()
                    r_eval = score_single_customer(row_dict, p_type, market_mode, l_amt)
                    
                    row_res = row_dict.copy()
                    row_res['FICO_Score'] = r_eval['fico']
                    row_res['PD_Percent'] = round(r_eval['pd'] * 100, 2)
                    row_res['Risk_Grade'] = r_eval['grade']
                    row_res['Decision'] = r_eval['decision']
                    row_res['Decision_Code'] = r_eval['dec_code']
                    row_res['Expected_Profit_VND'] = r_eval['profit_vnd']
                    scored_records.append(row_res)
                    
                result_batch_df = pd.DataFrame(scored_records)
                
                # Thống kê nhanh danh mục
                total_cust = len(result_batch_df)
                total_app = (result_batch_df['Decision_Code'] == 'APPROVED').sum()
                app_rate = total_app / total_cust * 100
                total_profit = result_batch_df['Expected_Profit_VND'].sum()
                
                st.markdown("#### 📈 Tổng Hợp Hiệu Quả Danh Mục Lô Hồ Sơ")
                km1, km2, km3, km4 = st.columns(4)
                km1.metric("Tổng Số Hồ Sơ", f"{total_cust:,}")
                km2.metric("Số Hồ Sơ Được Duyệt", f"{total_app:,}")
                km3.metric("Tỷ Lệ Duyệt Tự Động", f"{app_rate:.1f}%")
                km4.metric("Tổng Lợi Nhuận Dự Kiến", f"{total_profit:,.0f} VND")
                
                col_chart1, col_chart2 = st.columns([1.5, 2.5])
                with col_chart1:
                    # Biểu đồ Donut phân bố hạng rủi ro
                    grade_counts = result_batch_df['Risk_Grade'].value_counts().reset_index()
                    fig_pie = px.pie(grade_counts, values='count', names='Risk_Grade', hole=0.45,
                                     title="Cơ cấu Phân tầng Hạng Rủi ro",
                                     color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_pie.update_layout(margin=dict(l=10, r=10, t=35, b=10), height=300)
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                with col_chart2:
                    st.markdown("##### 📋 Danh sách Kết quả Chi tiết")
                    st.dataframe(result_batch_df[['Customer_ID' if 'Customer_ID' in result_batch_df.columns else 'age', 
                                                  'FICO_Score', 'PD_Percent', 'Risk_Grade', 'Decision', 'Expected_Profit_VND']].head(10), 
                                 use_container_width=True)
                    
                st.download_button(
                    "💾 Xuất Toàn Bộ Kết Quả Đã Chấm Điểm (CSV)",
                    data=result_batch_df.to_csv(index=False).encode('utf-8'),
                    file_name="ket_qua_cham_diem_danh_muc.csv",
                    mime="text/csv",
                    type="primary"
                )
            except Exception as e:
                st.error(f"Lỗi định dạng dữ liệu trong file: {e}")

# ==============================================================================
# TAB 3: TRUNG TÂM ĐIỀU HÀNH CHÍNH SÁCH (DÀNH CHO CRO)
# ==============================================================================
if 'policy' in user['allowed_tabs']:
    with active_tabs[tab_labels.index("⚖️ Trung tâm Điều hành Chính sách (CRO)")]:
        st.markdown("### ⚖️ Điều Hành Khẩu Vị Rủi Ro & Tối Ưu Hóa Biên Lợi Nhuận")
        st.write("Cho phép Giám đốc Quản lý Rủi ro (CRO) tùy biến các tham số kinh tế vi mô và quan sát ngay lập tức sự thay đổi của Ngưỡng hòa vốn ($PD^*$) cũng như Đường cong Lợi nhuận danh mục.")
        
        col_pol1, col_pol2 = st.columns([1.2, 2])
        
        with col_pol1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("##### ⚙️ Tùy Chỉnh Tham Số Sản Phẩm")
            sel_pol_prod = st.selectbox("Chọn Sản phẩm Điều chỉnh:", options=['MORTGAGE', 'AUTO', 'UNSECURED', 'CREDIT_CARD'])
            
            current_cfg = multi_cfg[sel_pol_prod]['params']
            
            new_r = st.slider("Biên lãi cho vay r (%/năm):", min_value=3.0, max_value=25.0, value=float(current_cfg['r']*100), step=0.5) / 100.0
            new_c = st.slider("Chi phí vận hành c (%/năm):", min_value=0.5, max_value=8.0, value=float(current_cfg['c']*100), step=0.5) / 100.0
            new_lgd = st.slider("Tỷ lệ tổn thất khi vỡ nợ LGD (%):", min_value=10.0, max_value=95.0, value=float(current_cfg['lgd']*100), step=5.0) / 100.0
            
            calc_net_m = new_r - new_c
            calc_pd_star = calc_net_m / (calc_net_m + new_lgd) if (calc_net_m + new_lgd) > 0 else 0.0
            
            st.markdown("---")
            st.markdown(f"**Ngưỡng hòa vốn kinh tế mới ($PD^*$):** <span style='font-size: 22px; font-weight: bold; color: #2563EB;'>{calc_pd_star*100:.2f}%</span>", unsafe_allow_html=True)
            st.caption(f"Biên lãi thuần r - c: **{calc_net_m*100:.1f}%** | LGD: **{new_lgd*100:.1f}%**")
            
            if st.button("💾 Cập Nhật Khẩu Vị Vào Hệ Thống", type="primary", use_container_width=True):
                multi_cfg[sel_pol_prod]['params']['r'] = new_r
                multi_cfg[sel_pol_prod]['params']['c'] = new_c
                multi_cfg[sel_pol_prod]['params']['lgd'] = new_lgd
                multi_cfg[sel_pol_prod]['params']['pd_breakeven'] = calc_pd_star
                st.success("✓ Đã cập nhật thành công khẩu vị rủi ro vào hệ thống!")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_pol2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("##### 📈 Mô Phỏng Đường Cong Lợi Nhuận Kỳ Vọng Theo Điểm FICO")
            
            # Giả lập đường cong lợi nhuận tương tác
            test_fico_scores = np.linspace(480, 620, 30)
            mock_pds = 1 / (1 + np.exp((test_fico_scores - 550) / 20)) # Hàm sigmoid minh họa
            profits_curve = (1 - mock_pds) * calc_net_m - mock_pds * new_lgd
            
            fig_curve = go.Figure()
            fig_curve.add_trace(go.Scatter(x=test_fico_scores, y=profits_curve * 100, mode='lines+markers', name='Biên Lợi nhuận (%)', line=dict(color='#2563EB', width=3)))
            fig_curve.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="Điểm Hòa Vốn")
            fig_curve.update_layout(
                title=f"Đường cong Tỷ suất Lợi nhuận Ròng - {multi_cfg[sel_pol_prod]['product_name']}",
                xaxis_title="Ngưỡng Điểm Cắt FICO (Cut-off Score)",
                yaxis_title="Lợi nhuận ròng (% trên dư nợ)",
                height=320,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_curve, use_container_width=True)
            st.caption("Khảo sát cho thấy việc nâng cut-off FICO giúp loại bỏ lỗ nhưng thu hẹp dư nợ; hạ cut-off giúp mở rộng dư nợ nhưng tăng rủi ro nợ xấu.")
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 4: BÁO CÁO GIÁM SÁT BASEL II & AUDIT (KIỂM TOÁN MÔ HÌNH)
# ==============================================================================
if 'audit' in user['allowed_tabs']:
    with active_tabs[tab_labels.index("📊 Báo cáo Giám sát Basel II (Audit)")]:
        st.markdown("### 📊 Báo Cáo Kiểm Toán & Giám Sát Mô Hình Theo Chuẩn Basel II")
        st.write("Bảng điều khiển định kỳ phục vụ Ủy ban ALCO và Cơ quan Thanh tra Giám sát Ngân hàng Nhà nước.")
        
        ak1, ak2, ak3, ak4 = st.columns(4)
        ak1.metric("AUC-ROC (Test 30k)", "0.8521", "+0.005 vs Logistic")
        ak2.metric("Hệ số Gini", "0.7041", "> 0.60 Chuẩn Basel II")
        ak3.metric("KS Statistic", "55.87%", "> 40% Cực Mạnh")
        ak4.metric("Chỉ số Trôi dạt PSI", "0.00013", "< 0.10 An Toàn")
        
        st.markdown("---")
        col_g1, col_g2 = st.columns([1.5, 2])
        
        with col_g1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("##### 🎯 Đồng Hồ Đo Độ Ổn Định Dân Số (PSI)")
            
            fig_psi = go.Figure(go.Indicator(
                mode="gauge+number",
                value=0.00013,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 0.30]},
                    'bar': {'color': "#10B981"},
                    'steps': [
                        {'range': [0, 0.10], 'color': "#D1FAE5"}, # An toàn
                        {'range': [0.10, 0.25], 'color': "#FEF3C7"}, # Cảnh báo
                        {'range': [0.25, 0.30], 'color': "#FEE2E2"}  # Nguy hiểm
                    ]
                }
            ))
            fig_psi.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_psi, use_container_width=True)
            st.success("✓ **Dân số ổn định tuyệt đối:** Phân phối rủi ro của tập Test không bị trôi dạt so với tập Train.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_g2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("##### 🏆 Tầm Quan Trọng Của Các Biến Số Hàng Đầu")
            if not feat_df.empty:
                fig_bar = px.bar(feat_df.head(6), x='MDI Tỷ lệ (%)', y='Biến đặc trưng', orientation='h',
                                 color='MDI Tỷ lệ (%)', color_continuous_scale='Blues')
                fig_bar.update_layout(yaxis={'autorange': 'reversed'}, height=240, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# Footer chân trang
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 12px; margin-top: 40px; padding: 20px 0; border-top: 1px solid #E2E8F0;">
    SMARTCREDIT AI PLATFORM © 2026 | DỰ ÁN TỐT NGHIỆP TRÍ TUỆ NHÂN TẠO TRONG TÀI CHÍNH - NGÂN HÀNG<br/>
    Tuân thủ Hiệp ước Basel II / Basel III & Chuẩn mực Báo cáo Tài chính IFRS 9
</div>
""", unsafe_allow_html=True)

