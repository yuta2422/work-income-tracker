import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, date
import calendar
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib

# === ページ設定 ===
st.set_page_config(layout="wide")
st.title("🗓️ バイト収支＆扶養チェッカー")

CSV_FILE = "work_records.csv"

# === 日本語フォント設定 ===
jp_font_path = fm.findSystemFonts(fontpaths=None, fontext="ttf")
jp_fonts = [f for f in jp_font_path if "msgothic" in f.lower() or "meiryo" in f.lower()]
if jp_fonts:
    matplotlib.rcParams["font.family"] = jp_fonts[0]
else:
    st.warning(
        "日本語フォントが見つからない場合、カレンダーの文字化けが起こることがあります。"
    )


# === 5分刻みの時間リスト ===
def generate_time_options():
    times = []
    current = datetime.strptime("00:00", "%H:%M")
    end = datetime.strptime("23:55", "%H:%M") + timedelta(minutes=1)
    while current < end:
        times.append(current.strftime("%H:%M"))
        current += timedelta(minutes=5)
    return times


time_options = generate_time_options()

# === 勤務データ入力 ===
st.header("勤務データ入力（深夜勤務OK）")

start_date = st.date_input("開始日", value=date.today())
start_time = st.selectbox("開始時刻", time_options, index=time_options.index("22:00"))

end_date = st.date_input("終了日", value=date.today())
end_time = st.selectbox("終了時刻", time_options, index=time_options.index("06:00"))

break_minutes = st.number_input(
    "休憩時間（分）", min_value=0, max_value=300, value=60, step=5
)
wage = st.number_input("時給（円）", min_value=0, value=1000, step=10)
transport = st.number_input("交通費（円）", min_value=0, value=0, step=10)

# === 記録ボタン処理 ===
if st.button("勤務を記録する"):
    start_dt = datetime.combine(
        start_date, datetime.strptime(start_time, "%H:%M").time()
    )
    end_dt = datetime.combine(end_date, datetime.strptime(end_time, "%H:%M").time())
    total_duration = (end_dt - start_dt).total_seconds() / 3600
    work_duration = total_duration - break_minutes / 60

    if work_duration <= 0:
        st.error("⚠️ 休憩が長すぎるか、終了日時が開始日時より前です。")
    else:
        income = work_duration * wage + transport
        st.success(f"{start_date} の勤務を記録しました。")
        st.write(f"勤務時間（休憩除く）: {work_duration:.2f} 時間")
        st.write(f"収入: ¥{income:.0f}（交通費込み）")

        record = pd.DataFrame(
            [
                {
                    "勤務日": start_dt.strftime("%Y-%m-%d"),
                    "開始": start_dt.strftime("%Y-%m-%d %H:%M"),
                    "終了": end_dt.strftime("%Y-%m-%d %H:%M"),
                    "休憩（分）": break_minutes,
                    "勤務時間": round(work_duration, 2),
                    "時給": wage,
                    "交通費": transport,
                    "収入": round(income),
                }
            ]
        )

        try:
            existing = pd.read_csv(CSV_FILE)
            updated = pd.concat([existing, record], ignore_index=True)
        except FileNotFoundError:
            updated = record

        updated.to_csv(CSV_FILE, index=False)

# === カレンダー表示 ===
st.header("📅 カレンダー表示")


def draw_calendar(data, year, month):
    cal = calendar.Calendar(firstweekday=6)  # 日曜始まり
    month_days = cal.monthdatescalendar(year, month)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_axis_off()
    table_data = []

    for week in month_days:
        row = []
        for day in week:
            if day.month != month:
                row.append("")
            else:
                match = data[data["勤務日"] == pd.to_datetime(day)]
                if not match.empty:
                    income = match["収入"].sum()
                    row.append(f"{day.day}\n¥{int(income)}")
                else:
                    row.append(str(day.day))
        table_data.append(row)

    table = ax.table(
        cellText=table_data,
        colLabels=["日", "月", "火", "水", "木", "金", "土"],
        cellLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.8)
    plt.title(f"{year}年 {month}月", fontsize=18)
    st.pyplot(fig)


# === カレンダーを表示するボタン ===
if st.button("カレンダーを表示"):
    try:
        df = pd.read_csv(CSV_FILE)
        df["勤務日"] = pd.to_datetime(df["勤務日"])
        today = date.today()
        draw_calendar(df, today.year, today.month)

        total_income = df["収入"].sum()
        total_hours = df["勤務時間"].sum()
        st.subheader("🧾 累計")
        st.write(f"💰 総収入: ¥{int(total_income)}")
        st.write(f"🕒 総勤務時間: {total_hours:.2f} 時間")

    except FileNotFoundError:
        st.warning("まだ勤務記録がありません。")
    except Exception as e:
        st.error(f"エラー: {e}")
