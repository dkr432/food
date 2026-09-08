import streamlit as st
import requests
import re
import plotly.graph_objects as go

NEIS_API_KEY = st.secrets["NEIS_API_KEY"]


def search_school(school_name):
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
        return []

    return data["mealServiceDietInfo"][1]["row"]


def extract_calorie(cal_info_str):
    match = re.search(r"[\d.]+", cal_info_str)
    return float(match.group()) if match else 0.0


def clean_menu_text(menu_str):
    return menu_str.replace("<br/>", "<br>")


def analyze_school_meals(rows):
    dates = [row["MLSV_YMD"] for row in rows]
    calories = [extract_calorie(row["CAL_INFO"]) for row in rows]
    menus = [clean_menu_text(row["DDISH_NM"]) for row in rows]
    return dates, calories, menus


def format_date(yyyymmdd):
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"


def school_search_ui(label_prefix, default_name=""):
    """
    학교 검색 + 선택 UI를 만들어주는 함수
    label_prefix: 화면에 표시할 구분용 이름 (예: "우리 학교", "비교 학교")
    반환값: (학교이름, 교육청코드, 학교코드) 또는 None
    """
    st.subheader(f"🏫 {label_prefix} 검색")
    name_input = st.text_input(f"{label_prefix} 이름을 입력하세요", default_name, key=f"input_{label_prefix}")

    search_key = f"search_results_{label_prefix}"

    if st.button(f"{label_prefix} 검색하기", key=f"btn_{label_prefix}"):
        results = search_school(name_input)
        if results:
            st.session_state[search_key] = results
        else:
            st.warning("검색 결과가 없습니다. 학교 이름을 다시 확인해주세요.")

    if search_key in st.session_state:
        options = {
            f'{r["SCHUL_NM"]} ({r["ATPT_OFCDC_SC_NM"]})': (r["SCHUL_NM"], r["ATPT_OFCDC_SC_CODE"], r["SD_SCHUL_CODE"])
            for r in st.session_state[search_key]
        }
        selected = st.selectbox(
            f"{label_prefix} 선택", list(options.keys()), key=f"select_{label_prefix}"
        )
        return options[selected]

    return None


# ============================
# Streamlit 화면 구성 시작
# ============================
st.title("🍱 급식 칼로리 분석 및 비교")

col1, col2 = st.columns(2)

with col1:
    my_school = school_search_ui("우리 학교", "당곡고등학교")

with col2:
    other_school = school_search_ui("비교할 학교")

st.divider()
st.header("급식 기간 선택")

col3, col4 = st.columns(2)
with col3:
    from_date = st.date_input("시작 날짜")
with col4:
    to_date = st.date_input("종료 날짜")

if st.button("데이터 조회 및 비교하기"):
    if not my_school:
        st.warning("우리 학교를 먼저 검색하고 선택해주세요.")
    else:
        from_str = from_date.strftime("%Y%m%d")
        to_str = to_date.strftime("%Y%m%d")

        # ----- 우리 학교 데이터 처리 -----
        my_name, my_office_code, my_school_code = my_school
        my_rows = get_meal_data(my_office_code, my_school_code, from_str, to_str)
        my_dates, my_calories, my_menus = analyze_school_meals(my_rows)

        if not my_calories:
            st.error(f"{my_name}의 급식 데이터를 가져오지 못했습니다.")
        else:
            # ---- 칼로리 높은 순 그래프 (우리 학교) ----
            combined = list(zip(my_dates, my_calories, my_menus))
            combined.sort(key=lambda x: x[1], reverse=True)

            sorted_labels = [f"{i+1}. {format_date(d)}" for i, (d, c, m) in enumerate(combined)]
            sorted_calories = [c for d, c, m in combined]
            sorted_menus = [m for d, c, m in combined]
            colors = ['red'] + ['royalblue'] * (len(sorted_calories) - 1)

            st.divider()
            st.header(f"1. {my_name} 칼로리 높은 순 그래프")

            fig1 = go.Figure(data=[
                go.Bar(
                    x=sorted_labels,
                    y=sorted_calories,
                    marker_color=colors,
                    text=[f"{c:.0f}" for c in sorted_calories],
                    textposition='outside',
                    customdata=sorted_menus,
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "칼로리: %{y} Kcal<br>"
                        "메뉴:<br>%{customdata}"
                        "<extra></extra>"
                    )
                )
            ])
            fig1.update_layout(
                title=f"{my_name} 급식 칼로리 순위",
                xaxis_title="급식 날짜 (순위)",
                yaxis_title="칼로리(Kcal)",
                xaxis_tickangle=-45,
                xaxis_type="category"
            )
            st.plotly_chart(fig1)

            st.success(f"가장 칼로리가 높은 급식: **{format_date(combined[0][0])}**, **{combined[0][1]} Kcal**")
            st.caption(f"메뉴: {combined[0][2].replace('<br>', ', ')}")

            my_avg = sum(my_calories) / len(my_calories)

            # ----- 비교 학교 데이터 처리 -----
            if other_school:
                other_name, other_office_code, other_school_code = other_school
                other_rows = get_meal_data(other_office_code, other_school_code, from_str, to_str)
                _, other_calories, _ = analyze_school_meals(other_rows)

                if other_calories:
                    other_avg = sum(other_calories) / len(other_calories)

                    st.divider()
                    st.header("2. 평균 칼로리 비교")

                    fig2 = go.Figure(data=[
                        go.Bar(
                            x=[my_name, other_name],
                            y=[my_avg, other_avg],
                            marker_color=['royalblue', 'salmon'],
                            text=[f"{my_avg:.1f}", f"{other_avg:.1f}"],
                            textposition='outside'
                        )
                    ])
                    fig2.update_layout(
                        title="학교별 평균 급식 칼로리 비교",
                        yaxis_title="평균 칼로리(Kcal)"
                    )
                    st.plotly_chart(fig2)

                    diff = my_avg - other_avg
                    if diff > 0:
                        st.info(f"{my_name}의 평균 칼로리가 {other_name}보다 **{diff:.1f} Kcal 더 높습니다.**")
                    elif diff < 0:
                        st.info(f"{my_name}의 평균 칼로리가 {other_name}보다 **{abs(diff):.1f} Kcal 더 낮습니다.**")
                    else:
                        st.info("두 학교의 평균 칼로리가 동일합니다.")
                else:
                    st.warning(f"{other_name}의 급식 데이터를 가져오지 못했습니다.")
            else:
                st.info("비교할 학교를 검색하고 선택하면 평균 칼로리를 비교할 수 있어요.")
