"""Generar los cuatro entregables del ejemplo sin red ni cambios en las fichas reales."""
import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from copiloto import ficha as F
from copiloto.demo import ejemplo
from copiloto.export import archivos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destino", type=Path)
    args = parser.parse_args()
    args.destino.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as directorio, patch.object(F, "FICHAS", Path(directorio)):
        f = ejemplo()
        f["case_id"] = "EJEMPLO-SINTETICO"
        F.confirmar(f, [{"sku": "SIM-DC-01", "cantidad": 1}, {"sku": "SIM-DC-08", "cantidad": 1}])
        q = F.cotizacion(f, True)
        for nombre, contenido in archivos(f, q).items():
            (args.destino / nombre).write_bytes(contenido)
            print(nombre)
        print(f"Mensual: {q['totales']['mensual']}; único: {q['totales']['unico']}; parcial: {q['parcial']}")


if __name__ == "__main__":
    main()
