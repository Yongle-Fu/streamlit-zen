import streamlit as st
import pandas as pd
import requests
import altair as alt
import hashlib

global bearer_token
bearer_token = ''

def getChannelData(user_token):
    headers = {
        'Authorization': user_token,
        'Content-Type': 'application/json',
    }
    # 获取数据
    data_url = 'https://zen-api.brainco.cn/zen/zen/ops/statistics/channelKeyStaticsData'        
    response = requests.get(data_url, headers=headers)

    # 检查HTTP状态码
    if response.status_code == 200:
        data = response.json()
        st.write('response.json')
        st.json(data, expanded=False)

        # 提取data中的items数据
        data = data['data']
        data_list = []
        # 遍历数据，展开 "items" 列并映射到新的列
        for item in data:
            channel = item['channel']
            items = item['items']
            df_items = pd.DataFrame(items)

            # 获取活跃硬件数的列表
            active_count_list = df_items['activeCount'].tolist()
            active_count_list.reverse()
            # st.write(active_count_list)

            # 计算除去最后一个元素的平均值
            if len(active_count_list) > 1:
                avg_active_count = sum(active_count_list[:-1]) / (len(active_count_list) - 1)
            else:
                avg_active_count = 0

            data_list.append({
                '渠道': channel,
                '平均活跃硬件数': round(avg_active_count, 1),  # 保留一位小数
                '活跃硬件数': df_items['activeCount'].tolist()[::-1],  # 反转活跃硬件数列表
                '硬件激活率': df_items['registerRate'].tolist()[::-1],  # 反转硬件激活率列表
                '活跃硬件用户次月留存率': df_items['nextMonthRetentionRate'].tolist()[::-1],  # 反转留存率列表
                '硬件出货量': df_items['deliveryCount'].tolist()[::-1],  # 反转出货量列表
            })

        # 创建DataFrame
        df = pd.DataFrame(data_list)

        # 根据平均活跃硬件数进行降序排序
        df_sorted = df.sort_values(by='平均活跃硬件数', ascending=False)
        df_sorted.reset_index(inplace=True, drop=True)

        st.write('最后一个月的数据为当前月份，由于当前月份尚未结束，因此最后一个月的数据可能会比过去三个月偏小，平均活跃硬件数取值为过去三个月的平均值')
        # 显示DataFrame
        st.dataframe(
            df_sorted,
            hide_index=False,
            column_config={
                "平均活跃硬件数": st.column_config.NumberColumn("平均活跃硬件数", format="%.1f", width='small'),
                "活跃硬件数": st.column_config.LineChartColumn(
                    "活跃硬件数 (recent months)", width='medium', y_min=0, y_max=500
                ),
                "硬件出货量": st.column_config.LineChartColumn(
                    "硬件出货量 (recent months)"
                ),
                "硬件激活率": st.column_config.LineChartColumn(
                    "硬件激活率 (recent months)", y_min=0, y_max=100
                ),
                "活跃硬件用户次月留存率": st.column_config.LineChartColumn(
                    "活跃硬件用户次月留存率 (recent months)", y_min=0, y_max=100
                ),
            },
        )

        # 默认显示前5个最多activeCount的渠道
        default_channels = df_sorted['渠道'].unique()[:5]
        channels = st.multiselect('## 选择渠道', df_sorted['渠道'].unique(), default=default_channels)

        # 将数据转换为DataFrame
        data_list = []
        for item in data:
            channel = item['channel']
            if channel not in channels: continue
            for month_data in item['items']:
                data_list.append({
                    'channel': channel,
                    'month': month_data['month'],
                    'registerRate': month_data['registerRate'], # 硬件激活率
                    'activeCount': month_data['activeCount'], # 活跃硬件数
                    'nextMonthRetentionRate': month_data['nextMonthRetentionRate'] # 活跃硬件用户次月留存率
                })
        # st.write(data_list)

        # 创建交互式图表
        df = pd.DataFrame(data_list)
        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X("month:O", title="月份"),
                y=alt.Y("activeCount:Q", title="活跃硬件数"),
                color=alt.Color("channel:N", scale=alt.Scale(scheme='set1'), title="渠道"),
            )
            .properties(
                width=800,
                title="月度各的活跃硬件数"
            )
        )
        st.altair_chart(chart, use_container_width=True)

    else:
        st.error(f'HTTP请求失败，状态码：{response.status_code}')

def login():
    global bearer_token
    if len(bearer_token) > 0:
        getChannelData(bearer_token)
        return

    # 添加输入框，用于用户输入用户名
    username = st.text_input("请输入用户名", "15605085209")

    # 添加密码输入框，用于用户输入密码，设置输入类型为密码
    password = st.text_input("请输入密码", type="password")
    # 添加登录按钮
    if st.button("登录"):
        if len(username) == 0:
            st.error("请输入用户名")
        elif len(password) == 0:
            st.error("请输入密码")    
        else:  
            # 将密码字符串编码为字节数组
            bytes = password.encode('utf-8')

            # 计算SHA-256哈希值
            hash = hashlib.sha256(bytes).hexdigest()  

            # 设置请求的URL和数据
            # uacHostDev = 'https://bc.dev.brainco.cn'
            uacHostProd = 'https://bc-api.brainco.cn'
            # ///host url
            # apiTestUrl = 'https://morpheus.dev.brainco.cn';
            # apiProdUrl = 'https://morpheus-api.brainco.cn';
            url = f'{uacHostProd}/uac/auth/login'
            headers = {
                'X-Domain': 'ops',
                'X-Access-type': '1',
                'Content-Type': 'application/json',
            }
            data = {
                'login': username,
                'password': hash,
                'isPasswordClientEncoded': True,
            }

            # 发送POST请求
            response = requests.post(url, headers=headers, json=data)

            # 检查响应
            if response.status_code == 200:
                result_data = response.json()
                if result_data['success'] != True:
                    st.error("登录失败，请重试。")
                    st.json(result_data)
                else:
                    token = result_data['data']['token']
                    bearer_token = f'Bearer {token}'
                    st.success("登录成功！欢迎, " + username)
                    getChannelData(bearer_token)
            else:
                st.error("登录失败，请重试。")
                st.json(response)

def run_channel_views():
    st.set_page_config(page_title="月度各渠道核心指标", page_icon="📊")
    st.markdown("# 月度各渠道核心指标")
    st.sidebar.header("月度各渠道核心指标")
    login()

run_channel_views()