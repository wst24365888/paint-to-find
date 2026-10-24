# 畫圖找股 (paint-to-find)

在網頁畫布上一筆畫出想要的走勢，找出最近一段期間走勢最相似的台股（上市＋上櫃）。

- 資料：FinLab `etl:adj_close`（調整後收盤價，避免除權息缺口影響形狀），保留最近 250 個交易日
- 比對：把畫的線依 x 軸重採樣成 N 點，與每檔股票最近 N 日收盤價做 z-score 標準化後計算 Pearson 相關係數，≥ 門檻即列出
- 純靜態網頁，所有比對在瀏覽器端完成，可直接部署在 GitHub Pages

## 結構

```
update_data.py                 從 FinLab 抓股價 → site/data/prices.json（比對用收盤價）
                               + site/data/ohlc/<id>.json（顯示用 K 棒）
site/index.html                畫布 + 比對邏輯 + Lightweight Charts K 棒（單一檔案，無建置步驟）
.github/workflows/deploy.yml   每個交易日 18:30（台灣時間）抓資料並部署 Pages
```

## 本機執行

```bash
uv run python update_data.py
```

```bash
python -m http.server 8000 -d site
```

然後打開 http://localhost:8000 。第一次執行若尚未登入，FinLab 會開瀏覽器登入（憑證存在 `~/.finlab/credentials.json`）。

## 部署到 GitHub Pages

FinLab 已棄用 `FINLAB_API_TOKEN`（2026/08/01 後移除），無瀏覽器環境改用三個環境變數。

1. 推上 GitHub。
2. 在本機（已登入 FinLab 的電腦）取得憑證：

   ```bash
   uv run python -m finlab token
   ```

   會印出 `FINLAB_REFRESH_TOKEN`、`FINLAB_SESSION_ID`、`FINLAB_API_KEY` 三行。
3. Repo → Settings → Secrets and variables → Actions，把這三個分別新增為 repository secret（名稱同上）。
4. Repo → Settings → Pages → Source 選 **GitHub Actions**。
5. 到 Actions 手動執行一次 “Update prices & deploy”，之後每個交易日自動更新。

股價 JSON 不進版控，每次部署都在 Actions 裡重新抓，repo 不會因每日資料膨脹。
