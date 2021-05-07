import pandas as pd
import streamlit as st
import pydeck as pdk

import plotly.express as px

#タイトルを表示
st.title('日本の賃金データダッシュボード')

#pandasで処理したCSVの読み込み
df_jp_ind = pd.read_csv('csv_data/雇用_医療福祉_一人当たり賃金_全国_全産業.csv', encoding='shift_jis')
df_jp_category = pd.read_csv('csv_data/雇用_医療福祉_一人当たり賃金_全国_大分類.csv', encoding='shift_jis')
df_pref_ind = pd.read_csv('csv_data/雇用_医療福祉_一人当たり賃金_都道府県_全産業.csv', encoding='shift_jis')

#ヘッダーの表示
st.header('■2019年：一人当たり平均賃金のヒートマップ')

#都道府県の緯度経度の読み込み、上の３つのDFと結合させるためカラムのリネイム
jp_lat_lon = pd.read_csv('pref_lat_lon.csv')
jp_lat_lon = jp_lat_lon.rename(columns={'pref_name': '都道府県名'})

#2019年の年齢計での一人当たり賃金
df_pref_map = df_pref_ind[(df_pref_ind['年齢'] == '年齢計') & (df_pref_ind['集計年'] == 2019)]
#都道府県名をonでキーに２つのファイルを横に結合する
df_pref_map = pd.merge(df_pref_map, jp_lat_lon, on='都道府県名')
#正規化処理：一人当たり賃金を最大値１、最小値０とする正規化処理
df_pref_map['一人当たり賃金（相対値）'] =  ((df_pref_map['一人当たり賃金（万円）']-df_pref_map['一人当たり賃金（万円）'].min())/(df_pref_map['一人当たり賃金（万円）'].max()-df_pref_map['一人当たり賃金（万円）'].min()))

#pydeckを用いて、正規化した数値を、地図上にヒートマップとして描画する
#中心の場所、東京を設定
view = pdk.ViewState(
    longitude=139.691648,
    latitude=35.689185,
    zoom=4,
    pitch=40.5,
)

#ヒートマップレイヤーを指定
layer = pdk.Layer(
    "HeatmapLayer",
    data=df_pref_map,
    #ヒートマップの不透明度
    opacity=0.4,
    get_position=["lon", "lat"],
    #ヒートマップの閾値
    threshold=0.3,
    #描画する列の指定
    get_weight = '一人当たり賃金（相対値）'
)

#レンダリングの設定
layer_map = pdk.Deck(
    layers=layer,
    initial_view_state=view,
)

#pydeckの呼び出し
st.pydeck_chart(layer_map)

#チャックボックスの有無でDFを表示させる
show_df = st.checkbox('Show DataFrame')
if show_df == True:
    st.write(df_pref_map)

#ヘッダーの表示
st.header('■集計年別の一人当たり賃金（万円）の推移')

# 全国の一人当たり賃金のDF
df_ts_mean = df_jp_ind[(df_jp_ind["年齢"] == "年齢計")]
#列名の変更（他のデータの被るため変更）
df_ts_mean = df_ts_mean.rename(columns={'一人当たり賃金（万円）': '全国_一人当たり賃金（万円）'})

# 都道府県別の一人当たり賃金DF
df_pref_mean = df_pref_ind[(df_pref_ind["年齢"] == "年齢計")]
# 都道府県名の抽出
pref_list = df_pref_mean['都道府県名'].unique()

# セレクトボックスの作成
option_pref = st.selectbox(
    '都道府県',
    (pref_list))
    #セレクトボックスで選択された都道府県のデータをDFから抽出
df_pref_mean = df_pref_mean[df_pref_mean['都道府県名'] == option_pref]
# データの結合、キーは集計年による
df_mean_line = pd.merge(df_ts_mean, df_pref_mean, on='集計年')
# このうち、必要な列だけのDFにする
df_mean_line = df_mean_line[['集計年', '全国_一人当たり賃金（万円）', '一人当たり賃金（万円）']]
#Indexの指定（集計年）
df_mean_line = df_mean_line.set_index('集計年')
#折れ線グラフの作図
st.line_chart(df_mean_line)


st.header('■年齢別の全国一人あたり平均賃金（万円）')

#年齢別の一人当たり賃金の推移
df_mean_bubble = df_jp_ind[df_jp_ind['年齢'] != '年齢計']

#バブルチャートの設定
fig = px.scatter(df_mean_bubble,
                x="一人当たり賃金（万円）",
                y="年間賞与その他特別給与額（万円）",
                range_x=[150,700],
                range_y=[0,150],
                #バブルに使う列
                size="所定内給与額（万円）",
                #バブルの最大値を指定（集計期間のうち所定内給与の最大値に近い数字）
	            size_max = 38,
                color="年齢",
                #アニメーションをどの軸でみたいか（年の推移）
                animation_frame="集計年",
                #グループとして見たい引数
                animation_group="年齢")

#バブルチャートの描画
st.plotly_chart(fig)


st.header('■産業別の賃金推移')

#集計年のリストを作成
year_list = df_jp_category["集計年"].unique()
#集計年のセレクトボックス
option_year = st.selectbox(
    '集計年',
    (year_list))

#見たい賃金の種類リストを作成
wage_list = ['一人当たり賃金（万円）', '所定内給与額（万円）', '年間賞与その他特別給与額（万円）']
#賃金のセレクトボックス
option_wage = st.selectbox(
    '賃金の種類',
    (wage_list))

#集計年のセレクトボックスによりDFを作成
df_mean_categ = df_jp_category[(df_jp_category["集計年"] == option_year)]

#選択した数値により最大値にマージン50を作るコード
max_x = df_mean_categ[option_wage].max() + 50

#棒グラフの設定
fig = px.bar(df_mean_categ,#集計年のセレクトボックスで選択されたDF
            #賃金セレクトボックスで選択した値
            x=option_wage,
            y="産業大分類名",
            color="産業大分類名",
            #アニメーション
            animation_frame="年齢",
            #数字のレンジが０～最大値＋50
            range_x=[0,max_x],
            #横棒で表示
            orientation='h',
            width=800,
            height=500)

#棒グラフの描画       
st.plotly_chart(fig)
