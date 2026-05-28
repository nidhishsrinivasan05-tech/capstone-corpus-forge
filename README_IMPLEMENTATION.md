# Capstone Project: Corpus Forge

## Contributors

- Nidhish Srinivasan — GitHub: nidhishsrinivasan05-tech — Email: nidhish-srinivasan_krishnassamy@epita.fr
- Omar Kahkahni — GitHub: omarkahaa — Email: omar.kahkahni@epita.fr
- Jean-Remy Iradukunda — GitHub: iradukunda277 — Email: jean-remy.iradukunda@epita.fr

## Project Goal

Corpus Forge is a small capstone project used to compare answers generated with normal model context and answers generated with retrieved document context.

## Project Structure

- `app/` — main Python code for loading documents, retrieving chunks, and generating answers
- `docs/` — text files used as the corpus
- `tests/` — small tests used to check the retrieval logic
- `prompts_history.md` — saved prompt history during the project
- `JOURNAL.md` — development journal updated during interactions

## How to Run

Install the requirements first:

```bash
pip install -r requirements.txt
```

Run the scripts from the main project folder:

```bash
python3 ask_rag_google.py "your question here"
```

```bash
python3 ask_norag_google.py "your question here"
```

## Notes

The project uses a simple workflow: load text documents, split them into chunks, retrieve the most relevant parts, then send the selected context to the model.

The `.env` file is not pushed to Git because it contains private API keys.
