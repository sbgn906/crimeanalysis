import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 지역별 범죄 통계 시각화 대시보드 (Plotly 기반)")

# -----------------------
# 데이터 로딩 및 전처리
# -----------------------
@st.cache_data
def load_data():
    df = pd.read_csv("경찰청_범죄 발생 지역별 통계_20231231.csv", encoding='cp949')
    df = df.melt(id_vars=['범죄대분류', '범죄중분류'], var_name='지역', value_name='발생건수')
    df = df.dropna(subset=['발생건수'])
    df['발생건수'] = pd.to_numeric(df['발생건수'], errors='coerce').fillna(0).astype(int)

    def extract_do(region):
        for prefix in ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
                       "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
            if region.startswith(prefix):
                return prefix
        return "기타"
    
    df['도'] = df['지역'].apply(extract_do)
    return df

df = load_data()

# -----------------------
# 사이드바 필터
# -----------------------
with st.sidebar:
    st.header("🔍 필터")

    selected_main = st.selectbox("대분류 선택", sorted(df['범죄대분류'].unique()))

    all_do = ['전체'] + sorted(df['도'].unique())
    selected_do = st.selectbox("광역단체(도/광역시) 선택", all_do)

    if selected_do == '전체':
        subregions = sorted(df['지역'].unique())
    else:
        subregions = sorted(df[df['도'] == selected_do]['지역'].unique())
    
    selected_subregions = st.multiselect("세부 지역 선택", subregions, default=subregions)

# -----------------------
# 필터 적용
# -----------------------
filtered_df = df[
    (df['범죄대분류'] == selected_main) &
    (df['지역'].isin(selected_subregions))
]

# -----------------------
# 중분류별 막대 그래프
# -----------------------
middle_summary = filtered_df.groupby('범죄중분류')['발생건수'].sum().sort_values(ascending=False)

st.subheader(f"✅ '{selected_main}' 대분류 내 중분류별 발생 건수")

if middle_summary.empty:
    st.warning("해당 대분류에 대한 중분류 데이터가 선택한 지역에서 존재하지 않습니다.")
elif len(middle_summary) == 1:
    label = middle_summary.index[0]
    value = middle_summary.iloc[0]
    st.info(f"🔹 중분류: **{label}** / 발생건수: **{value:,}건**")
else:
    fig = px.bar(
        middle_summary.reset_index(),
        x='발생건수',
        y='범죄중분류',
        orientation='h',
        color='범죄중분류',
        title=f"{selected_main} 중분류별 발생건수",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

# -----------------------
# 지역별 원형 차트
# -----------------------
st.subheader("📍 선택한 지역의 발생 비율 (원형 차트)")

if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 지역 데이터가 없습니다.")
else:
    if selected_do == '전체' or len(set(filtered_df['도'])) > 1:
        # 전체 선택 또는 복수 도 선택 → 도 기준 원형 차트
        region_summary = filtered_df.groupby('도')['발생건수'].sum().reset_index()
        pie_title = f"{selected_main} 도별 발생 비율"
        name_col = '도'
    else:
        # 하나의 도 선택 → 지역 기준 원형 차트
        region_summary = filtered_df.groupby('지역')['발생건수'].sum().reset_index()
        pie_title = f"{selected_main} 지역(시/군/구)별 발생 비율"
        name_col = '지역'

    # 상위 10개 + 기타 처리
    region_summary = region_summary.sort_values('발생건수', ascending=False).reset_index(drop=True)
    top_n = 10
    if len(region_summary) > top_n:
        top_regions = region_summary.iloc[:top_n]
        other_regions = region_summary.iloc[top_n:]
        other_sum = other_regions['발생건수'].sum()
        
        # top_regions + 기타 row 추가
        pie_data = pd.concat([
            top_regions,
            pd.DataFrame({name_col: ['기타'], '발생건수': [other_sum]})
        ], ignore_index=True)
    else:
        pie_data = region_summary.copy()

    # 원형 차트
    pie_fig = px.pie(
        pie_data,
        values='발생건수',
        names=name_col,
        title=pie_title,
        height=500
    )
    st.plotly_chart(pie_fig, use_container_width=True)

    # 기타 항목 클릭 시 표 출력
    if '기타' in pie_data[name_col].values and len(region_summary) > top_n:
        with st.expander("📋 기타 항목 세부 정보 보기"):
            st.write(other_regions.rename(columns={name_col: '지역명'}).reset_index(drop=True))
