# Digital Watermarking Application - Full Stack

Aplicație modernă de watermarking digital pentru poze istorice cu semnături criptografice RSA.

## 🚀 Componente

### Backend (Python/Flask)
- API REST pentru embedding și verificare watermark
- Semnături digitale RSA
- DWT (Discrete Wavelet Transform) pentru embedding

### Frontend (React/TypeScript)
- Interfață modernă și intuitivă
- Drag & drop pentru imagini
- Previzualizare în timp real
- Feedback vizual pentru validarea semnăturilor

## 📋 Cerințe

### Backend
- Python 3.8+
- pip

### Frontend
- Node.js 14+
- npm sau yarn

## 🔧 Instalare

### 1. Backend

```bash
cd backend

# Instalează dependințele
pip install -r requirements.txt

# Pornește serverul API
python api.py
```

Serverul va rula pe `http://localhost:5000`

### 2. Frontend

```bash
cd frontend

# Instalează dependințele
npm install

# Pornește aplicația React
npm start
```

Aplicația va rula pe `http://localhost:3000`

## 📖 Utilizare

### Embed Watermark

1. Selectează o imagine (PNG, JPG, BMP)
2. Introdu mesajul pe care vrei să-l embedezi
3. Ajustează block size-ul (dacă este necesar)
4. Verifică că mesajul se încadrează în capacitatea imaginii
5. Click pe "Embed & Sign Watermark"
6. Imaginea watermarked va fi descărcată automat

### Verify Watermark

1. Selectează o imagine watermarked
2. Setează același block size folosit la embedding
3. Click pe "Extract & Verify Watermark"
4. Vezi mesajul extras și statusul semnăturii digitale

## 🔐 Securitate

- Folosește semnături RSA pentru autentificare
- Verifică integritatea mesajului
- Detectează modificări în imagine

## 🛠️ Tehnologii

### Backend
- Flask - Web framework
- OpenCV - Procesare imagini
- PyWavelets - DWT
- Cryptography - Semnături RSA

### Frontend
- React - UI framework
- TypeScript - Type safety
- CSS3 - Styling modern
- Fetch API - Comunicare cu backend

## 📂 Structură Project

```
backend/
├── api.py              # Flask REST API
├── main.py             # Script demo original
├── crypto/             # Semnături RSA
├── watermarking/       # Embed/Extract
├── utils/              # Utilități
└── data/
    ├── keys/           # Chei RSA
    └── watermarked/    # Imagini procesate

frontend/
├── src/
│   ├── App.tsx         # Componenta principală
│   ├── components/
│   │   ├── EmbedTab.tsx    # Tab pentru embedding
│   │   └── VerifyTab.tsx   # Tab pentru verificare
│   └── App.css         # Styling
└── public/
```

## 🎨 Features

✅ Interfață modernă și responsivă  
✅ Preview în timp real  
✅ Calculare automată a capacității  
✅ Validare mesaj  
✅ Feedback vizual pentru semnături  
✅ Download automat  
✅ Handling erori  

## 🐛 Troubleshooting

### Backend nu pornește
- Verifică că toate dependințele sunt instalate: `pip install -r requirements.txt`
- Verifică că există chei în `data/keys/`

### Frontend nu se conectează la backend
- Asigură-te că backend-ul rulează pe port 5000
- Verifică CORS settings în `api.py`

### Erori la embedding
- Verifică că imaginea este în format suportat
- Reduce dimensiunea mesajului sau folosește block size mai mic
- Folosește imagini mai mari

## 📝 License

MIT License - Facultate Licență cu Crivei

## 👨‍💻 Autor

Developed with ❤️ for historical photo preservation

