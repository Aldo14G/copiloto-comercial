"""Continuación sintética del caso de diseño; no llama al modelo ni altera los casos originales."""
from . import ficha as F, claude_engine as C


def ejemplo():
    f = F.nueva(empresa="Aceros del Valle · ejemplo", industria="Manufactura", empleados=180)
    f["synthetic"] = True
    mensaje = ("Queremos conservar los dos servidores. Son estándar de rack, ocupan 8U y consumen 0.8 kVA "
               "en conjunto. Solo se conecta esta planta y 100 Mbps nos bastan. El ERP no puede detenerse "
               "más de 2 horas. Aceptamos cotizar alojamiento y enlace como primera etapa; la recuperación "
               "se revisará con el arquitecto. El plazo sería de 12 meses.")
    f["transcript"] = [{"rol": "cliente", "texto": mensaje, "ts": f["creado"]}]
    f.update(C.validate({
        "hechos": [{"clave": "servidores", "valor": 2, "cita": "conservar los dos servidores"},
                   {"clave": "rto_horas", "valor": 2, "cita": "El ERP no puede detenerse más de 2 horas"},
                   {"clave": "espacio_u", "valor": 8, "cita": "ocupan 8U"}],
        "candidatos": [{"sku": "SIM-DC-01", "cantidad": None, "justificacion": "Conservar los servidores fuera de la planta."},
                       {"sku": "SIM-DC-08", "cantidad": None, "justificacion": "Conectar la planta al centro de datos."}],
        "escalamientos": [{"id": "ESC-07", "estado": "confirmado", "evidencia": "más de 2 horas"}]}, mensaje))
    f["resumen_necesidad"] = "Dar continuidad al ERP ante apagones, conservando los servidores. Alojamiento y enlace son una primera etapa separable; la recuperación necesita diseño."
    f["preguntas_pendientes"] = [{"pregunta": "¿Cuántos minutos de información pueden perder?", "motivo": "Definir el RPO y el diseño de recuperación.", "prioridad": 1}]
    f["guion_vendedor"] = "Revisaremos alojamiento y enlace como primera etapa. El arquitecto definirá la recuperación solicitada de 2 horas."
    f["tipo_caso"] = "mixto"
    f["revision"] = 1
    F.guardar(f)
    return f
