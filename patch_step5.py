import re

with open('app.py', 'r') as f:
    content = f.read()

submit_old = """        async function submitNutrisi(e) {
            e.preventDefault();
            const rawInput = document.getElementById('jurnal_makanan_input').value;
            const input = rawInput.toLowerCase();
            let hasAllergen = false;"""
submit_new = """        async function submitNutrisi(e) {
            e.preventDefault();
            const rawInput = document.getElementById('jurnal_makanan_input').value;
            if(!rawInput.trim()) return;
            const input = rawInput.toLowerCase();
            let hasAllergen = false;"""
content = content.replace(submit_old, submit_new)

submit_fetch_old = """            try {
                const res = await fetch('/orang-tua/api/nutrisi', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
                    body: JSON.stringify({ food_name: input, has_allergen: hasAllergen })
                });
                if(res.ok) {
                    e.target.reset();
                    checkAllergens(); // Reset UI
                    loadNutrisiList();
                }
            } catch(err) { console.error(err); }
        }"""
submit_fetch_new = """            try {
                const res = await fetch('/orang-tua/api/nutrisi', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
                    body: JSON.stringify({ food_name: input, has_allergen: hasAllergen })
                });
                if(res.ok) {
                    e.target.reset();
                    checkAllergens(); // Reset UI
                    loadNutrisiList();
                } else {
                    alert('Gagal menyimpan jurnal. Silakan coba lagi.');
                }
            } catch(err) {
                console.error(err);
                alert('Gagal menyimpan jurnal. Silakan coba lagi.');
            }
        }"""
content = content.replace(submit_fetch_old, submit_fetch_new)

with open('app.py', 'w') as f:
    f.write(content)
print("Done patching.")
