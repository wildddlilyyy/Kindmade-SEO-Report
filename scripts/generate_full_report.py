from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


BASE = Path("output")
SCORED_CSV = BASE / "seo_report_scored.csv"
REPORT_MD = BASE / "seo_full_audit_report.md"
REPORT_HTML = BASE / "seo_full_audit_report.html"
REPORT_DATE = "2026-05-21"


def main() -> None:
    df = pd.read_csv(SCORED_CSV)
    prepare_dataframe(df)

    avg_score = df["seo_score"].mean()
    grade_counts = df["seo_grade"].value_counts().reindex(["A", "B", "C", "D"], fill_value=0)
    status_counts = df["status_code"].astype(int).value_counts().sort_index()
    issue_counts = build_issue_counts(df)
    priority_pages = build_priority_pages(df)

    field_rows = build_field_rows()
    score_rows = build_score_rows()
    page_rows = build_page_rows(df)
    priority_rows = build_priority_rows(priority_pages)

    REPORT_MD.write_text(
        build_markdown_report(
            df=df,
            avg_score=avg_score,
            grade_counts=grade_counts,
            status_counts=status_counts,
            issue_counts=issue_counts,
            field_rows=field_rows,
            score_rows=score_rows,
            page_rows=page_rows,
            priority_rows=priority_rows,
        ),
        encoding="utf-8",
    )
    REPORT_HTML.write_text(
        build_html_report(
            df=df,
            avg_score=avg_score,
            grade_counts=grade_counts,
            status_counts=status_counts,
            issue_counts=issue_counts,
            field_rows=field_rows,
            score_rows=score_rows,
            page_rows=page_rows,
            priority_rows=priority_rows,
        ),
        encoding="utf-8",
    )

    print(REPORT_MD)
    print(REPORT_HTML)
    print(f"rows={len(df)} avg_score={avg_score:.1f}")
    print(f"A={grade_counts['A']} B={grade_counts['B']} C={grade_counts['C']} D={grade_counts['D']}")


