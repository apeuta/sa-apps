# Re-provision folder pakai guard sederhana, bukan idempotensi penuh terhadap state Drive

`provision_project_folder()` membuat folder lalu set permission secara berurutan. Jika gagal di tengah, folder master/subfolder bisa sudah terlanjur dibuat di Drive sementara id belum tersimpan di DB (raise sebelum persist). Endpoint re-provision (`POST /projects/{id}/provision-folder`, Lead_SA/Admin) yang menjalankan ulang provisioning berisiko membuat set folder duplikat di Drive.

**Keputusan (sesi grill, 2026-10-26):** untuk MVP, re-provision hanya dijalankan bila `gdrive_folder_id` masih null (belum pernah sukses ter-provision); bila sudah terisi, request ditolak. Folder yatim akibat kegagalan parsial dibersihkan **manual** oleh admin di Drive. Idempotensi penuh (query Drive cari folder master by-name, reuse yang ada, lengkapi yang kurang) sengaja tidak diimplementasikan karena kompleks dan rapuh (match by-name) untuk kebutuhan single-team MVP.

## Consequences

Kegagalan parsial yang jarang meninggalkan folder yatim di Drive yang perlu dibersihkan manual — trade-off sadar: pembersihan manual sesekali lebih murah daripada kode rekonsiliasi Drive yang rapuh. Saat skala/volume naik, tinjau ulang untuk rekonsiliasi otomatis.
