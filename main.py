import streamlit as st
import requests
import re
import plotly.graph_objects as go


def get_meal_data(office_code, school_code, from_date, to_date, api_key):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": api_key,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "ATPT_OFCDC_SC_CODE": office_code,
        "SD_SCHUL_CODE": school_code,
        "MLSV_FROM_YMD": from_date,
        "MLSV_TO_YMD": to_date,
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "mealServiceDietInfo" not in data:
        st.error("데이터를 가져오지 못했습니다. 학교 코드나 날짜를 확인해보세요.")
        return []

    return data["mealServiceDietInfo"][1]["row"]


def extract_calorie(cal_info_str):
    match = re.search(r"[\d.]+", cal_info_str)
    return float(match.group()) if match else 0.0


def analyze_school_meals(rows):
    dates = [row["MLSV_YMD"] for row in rows]
    calories = [extract_calorie(row["CAL_INFO"]) for row in rows]
    return dates, calories


# ===== Streamlit 화면 구성 시작 =====
st.title("우리 학교 급식 칼로리 분석")

API_KEY =  NEIS_API_KEY = "4700574c38d548efb942c1605da72a53"
office_code = "B10"
school_code = "7010570"
from_date = "20240301"
to_date = "20240331"

rows = get_meal_data(office_code, school_code, from_date, to_date, API_KEY)
dates, calories = analyze_school_meals(rows)

if calories:
    max_cal = max(calories)
    max_index = calories.index(max_cal)
    max_date = dates[max_index]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=calories, mode='lines+markers', name="칼로리"))
    fig.add_trace(go.Scatter(
        x=[max_date], y=[max_cal],
        mode='markers', marker=dict(color='red', size=15, symbol='star'),
        name=f"최고 칼로리: {max_cal} Kcal"
    ))
    fig.update_layout(title="급식 칼로리 변화", xaxis_title="날짜", yaxis_title="칼로리(Kcal)")

    # 반드시 st.plotly_chart로 그려야 화면에 나타남!
    st.plotly_chart(fig)

    st.write(f"최고 칼로리 날짜: **{max_date}**, 칼로리: **{max_cal} Kcal**")
else:
    st.warning("표시할 데이터가 없습니다.")
