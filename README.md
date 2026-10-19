# 成語圖譜・縱橫解字

繁體中文成語縱橫解謎遊戲。棋盤在部署建置時預先產生，不在玩家開始遊戲時重新隨機排列。

## 已實作的功能

- 21 關：第 1 關 10 個成語，逐關增加，至第 21 關 30 個，合計 420 個不同詞目。
- 建置腳本產生靜態棋盤，檢查詞目重複、交叉字元一致及每關連通性。
- 每關最多一半成語初始揭示一字；答對成語後，揭示相交未完成成語的提示字。
- 候選字以獨立字磚列在主遊戲畫面，依筆畫數由少至多排列；字磚顯示筆畫數作參考，筆畫數相同時以 Unicode 碼位作穩定排序。字磚間有明顯間距；按住後拖曳至棋盤格，拖動預覽會放大並顯示在手指上方。
- 在棋盤上雙擊自己放入的字，可將字退回候選字區；提示字不能退回，已完成成語的相交格會依完成狀態保護。
- 拖曳時以放大字磚的可視中心作為落點判斷，不再只使用手指座標；放開時會優先吸附到附近、字元相符的空格，以容忍手指及預覽位置差異。
- 不使用中文文字輸入框；放錯字可選取格子並清除，候選字會回到字磚清單。
- 檢查本詞、提示一字、重玩本關、自由選關。
- 本機保存答案、完成狀態與計時；支援 JSON 匯出／匯入。資料不會自動跨裝置同步。
- 完成關卡後顯示用時，三秒後自動前往下一關，亦可選擇留在本關。
- 適配桌面及手機版面；窄螢幕時主遊戲／關卡面板可以左右滑動，桌面可拖動空白面板區水平移動。頂部狀態列壓縮為兩行；「本關成語」清單隱藏以增加遊戲空間。拖曳使用 Pointer Events，候選字磚設有觸控防誤選區域。

## 筆畫資料

- 依字的總筆畫數由少至多排列；相同筆畫數依 Unicode 碼位排序，確保順序固定。
- 筆畫數資料參考 [ChineseStrokes](https://github.com/caiguanhao/ChineseStrokes)（該專案標示來源為 zidian.911cha.com）。建置時只輸出遊戲實際使用字元的筆畫數，並驗證每個候選字都有資料。

## 詞庫規則

- 以教育部《成語典》下載資料為來源，只取「主條成語／非主條成語」欄標示為「主條成語」的四字詞目。
- 若釋義以「即『X』。見『X』條」明確轉引到另一主條詞目，排除轉引詞目。例如保留「紙醉金迷」，排除「金迷紙醉」。
- 不將官方釋義、例句、書證或典源原文複製進遊戲。遊戲目前的提示採揭示一字方式，並非語義釋義。
- 官方資料下載頁：https://language.moe.gov.tw/001/Upload/Files/site_content/M0001/respub/dict_idiomsdict_download.html
- 使用及再散布官方資料時，請遵守下載頁列明的授權條款。

## 本機建置

需要 Python 3 及 openpyxl：

```bash
python -m pip install openpyxl
python tools/build_levels.py source.xlsx public/data/levels.json
python tools/build_stroke_counts.py public/data/levels.json stroke-data/ public/data/strokes.json
```

建置腳本會在無法找到 21 關、420 個不重複且連通的棋盤時直接失敗，不會輸出未驗證的棋盤。

## GitHub Pages

`.github/workflows/deploy.yml` 會在推送到 `main` 時下載官方 ZIP、生成並驗證靜態棋盤，再部署 `public/`。請到 GitHub repository Settings → Pages 確認部署來源設為 GitHub Actions。部署網址通常為 https://harfock.github.io/4letters/ ，但必須以 Actions 顯示成功為準。
