1. **Model Updates**: Add the following SQLAlchemy models to store data for the new Idul Adha Qurban features:
   - `QurbanReport`: To store 'Laporan Qurban' data (Total Hewan Sapi, Total Hewan Kambing, Estimasi Daging, Paket Terdistribusi, Total Paket).
   - `QurbanShohibul`: To store 'Daftar Shohibul' data (PIN, Type, Queue Number, Name, Status).
   - `QurbanKupon`: To store 'Pembagian' data (Kupon, Nama Penerima, RT, Waktu Pengambilan, Lokasi).
   - `QurbanRT`: To store 'Peta Distribusi' data (Card Number, RT Name, Ketua RT Name, Allocation, Status).

2. **Template Updates**: Modify the HTML string variables to include Jinja templating logic for displaying dynamic data and admin edit forms.
   - `IDUL_ADHA_LAPORAN_HTML`: Display dynamic report data. Add edit form visible only to admins.
   - `IDUL_ADHA_SHOHIBUL_HTML`: Add form for admins to generate PINs, assign names/types. Display dynamic tracker based on PIN search for regular users and admins. Add status update mechanism for admins.
   - `IDUL_ADHA_PEMBAGIAN_HTML`: Add form for admins to generate kupons, assign recipient details. Display dynamic schedule check based on Kupon/Name search.
   - `IDUL_ADHA_PETA_DISTRIBUSI_HTML`: Display dynamic RT cards, total progress. Add form for admins to add/edit RT cards, update delivery status.

3. **Route Updates**: Create new routes to handle the CRUD operations for the new features.
   - Update `idul_adha_laporan()` to fetch data and render template. Create `/idul-adha/laporan/update` (POST) to handle report updates.
   - Update `idul_adha_shohibul()` to fetch data and render template. Create `/idul-adha/shohibul/generate` (POST) to generate PINs, `/idul-adha/shohibul/update_status` (POST) to update tracker status, `/idul-adha/shohibul/search` (GET/POST) to search by PIN.
   - Update `idul_adha_distribution()` to fetch data and render template. Create `/idul-adha/distribution/generate` (POST) to create kupons, `/idul-adha/distribution/search` (GET/POST) to check schedule.
   - Update `idul_adha_peta_distribusi()` to fetch data and render template. Create `/idul-adha/peta-distribusi/add` (POST) to add RT cards, `/idul-adha/peta-distribusi/update/<id>` (POST) to update RT card details and status.

4. **Raw SQL Schema Checks**: Add schema checks in the initialization block (before `app.run()`) to create the new tables if they don't exist, adhering to the "monolithic Flask apps (without Flask-Migrate)" constraint.

5. **Pre-commit**: Run pre-commit instructions to ensure everything passes before submitting.
