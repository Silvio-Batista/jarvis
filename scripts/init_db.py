"""Cria o banco jarvis, tabelas e seed inicial."""

from __future__ import annotations

import os
import sys
from datetime import date, time
from pathlib import Path

import pymysql
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def cfg() -> dict:
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "jarvis"),
        "charset": "utf8mb4",
        "autocommit": True,
    }


SCHEMA = """
CREATE TABLE IF NOT EXISTS recurring_plans (
    weekday TINYINT NOT NULL PRIMARY KEY COMMENT '0=monday ... 6=sunday',
    focus VARCHAR(255) NOT NULL DEFAULT 'Focus'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS recurring_schedule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    weekday TINYINT NOT NULL,
    time_at TIME NOT NULL,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255) NULL,
    INDEX idx_rec_sched_weekday (weekday)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS recurring_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    weekday TINYINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    remind_at TIME NULL,
    sort_order INT NOT NULL DEFAULT 0,
    INDEX idx_rec_tasks_weekday (weekday)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS day_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_date DATE NOT NULL UNIQUE,
    focus VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS day_schedule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_date DATE NOT NULL,
    time_at TIME NOT NULL,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255) NULL,
    INDEX idx_day_sched_date (plan_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_date DATE NOT NULL,
    title VARCHAR(255) NOT NULL,
    remind_at TIME NULL,
    done TINYINT(1) NOT NULL DEFAULT 0,
    notified TINYINT(1) NOT NULL DEFAULT 0,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tasks_date (plan_date),
    INDEX idx_tasks_remind (plan_date, done, notified, remind_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


SEED_RECURRING = {
    0: {
        "focus": "Planejamento da semana",
        "schedule": [
            (time(9, 30), "Daily standup", "Alinhamento do time"),
            (time(14, 0), "Deep work", "Features prioritarias"),
        ],
        "tasks": [
            ("Revisar backlog", time(10, 0)),
            ("Responder e-mails", time(11, 30)),
            ("Commit do dia", time(18, 0)),
        ],
    },
    1: {
        "focus": "Desenvolvimento",
        "schedule": [
            (time(10, 0), "Coding session", "JARVIS / projetos"),
            (time(16, 0), "Code review", "PRs abertas"),
        ],
        "tasks": [
            ("Avancar feature principal", time(10, 30)),
            ("Testes manuais", time(15, 0)),
        ],
    },
    2: {
        "focus": "Integracoes",
        "schedule": [
            (time(11, 0), "Sync com APIs", "Spotify / Azure"),
            (time(17, 0), "Documentacao", "Notas do projeto"),
        ],
        "tasks": [
            ("Atualizar docs do Jarvis", time(12, 0)),
            ("Backup configs", time(18, 30)),
        ],
    },
    3: {
        "focus": "Polimento",
        "schedule": [
            (time(9, 0), "Bugfix", "Issues abertas"),
            (time(15, 30), "UI polish", "Painel JARVIS"),
        ],
        "tasks": [
            ("Corrigir 2 bugs", time(11, 0)),
            ("Melhorar voz / STT", time(16, 0)),
        ],
    },
    4: {
        "focus": "Entrega",
        "schedule": [
            (time(10, 0), "Fechar sprint", "Checklist"),
            (time(16, 0), "Retrospectiva", "O que melhorar"),
        ],
        "tasks": [
            ("Deploy / build final", time(14, 0)),
            ("Planejar proxima semana", time(17, 30)),
        ],
    },
    5: {
        "focus": "Projeto pessoal — JARVIS",
        "schedule": [
            (time(10, 0), "Build session", "TowerHub / JARVIS"),
            (time(15, 0), "Experimentos", "Voz, UI, automacoes"),
        ],
        "tasks": [
            ("Polir painel JARVIS", time(11, 0)),
            ("Configurar lembretes do dia", time(14, 0)),
            ("Testar notificacoes Windows", time(16, 30)),
            ("Pausa / descanso", time(18, 0)),
        ],
    },
    6: {
        "focus": "Descanso + ideias",
        "schedule": [
            (time(11, 0), "Leitura / estudo", "Conteudo tecnico"),
            (time(17, 0), "Organizar semana", "Notas soltas"),
        ],
        "tasks": [
            ("Revisar metas da semana", time(12, 0)),
            ("Listar ideias pro Jarvis", time(18, 0)),
        ],
    },
}


def connect_server():
    conf = cfg()
    return pymysql.connect(
        host=conf["host"],
        port=conf["port"],
        user=conf["user"],
        password=conf["password"],
        charset=conf["charset"],
        autocommit=True,
    )


def connect_db():
    conf = cfg()
    return pymysql.connect(
        host=conf["host"],
        port=conf["port"],
        user=conf["user"],
        password=conf["password"],
        database=conf["database"],
        charset=conf["charset"],
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


def create_database() -> None:
    conf = cfg()
    conn = connect_server()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{conf['database']}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print(f"Database `{conf['database']}` OK")
    finally:
        conn.close()


def create_tables() -> None:
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            for stmt in SCHEMA.split(";"):
                sql = stmt.strip()
                if sql:
                    cur.execute(sql)
        print("Tables OK")
    finally:
        conn.close()


def seed() -> None:
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM recurring_plans")
            if cur.fetchone()["c"] > 0:
                print("Seed ja existe — pulando recurring")
            else:
                for weekday, data in SEED_RECURRING.items():
                    cur.execute(
                        "INSERT INTO recurring_plans (weekday, focus) VALUES (%s, %s)",
                        (weekday, data["focus"]),
                    )
                    for t, title, subtitle in data["schedule"]:
                        cur.execute(
                            "INSERT INTO recurring_schedule (weekday, time_at, title, subtitle) "
                            "VALUES (%s, %s, %s, %s)",
                            (weekday, t, title, subtitle),
                        )
                    for i, (title, remind) in enumerate(data["tasks"]):
                        cur.execute(
                            "INSERT INTO recurring_tasks (weekday, title, remind_at, sort_order) "
                            "VALUES (%s, %s, %s, %s)",
                            (weekday, title, remind, i),
                        )
                print("Recurring seed OK")

            # Materializa o dia de hoje
            today = date.today()
            weekday = today.weekday()  # Monday=0
            cur.execute("SELECT id FROM day_plans WHERE plan_date=%s", (today,))
            if cur.fetchone():
                print(f"Dia {today} ja materializado")
            else:
                cur.execute(
                    "SELECT focus FROM recurring_plans WHERE weekday=%s",
                    (weekday,),
                )
                row = cur.fetchone()
                focus = row["focus"] if row else "Focus"
                cur.execute(
                    "INSERT INTO day_plans (plan_date, focus) VALUES (%s, %s)",
                    (today, focus),
                )
                cur.execute(
                    "SELECT time_at, title, subtitle FROM recurring_schedule WHERE weekday=%s",
                    (weekday,),
                )
                for item in cur.fetchall():
                    cur.execute(
                        "INSERT INTO day_schedule (plan_date, time_at, title, subtitle) "
                        "VALUES (%s, %s, %s, %s)",
                        (today, item["time_at"], item["title"], item["subtitle"]),
                    )
                cur.execute(
                    "SELECT title, remind_at, sort_order FROM recurring_tasks "
                    "WHERE weekday=%s ORDER BY sort_order, id",
                    (weekday,),
                )
                for item in cur.fetchall():
                    cur.execute(
                        "INSERT INTO tasks (plan_date, title, remind_at, sort_order) "
                        "VALUES (%s, %s, %s, %s)",
                        (today, item["title"], item["remind_at"], item["sort_order"]),
                    )
                print(f"Dia {today} ({WEEKDAYS[weekday]}) materializado")
    finally:
        conn.close()


def main() -> int:
    print("Conectando MySQL...")
    create_database()
    create_tables()
    seed()
    print("Pronto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
