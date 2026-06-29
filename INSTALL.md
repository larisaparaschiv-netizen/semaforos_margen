# 🚀 Guía de Instalación Rápida

Sigue estos pasos para usar la herramienta en tu máquina local.

---

## Paso 1: Clonar/Descargar el Proyecto

```bash
# Si tienes git
git clone <url-del-repo>
cd semaforos_margen

# Si es un ZIP, simplemente extrae y abre la carpeta
cd semaforos_margen
```

---

## Paso 2: Instalar Python (si no lo tienes)

**macOS:**
```bash
brew install python@3.11
```

**Windows:**
Descarga desde https://www.python.org/downloads/

**Linux:**
```bash
sudo apt-get install python3.11
```

Verifica:
```bash
python3 --version  # Debe ser 3.9+
```

---

## Paso 3: Instalar Dependencias

```bash
# En la carpeta del proyecto
pip install -r requirements.txt
```

Esto instala:
- `pandas` → Procesamiento de datos
- `openpyxl` → Lectura de Excel
- `pytest` → Tests

---

## Paso 4: Verificar la Instalación (Opcional)

Ejecuta los tests para asegurar que todo funciona:

```bash
pytest tests/ -v
```

Debería ver **91 tests passing** ✅

---

## Paso 5: Ejecutar el Demo

Ahora puedes ver el proyecto en acción:

```bash
python3 demo.py
```

Esto genera:
- `output/proyectos_margen.csv` → Tabla de proyectos con margen
- `output/metricas_mes.csv` → Detalles mensuales
- `output/alertas.csv` → Validación de datos

Abre los archivos CSV en Excel o tu editor de texto favorito.

---

## Paso 6: Usar con Tus Datos

Una vez que todo funciona, puedes usar el pipeline con tus propios archivos:

```bash
python3 main.py -v \
  --presupuesto tu_presupuesto.xlsx \
  --actuals tu_actuals.csv \
  --horas tu_horas.csv \
  --billing tu_billing.csv \
  --mes 202606
```

Los resultados aparecerán en `output/`

---

## 🐛 Troubleshooting

### "Python no reconocido"
Windows: Usa `python` en lugar de `python3`
```bash
python demo.py
```

### "ModuleNotFoundError: No module named 'pandas'"
Reinstala las dependencias:
```bash
pip install -r requirements.txt
```

### "Error: No such file or directory"
Asegúrate de estar en la carpeta correcta:
```bash
ls   # Debe ver main.py, demo.py, requirements.txt, etc.
```

### Tests fallan
Ejecuta desde la carpeta raíz del proyecto:
```bash
pwd   # Verifica que estés en semaforos_margen/
pytest tests/ -v
```

---

## 📖 Próximos Pasos

1. **Leer la documentación:**
   - `README.md` → Uso y características
   - `SPEC.md` → Especificación técnica

2. **Explorar el código:**
   - `src/loaders/` → Cómo se leen los datos
   - `src/metrics.py` → Cálculo del margen y semáforo
   - `src/validate.py` → Validación de datos

3. **Personalizar:**
   - Editar `config/settings.py` para cambiar umbrales
   - Crear tus propios loaders si necesitas otras fuentes de datos

---

## ✅ Checklist Final

- [ ] Python 3.9+ instalado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Tests pasan (`pytest tests/ -v`)
- [ ] Demo ejecuta correctamente (`python3 demo.py`)
- [ ] Archivos CSV aparecen en `output/`

¡Listo! Ya puedes usar la herramienta en local.

---

**¿Preguntas?** Ver README.md o SPEC.md

**¿Bugs?** Revisa los tests para ejemplos de uso correcto.
