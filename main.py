import requests
import re
import plotly.graph_objects as go


def get_meal_data(office_code, school_code, from_date, to_date, api_key):
    """
    나이스 급식 API를 호출해서 급식 정보를 리스트로 반환하는 함수
    """
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
        print("데이터를 가져오지 못했습니다. 학교 코드나 날짜를 확인해보세요.")
        return []

    rows = data["mealServiceDietInfo"][1]["row"]
    return rows


def extract_calorie(cal_info_str):
    """
    '560.5 Kcal' 같은 문자열에서 숫자만 뽑아내는 함수
    """
    match = re.search(r"[\d.]+", cal_info_str)
    if match:
        return float(match.group())
    return 0.0


def analyze_school_meals(rows):
    """
    급식 데이터 리스트를 받아서 (날짜리스트, 칼로리리스트)를 반환
    """
    dates = []
    calories = []

    for row in rows:
        date = row["MLSV_YMD"]
        cal = extract_calorie(row["CAL_INFO"])
        dates.append(date)
        calories.append(cal)

    return dates, calories


def plot_my_school(dates, calories, school_name):
    """
    Plotly를 이용해 우리 학교의 날짜별 칼로리 그래프 + 최고 칼로리 급식 표시
    """
    max_cal = max(calories)
    max_index = calories.index(max_cal)
    max_date = dates[max_index]

    fig = go.Figure()

    # 전체 칼로리 변화 선 그래프
    fig.add_trace(go.Scatter(
        x=dates,
        y=calories,
        mode='lines+markers',
        name=f"{school_name} 칼로리",
        line=dict(color='royalblue')
    ))

    # 최고 칼로리 지점 강조 표시
    fig.add_trace(go.Scatter(
        x=[max_date],
        y=[max_cal],
        mode='markers',
        marker=dict(color='red', size=15, symbol='star'),
        name=f"최고 칼로리: {max_cal} Kcal ({max_date})"
    ))

    fig.update_layout(
        title=f"{school_name} 급식 칼로리 변화",
        xaxis_title="급식 날짜",
        yaxis_title="칼로리 (Kcal)",
        hovermode="x unified"
    )

    fig.show()

    print(f"\n[결과] {school_name}에서 칼로리가 가장 높았던 급식 날짜는 {max_date}이며, {max_cal} Kcal 입니다.")


def plot_average_comparison(school_names, average_calories):
    """
    Plotly 막대그래프로 여러 학교의 평균 칼로리 비교
    """
    fig = go.Figure(data=[
        go.Bar(
            x=school_names,
            y=average_calories,
            text=[f"{avg:.1f}" for avg in average_calories],
            textposition='outside',
            marker_color=['skyblue', 'salmon', 'lightgreen']
        )
    ])

    fig.update_layout(
        title="학교별 평균 급식 칼로리 비교",
        yaxis_title="평균 칼로리 (Kcal)"
    )

    fig.show()


# ========================================
# 실제 사용 예시 (본인 상황에 맞게 값 수정!)
# ========================================
if __name__ == "__main__":
    API_KEY = "여기에_발급받은_인증키_입력"  # 나이스 오픈API에서 신청

    # 예시: 당곡고등학교 (실제 코드로 바꿔서 사용하세요)
    my_office_code = "B10"       # 시도교육청코드 (예: 서울=B10)
    my_school_code = "7010570"   # 행정표준코드 (당곡고 예시, 확인 필요)

    from_date = "20240301"
    to_date = "20240331"

    # 1. 우리 학교 데이터 가져오기
    my_rows = get_meal_data(my_office_code, my_school_code, from_date, to_date, API_KEY)
    my_dates, my_calories = analyze_school_meals(my_rows)

    if my_calories:
        plot_my_school(my_dates, my_calories, "당곡고등학교")
        my_avg = sum(my_calories) / len(my_calories)
    else:
        my_avg = 0

    # 2. 비교할 다른 학교 데이터 가져오기 (학교 코드 직접 조사해서 입력)
    other_office_code = "B10"
    other_school_code = "다른학교_행정표준코드"

    other_rows = get_meal_data(other_office_code, other_school_code, from_date, to_date, API_KEY)
    _, other_calories = analyze_school_meals(other_rows)

    if other_calories:
        other_avg = sum(other_calories) / len(other_calories)
    else:
        other_avg = 0

    # 3. 평균 칼로리 비교 그래프
    plot_average_comparison(
        ["당곡고등학교", "비교 학교"],
        [my_avg, other_avg]
    )
