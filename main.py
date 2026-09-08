import streamlit as st
import requests
import re
import plotly.graph_objects as go

# Streamlit Secrets에서 API 키 불러오기
NEIS_API_KEY = st.secrets["NEIS_API_KEY"]


def search_school(school_name):
    """
    학교 이름으로 학교 코드와 교육청 코드를 찾는 함수
    """
    url = "https://open.neis.go.kr/hub/schoolInfo"
    params = {
        "KEY": NEIS_API_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 10,
        "SCHUL_NM": school_name,
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "schoolInfo" not in data:
        return []

    return data["schoolInfo"][1]["row"]


def get_meal_data(office_code, school_code, from_date, to_date):
    """
    나이스 급식 API를 호출해서 급식 정보를 리스트로 반환하는 함수
    """
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": NEIS_API_KEY,
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
        st.error("급식 데이터를 가져오지 못했습니다. 날짜나 학교 코드를 확인해주세요.")
        st.write("API 응답 내용:", data)  # 에러 원인 확인용
        return []

    return data["mealServiceDietInfo"][1]["row"]


def extract_calorie(cal_info_str):
    """
    '560.5 Kcal' 같은 문자열에서 숫자만 뽑아내는 함수
    """
    match = re.search(r"[\d.]+", cal_info_str)
    return float(match.group()) if match else 0.0


def analyze_school_meals(rows):
    """
    급식 데이터 리스트를 받아서 (날짜리스트, 칼로리리스트)를 반환
    """
    dates = [row["MLSV_YMD"] for row in rows]
    calories = [extract_calorie(row["CAL_INFO"]) for row in rows]
    return dates, calories


# ============================
# Streamlit 화면 구성 시작
# ============================
st.title("🍱 급식 칼로리 분석")

st.header("1. 학교 검색")
school_name_input = st.text_input("학교 이름을 입력하세요", "당곡고등학교")

if st.button("학교 검색하기"):
    results = search_school(school_name_input)
    if results:
        st.session_state["search_results"] = results
    else:
        st.warning("검색 결과가 없습니다. 학교 이름을 다시 확인해주세요.")

if "search_results" in st.session_state:
    options = {
        f'{r["SCHUL_NM"]} ({r["ATPT_OFCDC_SC_NM"]})': (r["ATPT_OFCDC_SC_CODE"], r["SD_SCHUL_CODE"])
        for r in st.session_state["search_results"]
    }
    selected = st.selectbox("검색된 학교 중 선택하세요", list(options.keys()))
    office_code, school_code = options[selected]

    st.divider()
    st.header("2. 급식 기간 선택")

    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("시작 날짜")
    with col2:
        to_date = st.date_input("종료 날짜")

    if st.button("급식 데이터 조회하기"):
        from_str = from_date.strftime("%Y%m%d")
        to_str = to_date.strftime("%Y%m%d")

        rows = get_meal_data(office_code, school_code, from_str, to_str)
        dates, calories = analyze_school_meals(rows)

        if calories:
            max_cal = max(calories)
            max_index = calories.index(max_cal)
            max_date = dates[max_index]
            avg_cal = sum(calories) / len(calories)

            st.divider()
            st.header("3. 결과 그래프")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=calories,
                mode='lines+markers',
                name="칼로리"
            ))
            fig.add_trace(go.Scatter(
                x=[max_date], y=[max_cal],
                mode='markers',
                marker=dict(color='red', size=15, symbol='star'),
                name=f"최고 칼로리: {max_cal} Kcal"
            ))
            fig.update_layout(
                title=f"{selected} 급식 칼로리 변화",
                xaxis_title="날짜",
                yaxis_title="칼로리(Kcal)",
                hovermode="x unified"
            )
            st.plotly_chart(fig)

            st.success(f"최고 칼로리 날짜: **{max_date}**, 칼로리: **{max_cal} Kcal**")
            st.info(f"평균 칼로리: **{avg_cal:.1f} Kcal**")
        else:
            st.warning("표시할 급식 데이터가 없습니다.")
