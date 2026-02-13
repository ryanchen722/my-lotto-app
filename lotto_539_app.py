import pandas as pd
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# 【設定區】這部分用來設定網頁的分頁標題和排版方式
st.set_page_config(page_title="今彩 539 大數據分析師", layout="centered")

def calculate_ac_value(nums):
    """
    【功能】計算 AC 值 (算術複雜度)
    原理：計算號碼之間差值的種類，差值越多代表號碼分佈越隨機。
    """
    differences = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            differences.add(abs(nums[i] - nums[j]))
    return len(differences) - (len(nums) - 1)

def count_consecutive_groups(nums):
    """
    【功能】計算連號組數
    例如：[1, 2, 10, 11, 20] 會算出有 2 組連號。
    """
    groups = 0
    i = 0
    while i < len(nums) - 1:
        if nums[i] + 1 == nums[i+1]:
            groups += 1
            while i < len(nums) - 1 and nums[i] + 1 == nums[i+1]:
                i += 1
        else:
            i += 1
    return groups

# 【介面區】顯示網頁大標題
st.title("🍀 今彩 539 精準分析 App")
st.markdown("---")

# 1. 檔案上傳區：讓使用者把 Excel 丟進來
uploaded_file = st.file_uploader("📂 請上傳今彩 539 歷史數據 (lotto_539.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # 使用 pandas 讀取 Excel 檔案
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history_rows = []
        all_nums = []
        history_ac_values = []
        
        # 【數據清理】把 Excel 裡的文字轉成數字清單
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',').replace('?', '')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == 5:
                history_rows.append(nums)      # 儲存每一期的結果
                all_nums.extend(nums)          # 把所有號碼攤平，用來算機率
                history_ac_values.append(calculate_ac_value(nums))
        
        # --- 側邊欄：手動樣本輸入 (趨勢校正) ---
        st.sidebar.header("📝 趨勢校正模式")
        st.sidebar.write("如果你在投注站看到別人的選號總和，可以輸入在這裡。")
        sample_sum = st.sidebar.number_input("輸入現場樣本總和 (若無則維持 0)", min_value=0, value=0)
        
        if sample_sum > 0:
            st.sidebar.success(f"✅ 已啟用趨勢鎖定：{sample_sum-15} ~ {sample_sum+15}")

        # --- 歷史規律展示 ---
        st.subheader("🕵️ 歷史規律掃描 (最近 30 期)")
        
        st.markdown("##### 最近 5 期摘要")
        cols = st.columns(5)
        for i in range(min(5, len(history_rows))):
            current_ac = history_ac_values[i]
            cols[i].metric(
                f"前 {i+1} 期", 
                f"AC: {current_ac}", 
                f"Sum: {sum(history_rows[i])}"
            )
            cols[i].caption(f"{history_rows[i]}")

        # 使用收納盒顯示更多歷史資料
        with st.expander("查看更多歷史數據 (前 6-30 期)"):
            history_data = []
            max_hist = min(30, len(history_rows))
            for i in range(max_hist):
                history_data.append({
                    "期數": f"前 {i+1} 期",
                    "號碼": str(history_rows[i]),
                    "總和": sum(history_rows[i]),
                    "AC值": history_ac_values[i],
                    "連號": f"{count_consecutive_groups(history_rows[i])} 組"
                })
            st.table(pd.DataFrame(history_data))

        if history_ac_values:
            recent_30_ac = history_ac_values[:30]
            avg_ac = sum(recent_30_ac) / len(recent_30_ac)
            
            st.info(f"""
            **📈 數據分析指標 (最近 30 期)：**
            * 歷史平均 AC 值：`{avg_ac:.2f}`
            * 系統建議區間：`AC 值 5 或 6` (隨機性較佳)
            """)

        # --- 核心分析按鈕 ---
        if st.button("🚀 執行大數據校正模擬 (8000次)", use_container_width=True):
            # 計算號碼出現頻率，頻率越高，抽到的機率越大 (權重池)
            f_counts = Counter(all_nums)
            weighted_pool = []
            for n, count in f_counts.items():
                weighted_pool.extend([n] * count)
            
            # 設定模擬要搜尋的總和範圍
            if sample_sum > 0:
                target_min, target_max = sample_sum - 15, sample_sum + 15
            else:
                target_min, target_max = 60, 130 # 預設合理範圍

            last_draw = set(history_rows[0]) if history_rows else set()
            candidates = []
            
            # 開始進行 8000 次電腦隨機模擬
            with st.spinner('正在從數萬種組合中篩選最符合規律的 10 組...'):
                for _ in range(8000):
                    res_set = set()
                    while len(res_set) < 5:
                        res_set.add(random.choice(weighted_pool))
                    
                    res_list = sorted(list(res_set))
                    f_sum = sum(res_list)
                    ac_val = calculate_ac_value(res_list)
                    # 檢查與上一期重複幾個號碼 (通常不超過 2 個)
                    overlap = len(set(res_list).intersection(last_draw))
                    # 檢查是否出現三連號 (如 1, 2, 3，這種機率極低，故過濾掉)
                    has_triple = any(res_list[j]+2 == res_list[j+1]+1 == res_list[j+2] for j in range(len(res_list)-2))

                    # 篩選條件：總和要在範圍內、AC值要夠高、重複號碼不多、沒有三連號
                    if (target_min <= f_sum <= target_max and 
                        ac_val >= 5 and overlap <= 2 and not has_triple):
                        candidates.append((res_list, f_sum, ac_val))
                        if len(candidates) >= 10: break # 存夠 10 組就收工

            # 如果有找到符合條件的組合，隨機從中選一組推薦給使用者
            if candidates:
                rec_f, f_sum, ac_val = random.choice(candidates)

                st.success("✨ 分析完成！推薦組合如下：")
                st.markdown(f"## 推薦號碼：\n`{rec_f}`")

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("預測總和", f_sum)
                col_b.metric("AC 複雜度", ac_val)
                col_c.metric("連號組數", count_consecutive_groups(rec_f))
                
                # 提供下載功能
                result_text = f"539 分析結果\n時間: {datetime.now()}\n號碼: {rec_f}\n總和: {f_sum}\nAC值: {ac_val}"
                st.download_button("📥 下載此組分析結果", result_text, file_name="539_result.txt")
            else:
                st.error("❌ 執行 8000 次模擬後仍找不到組合。建議放寬「現場總和」的範圍再試一次。")

    except Exception as e:
        st.error(f"讀取失敗，請確認檔案格式是否正確： {e}")
else:
    st.info("💡 歡迎使用！請先從上方按鈕上傳您的 Excel 歷史資料表。")

st.markdown("---")
st.caption("⚠️ 本工具僅供數據研究與統計分析參考，投注請量力而為。")
