# おしゃべりデータ（Datask） 🎫

**Datask** は「自然言語で Azure SQL を検索・可視化できる」 Streamlit 製アプリです。

> *"田中さんの月別利用状況をグラフで見せて"*──そんな会話だけで、AI が  
> ① 日本語 → ② T-SQL 変換 → ③ DB クエリ → ④ 表・グラフ表示 まで自動で行います。



---

## ✨ 特長

| 機能 | 説明 |
|------|------|
| 自然言語 ➜ SQL 変換 | Azure OpenAI（GPT-4）Function Calling で SELECT 文を自動生成 |
| グラフ／表の自動切替 | 質問意図を解析し、表・棒グラフ・ヒートマップなどを自動で選択表示 |
| FAQ × AI Search | よくある質問を Azure AI Search にインデックス。類似質問には即 FAQ で回答 |
| スキーマ安全性 | INSERT/UPDATE/DELETE を禁止し、読み取り専用クエリだけ生成 |
| Streamlit UI | ワンページ＆角丸デザインでシンプル・フレンドリー |

---

## 🗺️ アーキテクチャ概要

```
User ──▶ Streamlit UI ──▶ Azure OpenAI (GPT-4) ──▶
           │                    │                   │
       (自然言語)          Function Calling         ▼
           │                    │                   │
           ▼                    ▼                   │
   Azure AI Search ◀─────────────── 生成SQL / グラフ指示
                                   │
                                   ▼
                           Azure SQL Database
```

---

## 🛠 技術スタック

| レイヤ | 採用技術 |
|-----------------|----------|
| フロント | **Streamlit** (Python) |
| 言語モデル | **Azure OpenAI** GPT-4 / GPT-4o |
| DB | **Azure SQL** (Managed) |
| 検索補助 (RAG) | **Azure AI Search** |
| シークレット | Streamlit Cloud Secrets |

※ 本プロジェクトの設計・実装には **ChatGPT (GPT-4o)** を開発補助として活用しています。

---

## 📦 クイックスタート

### 1. クローン & 依存パッケージのインストール

```bash
git clone https://github.com/<your-account>/datask-hackathon.git
cd datask-hackathon
pip install -r requirements.txt
```

### 2. シークレット設定（`.streamlit/secrets.toml` または環境変数）

```toml
# Azure SQL
AZURE_SQL_SERVER = "<your-sql-server>.database.windows.net"
AZURE_SQL_DB = "SeatDB"
AZURE_SQL_USER = "sqladmin"
AZURE_SQL_PASSWORD = "********"

# Azure OpenAI
AZURE_OPENAI_ENDPOINT = "https://<your-resource>.openai.azure.com/"
AZURE_OPENAI_API_KEY = "********"
AZURE_OPENAI_DEPLOYMENT = "gpt4o-sql"

# Azure AI Search（任意）
AZURE_SEARCH_ENDPOINT = "https://<your-search>.search.windows.net"
AZURE_SEARCH_API_KEY = "********"
```

### 3. ダミーデータ投入（任意）

```bash
python -m datask_app.testdata.seatlog_dummy
```

### 4. アプリ起動

```bash
streamlit run datask_app/app.py
```

ブラウザで `http://localhost:8501` を開くとUIが表示されます。

---

## 📁 ディレクトリ構成

```
datask_app/
├── app.py                    # Streamlit のエントリーポイント
├── core/                     # DB接続・SQL生成・OpenAI連携
│   ├── db.py
│   ├── openai_sql.py
│   ├── schema.py
│   └── config.py
├── visual/                   # グラフや座席マップ描画モジュール
│   ├── charts.py
│   └── seatmap.py
├── testdata/
│   └── seatlog_dummy.py      # ダミーデータ生成スクリプト
├── tools/
│   └── upload_faq.py         # FAQデータをAzure AI Searchに登録
└── .streamlit/
    └── secrets.toml          # 認証キー設定ファイル
```

---

## 🗒️ ライセンス

MIT License を採用しています。詳細は LICENSE をご覧ください。

---

## 🙏 クレジット

* Azure OpenAI Service
* Streamlit  
* Azure AI Search
* 本プロジェクトは OpenAI の GPT-4o を活用して、設計・コード生成・資料作成を支援しています。

---

必要に応じてスクリーンショット (`docs/img/datask-demo.png`) を追加したり、リポジトリ URL やチーム名などを差し替えてください。英語版が必要な場合も対応可能です。
