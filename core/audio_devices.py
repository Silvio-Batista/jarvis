import sounddevice as sd


def listar_dispositivos_entrada() -> list[dict]:
    dispositivos = []
    for idx, device in enumerate(sd.query_devices()):
        if device["max_input_channels"] > 0:
            dispositivos.append(
                {
                    "index": idx,
                    "name": device["name"],
                    "hostapi": sd.query_hostapis(device["hostapi"])["name"],
                    "channels": device["max_input_channels"],
                    "samplerate": int(device["default_samplerate"]),
                    "default": idx == sd.default.device[0],
                }
            )
    return dispositivos


def resolver_microfone(preferencia: str | int | None = None) -> tuple[int, dict]:
    """Resolve índice do microfone por nome parcial ou índice."""
    entradas = listar_dispositivos_entrada()
    if not entradas:
        raise RuntimeError("Nenhum microfone encontrado.")

    if preferencia is None or preferencia == "" or preferencia == "default":
        padrao = sd.default.device[0]
        info = sd.query_devices(padrao)
        return padrao, info

    if isinstance(preferencia, int) or str(preferencia).isdigit():
        idx = int(preferencia)
        return idx, sd.query_devices(idx)

    termo = str(preferencia).lower()
    # Prefere API MME (mais estável no Windows para captura simples)
    mme = [d for d in entradas if termo in d["name"].lower() and d["hostapi"] == "MME"]
    if mme:
        idx = mme[0]["index"]
        return idx, sd.query_devices(idx)

    for device in entradas:
        if termo in device["name"].lower():
            return device["index"], sd.query_devices(device["index"])

    disponiveis = ", ".join(f'{d["index"]}:{d["name"]}' for d in entradas[:12])
    raise RuntimeError(
        f'Microfone "{preferencia}" não encontrado. Disponíveis: {disponiveis}'
    )


def imprimir_dispositivos() -> None:
    print("Dispositivos de entrada (microfone):\n")
    for device in listar_dispositivos_entrada():
        marca = " <- padrão" if device["default"] else ""
        print(
            f'  [{device["index"]:>2}] {device["name"]} '
            f'({device["hostapi"]}, {device["samplerate"]} Hz){marca}'
        )
    print("\nPara escolher, edite config.yaml -> assistente.microfone")
    print('Exemplo: microfone: "fifine"  ou  microfone: 1')
