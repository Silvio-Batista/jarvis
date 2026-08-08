<p align="center">
  <img src="assets/logo/Logo%20I.A%20TowerHub.png" alt="TowerHub" width="120" />
</p>

<h1 align="center">JARVIS</h1>
<p align="center">
  <strong>Just A Rather Very Intelligent System</strong><br/>
  Assistente pessoal com painel desktop, voz e automações no Windows
</p>

<p align="center">
  Desenvolvido por <strong>TowerHub</strong>
</p>

---

## Sobre o projeto

O **JARVIS** é um assistente virtual para Windows com:

- Painel desktop (HUD) em PySide6
- Comandos de voz (ativar com “Jarvis”, descansar com “descanse”)
- Abertura de aplicativos e automações do sistema
- Agenda e tarefas dinâmicas por dia
- Lembretes via notificação nativa do Windows
- Banco MySQL para persistência das tarefas

---

## Requisitos

- Windows 10/11
- Python **3.12+** (testado também em 3.14)
- Microfone (para o modo voz)
- MySQL/MariaDB em `localhost:3306`
- Conexão com internet (STT Google + TTS Edge, no MVP)

---

## Instalação

### 1. Clone / abra a pasta do projeto

```powershell
cd "caminho\para\jarvis"
```

### 2. Crie e ative o ambiente virtual

```powershell
py -m venv .venv
.\.venv\Scripts\activate
```

### 3. Instale as dependências

```powershell
pip install -r requirements.txt
```

### 4. Configure o `.env`

```powershell
copy .env.example .env
```

Edite o `.env` conforme necessário. Configuração mínima do MySQL:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=jarvis
```

Opcionais:

- **Spotify** (`SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET`) para tocar músicas de verdade
- **Azure Speech** para vozes extras (ex.: Julio)

### 5. Crie o banco de dados

Com o MySQL rodando:

```powershell
py scripts\init_db.py
```

Isso cria o database `jarvis`, as tabelas e um seed inicial (templates da semana + dia de hoje).

### 6. (Opcional) Ajuste seu nome no painel

Em `config/settings.json`:

```json
{
  "user_name": "Silvio",
  "window_title": "TowerHub · JARVIS"
}
```

---

## Como rodar

### Painel principal (recomendado)

```powershell
.\.venv\Scripts\activate
py main.py
```

### Somente voz (CLI)

```powershell
py main.py --voice
py main.py --text
```

### Utilitários

```powershell
py main.py --devices          # microfones
py main.py --voices           # presets de voz
py main.py --voices-all pt    # pesquisar vozes Edge
py main.py --reindex-apps     # reindexar apps do Windows
py scripts\init_db.py         # recriar/seed do banco
```

---

## Uso rápido do assistente

| Situação | O que falar / fazer |
|----------|---------------------|
| Ativar | `Jarvis` ou `Jarvis abre o chrome` |
| Enquanto ativo | `abre o discord`, `que horas são`, `toque lo-fi no spotify` |
| Descansar | `Jarvis descanse` / `descansar Jarvis` |
| Painel | Botão **ACTIVATE / DEACTIVATE** na Voice Interface |
| Tarefas | Adicionar no painel (título + `HH:MM`) — salva no MySQL |

---

## Estrutura do projeto

```text
jarvis/
├── main.py                 # entrada (GUI ou --voice)
├── app/                    # janela, tema, config da UI
├── components/             # painéis do HUD
├── services/               # sistema, voz, MySQL, lembretes
├── core/                   # listener, speaker, brain
├── actions/                # ações no Windows / Spotify
├── config/                 # settings, apps
├── scripts/init_db.py      # cria banco + seed
├── assets/
│   ├── logo/               # logo TowerHub
│   └── fonts/              # Outfit
├── requirements.txt
└── .env.example
```

---

## Banco de dados (`jarvis`)

Principais tabelas:

- `recurring_plans` / `recurring_schedule` / `recurring_tasks` — templates por dia da semana  
- `day_plans` / `day_schedule` / `tasks` — plano e tarefas do dia (dinâmico)

As tarefas do dia são materializadas automaticamente a partir do template semanal.

---

## Stack

- **Python**
- **PySide6** — interface
- **SpeechRecognition + sounddevice** — microfone / STT
- **edge-tts** — voz
- **MySQL + PyMySQL** — tarefas
- **psutil** — monitoramento do sistema
- **winotify** — notificações Windows

---

## Créditos

<p align="center">
  <img src="assets/logo/Logo%20I.A%20TowerHub.png" alt="TowerHub" width="80" />
</p>

<p align="center">
  Desenvolvido por <strong>TowerHub</strong><br/>
  Inteligência artificial aplicada a produtos e automações.
</p>

---

## Licença

Uso pessoal / projeto privado TowerHub. Ajuste esta seção se for publicar o repositório.
