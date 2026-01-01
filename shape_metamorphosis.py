from manim import *

class MorphingShapes(Scene):
    def construct(self):
        # Konfigurasi estetika Dark Mode (Latar hitam)
        self.camera.background_color = BLACK

        # 3. Tampilkan teks "Geometry" di bagian atas layar.
        text = Text("Geometry", font_size=48, color=WHITE).to_edge(UP)

        # 2. Mulai dengan bentuk Square berwarna BLUE, isi opacity 0.5.
        # Menambahkan stroke width untuk efek neon
        square = Square(color=BLUE, fill_opacity=0.5)
        square.set_stroke(width=5)

        # Tampilkan elemen awal
        self.add(text, square)
        self.wait(0.5)

        # 4. Animasi 1: Putar Square 45 derajat sambil mengubahnya (Transform) menjadi Circle berwarna RED.
        # Gunakan run_time=2 detik.
        circle = Circle(color=RED, fill_opacity=0.5)
        circle.set_stroke(width=5)

        # Transform secara otomatis menangani interpolasi bentuk.
        # Rotate ditambahkan ke animasi group atau menggunakan path_arc jika ingin rotasi spasial,
        # tapi instruksi meminta "Putar... sambil mengubahnya".
        # Transform sendiri memetakan titik ke titik. Untuk visual rotasi yang jelas, kita putar mobjectnya.
        self.play(
            Transform(square, circle),
            Rotate(square, angle=45*DEGREES),
            run_time=2,
            rate_func=smooth
        )

        self.wait(0.5)

        # 5. Animasi 2: Ubah Circle tersebut menjadi Star (Poligon bintang) berwarna YELLOW dengan border tipis.
        star = Star(color=YELLOW, fill_opacity=0.5, outer_radius=2)
        star.set_stroke(width=2) # Border tipis

        self.play(
            Transform(square, star), # square variable mereferensikan mobject yang sedang dimodifikasi
            run_time=2,
            rate_func=smooth
        )

        self.wait(0.5)

        # 6. Animasi 3: Kecilkan (Scale) objek hingga hilang (FadeOut) bersamaan dengan teks.
        # Groupkan animasi scale dan fadeout
        self.play(
            square.animate.scale(0),
            FadeOut(square),
            FadeOut(text),
            run_time=1.5,
            rate_func=smooth
        )

        self.wait()
