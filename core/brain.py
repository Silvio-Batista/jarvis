import random
import re
from datetime import datetime

from actions.computer import ComputerActions
from core.listener import extrair_comando


class Brain:
    """Cérebro conversacional: conversa + ações, sem parecer um terminal."""

    def __init__(self, actions: ComputerActions, nome: str = "Jarvis") -> None:
        self.actions = actions
        self.nome = nome

    def pensar(self, frase: str, wake_words: list[str] | None = None) -> str:
        bruto = (frase or "").strip()
        if not bruto:
            return random.choice(
                [
                    "Estou aqui. Pode falar.",
                    "Pode dizer, estou ouvindo.",
                    "Sim? Em que posso ajudar?",
                ]
            )

        # Remove wake word se veio junto
        if wake_words:
            depois = extrair_comando(bruto, wake_words)
            if depois is not None:
                bruto = depois if depois else ""

        texto = bruto.lower().strip()
        texto = re.sub(r"\s+", " ", texto)

        # Só o nome / silêncio após wake
        if not texto:
            return random.choice(
                [
                    "Estou aqui.",
                    "Pode falar.",
                    "Diga aí.",
                    "Ouvindo.",
                ]
            )

        # Conversa pura
        chat = self._conversa(texto)
        if chat is not None:
            return chat

        # Saudação + pedido no mesmo fôlego: "bom dia, abre o chrome"
        saudacao, resto = self._separar_saudacao(texto)
        if resto:
            resultado = self.actions.executar(resto)
            resultado = self._humanizar_acao(resultado, resto)
            if saudacao:
                return f"{saudacao} {resultado}"
            return resultado

        # Sem pedido claro: tenta ação no texto inteiro
        resultado = self.actions.executar(texto)
        return self._humanizar_acao(resultado, texto)

    def _conversa(self, texto: str) -> str | None:
        if re.fullmatch(r"(oi|ola|olá|hey|eai|e ai|iae|fala)", texto):
            return random.choice(
                [
                    "Oi. Em que posso ajudar?",
                    "Olá. Pode falar.",
                    "Oi! Estou por aqui.",
                ]
            )

        if any(p in texto for p in ("bom dia", "boa tarde", "boa noite")):
            # Se tem mais coisa além da saudação, deixa o fluxo principal tratar
            resto = self._separar_saudacao(texto)[1]
            if resto:
                return None
            agora = datetime.now().hour
            if "bom dia" in texto or agora < 12:
                return "Bom dia. Como posso ajudar?"
            if "boa tarde" in texto or agora < 18:
                return "Boa tarde. Pode falar."
            return "Boa noite. Estou à disposição."

        if any(
            p in texto
            for p in (
                "tudo bem",
                "tudo bom",
                "como voce esta",
                "como você está",
                "como vai",
                "beleza?",
            )
        ):
            return random.choice(
                [
                    "Tudo certo por aqui. E você?",
                    "Funcionando bem. Precisa de alguma coisa?",
                    "Tudo bem. Manda o que quiser.",
                ]
            )

        if any(p in texto for p in ("obrigado", "obrigada", "valeu", "thanks")):
            return random.choice(
                [
                    "Por nada.",
                    "Sempre.",
                    "Disponha.",
                ]
            )

        if any(
            p in texto
            for p in (
                "quem e voce",
                "quem é você",
                "qual seu nome",
                "o que voce e",
                "o que você é",
            )
        ):
            return f"Eu sou o {self.nome}, seu assistente no computador."

        if any(p in texto for p in ("voce me ouve", "está ai", "esta ai", "ainda ai", "me escuta")):
            return random.choice(["Estou aqui.", "Ouvindo sim.", "Pode falar."])

        if any(p in texto for p in ("me ajuda", "preciso de ajuda", "socorro")):
            return (
                "Claro. Pode pedir para abrir apps, tocar música no Spotify, "
                "pesquisar algo ou controlar o volume."
            )

        if texto in {"ok", "okay", "certo", "entendi", "blz", "beleza", "show", "massa"}:
            return random.choice(["Certo.", "Ok.", "Perfeito."])

        return None

    def _separar_saudacao(self, texto: str) -> tuple[str | None, str]:
        padrao = re.compile(
            r"^(bom dia|boa tarde|boa noite|oi|ola|olá)[,!]?\s*(.*)$",
            re.IGNORECASE,
        )
        match = padrao.match(texto)
        if not match:
            return None, texto

        tipo = match.group(1).lower()
        resto = (match.group(2) or "").strip(" ,.-")
        if tipo == "bom dia":
            falas = "Bom dia."
        elif tipo == "boa tarde":
            falas = "Boa tarde."
        elif tipo == "boa noite":
            falas = "Boa noite."
        else:
            falas = "Oi."
        return falas, resto

    def _humanizar_acao(self, resultado: str, pedido: str) -> str:
        """Suaviza respostas mecânicas das ações."""
        r = (resultado or "").strip()
        baixo = r.lower()

        if baixo.startswith("abrindo "):
            alvo = r[8:].rstrip(".")
            return random.choice(
                [
                    f"Claro, abrindo {alvo}.",
                    f"Beleza, {alvo} na tela.",
                    f"Abrindo {alvo} pra você.",
                ]
            )

        if baixo.startswith("tocando "):
            return random.choice(
                [
                    r.replace("Tocando", "Colocando").rstrip(".") + ".",
                    "Fechado, já estou colocando.",
                    r,
                ]
            )

        if "pesquisei no google" in baixo:
            return random.choice(
                [
                    "Deixa eu olhar isso no Google pra você.",
                    "Pesquisei e abri o resultado.",
                    "Pronto, abri a pesquisa.",
                ]
            )

        if baixo.startswith("pesquisando "):
            return random.choice(
                [
                    "Pesquisando isso agora.",
                    "Já estou buscando.",
                    r,
                ]
            )

        if "nao entendi" in baixo or "não entendi" in baixo:
            return random.choice(
                [
                    "Não peguei direito. Pode repetir de outro jeito?",
                    "Hmm, não entendi. Quer abrir algo, tocar música ou pesquisar?",
                    "Pode falar de novo? Tipo: abre o Discord, ou toca lo-fi no Spotify.",
                ]
            )

        if baixo in {"pois nao?", "pois não?"}:
            return random.choice(["Pode falar.", "Estou ouvindo.", "Diga aí."])

        return r