def prepare_dataframe(df: pd.DataFrame) -> None:
    text_cols = [
        "url",
        "title",
        "meta_description",
        "h1_text",
        "canonical",
        "error",
        "recommendations",
        "seo_grade",
        "fix_priority",
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    numeric_cols = [
        "status_code",
        "title_length",
        "meta_description_length",
        "h1_count",
        "image_count",
        "images_missing_alt",
        "images_missing_alt_ratio",
        "internal_links_count",
        "external_links_count",
        "seo_score",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


def build_issue_counts(df: pd.DataFrame) -> dict[str, int]:
    return {
        "非 200 狀態頁": int((df["status_code"] != 200).sum()),
        "缺少 title": int(df["title"].eq("").sum()),
        "Title 過短或過長": int(((df["title_length"] > 0) & ~df["title_length"].between(15, 35)).sum()),
        "缺少 meta description": int(df["meta_description"].eq("").sum()),
        "Meta description 過短或過長": int(
            ((df["meta_description_length"] > 0) & ~df["meta_description_length"].between(50, 160)).sum()
        ),
        "缺少 H1": int((df["h1_count"] == 0).sum()),
        "多個 H1": int((df["h1_count"] > 1).sum()),
        "缺少 canonical": int(df["canonical"].eq("").sum()),
        "圖片缺少 alt 總數": int(df["images_missing_alt"].sum()),
        "爬取錯誤頁": int(df["error"].str.len().gt(0).sum()),
    }


def build_priority_pages(df: pd.DataFrame) -> pd.DataFrame:
    priority_order = {"緊急": 0, "高": 1, "中": 2, "低": 3}
    sortable = df.copy()
    sortable["_priority_order"] = sortable["fix_priority"].map(priority_order).fillna(9)
    return sortable.sort_values(
        ["_priority_order", "seo_score", "images_missing_alt"],
        ascending=[True, True, False],
    ).head(20)


def build_field_rows() -> list[tuple[str, str, str]]:
    return [
        ("url", "頁面網址", "被爬蟲實際檢查的網址，用來定位每一頁的 SEO 狀態。"),
        ("status_code", "HTTP 狀態碼", "判斷頁面是否可正常存取，200 正常，404 代表找不到頁面。"),
        ("title / title_length", "頁面標題與長度", "搜尋結果標題的重要來源，應清楚、獨特並包含核心關鍵字。"),
        ("meta_description / meta_description_length", "頁面描述與長度", "搜尋結果摘要的重要來源，影響使用者點擊意願。"),
        ("h1_count / h1_text", "H1 數量與文字", "判斷頁面主題是否明確，通常建議一頁有一個主要 H1。"),
        ("canonical", "標準網址", "協助搜尋引擎辨識主要 URL，避免重複內容分散權重。"),
        ("image_count / images_missing_alt", "圖片數與缺 alt 數", "圖片 alt 有助圖片 SEO、無障礙與搜尋引擎理解圖片內容。"),
        ("internal_links_count", "內部連結數", "衡量頁面與站內其他頁面的關聯，有助爬取與權重傳遞。"),
        ("external_links_count", "外部連結數", "衡量頁面連到外部網站的數量，需注意品質與必要性。"),
        ("seo_score / seo_grade", "SEO 分數與等級", "依技術與內容基礎項目換算出的 100 分制與 A-D 等級。"),
        ("fix_priority", "修改優先級", "依分數與問題嚴重度標示低、中、高或緊急。"),
        ("recommendations", "頁面建議", "針對該頁目前偵測到的問題給出的修改方向。"),
    ]


def build_score_rows() -> list[tuple[str, str, str]]:
    return [
        ("HTTP 狀態碼", "20", "200 滿分；轉址部分扣分；404/500 為 0 分。"),
        ("Title", "15", "檢查是否存在，以及長度是否適合搜尋結果呈現。"),
        ("Meta description", "15", "檢查是否存在，以及是否有足夠資訊吸引用戶點擊。"),
        ("H1", "15", "檢查是否有唯一且清楚的頁面主標題。"),
        ("Canonical", "10", "檢查是否有標準網址設定，避免重複內容問題。"),
        ("圖片 alt", "10", "依缺少 alt 的圖片比例扣分。"),
        ("內部連結", "10", "檢查頁面是否有足夠站內連結支援爬取與權重流動。"),
        ("爬取錯誤", "5", "確認頁面是否能被正常抓取與分析。"),
    ]


def build_priority_rows(priority_pages: pd.DataFrame) -> list[tuple[object, ...]]:
    return [
        (
            link(row["url"]),
            int(row["seo_score"]),
            row["seo_grade"],
            row["fix_priority"],
            format_recommendations(row["recommendations"]),
        )
        for _, row in priority_pages.iterrows()
    ]


def build_page_rows(df: pd.DataFrame) -> list[tuple[object, ...]]:
    rows = []
    for idx, row in df.iterrows():
        rows.append(
            (
                idx + 1,
                link(row["url"]),
                int(row["status_code"]),
                int(row["seo_score"]),
                row["seo_grade"],
                row["fix_priority"],
                row["title"],
                int(row["title_length"]),
                row["meta_description"],
                int(row["meta_description_length"]),
                int(row["h1_count"]),
                row["h1_text"],
                link(row["canonical"]),
                int(row["image_count"]),
                int(row["images_missing_alt"]),
                row["images_missing_alt_ratio"],
                int(row["internal_links_count"]),
                int(row["external_links_count"]),
                format_recommendations(row["recommendations"]),
                row["error"],
            )
        )
    return rows


def build_markdown_report(
    *,
    df: pd.DataFrame,
    avg_score: float,
    grade_counts: pd.Series,
    status_counts: pd.Series,
    issue_counts: dict[str, int],
    field_rows: list[tuple[str, str, str]],
    score_rows: list[tuple[str, str, str]],
    page_rows: list[tuple[object, ...]],
    priority_rows: list[tuple[object, ...]],
) -> str:
    return f"""# Kindmade SEO 完整稽核報告

資料來源：`output/seo_report_scored.csv`  
分析網站：<https://kindmade.com.tw/>  
SEO 報告日期：{REPORT_DATE}  
分析範圍：同網域前 {len(df)} 頁

## 1. 整體健康狀態

- 平均 SEO 分數：{avg_score:.1f} / 100
- A 級頁面：{grade_counts["A"]} 頁
- B 級頁面：{grade_counts["B"]} 頁
- C 級頁面：{grade_counts["C"]} 頁
- D 級頁面：{grade_counts["D"]} 頁
- 主要判讀：本報告協助業主快速掌握每個頁面的 SEO 現況，包含分數、問題位置與建議處理方向，作為後續排程修正與成效追蹤的依據。

## 2. HTTP 狀態碼分布

{md_table(["狀態碼", "頁數"], [(int(k), int(v)) for k, v in status_counts.items()])}

## 3. 問題統計

{md_table(["問題類型", "數量"], issue_counts.items())}

## 4. 評分方式

總分 100 分，分數越高代表基礎 SEO 狀態越完整。

{md_table(["評分項目", "配分", "判斷方式"], score_rows)}

## 5. CSV 欄位說明

{md_table(["欄位", "中文名稱", "SEO 意涵"], field_rows)}

## 6. 優先處理頁面 Top 20

以下頁面依修改優先級、SEO 分數與圖片 alt 缺漏排序，建議優先處理。

{md_table(["URL", "分數", "等級", "優先級", "建議修改方向"], priority_rows)}

## 7. 每頁完整 SEO 爬蟲內容

{md_table([
    "#", "URL", "狀態碼", "分數", "等級", "優先級", "Title", "Title 長度",
    "Meta Description", "Description 長度", "H1 數量", "H1 文字", "Canonical",
    "圖片數", "缺 alt 圖片數", "缺 alt 比例", "內部連結", "外部連結", "建議修改方向", "錯誤"
], page_rows)}

## 8. 建議執行順序

1. 修正非 200 頁面，尤其是 404，確認要恢復頁面、建立 301 轉址，或移除站內錯誤連結。
2. 補齊缺少 meta description 的頁面，讓搜尋結果摘要更完整且更有點擊吸引力。
3. 補上缺少 H1 與 canonical 的頁面，穩定頁面主題與標準網址訊號。
4. 批次補齊圖片 alt，先處理首頁、產品頁、服務頁與高流量頁面。
5. 檢查低分頁面的內部連結，建立更清楚的主題關聯與導流路徑。
6. 完成基礎修正後，再進一步做關鍵字布局、內容深度與搜尋意圖優化。
"""


def md_table(headers: list[str], rows) -> str:
    output = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        escaped = [md_cell(cell) for cell in row]
        output.append("| " + " | ".join(escaped) + " |")
    return "\n".join(output)


def md_cell(value: object) -> str:
    if isinstance(value, Link):
        return f"[{value.text}]({value.href})"
    if isinstance(value, list):
        return "<br>".join(f"- {str(item).replace('|', '\\|')}" for item in value)
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def build_html_report(
    *,
    df: pd.DataFrame,
    avg_score: float,
    grade_counts: pd.Series,
    status_counts: pd.Series,
    issue_counts: dict[str, int],
    field_rows: list[tuple[str, str, str]],
    score_rows: list[tuple[str, str, str]],
    page_rows: list[tuple[object, ...]],
    priority_rows: list[tuple[object, ...]],
) -> str:
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kindmade SEO 完整稽核報告</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC", Arial, sans-serif; margin: 0; color: #1f2933; background: #f6f7f9; }}
header {{ background: #173f35; color: white; padding: 36px 48px; }}
main {{ padding: 28px 48px 56px; }}
h1 {{ margin: 0 0 8px; font-size: 32px; }}
h2 {{ margin-top: 34px; color: #173f35; }}
.summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin: 22px 0; }}
.card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; }}
.label {{ color: #64748b; font-size: 13px; }}
.value {{ font-size: 28px; font-weight: 700; margin-top: 6px; }}
.table-wrap {{ overflow: auto; max-height: 720px; border: 1px solid #d9e2ec; border-radius: 8px; background: white; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; table-layout: auto; }}
th, td {{ border-bottom: 1px solid #e5e7eb; padding: 10px 12px; text-align: left; vertical-align: top; line-height: 1.55; max-width: 360px; white-space: normal; overflow-wrap: anywhere; }}
th {{ position: sticky; top: 0; background: #eef5f1; color: #173f35; z-index: 1; }}
tr:hover td {{ background: #fafafa; }}
.note {{ background: #fff; border-left: 4px solid #2f7d5f; padding: 14px 16px; margin: 16px 0; }}
.url-cell {{ min-width: 260px; max-width: 420px; }}
.title-cell {{ min-width: 220px; max-width: 360px; }}
.desc-cell {{ min-width: 280px; max-width: 460px; }}
.recommendation-cell {{ min-width: 300px; max-width: 480px; }}
.recommendation-cell ul {{ margin: 0; padding-left: 18px; }}
a {{ color: #116149; text-decoration: underline; text-underline-offset: 2px; }}
</style>
</head>
<body>
<header>
<h1>Kindmade SEO 完整稽核報告</h1>
<div>分析網站：https://kindmade.com.tw/｜SEO 報告日期：{REPORT_DATE}｜分析範圍：同網域前 {len(df)} 頁</div>
</header>
<main>
<section class="summary-grid">
<div class="card"><div class="label">平均 SEO 分數</div><div class="value">{avg_score:.1f}</div></div>
<div class="card"><div class="label">A 級頁面</div><div class="value">{grade_counts["A"]}</div></div>
<div class="card"><div class="label">B 級頁面</div><div class="value">{grade_counts["B"]}</div></div>
<div class="card"><div class="label">D 級頁面</div><div class="value">{grade_counts["D"]}</div></div>
<div class="card"><div class="label">缺少 Description</div><div class="value">{issue_counts["缺少 meta description"]}</div></div>
<div class="card"><div class="label">缺 alt 圖片</div><div class="value">{issue_counts["圖片缺少 alt 總數"]}</div></div>
</section>
<div class="note">本報告將每個被檢查頁面的 SEO 狀態、分數、問題與建議處理方向完整整理，方便業主掌握目前網站健康度，並作為後續修正排程與驗收追蹤的依據。</div>
<h2>HTTP 狀態碼分布</h2>
{html_table(["狀態碼", "頁數"], [(int(k), int(v)) for k, v in status_counts.items()])}
<h2>問題統計</h2>
{html_table(["問題類型", "數量"], issue_counts.items())}
<h2>評分方式</h2>
{html_table(["評分項目", "配分", "判斷方式"], score_rows)}
<h2>CSV 欄位說明</h2>
{html_table(["欄位", "中文名稱", "SEO 意涵"], field_rows)}
<h2>優先處理頁面 Top 20</h2>
{html_table(["URL", "分數", "等級", "優先級", "建議修改方向"], priority_rows)}
<h2>每頁完整 SEO 爬蟲內容</h2>
{html_table([
    "#", "URL", "狀態碼", "分數", "等級", "優先級", "Title", "Title 長度",
    "Meta Description", "Description 長度", "H1 數量", "H1 文字", "Canonical",
    "圖片數", "缺 alt 圖片數", "缺 alt 比例", "內部連結", "外部連結", "建議修改方向", "錯誤"
], page_rows)}
<h2>建議執行順序</h2>
<ol>
<li>修正非 200 頁面，尤其是 404，確認要恢復頁面、建立 301 轉址，或移除站內錯誤連結。</li>
<li>補齊缺少 meta description 的頁面，讓搜尋結果摘要更完整且更有點擊吸引力。</li>
<li>補上缺少 H1 與 canonical 的頁面，穩定頁面主題與標準網址訊號。</li>
<li>批次補齊圖片 alt，先處理首頁、產品頁、服務頁與高流量頁面。</li>
<li>檢查低分頁面的內部連結，建立更清楚的主題關聯與導流路徑。</li>
<li>完成基礎修正後，再進一步做關鍵字布局、內容深度與搜尋意圖優化。</li>
</ol>
</main>
</body>
</html>"""


def html_table(headers: list[str], rows) -> str:
    head = "".join(f"<th>{html.escape(str(header))}</th>" for header in headers)
    body_rows = []
    for row in rows:
        cells = "".join(html_cell(header, cell) for header, cell in zip(headers, row))
        body_rows.append(f"<tr>{cells}</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


class Link:
    def __init__(self, href: str, text: str | None = None) -> None:
        self.href = href
        self.text = text or href


def link(url: str) -> Link | str:
    if url.startswith(("http://", "https://")):
        return Link(url)
    return url


def format_recommendations(value: str) -> list[str]:
    parts = [part.strip() for part in str(value).split("；") if part.strip()]
    return parts or [str(value)]


def html_cell(header: str, value: object) -> str:
    classes = []
    if header.upper() == "URL" or header == "Canonical":
        classes.append("url-cell")
    if header == "Title":
        classes.append("title-cell")
    if header == "Meta Description":
        classes.append("desc-cell")
    if header == "建議修改方向":
        classes.append("recommendation-cell")

    class_attr = f' class="{" ".join(classes)}"' if classes else ""

    if isinstance(value, Link):
        safe_href = html.escape(value.href, quote=True)
        safe_text = html.escape(value.text)
        return f'<td{class_attr}><a href="{safe_href}" target="_blank" rel="noopener noreferrer">{safe_text}</a></td>'

    if isinstance(value, list):
        items = "".join(f"<li>{html.escape(str(item))}</li>" for item in value)
        return f"<td{class_attr}><ul>{items}</ul></td>"

    return f"<td{class_attr}>{html.escape(str(value))}</td>"


if __name__ == "__main__":
    main()
