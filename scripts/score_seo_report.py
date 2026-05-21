from __future__ import annotations

from pathlib import Path

import pandas as pd


INPUT_PATH = Path("output/seo_report_full.csv")
OUTPUT_PATH = Path("output/seo_report_scored.csv")


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    for col in ["title", "meta_description", "h1_text", "canonical", "error"]:
        df[col] = df[col].fillna("").astype(str)

    score_rows = [score_row(row) for _, row in df.iterrows()]
    output = pd.concat([df, pd.DataFrame(score_rows)], axis=1)
    output.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(OUTPUT_PATH)
    print(f"rows={len(output)} avg_score={output['seo_score'].mean():.1f}")


def score_row(row: pd.Series) -> dict[str, object]:
    parts: dict[str, int] = {}
    recommendations: list[str] = []

    status_code = number(row["status_code"])
    title_length = number(row["title_length"])
    description_length = number(row["meta_description_length"])
    h1_count = number(row["h1_count"])
    image_count = number(row["image_count"])
    images_missing_alt = number(row["images_missing_alt"])
    internal_links_count = number(row["internal_links_count"])

    if status_code == 200:
        parts["status_score"] = 20
    elif 300 <= status_code < 400:
        parts["status_score"] = 10
        recommendations.append("確認轉址是否必要，避免重要頁面透過多層轉址被搜尋引擎爬取。")
    else:
        parts["status_score"] = 0
        recommendations.append("優先修正非 200 狀態碼頁面，避免搜尋引擎收錄錯誤頁或浪費爬取資源。")

    if title_length == 0:
        parts["title_score"] = 0
        recommendations.append("補上頁面 title，並加入核心關鍵字與品牌名稱。")
    elif 15 <= title_length <= 35:
        parts["title_score"] = 15
    elif 10 <= title_length < 15 or 36 <= title_length <= 45:
        parts["title_score"] = 10
        recommendations.append("調整 title 長度，讓標題更完整且避免搜尋結果截斷。")
    else:
        parts["title_score"] = 5
        recommendations.append("重寫 title，避免過短、過長或主題不明確。")

    if description_length == 0:
        parts["description_score"] = 0
        recommendations.append("補上 meta description，提升搜尋結果摘要品質與點擊率。")
    elif 50 <= description_length <= 160:
        parts["description_score"] = 15
    elif 30 <= description_length < 50 or 161 <= description_length <= 200:
        parts["description_score"] = 10
        recommendations.append("優化 meta description 長度與內容，聚焦頁面賣點。")
    else:
        parts["description_score"] = 5
        recommendations.append("重寫 meta description，避免過短、過長或不具吸引力。")

    if h1_count == 1:
        parts["h1_score"] = 15
    elif h1_count == 0:
        parts["h1_score"] = 0
        recommendations.append("補上唯一且清楚的 H1，讓頁面主題更明確。")
    elif h1_count <= 3:
        parts["h1_score"] = 8
        recommendations.append("檢查多個 H1 是否造成主題分散，建議保留主要標題為 H1。")
    else:
        parts["h1_score"] = 5
        recommendations.append("整理頁面標題層級，避免過多 H1 稀釋頁面主題。")

    if row["canonical"].strip():
        parts["canonical_score"] = 10
    else:
        parts["canonical_score"] = 0
        recommendations.append("補上 canonical，避免重複內容分散 SEO 權重。")

    if image_count == 0:
        parts["image_alt_score"] = 10
    else:
        ratio = images_missing_alt / image_count
        if ratio == 0:
            parts["image_alt_score"] = 10
        elif ratio <= 0.1:
            parts["image_alt_score"] = 8
            recommendations.append("補齊少數缺少 alt 的圖片，強化圖片 SEO 與無障礙體驗。")
        elif ratio <= 0.3:
            parts["image_alt_score"] = 5
            recommendations.append("優先補齊重點圖片 alt，讓搜尋引擎理解圖片內容。")
        else:
            parts["image_alt_score"] = 2
            recommendations.append("大量圖片缺少 alt，建議建立圖片替代文字規則並批次補強。")

    if internal_links_count >= 5:
        parts["internal_links_score"] = 10
    elif internal_links_count >= 1:
        parts["internal_links_score"] = 6
        recommendations.append("增加相關頁面的內部連結，提升內容關聯與爬取效率。")
    else:
        parts["internal_links_score"] = 0
        recommendations.append("補上內部連結，避免頁面成為孤立頁。")

    if row["error"].strip():
        parts["error_score"] = 0
        recommendations.append("排除爬取錯誤，確認頁面可被正常存取。")
    else:
        parts["error_score"] = 5

    total = sum(parts.values())
    if total >= 85:
        grade = "A"
        priority = "低"
    elif total >= 70:
        grade = "B"
        priority = "中"
    elif total >= 50:
        grade = "C"
        priority = "高"
    else:
        grade = "D"
        priority = "緊急"

    return {
        **parts,
        "seo_score": total,
        "seo_grade": grade,
        "fix_priority": priority,
        "recommendations": "；".join(dict.fromkeys(recommendations))
        or "目前基礎 SEO 狀態良好，可進一步檢查關鍵字布局、內容深度與轉換路徑。",
    }


def number(value: object) -> float:
    try:
        if pd.isna(value):
            return 0
        return float(value)
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    main()
