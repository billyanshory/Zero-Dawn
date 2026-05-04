1. **Batch 1: CRITICAL SSTI ELIMINATION**
   - In `app.py`, locate the `content = f"""` block in the `donate` route (around line 7968).
   - Change `content = f"""` to `content = """`.
   - Replace `{acc_no}` with `{{ acc_no }}`, `{qris_url}` with `{{ qris_url }}`, `{bg_class}` with `{{ bg_class }}`, `{card_class}` with `{{ card_class }}`, and `{text_highlight}` with `{{ text_highlight }}`.
   - Change `{{% if is_admin %}}` and `{{% endif %}}` to `{% if is_admin %}` and `{% endif %}`.
   - Change `{{ if(typeof formatBankDisplay === 'function') formatBankDisplay('donate-rek-text'); }}` to `{ if(typeof formatBankDisplay === 'function') formatBankDisplay('donate-rek-text'); }`.
   - Update the `render_template_string` call for `content` (around line 8045) to include `acc_no=acc_no, qris_url=qris_url, bg_class=bg_class, card_class=card_class, text_highlight=text_highlight`.
   - Update the outer `render_template_string(BASE_LAYOUT, ...)` to include `settings=get_settings()`.

2. **Batch 2: IDUL ADHA THEME RESTORATION**
   - Add the `IDUL_ADHA_THEME` dictionary after `IRMA_STYLES` closing triple-quote.
   - Add `theme=IDUL_ADHA_THEME` to the 7 outer `render_template_string(BASE_LAYOUT, ...)` calls for Idul Adha pages (absen panitia, main dashboard, laporan, shohibul, peta distribusi, panduan, pembagian).

3. **Batch 3: JAVASCRIPT CONTEXT SAFETY**
   - In `RAMADHAN_DASHBOARD_HTML` and `IRMA_DASHBOARD_HTML`, replace `const open = '{{ open_modal }}';\nif(open && open !== 'None') openModal(open);` with `const open = {{ open_modal|tojson }};\nif(open) openModal(open);`.
   - In `IDUL_ADHA_SHOHIBUL_HTML`, `IDUL_ADHA_PEMBAGIAN_HTML`, and `IDUL_ADHA_PETA_DISTRIBUSI_HTML`, replace `const pin = '{{ shohibul.pin }}';` with `const pin = {{ shohibul.pin|tojson }};`.

4. **Batch 4: MINOR CLEANUP**
   - In `model_getitem` (line 984), change `return getattr(self, key)` to `return getattr(self, key, None)`.
   - In `rendered_home` render call in the `index` route (line 7013), remove `open_modal=request.args.get('open')`.
   - In the `fitur_masjid` route (line 7871), combine the two lines into one, passing `FITUR_MASJID_HTML` directly as the `content` argument.

5. **Pre-commit Steps**
   - Ensure proper testing, verification, review, and reflection are done by calling `pre_commit_instructions`.

6. **Submit**
   - Submit the changes with a descriptive branch name and commit message.
