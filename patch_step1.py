import re

with open('app.py', 'r') as f:
    content = f.read()

# Fallback script block right after the element
fallback_script = """        </div>
        <div class="text-right">
            <p class="text-[8px] text-gray-500 font-bold mb-0.5 uppercase tracking-wider"><i class="fas fa-clock text-emerald-500"></i> Waktu Samarinda</p>
            <p class="text-[10px] font-bold {{ t_icon_text }} {{ t_icon_bg }} px-2 py-1 rounded-full border border-emerald-200" id="hijri-date">Loading...</p>
            <script>
                (function(){
                    function f(){
                        try {
                            var el = document.getElementById('hijri-date');
                            if(el) {
                                var opts = { timeZone: 'Asia/Makassar', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
                                var d = new Date();
                                var fmtr = new Intl.DateTimeFormat('id-ID', opts);
                                var parts = fmtr.formatToParts(d);
                                var p = function(t){ var o = parts.find(function(x){return x.type===t;}); return o ? o.value : ''; };
                                el.innerText = p('weekday') + ', ' + p('day') + ' ' + p('month') + ' ' + p('year') + ' • ' + (p('hour')||'00') + ':' + (p('minute')||'00') + ':' + (p('second')||'00');
                            }
                        } catch(e) { console.error('Fallback clock error', e); }
                    }
                    f();
                    setInterval(f, 1000);
                })();
            </script>
        </div>"""
content = content.replace("""        </div>
        <div class="text-right">
            <p class="text-[8px] text-gray-500 font-bold mb-0.5 uppercase tracking-wider"><i class="fas fa-clock text-emerald-500"></i> Waktu Samarinda</p>
            <p class="text-[10px] font-bold {{ t_icon_text }} {{ t_icon_bg }} px-2 py-1 rounded-full border border-emerald-200" id="hijri-date">Loading...</p>
        </div>""", fallback_script)

# Try-catch inside fetchHijri
fetch_hijri_old = """        function fetchHijri() {
            function updateDate() {
                const today = new Date();
                // Set timezone to Asia/Makassar for Samarinda time
                const options = {
                    timeZone: 'Asia/Makassar',
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                };

                // Format directly into "Senin, 10 Juli 2024 - 14:30:00" format depending on toLocaleString implementation
                const formatter = new Intl.DateTimeFormat('id-ID', options);
                const parts = formatter.formatToParts(today);

                let dayName = parts.find(p => p.type === 'weekday')?.value || '';
                let day = parts.find(p => p.type === 'day')?.value || '';
                let month = parts.find(p => p.type === 'month')?.value || '';
                let year = parts.find(p => p.type === 'year')?.value || '';
                let hour = parts.find(p => p.type === 'hour')?.value || '00';
                let minute = parts.find(p => p.type === 'minute')?.value || '00';
                let second = parts.find(p => p.type === 'second')?.value || '00';

                const dateString = `${dayName}, ${day} ${month} ${year} • ${hour}:${minute}:${second}`;

                const elements = document.querySelectorAll('[id^="hijri-date"]');
                elements.forEach(el => {
                    el.innerText = dateString;
                });
            }
            updateDate();
            setInterval(updateDate, 1000); // Update every second for real-time clock
        }"""
fetch_hijri_new = """        function fetchHijri() {
            try {
                function updateDate() {
                    try {
                        const today = new Date();
                        // Set timezone to Asia/Makassar for Samarinda time
                        const options = {
                            timeZone: 'Asia/Makassar',
                            weekday: 'long',
                            day: 'numeric',
                            month: 'long',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit'
                        };

                        // Format directly into "Senin, 10 Juli 2024 - 14:30:00" format depending on toLocaleString implementation
                        const formatter = new Intl.DateTimeFormat('id-ID', options);
                        const parts = formatter.formatToParts(today);

                        let dayName = parts.find(p => p.type === 'weekday')?.value || '';
                        let day = parts.find(p => p.type === 'day')?.value || '';
                        let month = parts.find(p => p.type === 'month')?.value || '';
                        let year = parts.find(p => p.type === 'year')?.value || '';
                        let hour = parts.find(p => p.type === 'hour')?.value || '00';
                        let minute = parts.find(p => p.type === 'minute')?.value || '00';
                        let second = parts.find(p => p.type === 'second')?.value || '00';

                        const dateString = `${dayName}, ${day} ${month} ${year} • ${hour}:${minute}:${second}`;

                        const elements = document.querySelectorAll('[id^="hijri-date"]');
                        elements.forEach(el => {
                            el.innerText = dateString;
                        });
                    } catch (e) {
                        console.error('Error in updateDate:', e);
                    }
                }
                updateDate();
                setInterval(updateDate, 1000); // Update every second for real-time clock
            } catch (err) {
                console.error('Error in fetchHijri:', err);
            }
        }"""
content = content.replace(fetch_hijri_old, fetch_hijri_new)

# Try catch the DOMContentLoaded listener calling fetchHijri
dom_loaded_old = """        document.addEventListener('DOMContentLoaded', () => {
            fetchHijri();
        });"""
dom_loaded_new = """        document.addEventListener('DOMContentLoaded', () => {
            try {
                fetchHijri();
            } catch (e) {
                console.error("Error calling fetchHijri on DOMContentLoaded", e);
            }
        });"""
content = content.replace(dom_loaded_old, dom_loaded_new)

with open('app.py', 'w') as f:
    f.write(content)
print("Done patching.")
