# Backend API - Digital Watermarking

API REST pentru aplicația de watermarking digital.

## 🚀 Start Rapid

```bash
cd backend
pip install -r requirements.txt
python api.py
```

API-ul va rula pe `http://localhost:5000`

## 📡 Endpoints

### Health Check
```
GET /api/health
```
Verifică status API.

**Response:**
```json
{
  "status": "ok",
  "message": "Digital Watermarking API is running"
}
```

### Calculate Capacity
```
POST /api/capacity
```
Calculează capacitatea de embedding pentru o imagine.

**Parameters:**
- `image` (file) - Imaginea de analizat
- `block_size` (int, optional) - Block size (default: 8)

**Response:**
```json
{
  "capacity_bits": 16384,
  "capacity_bytes": 2048,
  "image_size": {"width": 1920, "height": 1080},
  "block_size": 8
}
```

### Embed Watermark
```
POST /api/embed
```
Embedează un watermark semnat în imagine.

**Parameters:**
- `image` (file) - Imaginea originală
- `message` (string) - Mesajul de embedat
- `block_size` (int, optional) - Block size (default: 8)

**Response:**
- File download: imaginea watermarked

**Errors:**
- `400` - Mesaj prea lung sau fișier invalid
- `500` - Eroare server

### Verify Watermark
```
POST /api/verify
```
Extrage și verifică watermark-ul dintr-o imagine.

**Parameters:**
- `image` (file) - Imaginea watermarked
- `block_size` (int, optional) - Block size (default: 8)

**Response:**
```json
{
  "message": "GloryToLordJesusChrist",
  "valid": true,
  "signature_length": 256
}
```

## 🔧 Configurare

Editează `config.py` pentru a modifica setările:

```python
API_HOST = '0.0.0.0'
API_PORT = 5000
DEBUG_MODE = True

PRIVATE_KEY_PATH = 'data/keys/private.pem'
PUBLIC_KEY_PATH = 'data/keys/public.pem'

DEFAULT_BLOCK_SIZE = 8
```

## 📁 Structură

```
backend/
├── api.py              # Flask REST API
├── config.py           # Configurare
├── main.py             # Script demo CLI
├── requirements.txt    # Dependențe Python
├── crypto/
│   ├── keys.py         # Generare chei RSA
│   ├── sign.py         # Semnare mesaje
│   └── verify.py       # Verificare semnături
├── watermarking/
│   ├── embed.py        # Embedding watermark
│   └── extract.py      # Extragere watermark
├── utils/
│   ├── conversions.py  # Conversii bytes/bits
│   ├── hashing.py      # Hash-uri
│   └── image_utils.py  # Utilități imagini
└── data/
    ├── keys/           # Chei RSA
    └── watermarked/    # Imagini procesate
```

## 🔐 Securitate

### Generare Chei RSA

Dacă nu ai chei RSA, generează-le:

```python
from crypto.keys import generate_key_pair

private_key, public_key = generate_key_pair()
# Salvează în data/keys/
```

### Workflow Semnături

1. **Embed**: Mesaj → Hash → Semnare cu cheia privată → Embed în imagine
2. **Verify**: Extract din imagine → Verificare cu cheia publică → Valid/Invalid

## 🧪 Testing

### Test cu curl

```bash
# Health check
curl http://localhost:5000/api/health

# Capacity
curl -X POST -F "image=@test.png" http://localhost:5000/api/capacity

# Embed
curl -X POST \
  -F "image=@test.png" \
  -F "message=Test message" \
  -F "block_size=8" \
  http://localhost:5000/api/embed \
  --output watermarked.png

# Verify
curl -X POST \
  -F "image=@watermarked.png" \
  -F "block_size=8" \
  http://localhost:5000/api/verify
```

### Test cu Python

```python
import requests

# Embed
files = {'image': open('test.png', 'rb')}
data = {'message': 'Test message', 'block_size': 8}
response = requests.post('http://localhost:5000/api/embed', files=files, data=data)
with open('watermarked.png', 'wb') as f:
    f.write(response.content)

# Verify
files = {'image': open('watermarked.png', 'rb')}
data = {'block_size': 8}
response = requests.post('http://localhost:5000/api/verify', files=files, data=data)
print(response.json())
```

## 🐛 Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "FileNotFoundError: private.pem"
Generează cheile RSA sau verifică calea în `config.py`

### CORS errors
Verifică că `flask-cors` este instalat și CORS_ORIGINS în `config.py`

### "Port already in use"
Schimbă portul în `config.py` sau oprește procesul care folosește portul 5000

## 📊 Performance

- **Embed**: ~1-3 secunde pentru imagini HD
- **Verify**: ~0.5-1 secundă
- **Capacity**: ~0.1 secunde

Depinde de:
- Dimensiunea imaginii
- Block size
- Dimensiunea mesajului

## 🔄 Updates

Pentru a actualiza dependențele:

```bash
pip install --upgrade -r requirements.txt
```

---

**Note**: Acest API este pentru development. Pentru producție, folosește un server WSGI (gunicorn, uwsgi).

