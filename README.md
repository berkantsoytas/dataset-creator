# Dataset Creator

EN: Convert source code repositories into high-quality JSONL training samples for code understanding models.

TR: Kaynak kod depolarini, kod anlama modelleri icin yuksek kaliteli JSONL egitim orneklerine donusturur.

## Highlights / One Cikanlar

EN:

- Multi-language extraction pipeline (Python AST + non-Python language-specific parsing)
- Function/method/class level chunking
- Optional AI-powered explanation generation
- Quality scoring and filtering
- Duplicate code-body deduplication
- Colorized CLI output and progress reporting
- Local folder or Git URL input support

TR:

- Cok dilli cikarma hattı (Python AST + Python disi diller icin dil-ozel ayrisma)
- Fonksiyon/metot/sinif seviyesinde parcalama
- Opsiyonel AI destekli aciklama uretimi
- Kalite puanlama ve filtreleme
- Ayni kod govdesi tekrarlarinda tekillestirme
- Renkli CLI ciktilari ve ilerleme gostergesi
- Yerel klasor veya Git URL kaynak destegi

## Supported Languages / Desteklenen Diller

- Python
- JavaScript / TypeScript
- Java
- Go
- Rust
- C / C++ / C#
- PHP
- Ruby

## Installation / Kurulum

EN:

1. Use Python 3.10+.
2. Run from project root.
3. (Optional) Create and activate a virtual environment.

TR:

1. Python 3.10+ kullanin.
2. Komutlari proje kokunden calistirin.
3. (Opsiyonel) Sanal ortam olusturup aktif edin.

## Quick Start / Hizli Baslangic

### Local source folder / Yerel kaynak klasoru

```bash
python dataset_creator.py \
  --source /path/to/repository \
  --output dataset.jsonl
```

### Git URL source / Git URL kaynagi

```bash
python dataset_creator.py \
  --source https://github.com/pallets/flask.git \
  --output dataset.jsonl
```

EN: If `--source` is a Git URL, the repo is cloned to a temporary directory and analyzed.

TR: `--source` bir Git URL ise depo gecici bir klasore klonlanir ve analiz edilir.

## AI Mode / AI Modu

EN:

- Without `--use-ai`, explanations are produced by heuristic rules.
- With `--use-ai`, explanations and complexity are requested from OpenAI-compatible endpoint.
- If AI call fails, system falls back to heuristic explanation.

TR:

- `--use-ai` olmadan aciklamalar sezgisel kurallarla uretilir.
- `--use-ai` ile aciklama ve karmasiklik OpenAI uyumlu endpointten alinmaya calisilir.
- AI cagrisi basarisiz olursa sistem otomatik sezgisel moda geri duser.

Example / Ornek:

```bash
python dataset_creator.py \
  --source /path/to/repository \
  --output dataset.jsonl \
  --use-ai \
  --ai-api-key-file .openai_key
```

## Language Selection / Dil Secimi

EN:

- `--lang en` (default) or `--lang tr`
- Affects CLI text, heuristic explanations, and AI prompt language.

TR:

- `--lang en` (varsayilan) veya `--lang tr`
- CLI metinlerini, sezgisel aciklamalari ve AI prompt dilini etkiler.

## Verbose and Progress / Verbose ve Ilerleme

EN:

- Verbose is enabled by default.
- Use `--no-verbose` to disable per-chunk logs.
- When AI is enabled and verbose is off, a single-line loading/progress indicator is shown.

TR:

- Varsayilan olarak verbose aciktir.
- Parca bazli loglari kapatmak icin `--no-verbose` kullanin.
- AI acik ve verbose kapaliyken tek satirlik loading/progress gostergesi gorunur.

## Git Clone Control / Git Klon Kontrolu

EN:

- `--clone-base-dir /your/path`: choose where temporary clone folder is created.
- `--keep-cloned-repo`: keep cloned repository after analysis.
- Without `--keep-cloned-repo`, temporary clone directory is deleted automatically.

TR:

- `--clone-base-dir /your/path`: gecici klon klasorunun olusacagi yeri secer.
- `--keep-cloned-repo`: analizden sonra klonlanan depoyu saklar.
- `--keep-cloned-repo` verilmezse gecici klon klasoru otomatik silinir.

## CLI Options / CLI Parametreleri

- `--source`: Source directory path or Git URL
- `--clone-base-dir`: Base directory for temporary clone when source is URL
- `--keep-cloned-repo`: Keep temporary clone after analysis
- `--output`: Output JSONL file
- `--min-file-lines`: Skip short files
- `--min-chunk-lines`: Skip short chunks
- `--exclude-classes`: Disable class-level chunks
- `--use-ai`: Enable AI explanations
- `--ai-provider`: AI provider (currently openai)
- `--ai-model`: Model name
- `--ai-base-url`: Completion endpoint
- `--ai-timeout-seconds`: Request timeout
- `--ai-api-key-file`: API key file path
- `--min-quality-score`: Quality threshold in [0,1]
- `--verbose`: Enable detailed logs
- `--no-verbose`: Disable detailed logs
- `--lang`: `en` or `tr`

## Output Schema / Cikti Semasi

Each JSONL line contains:

- `id`
- `path`
- `language`
- `chunk_type`
- `name`
- `code`
- `start_line`
- `end_line`
- `explanation`
- `time_complexity`
- `quality_score`

## Project Structure / Proje Yapisi

- `dataset_creator.py`: Thin entry point
- `code_dataset_creator/cli.py`: CLI argument parsing and run orchestration
- `code_dataset_creator/creator.py`: End-to-end dataset generation pipeline
- `code_dataset_creator/extractors.py`: Chunk extraction logic
- `code_dataset_creator/signatures.py`: Language-aware signature detection
- `code_dataset_creator/explainers.py`: Heuristic explanation generation
- `code_dataset_creator/ai_client.py`: AI request client
- `code_dataset_creator/quality.py`: Quality scoring and filtering
- `code_dataset_creator/filters.py`: File-level pre-filtering
- `code_dataset_creator/models.py`: Dataclasses
- `code_dataset_creator/constants.py`: Extensions and skip dirs
- `code_dataset_creator/i18n.py`: EN/TR user-facing text resources
- `code_dataset_creator/colors.py`: Terminal color helpers

## Security Notes / Guvenlik Notlari

EN:

- Do not commit API keys into Git.
- Prefer `--ai-api-key-file` and keep key files private (`chmod 600`).

TR:

- API anahtarlarini Git'e commit etmeyin.
- `--ai-api-key-file` kullanin ve anahtar dosyasini ozel tutun (`chmod 600`).

## Acknowledgements / Tesekkur

EN: This project was developed with help from GitHub Copilot (GPT-5.3-Codex) during design and implementation.

TR: Bu proje, tasarim ve gelistirme surecinde GitHub Copilot (GPT-5.3-Codex) destegi kullanilarak gelistirilmistir.
