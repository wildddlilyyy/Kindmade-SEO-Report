# Python SEO 爬蟲

這是一個第一版 SEO 爬蟲工具，預設從 `https://kindmade.com.tw/` 開始，最多爬取同網域內 100 個頁面，並輸出 CSV 報表。

## 功能

- 只爬取同網域頁面
- 避免重複爬取相同 URL
- 跳過常見非 HTML 檔案，例如圖片、PDF、CSS、JS、ZIP
- 擷取 HTTP status code、title、meta description、H1、canonical、圖片 alt 狀態
- 輸出 UTF-8 BOM CSV，方便用 Excel 開啟中文內容
- 單頁失敗不會中斷整體爬取，錯誤會寫入報表的 `error` 欄位

## 環境需求

建議使用 Python 3.11 或更新版本。

## 安裝

在專案資料夾中建立虛擬環境：

```bash
python -m venv .venv
```

啟用虛擬環境：

```bash
.venv\Scripts\activate
```

安裝依賴：

```bash
pip install -r requirements.txt
```

## 執行

使用預設設定爬取 `https://kindmade.com.tw/`，最多 100 頁，輸出到 `output/seo_report.csv`：

```bash
python -m seo_crawler.main
```

指定網址、頁數與輸出路徑：

```bash
python -m seo_crawler.main --url https://kindmade.com.tw/ --max-pages 100 --output output/seo_report.csv
```

小量測試：

```bash
python -m seo_crawler.main --url https://kindmade.com.tw/ --max-pages 5 --output output/seo_report.csv
```

## CSV 欄位

| 欄位 | 說明 |
| --- | --- |
| `url` | 實際分析的頁面 URL |
| `status_code` | HTTP 狀態碼 |
| `title` | 頁面 title |
| `title_length` | title 字元數 |
| `meta_description` | meta description 內容 |
| `meta_description_length` | meta description 字元數 |
| `h1_count` | H1 數量 |
| `h1_text` | H1 文字，多個 H1 以 `\|` 分隔 |
| `canonical` | canonical URL |
| `image_count` | 圖片數量 |
| `images_missing_alt` | 缺少 alt 或 alt 為空的圖片數量 |
| `images_missing_alt_ratio` | 缺少 alt 的圖片比例 |
| `internal_links_count` | 頁面內部連結數 |
| `external_links_count` | 頁面外部連結數 |
| `error` | 抓取或解析錯誤訊息 |

## 禮貌爬取提醒

請只爬取你有權分析的網站，並避免設定過高的爬取頁數或過短的請求間隔。若網站有 `robots.txt` 或其他爬取政策，請依照網站規範調整使用方式。

