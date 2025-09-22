# API de Gestión de Empresas - Prueba Técnica RPA

##  Descripción
API REST desarrollada con Python + Flask + SQLite que permite la gestión de empresas y su estado dentro de procesos automatizados.
Se diseñó como apoyo a un flujo en Automation Anywhere, donde el bot consulta empresas pendientes, actualiza su estado y genera reportes en Excel.

## Endpoints
- `POST /process-data`  
  Recibe un JSON con los datos de una empresa (ej:nombre) y la guarda en la BD con estado inicial `PENDIENTE`.

- `POST /update-status`  
  Actualiza el estado de una empresa (`PENDIENTE`, `PROCESADO`, `ERROR`).

- `GET /empresas`  
  Lista todas las empresas registradas.
  ejemplo ` empresas/estado/Procesado` 

- `GET /export`

  Genera y descarga un archivo Excel (.xlsx) con todas las empresas y su estado.

## Ejecución
1. Instalar dependencias:
   bash
   ip install flask flask-cors openpyxl
2. Ejecutar la API:
    python app.py
3. La API estará disponible en:
    http://127.0.0.1:5000


## Flujo con Automation Anywhere

  Bot consulta empresas con GET [/empresas?estado=PENDIENTE.](http://127.0.0.1:5000/empresas/estado/Pendiente)

  Itera sobre cada empresa y procesa la validación.

  Actualiza su estado con POST /update-status.

  Al finalizar, genera un reporte con GET /export.

  (Opcional) Envía el reporte por correo.

## Tecnologías usadas

  Python 3.13

  Flask (framework API REST)

  SQLite3 (base de datos ligera)

  Openpyxl (generación de reportes Excel)

  Flask-CORS (integración con AA u otros clientes)

## Url del Sheet
  https://docs.google.com/spreadsheets/d/1hoXhp_kO_RBM1C61R12ety2LDLcesl04E26mnbz74Oo/edit?usp=sharing  
