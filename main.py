import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 지역별 범죄 통계 시각화 대시부드 (Plotly 기반)")

# -----------------------
# 데이터 로드 및 전처리
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
            if str(region).startswith(prefix):
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
        region_summary = filtered_df.groupby('도')['발생건수'].sum().reset_index()
        region_summary = region_summary.sort_values('발생건수', ascending=False)
        region_summary['label'] = region_summary['도']
    else:
        region_summary = filtered_df.groupby('지역')['발생건수'].sum().reset_index()
        region_summary = region_summary.sort_values('발생건수', ascending=False)
        region_summary['label'] = region_summary['지역']

    threshold = 5
    top_regions = region_summary.head(threshold)
    others_sum = region_summary['발생건수'].iloc[threshold:].sum()

    if others_sum > 0:
        top_regions = pd.concat([
            top_regions,
            pd.DataFrame([{
                'label': '기타',
                '발생건수': others_sum
            }])
        ])

    pie_fig = px.pie(
        top_regions,
        values='발생건수',
        names='label',
        title=f"{selected_main} {'도별' if selected_do == '전체' else '지역별'} 발생 비율 (상위 {threshold} + 기타)",
        height=500
    )
    st.plotly_chart(pie_fig, use_container_width=True)
