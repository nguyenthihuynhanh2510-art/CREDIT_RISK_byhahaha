# -*- coding: utf-8 -*-
"""
MODULE TIỀN XỬ LÝ DỮ LIỆU CHUẨN MỰC - SMARTCREDIT AI
Tích hợp trọn vẹn Thuật toán Ý tưởng 2:
1. Xử lý mã lỗi hệ thống 96/98 bằng cờ phân loại rủi ro Has_Code_96_98.
2. Tái lập Thu nhập và DebtRatio bằng mô hình hồi quy ước lượng có điều kiện (Two-Stage Predictive Imputation).
3. Đảm bảo chống rò rỉ dữ liệu (Zero Data Leakage) 100% theo chuẩn Basel II / IFRS 9.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

TARGET = "SeriousDlqin2yrs"

DELINQ = [
    "NumberOfTime30-59DaysPastDueNotWorse",
    "NumberOfTimes90DaysLate",
    "NumberOfTime60-89DaysPastDueNotWorse",
]

RAW_FEATURES = [
    "RevolvingUtilizationOfUnsecuredLines",
    "age",
    "NumberOfTime30-59DaysPastDueNotWorse",
    "DebtRatio",
    "MonthlyIncome",
    "NumberOfOpenCreditLinesAndLoans",
    "NumberOfTimes90DaysLate",
    "NumberRealEstateLoansOrLines",
    "NumberOfTime60-89DaysPastDueNotWorse",
    "NumberOfDependents",
]

FLAGS = ["MonthlyIncome_is_missing", "Has_Code_96_98"]
FEATURES = RAW_FEATURES + FLAGS  # Đúng 12 biến đặc trưng đưa vào mô hình


def fit_preprocessor(train: pd.DataFrame) -> dict:
    """
    Học tham số thống kê và mô hình hồi quy thu nhập DUY NHẤT từ TẬP TRAIN RAW.
    Tuyệt đối không gọi hàm này trên tập Test hay toàn bộ dữ liệu gộp.
    """
    # 1. Lọc nhóm hồ sơ có thu nhập hợp lệ trong tập Train
    has_income = train["MonthlyIncome"].notna() & (train["MonthlyIncome"] > 0)
    train_valid = train[has_income].copy()

    # 2. Ngưỡng cắt trần và trung vị cơ sở trên tập Train
    cap_revolving = float(train["RevolvingUtilizationOfUnsecuredLines"].quantile(0.995))
    cap_debtratio = float(train_valid["DebtRatio"].quantile(0.995))
    median_debtratio = float(train_valid["DebtRatio"].median())
    cap_income = float(train_valid["MonthlyIncome"].quantile(0.995))
    median_income = float(train_valid["MonthlyIncome"].median())
    median_age = float(train.loc[train["age"] >= 18, "age"].median())
    median_dependents = float(train["NumberOfDependents"].median())

    # 3. Ý TƯỞNG 2: Huấn luyện mô hình hồi quy Ridge ước lượng thu nhập log(1 + Income)
    pred_features = [
        "age",
        "NumberRealEstateLoansOrLines",
        "NumberOfOpenCreditLinesAndLoans",
        "RevolvingUtilizationOfUnsecuredLines",
    ]

    X_impute = train_valid[pred_features].copy()
    X_impute["RevolvingUtilizationOfUnsecuredLines"] = X_impute[
        "RevolvingUtilizationOfUnsecuredLines"
    ].clip(0, 2.0)
    X_impute["NumberRealEstateLoansOrLines"] = X_impute[
        "NumberRealEstateLoansOrLines"
    ].clip(0, 10)
    X_impute["NumberOfOpenCreditLinesAndLoans"] = X_impute[
        "NumberOfOpenCreditLinesAndLoans"
    ].clip(0, 30)

    y_impute_log = np.log1p(train_valid["MonthlyIncome"].clip(0, cap_income))

    imputer_ridge = Ridge(alpha=10.0, random_state=42)
    imputer_ridge.fit(X_impute, y_impute_log)

    params = {
        "median_age": median_age,
        "cap_revolving": cap_revolving,
        "cap_debtratio": cap_debtratio,
        "median_debtratio": median_debtratio,
        "cap_income": cap_income,
        "median_income": median_income,
        "median_dependents": median_dependents,
        "imputer_pred_features": pred_features,
        "imputer_intercept": float(imputer_ridge.intercept_),
        "imputer_coefs": {
            feat: float(coef)
            for feat, coef in zip(pred_features, imputer_ridge.coef_)
        },
    }
    return params


def apply_preprocessor(data: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Áp dụng các tham số đã học từ Train sang bất kỳ tập dữ liệu nào (Train, Test, Web).
    Tích hợp trọn vẹn Ý tưởng 2: Tái lập DebtRatio = D / Income_hat cho nhóm khuyết thu nhập.
    """
    out = data.copy()

    # BƯỚC 1: Tạo cờ nhận diện đặc trưng TRƯỚC KHI thay đổi giá trị
    out["Has_Code_96_98"] = out[DELINQ].isin([96, 98]).any(axis=1).astype(int)
    out["MonthlyIncome_is_missing"] = (
        out["MonthlyIncome"].isna() | (out["MonthlyIncome"] == 0)
    ).astype(int)

    # BƯỚC 2: Đưa mã 96/98 về 0 ở các cột quá hạn (vì không phải số lần thực tế)
    for col in DELINQ:
        out[col] = out[col].replace([96, 98], 0)

    # BƯỚC 3: Xử lý tuổi lỗi nhập liệu (< 18) bằng trung vị train
    out["age"] = np.where(out["age"] < 18, params["median_age"], out["age"])

    # BƯỚC 4: Ý TƯỞNG 2 - ƯỚC LƯỢNG THU NHẬP VÀ TÁI LẬP DEBT RATIO
    pred_feats = params["imputer_pred_features"]
    X_pred = out[pred_feats].copy()
    X_pred["RevolvingUtilizationOfUnsecuredLines"] = X_pred[
        "RevolvingUtilizationOfUnsecuredLines"
    ].clip(0, 2.0)
    X_pred["NumberRealEstateLoansOrLines"] = X_pred[
        "NumberRealEstateLoansOrLines"
    ].clip(0, 10)
    X_pred["NumberOfOpenCreditLinesAndLoans"] = X_pred[
        "NumberOfOpenCreditLinesAndLoans"
    ].clip(0, 30)

    # Tính log_income_hat = Intercept + sum(X_j * coef_j)
    pred_log_income = np.full(len(out), params["imputer_intercept"])
    for feat, coef in params["imputer_coefs"].items():
        pred_log_income += X_pred[feat].values * coef

    pred_income = np.expm1(pred_log_income)
    # Đặt sàn tối thiểu 500 USD (tránh chia cho số gần 0) và trần cap_income
    pred_income = np.clip(pred_income, 500.0, params["cap_income"])

    # Với nhóm khuyết thu nhập: DebtRatio gốc bản chất là số tiền nợ D (USD)
    out["DebtRatio"] = out["DebtRatio"].astype(float)
    out["MonthlyIncome"] = out["MonthlyIncome"].astype(float)
    missing_mask = out["MonthlyIncome_is_missing"] == 1
    out.loc[missing_mask, "DebtRatio"] = (
        out.loc[missing_mask, "DebtRatio"] / pred_income[missing_mask]
    )
    out.loc[missing_mask, "MonthlyIncome"] = pred_income[missing_mask]

    # Cắt trần DebtRatio chuẩn tắc
    out["DebtRatio"] = out["DebtRatio"].clip(0, params["cap_debtratio"])

    # BƯỚC 5: Cắt trần tỷ lệ sử dụng hạn mức thẻ
    out["RevolvingUtilizationOfUnsecuredLines"] = out[
        "RevolvingUtilizationOfUnsecuredLines"
    ].clip(0, params["cap_revolving"])

    # BƯỚC 6: Cắt trần thu nhập nhóm hợp lệ
    out["MonthlyIncome"] = out["MonthlyIncome"].clip(0, params["cap_income"])

    # BƯỚC 7: Số người phụ thuộc điền trung vị
    out["NumberOfDependents"] = out["NumberOfDependents"].fillna(
        params["median_dependents"]
    )

    cols = ([TARGET] if TARGET in out.columns else []) + FEATURES
    return out[cols]


def add_business_features(raw: pd.DataFrame, cleaned: pd.DataFrame) -> pd.DataFrame:
    """
    (Tùy chọn) Tạo thêm 2 biến nghiệp vụ bổ sung phục vụ bài toán Thí nghiệm (Ablation Study).
    Yêu cầu cả dữ liệu thô và dữ liệu đã làm sạch.
    """
    out = cleaned.copy()
    invalid = raw["MonthlyIncome"].isna() | (raw["MonthlyIncome"] == 0)

    # Số tiền nợ hàng tháng quy đổi (USD)
    amount = np.where(
        invalid, raw["DebtRatio"], raw["DebtRatio"] * raw["MonthlyIncome"]
    )
    out["MonthlyDebtPayment_log"] = np.log1p(np.clip(amount, 0, None))

    # Tổng số lần quá hạn tích lũy cả 3 kỳ hạn
    out["TotalPastDue"] = cleaned[DELINQ].sum(axis=1)
    return out


def preprocess_one(record: dict, params: dict) -> pd.DataFrame:
    """
    Dùng cho Web Portal Streamlit hoặc chấm điểm đơn lẻ:
    record: dictionary chứa 10 biến gốc của 1 khách hàng.
    """
    row = pd.DataFrame([record]).apply(pd.to_numeric, errors="coerce")
    row = row.reindex(columns=RAW_FEATURES)
    return apply_preprocessor(row, params)[FEATURES]
